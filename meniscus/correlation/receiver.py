from meniscus import env
from meniscus.correlation import correlator
from meniscus.storage import dispatch
from meniscus import transport

from meniscus.normalization.normalizer import *

_LOG = env.get_logger(__name__)


class CorrelationInputServer(transport.ZeroMQInputServer):

    def process_msg(self):
        msg = self._get_msg()
        cee_message = correlator.correlate_src_message(msg)

        try:
            if should_normalize(cee_message):
                # send the message to normalization then to
                # the data dispatch
                normalize_message.apply_async(
                    (cee_message,),
                    link=dispatch.persist_message.subtask())
            else:
                dispatch.persist_message(cee_message)
        except Exception:
            _LOG.exception('unable to place persist_message '
                           'task on queue')


def new_correlation_input_server():
    zmq_receiver = transport.new_zqm_receiver()
    return CorrelationInputServer(zmq_receiver)
