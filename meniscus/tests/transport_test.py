import unittest

from mock import MagicMock, patch
import simplejson as json

from meniscus import transport


class WhenTestingZeroMqReceiver(unittest.TestCase):

    def setUp(self):
        self.host = '127.0.0.1'
        self.port = '5000'
        self.connect_host_tuple = (self.host, self.port)
        self.connect_host_tuples = [self.connect_host_tuple]
        self.validate_hosts = [
            "tcp://{}:{}".format(*host_tuple)
            for host_tuple in self.connect_host_tuples]
        self.zmq_mock = MagicMock()
        self.zmq_mock.PULL = transport.zmq.PULL

        #set up the mock of the socket object
        self.socket_mock = MagicMock()
        #create a mock for the zmq context object
        self.context_mock = MagicMock()
        #have the mock context object return the mock socket
        # when the context.socket() method is called
        self.context_mock.socket.return_value = self.socket_mock
        #have the mock zmq module return the mocked context object
        # when the Context() constructor is called
        self.zmq_mock.Context.return_value = self.context_mock

        self.receiver = transport.ZeroMQReceiver(self.connect_host_tuples)

    def test_constructor(self):
        self.assertEqual(
            self.receiver.upstream_hosts,
            self.validate_hosts)
        self.assertEqual(self.receiver.socket_type, transport.zmq.PULL)
        self.assertIsNone(self.receiver.context)
        self.assertIsNone(self.receiver.socket)
        self.assertFalse(self.receiver.connected)

    def test_connect(self):
        with patch('meniscus.transport.zmq', self.zmq_mock):
            self.receiver.connect()
        self.context_mock.socket.assert_called_once_with(transport.zmq.PULL)
        self.socket_mock.connect.assert_called_once_with(
            'tcp://{0}:{1}'.format(self.host, self.port))
        self.assertTrue(self.receiver.connected)

    def test_get(self):
        with patch('meniscus.transport.zmq', self.zmq_mock):
            self.receiver.connect()
        self.receiver.get()
        self.socket_mock.recv.assert_called_once()

        self.receiver.close()
        with self.assertRaises(transport.zmq.error.ZMQError):
            self.receiver.get()

    def test_close(self):
        with patch('meniscus.transport.zmq', self.zmq_mock):
            self.receiver.connect()
        self.receiver.close()
        self.socket_mock.close.assert_called_once_with()
        self.context_mock.destroy.assert_called_once_with()
        self.assertIsNone(self.receiver.context)
        self.assertIsNone(self.receiver.socket)
        self.assertFalse(self.receiver.connected)


class WhenTestingReceiverFactory(unittest.TestCase):

    def setUp(self):
        self.conf_mock = MagicMock()
        self.conf_mock.zmq_in.zmq_upstream_hosts = [
            '127.0.0.1:5000', '127.0.0.1:5003']
        self.upstream_host_tuples = [
            (host_port_str.split(':'))
            for host_port_str in self.conf_mock.zmq_in.zmq_upstream_hosts
        ]
        self.validate_hosts = [
            "tcp://{}:{}".format(*host_tuple)
            for host_tuple in self.upstream_host_tuples]
        self.zmq_mock = MagicMock()

    def test_new_zmq_receiver(self):
        with patch('meniscus.transport._CONF', self.conf_mock):
            zmq_receiver = transport.new_zqm_receiver()
        self.assertIsInstance(zmq_receiver, transport.ZeroMQReceiver)
        self.assertEqual(zmq_receiver.upstream_hosts, self.validate_hosts)


