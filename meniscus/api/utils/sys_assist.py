import fcntl
import multiprocessing
import os
import socket
import struct
import subprocess
import sys

from oslo.config import cfg

from meniscus import env
from meniscus import config


_LOG = env.get_logger(__name__)


_network_interface_group = cfg.OptGroup(
    name='network_interface',
    title='Default network interface name'
)
config.get_config().register_group(_network_interface_group)

_network_interface_options = [
    cfg.StrOpt('default_ifname',
               default='eth0',
               help="""The default network interface to pull the IP from"""
               )
]

config.get_config().register_opts(
    _network_interface_options,
    group=_network_interface_group
)

try:
    config.init_config()
except config.cfg.ConfigFilesNotFoundError as ex:
    _LOG.exception(ex.message)

conf = config.get_config()

DEFAULT_NETWORK_IFNAME = conf.network_interface.default_ifname


def get_sys_mem_total_kB():
    memory_total = None
    if 'linux' in sys.platform:
        memory_line = None
        for line in open("/proc/meminfo"):
            if 'MemTotal:' in line:
                memory_line = line
                break

        if memory_line:
            memory_line = memory_line.replace('MemTotal:', '').strip()
            memory_line = memory_line.replace('kB', '')
            memory_line = memory_line.strip()
            memory_total = int(memory_line)

    return memory_total


def get_sys_mem_total_MB():
    memory_total_kb = get_sys_mem_total_kB()
    if memory_total_kb:
        memory_total_mb = memory_total_kb / 1024
        return memory_total_mb


def get_disk_size_GB(file_sys='/'):
    disk_size = None
    if 'linux' in sys.platform:
        file_system = os.statvfs(file_sys)
        disk_size = (file_system.f_blocks * file_system.f_frsize) / (1024 ** 3)

    return disk_size


def get_disk_usage():

    def get_size_in_GB(disk_size):
        if 'G' in disk_size:
            return float(disk_size.replace('G', ''))
        if 'M' in disk_size:
            return float(disk_size.replace('M', '')) / 1024
        if 'K' in disk_size:
            return float(disk_size.replace('K', '')) / (1024 ** 2)
        return 0

    disk_usage = dict()

    if 'linux' in sys.platform:
        df_command = subprocess.Popen(["df", "-h"], stdout=subprocess.PIPE)
        df_output = df_command.communicate()[0]
        disk_usage = list()
        for file_system in df_output.split("\n")[1:]:
            if 'none'not in file_system:
                try:
                    name,  size, used, avail, use, mount = file_system.split()
                    device = {
                        'device': name,
                        'total': get_size_in_GB(size),
                        'used': get_size_in_GB(used)}
                    disk_usage.append(device)
                except ValueError:
                    pass
    return disk_usage


def get_interface_ip(ifname=DEFAULT_NETWORK_IFNAME):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(s.fileno(), 0x8915,
                        struct.pack('256s', ifname[:15]))[20:24])
    except IOError:
        pass

    try:
        return socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        return '127.0.0.1'


def get_cpu_core_count():
    return multiprocessing.cpu_count()


def get_load_average():
    load_average = os.getloadavg()
    return {
        '1': load_average[0],
        '5': load_average[1],
        '15': load_average[2]
    }
