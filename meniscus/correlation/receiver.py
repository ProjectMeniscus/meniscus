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
            #Queue the message for correlation
            correlator.correlate_syslog_message.delay(msg)
        except Exception:
            _LOG.exception('unable to place persist_message task on queue')


def new_correlation_input_server():
    """
    Create a correlation input server for receiving json messages form the
    syslog parser of ZeroMQ
    """
    zmq_receiver = transport.new_zmq_receiver()
    return CorrelationInputServer(zmq_receiver)
