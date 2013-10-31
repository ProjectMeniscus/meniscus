"""
This Module contains classes that define different data structures used to
represent meniscus worker nodes and their registration, configuration, and
system status.
"""

import platform

import meniscus.api.utils.sys_assist as sys_assist
from meniscus.openstack.common import timeutils


class Worker(object):
    """
    Class that represents the data structure of worker node in a meniscus
    cluster.  The data contains basic identification and system info.
    """
    def __init__(self, **kwargs):
        """
        The init function accepts **kwargs so that a Worker object can be
        constructed from its dictionary representation or from a
        WorkerRegistration object's dictionary representation.
        """

        self._id = kwargs.get('_id')
        self.hostname = kwargs['hostname']
        self.ip_address_v4 = kwargs['ip_address_v4']
        self.ip_address_v6 = kwargs['ip_address_v6']
        self.personality = kwargs['personality']
        self.status = kwargs['status']
        self.system_info = SystemInfo(**kwargs['system_info'])

    def format(self):
        """
        Format an instance of the Worker object as a dictionary
        """
        return{
            'hostname': self.hostname,
            'ip_address_v4': self.ip_address_v4,
            'ip_address_v6': self.ip_address_v6,
            'personality': self.personality,
            'status': self.status,
            'system_info': self.system_info.format()
        }

    def format_for_save(self):
        """
        Format an instance of the Worker object with its internal _id
        for persistence in the datastore
        """
        worker_dict = self.format()
        worker_dict['_id'] = self._id
        return worker_dict

    def get_status(self):
        """
        Return a dictionary defining a worker node's system status
        """
        return{
            'hostname': self.hostname,
            'ip_address_v4': self.ip_address_v4,
            'ip_address_v6': self.ip_address_v6,
            'personality': self.personality,
            'status': self.status,
            'system_info': self.system_info.format()
        }


class WorkerRegistration(object):
    """
    A class defining the data structure of a worker node's
    registration information
    """
    def __init__(self, personality, status='new'):
        self.hostname = platform.node()
        self.ip_address_v4 = sys_assist.get_interface_ip()
        self.ip_address_v6 = ""
        self.personality = personality
        self.status = status
        self.system_info = SystemInfo()

    def format(self):
        """
        Format an instance fo the WorkerRegistration object as a dictionary.
        The output of this method can be passed to the constructor of the
        Worker class to create a new Worker instance.
        """
        return{
            'hostname': self.hostname,
            'ip_address_v4': self.ip_address_v4,
            'ip_address_v6': self.ip_address_v6,
            'personality': self.personality,
            'status': self.status,
            'system_info': self.system_info.format()
        }


class SystemInfo(object):
    """
    A class defining the data structure for system stats for a worker node.
    """
    def __init__(self, **kwargs):
        """
        An object can be initialized by passing in a dictionary representation
        of the data as **kwargs.  Otherwise the constructor will retrieve
        system stats from the machine it is executing on.
        """
        if kwargs:
            self.cpu_cores = kwargs['cpu_cores']
            self.os_type = kwargs['os_type']
            self.memory_mb = kwargs['memory_mb']
            self.architecture = kwargs['architecture']
            self.load_average = kwargs['load_average']
            self.disk_usage = kwargs['disk_usage']
            self.timestamp = kwargs['timestamp']
        else:
            self.cpu_cores = sys_assist.get_cpu_core_count()
            self.os_type = platform.platform()
            self.memory_mb = sys_assist.get_sys_mem_total_MB()
            self.architecture = platform.machine()
            self.load_average = sys_assist.get_load_average()
            self.disk_usage = sys_assist.get_disk_usage()
            self.timestamp = timeutils.utcnow()

    def format(self):
        """
        Formats an instance of a SystemInfo object as a dictionary
        """
        return {
            'cpu_cores': self.cpu_cores,
            'os_type': self.os_type,
            'memory_mb': self.memory_mb,
            'architecture': self.architecture,
            'load_average': self.load_average,
            'disk_usage': self.disk_usage,
            'timestamp': self.timestamp
        }


class WorkerConfiguration(object):
    """
    The class defines a data structure for a worker's configuration info.
    """
    def __init__(self, personality, coordinator_uri):

        self.personality = personality
        self.coordinator_uri = coordinator_uri

    def format(self):
        """
        Formats an instance fo a WorkerConfiguration object as a dictionary.
        """
        return{
            'personality': self.personality,
            'coordinator_uri': self.coordinator_uri
        }
