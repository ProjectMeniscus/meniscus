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
