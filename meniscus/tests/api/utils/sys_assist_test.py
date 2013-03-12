import unittest
import sys
import meniscus.api.utils.sys_assist as sys_assist
from mock import MagicMock
from mock import patch
import __builtin__


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingSysAssist())
    return suite


class WhenTestingSysAssist(unittest.TestCase):
    def setUp(self):
        self.platform = 'linux'
        self.meminfo = ["MemTotal:        4196354 kB\n",
                        "MemFree:         1232352 kB\n",
                        "Buffers:          151176 kB\n"]
        self.statvfs = MagicMock()
        self.statvfs.f_blocks = 26214400
        self.statvfs.f_frsize = 4096

    def test_get_sys_mem_total_kB_should_return_4196354(self):
        with patch.object(sys_assist.sys, 'platform', self.platform), \
                patch.object(__builtin__, 'open', return_value=self.meminfo):
            mem_total = sys_assist.get_sys_mem_total_kB()
            self.assertEqual(mem_total, 4196354)

    def test_get_sys_mem_total_MB_should_return_4098(self):
        with patch.object(sys_assist.sys, 'platform', self.platform), \
                patch.object(__builtin__, 'open', return_value=self.meminfo):
            mem_total = sys_assist.get_sys_mem_total_MB()
            self.assertEqual(mem_total, 4098)

    def test_get_disk_size_GB_should_return_100(self):
        with patch.object(sys_assist.sys, 'platform', self.platform), \
             patch.object(sys_assist.os, 'statvfs', return_value=self.statvfs):
            mem_total = sys_assist.get_disk_size_GB()
            self.assertEqual(mem_total, 100)

    def test_get_cpu_core_count_should_return_4(self):
        with patch.object(sys_assist.multiprocessing, 'cpu_count',
                          return_value=4):
            cpu_count = sys_assist.get_cpu_core_count()
            self.assertEqual(cpu_count, 4)

    def test_get_interface_ip(self):

        with patch.object(sys_assist.socket, 'socket',
                          MagicMock()), \
            patch.object(sys_assist.fcntl, 'ioctl',
                         MagicMock()), \
            patch.object(sys_assist.socket, 'inet_ntoa',
                         return_value='10.6.60.95'):
            ip = sys_assist.get_interface_ip('etho0')
            self.assertEqual(ip, '10.6.60.95')

    def test_get_lan_ip_should_return_external_ip(self):
        with patch.object(sys_assist, 'get_interface_ip',
                          return_value='10.6.60.95'), \
            patch.object(sys_assist.socket, 'gethostbyname',
                         return_value='127.0.0.1'):
            ip = sys_assist.get_lan_ip()
            self.assertEqual(ip, '10.6.60.95')

    def test_get_lan_ip_should_return_localhost(self):
        self.io_error = MagicMock()
        self.io_error.side_effect = IOError
        with patch.object(sys_assist, 'get_interface_ip',
                          self.io_error), \
            patch.object(sys_assist.socket, 'gethostbyname',
                         return_value='127.0.0.1'):
            ip = sys_assist.get_lan_ip()
            self.assertEqual(ip, '127.0.0.1')

if __name__ == '__main__':
    unittest.main()
