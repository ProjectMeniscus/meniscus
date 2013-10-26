import meniscus.api.correlation.correlation_exceptions as errors
import simplejson as json

from portal.input.zmq_in import ZeroMQReciever

from oslo.config import cfg

from meniscus import env
from meniscus.storage import dispatch
from meniscus.api.correlation import correlator

from meniscus.normalization.normalizer import *

# ZMQ configuration options
_CONF = cfg.CONF

_ZMQ_GROUP = cfg.OptGroup(
    name='zmq_in', title='ZeroMQ Input Options')

_CONF.register_group(_ZMQ_GROUP)

_ZMQ_OPTS = [
    cfg.ListOpt('zmq_downstream_hosts',
                help='list of downstream host:port pairs to poll for '
                'zmq messages')
]

_CONF.register_opts(_ZMQ_OPTS)

_LOG = env.get_logger(__name__)


def new_zqm_input_server(conf):
    downstream_hosts = list()
    for host_port_str in conf.zmq_in.zmq_downstream_hosts:
        downstream_hosts.append(host_port_str.split(':'))

    return ZeroMQInputServer(ZeroMQReciever(downstream_hosts))


class ZeroMQInputServer(object):

    def __init__(self, zmq_reciever):
        self.zmq_sock = zmq_reciever

    def stop(self):
        self._stop = True

    def start(self):
        read = 0
        msg = ''

        self._stop = False

        while not self._stop:
            self.process_msg()

    def process_msg(self):
        msg = self.get_msg()
        print(msg)
        cee_message = _correlate_src_message(msg)

        try:
            if should_normalize(cee_message):
                # send the message to normalization then to
                # the data dispatch
                normalize_message.apply_async(
                    (cee_message,),
                    link=dispatch.persist_message.subtask())
            else:
                dispatch.persist_message(cee_message)
        except Exception as ex:
            _LOG.exception('unable to place persist_message '
                           'task on queue')

    def get_msg(self):
        msg_dict = None

        try:
            msg = self.zmq_sock.get()
            return json.loads(msg)
        except Exception as ex:
            _LOG.exception(ex)


def _correlate_src_message(src_message):
    #remove meniscus tenant id and message token
    # from the syslog structured data
    try:
        tenant_data = src_message['sd'].pop('meniscus')
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

    cee_message = _convert_message_cee(src_message)
    correlator.add_correlation_info_to_message(tenant, cee_message)

    return cee_message


def _convert_message_cee(src_message):
    cee_message = dict()

    cee_message['time'] = src_message['timestamp']
    cee_message['host'] = src_message['hostname']
    cee_message['pname'] = src_message['appname']
    cee_message['pri'] = src_message['priority']
    cee_message['ver'] = src_message['version']
    cee_message['pid'] = src_message['processid']
    cee_message['msgid'] = src_message['messageid']
    cee_message['msg'] = src_message['message']

    cee_message['native'] = src_message['sd']

    return cee_message
