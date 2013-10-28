import meniscus.api.correlation.correlation_exceptions as errors
import simplejson as json

import zmq

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


class ZeroMQReciever(object):

    def __init__(self, connect_host_tuples):
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.PULL)

        for host_tuple in connect_host_tuples:
            self.sock.connect("tcp://{}:{}".format(*host_tuple))

    def get(self):
        return self.sock.recv()


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

        self._stop = False

        while not self._stop:
            self.process_msg()

    def process_msg(self):
        msg = self.get_msg()
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

    def get_msg(self):
        try:
            msg = self.zmq_sock.get()
            return json.loads(msg)
        except Exception as ex:
            _LOG.exception(ex)



