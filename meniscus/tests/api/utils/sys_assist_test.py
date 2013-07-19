import unittest
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
        self.conf = MagicMock()
        self.conf.network_interface.default_ifname = 'eth1'
        self.get_config = MagicMock(return_value=self.conf)

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
                patch.object(sys_assist.os, 'statvfs',
                             return_value=self.statvfs):
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

    def test_get_interface_ip_should_return_external_ip(self):
        with patch.object(sys_assist, 'get_interface_ip',
                          return_value='10.6.60.99'), \
            patch.object(sys_assist.socket, 'gethostbyname',
                         return_value='127.0.0.1'):
            ip = sys_assist.get_interface_ip()
            self.assertEqual(ip, '10.6.60.99')

    def test_get_lan_ip_should_return_localhost(self):
        with patch.object(sys_assist.socket, 'gethostbyname',
                         return_value='127.0.0.1'):
            ip = sys_assist.get_interface_ip('ABC9')
            self.assertEqual(ip, '127.0.0.1')

    def test_get_load_avergae(self):
        ave = sys_assist.get_load_average()
        self.assertTrue('1'in ave)
        self.assertTrue('5'in ave)
        self.assertTrue('15'in ave)

    def test_get_disk_usage__(self):
        output = ('Filesystem      Size  Used Avail Use% Mounted on\n'
                  '/dev/sda5        24G  5.2G   18G  24% /\n'
                  'udev            7.8G  4.0K  7.8G   1% /dev\n'
                  'tmpfs           3.2G  892K  3.2G   1% /run\n'
                  'none            5.0M     0  5.0M   0% /run/lock\n'
                  '/dev/sda4       7.8G  164K  7.8G   1% /run/shm\n'
                  '/dev/sda6       255G  434M  209G  14% /home')
        df = MagicMock()
        df.communicate.return_value = [output]
        with patch.object(sys_assist.sys, 'platform', self.platform), \
                patch.object(sys_assist.subprocess, 'Popen', return_value=df):
            usage = sys_assist.get_disk_usage()

        sda4 = {
            'device': '/dev/sda4',
            'total': 7.8,
            'used': 0.000156402587890625
        }
        self.assertTrue(sda4 in usage)
        sda5 = {
            'device': '/dev/sda5',
            'total': 24.0,
            'used': 5.2
        }
        self.assertTrue(sda5 in usage)
        sda6 = {
            'device': '/dev/sda6',
            'total': 255.0,
            'used': 0.423828125
        }
        self.assertTrue(sda6 in usage)
        sda4 = {
            'device': '/dev/sda4',
            'total': 7.8,
            'used': 0.000156402587890625
        }
        self.assertTrue(sda4 in usage)
        sda4 = {
            'device': '/dev/sda4',
            'total': 7.8,
            'used': 0.000156402587890625
        }
        self.assertTrue(sda4 in usage)


if __name__ == '__main__':
    unittest.main()
