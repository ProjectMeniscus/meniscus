from portal.input.rfc5424 import SyslogMessageHandler

from meniscus.api.tenant.resources import MESSAGE_TOKEN
from meniscus.api.correlation import correlator
import meniscus.api.correlation.correlation_exceptions as errors

class MessageHandler(SyslogMessageHandler):

    def __init__(self, router):
        self.msg = b''
        self.msg_head = None
        self.outbound = None
        self.msg_count = 0
        self.router = router

    def message_head(self, message_head):
        self.msg_count += 1
        self.msg_head = message_head

    def message_part(self, message_part):
        self.msg += message_part

    def message_complete(self, last_message_part):
        full_message = self.msg + last_message_part
        syslog_message = self.msg_head.as_dict()
        syslog_message['message'] = full_message.decode('utf-8')
        outbound_message = self._correlate_syslog_message(syslog_message)
        self.router.route_message(outbound_message)
        self.msg_head = None
        self.msg = b''

    def _correlate_syslog_message(self, syslog_message):
        #remove meniscus tenant id and message token
        # from the syslog structured data
        try:
            tenant_data = syslog_message['sd'].pop('meniscus')
            tenant_id = tenant_data['tenant']
            message_token = tenant_data['token']

        #if there is a key error then the syslog message did
        #not contain necessary credential information
        except KeyError:
            raise errors.MessageValidationError(
                'tenant_id or message token not provided')

        #validate the tenant and the message token
        tenant_identification = correlator.TenantIdentification(
            tenant_id, message_token)
        tenant = tenant_identification.get_validated_tenant()

        cee_message = self._convert_message_cee(syslog_message)
        correlator.add_correlation_info_to_message(cee_message)

        return cee_message

    def _convert_message_cee(self, syslog_message):
        cee_message = dict()

        cee_message['time'] = syslog_message['timestamp']
        cee_message['host'] =  syslog_message['hostname']
        cee_message['pname'] =  syslog_message['appname']
        cee_message['pri'] = syslog_message['priority']
        cee_message['ver'] =  syslog_message['version']
        cee_message['pid'] =  syslog_message['processid']
        cee_message['msgid'] =  syslog_message['messageid']
        cee_message['msg'] =  syslog_message['message']

        cee_message['native']  = syslog_message['sd']

        return cee_message
