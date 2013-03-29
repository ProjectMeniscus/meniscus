import platform
import uuid

import meniscus.api.utils.sys_assist as sys_assist


class Worker(object):
    def __init__(self, **kwargs):

        self._id = kwargs.get('_id', None)
        self.worker_id = kwargs.get('worker_id', str(uuid.uuid4()))
        self.worker_token = kwargs.get('worker_token', str(uuid.uuid4()))
        self.hostname = kwargs['hostname']
        self.callback = kwargs['callback']
        self.ip_address_v4 = kwargs['ip_address_v4']
        self.ip_address_v6 = kwargs['ip_address_v6']
        self.personality = kwargs['personality']
        self.status = kwargs['status']
        self.system_info = SystemInfo(**kwargs['system_info'])

    def format(self):
        return{
            'worker_id': self.worker_id,
            'worker_token': self.worker_token,
            'hostname': self.hostname,
            'callback': self.callback,
            'ip_address_v4': self.ip_address_v4,
            'ip_address_v6': self.ip_address_v6,
            'personality': self.personality,
            'status': self.status,
            'system_info': self.system_info.format()
        }

    def format_for_save(self):
        worker_dict = self.format()
        worker_dict['_id'] = self._id
        return worker_dict

    def get_registration_identity(self):
        return{
            'personality_module': 'meniscus.personas.{0}.app'
            .format(self.personality),
            'worker_id': self.worker_id,
            'worker_token': self.worker_token
        }

    def get_pipeline_info(self):
        return {
            'hostname': self.hostname,
            'ip_address_v4': self.ip_address_v4,
            'ip_address_v6': self.ip_address_v6,
            'personality': self.personality
        }


class WorkerRegistration(object):
    def __init__(self, personality, status='waiting'):
        self.hostname = platform.node()
        self.ip_address_v4 = sys_assist.get_lan_ip()
        self.ip_address_v6 = ""
        self.callback = self.ip_address_v4 + ':8080/v1/configuration'
        self.personality = personality
        self.status = status
        self.system_info = SystemInfo()

    def format(self):
        return{
            'hostname': platform.node(),
            'callback': self.callback,
            'ip_address_v4': self.ip_address_v4,
            'ip_address_v6': self.ip_address_v6,
            'personality': self.personality,
            'status': self.status,
            'system_info': self.system_info.format()
        }


class SystemInfo(object):
    def __init__(self, **kwargs):
        if kwargs:
            self.cpu_cores = kwargs['cpu_cores']
            self.disk_gb = kwargs['disk_gb']
            self.os_type = kwargs['os_type']
            self.memory_mb = kwargs['memory_mb']
            self.architecture = kwargs['architecture']
        else:
            self.cpu_cores = sys_assist.get_cpu_core_count()
            self.disk_gb = sys_assist.get_disk_size_GB()
            self.os_type = platform.platform()
            self.memory_mb = sys_assist.get_sys_mem_total_MB()
            self.architecture = platform.machine()

    def format(self):
        return {
            'cpu_cores': self.cpu_cores,
            'disk_gb': self.disk_gb,
            'os_type': self.os_type,
            'memory_mb': self.memory_mb,
            'architecture': self.architecture
        }


class WorkerConfiguration(object):
    def __init__(self, personality, personality_module, worker_token,
                 worker_id, coordinator_uri, pipeline_workers=None):

        self.personality = personality
        self.personality_module = personality_module
        self.worker_token = worker_token
        self.worker_id = worker_id
        self.coordinator_uri = coordinator_uri
        self.pipeline_workers = pipeline_workers if pipeline_workers else []
