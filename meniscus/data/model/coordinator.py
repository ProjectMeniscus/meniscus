class Worker():
    """
    Workers are used to perform functions in the grid corresponding
    personalities which define their purpose
    personalities: correlation | normalization | storage
    """

    ## TODO: Consider builder pattern to avoid long constructor arg lists
    def __init__(self, worker_id, worker_token, host_name, callback,
                 ip_address_v4, ip_address_v6, personality, status,
                 system_info):
        self.worker_id = worker_id
        self.worker_token = worker_token
        self.host_name = host_name
        self.callback = callback
        self.ip_address_v4 = ip_address_v4
        self.ip_address_v6 = ip_address_v6
        self.personality = personality
        self.status = status
        if not system_info:
            self.system_info = [{'disk_gb': '', 'os_type': '', 'memory_mb': '',
                                 'architecture': ''}]
        else:
            self.system_info = system_info
    ## TODO: If it's commented, don't check it in

    # def __init__(self, mongo_worker):
    #     """
    #     constructor that takes in a mongodb worker and stores in worker object
    #     """
    #     self.worker_id = mongo_worker['worker_id']
    #     self.worker_token = mongo_worker['worker_token']
    #     self.host_name = mongo_worker['host_name']
    #     self.callback = mongo_worker['callback']
    #     self.ip_address_v4 = mongo_worker['ip_address_v4']
    #     self.ip_address_v6 = mongo_worker['ip_address_v6']
    #     self.personality = mongo_worker['personality']
    #     self.status = mongo_worker['status']
    #     if not mongo_worker['system_info']:
    #         self.system_info = [{'disk_gb': '', 'os_type': '', 'memory_mb': '',
    #                              'architecture': ''}]
    #     else:
    #         self.system_info = mongo_worker['system_info']

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

    def format_for_save(self, id):
        worker_dict = self.format()
        worker_dict['_id'] = id
        return worker_dict
