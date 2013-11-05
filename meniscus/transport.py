"""
The transport module defines the classes that serve as the transport layer for
Meniscus when passing log messages between nodes.  ZeroMQ is used as the
transport mechanism.
"""

from oslo.config import cfg
import simplejson as json
import zmq

import meniscus.config as config
from meniscus import env


_LOG = env.get_logger(__name__)


# ZMQ configuration options
_ZMQ_GROUP = cfg.OptGroup(
    name='zmq_in', title='ZeroMQ Input Options')

config.get_config().register_group(_ZMQ_GROUP)

_ZMQ_OPTS = [
    cfg.ListOpt('zmq_upstream_hosts',
                default=['127.0.0.1:5000'],
                help='list of upstream host:port pairs to poll for '
                     'zmq messages')
]

config.get_config().register_opts(_ZMQ_OPTS, group=_ZMQ_GROUP)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)

_CONF = config.get_config()


class ZeroMQReceiver(object):
    """
    ZeroMQReceiver allows for messages to be received by pulling
    messages over a zmq socket from an upstream host.  This client may
    connect to multiple upstream hosts.
    """

    def __init__(self, connect_host_tuples):
        """
        Creates an instance of the ZeroMQReceiver.

        :param connect_host_tuples: [(host, port), (host, port)],
        for example [('127.0.0.1', '5000'), ('127.0.0.1', '5001')]
        """
        self.upstream_hosts = [
            "tcp://{}:{}".format(*host_tuple)
            for host_tuple in connect_host_tuples]
        self.socket_type = zmq.PULL
        self.context = None
        self.socket = None
        self.connected = False

    def connect(self):
        """
        Connect the receiver to upstream hosts.  Create a zmq.Context
        and a zmq.PULL socket, and is connect the socket to all
        specified host:port tuples.
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(self.socket_type)

        for host in self.upstream_hosts:
            self.socket.connect(host)

        self.connected = True

    def get(self):
        """
        Read a message form the zmq socket and return
        """
        if not self.connected:
            raise zmq.error.ZMQError(
                "ZeroMQReceiver is not connected to a socket")
        return self.socket.recv()

    def close(self):
        """
        Close the zmq socket
        """
        if self.connected:
            self.socket.close()
            self.context.destroy()
            self.socket = None
            self.context = None
            self.connected = False


def new_zqm_receiver():
    """
    Factory method creates a new instance of ZeroMQReceiver to connect to all
    host:ports listed in zmq_upstream_hosts from meniscus config.
    """

    #build a list of (host, port) tuples from config
    upstream_hosts = [
        (host_port_str.split(':'))
        for host_port_str in _CONF.zmq_in.zmq_upstream_hosts
    ]

    return ZeroMQReceiver(upstream_hosts)


class ZeroMQInputServer(object):
    """
    ZeroMQInputServer is a base class creates an IO Loop that continues
    to pull messages through a ZeroMQReceiver for processing.
    This class should be inherited and the process_msg() method overridden in
    order to implement the desired behavior.
    """

    def __init__(self, zmq_receiver):
        """
        Creates a new instance of ZeroMQInputServer by setting the receiver to
        be used to pull messages.

        :param zmq_receiver: an instance of ZeroMQReceiver
        """
        self.zmq_receiver = zmq_receiver
        self._stop = True

    def start(self):
        """
        Connect the ZeroMQReceiver and start the server IO loop to
        process messages. The receiver is connected here so that this method
        can easily be passed as a runnable to a child process, as zmq should
        not share context and sockets between a parent and child process.
        """
        self.zmq_receiver.connect()
        self._stop = False

        while not self._stop:
            self.process_msg()

    def stop(self):
        """
        set the server control variable that will break the IO Loop
        """
        self._stop = True

    def process_msg(self):
        """
        This method should be overridden to implement the desired message
        processing.  To retrieve the message for processing you can call:
        >>>  msg = self._get_msg()
        """
        pass

    def _get_msg(self):
        """
        Pulls a JSON message received over the ZeroMQ socket.  This call will
        block until a message is received.
        """
        try:
            msg = self.zmq_receiver.get()
            return json.loads(msg)
        except Exception as ex:
            _LOG.exception(ex)


class ZeroMQCaster(object):
    """
    ZeroMQCaster allows for messages to be sent downstream by pushing
    messages over a zmq socket to downstream clients.  If multiple clients
    connect to this PUSH socket the messages will be load balanced evenly
    across the clients.
    """

    def __init__(self, bind_host_tuple):
        """
        Creates an instance of the ZeroMQCaster.  A zmq PUSH socket is
        created and is bound to the specified host:port.

        :param bind_host_tuple: (host, port), for example ('127.0.0.1', '5000')
        """

        self.socket_type = zmq.PUSH
        self.bind_host = 'tcp://{0}:{1}'.format(*bind_host_tuple)
        self.context = None
        self.socket = None
        self.bound = False

    def bind(self):
        """
        Bind the ZeroMQCaster to a host:port to push out messages.
        Create a zmq.Context and a zmq.PUSH socket, and bind the
        socket to the specified host:port
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(self.socket_type)
        self.socket.bind(self.bind_host)
        self.bound = True

    def cast(self, msg):
        """
        Sends a message over the zmq PUSH socket
        """
        if not self.bound:
            raise zmq.error.ZMQError(
                "ZeroMQCaster is not bound to a socket")
        try:
            self.socket.send(msg)
        except Exception as ex:
            _LOG.exception(ex)

    def close(self):
        """
        Close the zmq socket
        """
        if self.bound:
            self.socket.close()
            self.context.destroy()
            self.socket = None
            self.context = None
            self.bound = False


