from meniscus import env
from meniscus.correlation import correlator
from meniscus.storage import dispatch
from meniscus import transport

from meniscus.normalization.normalizer import *

_LOG = env.get_logger(__name__)


class CorrelationInputServer(transport.ZeroMQInputServer):

    def process_msg(self):
        msg = self._get_msg()

        try:
            correlator.correlate_syslog_message.delay(msg)
        except Exception:
            _LOG.exception('unable to place persist_message task on queue')


def new_correlation_input_server():
    zmq_receiver = transport.new_zqm_receiver()
    return CorrelationInputServer(zmq_receiver)
