import os
import socket
import sys
import multiprocessing


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
        print memory_total_mb


if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',                                ifname[:15]))[20:24])


def get_disk_size_GB():
    disk_size = None
    if 'linux' in sys.platform:
        file_system = os.statvfs('/')
        disk_size = (file_system.f_blocks * file_system.f_frsize) / 3072

    return disk_size


def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip


def get_cpu_core_count():
    return multiprocessing.cpu_count()
