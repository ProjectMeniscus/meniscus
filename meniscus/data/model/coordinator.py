import uuid


class Worker():
    """
    Workers are used to perform functions in the grid corresponding
    personalities which define their purpose
    personalities: correlation | normalization | storage
    """

    def __init__(self, worker_id, worker_token):
        self.worker_id = worker_id
        self.worker_token = worker_token

    def set_worker_network_layer_stats(self, host_name, callback,
                                       ip_address_v4, ip_address_v6):
        self.host_name = host_name
        self.callback = callback
        self.ip_address_v4 = ip_address_v4
        self.ip_address_v6 = ip_address_v6

    def set_worker_personality_stats(self, personality, status, system_info):
        self.personality = personality
        self.status = status
        if not system_info:
            self.system_info = [{'disk_gb': '', 'os_type': '', 'memory_mb': '',
                                 'architecture': ''}]
        else:
            self.system_info = system_info

    def get_hostname(self):
        return self.host_name

    def get_worker_id(self):
        return self.worker_id

    def format(self):
        return {'worker_id': self.worker_id,
                'worker_token': self.worker_token,
                'hostname': self.host_name,
                'callback': self.callback,
                'ip_address_v4': self.ip_address_v4,
                'ip_address_v6': self.ip_address_v6,
                'personality': self.personality,
                'status': self.status,
                'system_info': self.system_info}

    def format_for_save(self, db_id):
        worker_dict = self.format()
        worker_dict['_id'] = db_id
        return worker_dict


class MyWorker(object):
    def __init__(self, **kwargs):

        if '_id' in kwargs.keys():
            self._id = kwargs['_id']

        if 'worker_id' in kwargs.keys():
            self.worker_id = kwargs['worker_id']
        else:
            self.worker_id = uuid.uuid4()

        if 'worker_token' in kwargs.keys():
            self.worker_token = kwargs['worker_token']
        else:
            self.worker_token = uuid.uuid4()

        self.hostname = kwargs['hostname']
        self.callback = kwargs['callback']
        self.ip_address_v4 = kwargs['ip_address_v4']
        self.ip_address_v6 = kwargs['ip_address_v6']
        self.personality = kwargs['personality']
        self.status = kwargs['status']
        sys_info = kwargs['system_info']
        self.system_info = SystemInfo(
            sys_info['disk_gb'],
            sys_info['os_type'],
            sys_info['memory_mb'],
            sys_info['architecture'])

    def format(self):
        return{
            'worker_id': self.worker_id,
            'worker_token': self.worker_token,
            'hostname': self.hostname,
            'callback': self.callback,
            'ip_address_v4': self.ip_address_v4,
            'ip_address_v6': self.ip_address_v6,
            'personality': self.personality,
            'status': self.personality,
            'system_info': self.system_info.format()
        }

    def format_for_save(self):
        return self.format().update({'_id': self._id})


class WorkerRegistration(object):
    def __init__(self, hostname, ip_address_v4, ip_address_v6,
                 personality, system_info):
        self.hostname = hostname
        self.callback = ip_address_v4 + ':8080/v1/configuration'
        self.ip_address_v4 = ip_address_v4
        self.ip_address_v6 = ip_address_v6
        self.personality = personality
        self.status = 'waiting'
        self.system_info = system_info

    def format_registration(self):
        return{
            'hostname': self.hostname,
            'callback': self.callback,
            'ip_address_v4': self.ip_address_v4,
            'ip_address_v6': self.ip_address_v6,
            'personality': self.personality,
            'system_info': self.system_info.format()
        }


class SystemInfo(object):
    def __init__(self, disk_gb, os_type, memory_mb, architecture):
        self.disk_gb = disk_gb
        self.os_type = os_type
        self.memory_mb = memory_mb
        self.architecture = architecture

    def format(self):
        return {
            'disk_gb': self.disk_gb,
            'os_type': self.os_type,
            'memory_mb': self.memory_mb,
            'architecture': self.architecture
        }
