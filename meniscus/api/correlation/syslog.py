from portal.input.usyslog import SyslogMessageHandler

from meniscus.api.correlation import correlator
import meniscus.api.correlation.correlation_exceptions as errors
from meniscus import env
from meniscus import config
from oslo.config import cfg
from meniscus.storage import dispatch
from meniscus.normalization.normalizer import *


# Syslog server options
syslog_group = cfg.OptGroup(
    name='syslog_server', title='Syslog server options')
config.get_config().register_group(syslog_group)

config.get_config().register_opts(
    [cfg.IntOpt('max_messages_per_stream',
        default=-1,
        help="""Sets the number of messages to consume per stream until the
             the server should break the connection to force a reconenct
             and hopefully a loadbalanced node rotation for the client.
             """
        )],
        group=syslog_group)

_LOG = env.get_logger(__name__)


class MessageHandler(SyslogMessageHandler):

    def __init__(self, conf):
        self.msg = b''
        self.msg_head = None
        self.outbound = None
        self.msg_count = 0
        self.max_messages = conf.syslog_server.max_messages_per_stream
        self.has_max = self.max_messages > 0

    def message_head(self, message_head):
        if self.has_max:
            self.msg_count += 1
        self.msg_head = message_head

    def message_part(self, message_part):
        self.msg += message_part

    def message_complete(self, last_message_part):
        full_message = self.msg + last_message_part
        syslog_message = self.msg_head.as_dict()
        syslog_message['message'] = full_message.decode('utf-8')
        cee_message = _correlate_syslog_message(syslog_message)

        try:
            if should_normalize(cee_message):
                #send the message to normalization then to the data dispatch
                normalize_message.apply_async(
                    (cee_message,),
                    link=dispatch.persist_message.subtask())
            else:
                dispatch.persist_message(cee_message)
        except Exception as ex:
            _LOG.exception('unable to place persist_message task on queue')

        if self.has_max and self.msg_count > self.max_messages:
            return True # True means break the current connection

        #reset for next message
        self.msg_head = None
        self.msg = b''

    def exception(self, ex):
        _LOG.debug('syslog parser error: {0}'.format(ex.message))


def _correlate_syslog_message(syslog_message):
    #remove meniscus tenant id and message token
    # from the syslog structured data
    try:
        tenant_data = syslog_message['sd'].pop('meniscus')
        tenant_id = tenant_data['tenant']
        message_token = tenant_data['token']

    #if there is a key error then the syslog message did
    #not contain necessary credential information
    except KeyError:
        message = 'tenant_id or message token not provided'
        _LOG.debug('Message validation failed: {0}'.format(message))
        raise errors.MessageValidationError(message)

    #validate the tenant and the message token
    tenant_identification = correlator.TenantIdentification(
        tenant_id, message_token)
    tenant = tenant_identification.get_validated_tenant()

    cee_message = _convert_message_cee(syslog_message)
    correlator.add_correlation_info_to_message(tenant, cee_message)

    return cee_message


def _convert_message_cee(syslog_message):
    cee_message = dict()

    cee_message['time'] = syslog_message['timestamp']
    cee_message['host'] = syslog_message['hostname']
    cee_message['pname'] = syslog_message['appname']
    cee_message['pri'] = syslog_message['priority']
    cee_message['ver'] = syslog_message['version']
    cee_message['pid'] = syslog_message['processid']
    cee_message['msgid'] = syslog_message['messageid']
    cee_message['msg'] = syslog_message['message']

    cee_message['native'] = syslog_message['sd']

    return cee_message