class WhenTestingZeroMQInputServer(unittest.TestCase):
    def setUp(self):
        self.receiver_mock = MagicMock()

        #create a test class from the base class and override process_msg
        class TestInputServer(transport.ZeroMQInputServer):
            def process_msg(self):
                self.test_stop = self._stop
                self.process_msg_called = True
                self.stop()

        self.server = TestInputServer(self.receiver_mock)
        self.msg = {"key": "value"}
        self.valid_json_msg = json.dumps(self.msg)
        self.bad_msg = "gigdiu"

    def test_constructor(self):
        self.assertEqual(self.server.zmq_receiver, self.receiver_mock)
        self.assertTrue(self.server._stop)

    def test_start_stop(self):
        self.assertTrue(self.server._stop)
        self.server.start()
        self.receiver_mock.connect.assert_called_once_with()
        self.assertFalse(self.server.test_stop)
        self.assertTrue(self.server._stop)
        self.assertTrue(self.server.process_msg_called)

    def test_get_msg_returns_dict(self):
        self.receiver_mock.get.return_value = self.valid_json_msg
        msg = self.server._get_msg()
        self.receiver_mock.get.assert_called_once_with()
        self.assertEquals(msg, self.msg)


class WhenTestingZeroMqCaster(unittest.TestCase):

    def setUp(self):
        self.host = '127.0.0.1'
        self.port = '5000'
        self.bind_host_tuple = (self.host, self.port)
        self.msg = '{"key": "value"}'
        self.zmq_mock = MagicMock()
        self.zmq_mock.PUSH = transport.zmq.PUSH

        #set up the mock of the socket object
        self.socket_mock = MagicMock()
        #create a mock for the zmq context object
        self.context_mock = MagicMock()
        #have the mock context object return the mock socket
        # when the context.socket() method is called
        self.context_mock.socket.return_value = self.socket_mock
        #have the mock zmq module return the mocked context object
        # when the Context() constructor is called
        self.zmq_mock.Context.return_value = self.context_mock

        self.caster = transport.ZeroMQCaster(self.bind_host_tuple)

    def test_constructor(self):
        self.assertEqual(self.caster.socket_type, transport.zmq.PUSH)
        self.assertEqual(
            self.caster.bind_host,
            'tcp://{0}:{1}'.format(self.host, self.port))
        self.assertIsNone(self.caster.context)
        self.assertIsNone(self.caster.socket)
        self.assertFalse(self.caster.bound)

    def test_bind(self):
        with patch('meniscus.transport.zmq', self.zmq_mock):
            self.caster.bind()
        self.context_mock.socket.assert_called_once_with(transport.zmq.PUSH)
        self.socket_mock.bind.assert_called_once_with(
            'tcp://{0}:{1}'.format(self.host, self.port))
        self.assertTrue(self.caster.bound)

    def test_cast(self):
        with patch('meniscus.transport.zmq', self.zmq_mock):
            self.caster.bind()
        self.caster.cast(self.msg)
        self.socket_mock.send.assert_called_once_with(self.msg)

        self.caster.close()
        with self.assertRaises(transport.zmq.error.ZMQError):
            self.caster.cast(self.msg)

    def test_close(self):
        with patch('meniscus.transport.zmq', self.zmq_mock):
            self.caster.bind()
        self.caster.close()
        self.socket_mock.close.assert_called_once_with()
        self.context_mock.destroy.assert_called_once_with()
        self.assertIsNone(self.caster.context)
        self.assertIsNone(self.caster.socket)
        self.assertFalse(self.caster.bound)


class WhenIntegrationTestingTransport(unittest.TestCase):

    def setUp(self):
        self.host = '127.0.0.1'
        self.port = '5000'
        self.host_tuple = (self.host, self.port)
        self.connect_host_tuples = [self.host_tuple]

        self.msg = {"key": "value"}
        self.msg_json = json.dumps(self.msg)

    def test_message_transport_over_zmq(self):
        self.caster = transport.ZeroMQCaster(self.host_tuple)
        self.caster.bind()
        self.receiver = transport.ZeroMQReceiver(self.connect_host_tuples)

        class TestInputServer(transport.ZeroMQInputServer):
            def process_msg(self):
                self.test_stop = self._stop
                self.process_msg_called = True
                msg = self._get_msg()
                self.stop()

        self.server = TestInputServer(self.receiver)
        from multiprocessing import Process
        self.server_proc = Process(target=self.server.start)
        self.server_proc.start()
        import time
        time.sleep(1)
        self.caster.cast(self.msg_json)
        time.sleep(2)
        self.server_proc.terminate()

    def tearDown(self):
        self.server_proc.terminate()


if __name__ == '__main__':
    unittest.main()