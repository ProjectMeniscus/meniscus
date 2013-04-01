import unittest

from meniscus.data.model.worker import SystemInfo
from meniscus.data.model.worker import Worker
from meniscus.data.model.worker import WorkerConfiguration
from meniscus.data.model.worker import WorkerRegistration


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenTestingWorkerObject())
    suite.addTest(WhenTestingWorkerRegistrationObject())
    suite.addTest(WhenTestingSystemInfoObject())
    suite.addTest(WhenTestingWorkerConfigurationObject())


class WhenTestingWorkerObject(unittest.TestCase):

    def setUp(self):
        self.system_info = SystemInfo(cpu_cores='4',
                                      disk_gb='20',
                                      os_type='Darwin-11.4.2-x86-64bit',
                                      memory_mb='1024',
                                      architecture='x86_64')

    def test_new_worker_no_ids(self):
        self.test_worker = Worker(hostname='worker01',
                                  callback='172.22.15.25:8080/v1/config/',
                                  ip_address_v4='172.23.1.100',
                                  ip_address_v6='::1',
                                  personality='worker.correlation',
                                  status='new',
                                  system_info=self.system_info.format())
        self.assertTrue('worker_id' in self.test_worker.format())
        self.assertTrue('worker_token' in self.test_worker.format())

    def test_new_worker_format_for_save(self):
        self.test_worker = Worker(_id='010101',
                                  worker_id='0123456789',
                                  worker_token='9876543210',
                                  hostname='worker01',
                                  callback='172.22.15.25:8080/v1/config/',
                                  ip_address_v4='172.23.1.100',
                                  ip_address_v6='::1',
                                  personality='worker.correlation',
                                  status='new',
                                  system_info=self.system_info.format())
        self.assertTrue('_id' in self.test_worker.format_for_save())

    def test_new_worker_get_registration_identity(self):
        self.test_worker = Worker(_id='010101',
                                  worker_id='0123456789',
                                  worker_token='9876543210',
                                  hostname='worker01',
                                  callback='172.22.15.25:8080/v1/config/',
                                  ip_address_v4='172.23.1.100',
                                  ip_address_v6='::1',
                                  personality='worker.correlation',
                                  status='new',
                                  system_info=self.system_info.format())
        self.assertTrue('personality_module'
                        in self.test_worker.get_registration_identity())

    def test_new_worker_pipeline(self):
        self.test_worker = Worker(_id='010101',
                                  worker_id='0123456789',
                                  worker_token='9876543210',
                                  hostname='worker01',
                                  callback='172.22.15.25:8080/v1/config/',
                                  ip_address_v4='172.23.1.100',
                                  ip_address_v6='::1',
                                  personality='worker.correlation',
                                  status='new',
                                  system_info=self.system_info.format())
        self.worker_pipeline = self.test_worker.get_pipeline_info()
        self.assertEqual(self.worker_pipeline['hostname'],
                         'worker01')
        self.assertEqual(self.worker_pipeline['ip_address_v4'],
                         '172.23.1.100')
        self.assertEqual(self.worker_pipeline['ip_address_v6'],
                         '::1')
        self.assertEqual(self.worker_pipeline['personality'],
                         'worker.correlation')


class WhenTestingWorkerRegistrationObject(unittest.TestCase):
    def test_WorkerRegistration_new(self):
        self.worker_reg = WorkerRegistration('correlation', 'new')
        self.assertTrue('hostname' in self.worker_reg.format())
        self.assertTrue('callback' in self.worker_reg.format())
        self.assertTrue('ip_address_v4' in self.worker_reg.format())
        self.assertTrue('ip_address_v6' in self.worker_reg.format())
        self.assertTrue('personality' in self.worker_reg.format())
        self.assertTrue('status' in self.worker_reg.format())
        self.assertTrue('system_info' in self.worker_reg.format())


class WhenTestingSystemInfoObject(unittest.TestCase):
    def test_new_system_info_obj(self):
        self.system_info = SystemInfo(cpu_cores='4',
                                      disk_gb='20',
                                      os_type='Darwin-11.4.2-x86-64bit',
                                      memory_mb='1024',
                                      architecture='x86_64')

        self.assertEqual(self.system_info.format()['cpu_cores'], '4')
        self.assertEqual(self.system_info.format()['disk_gb'], '20')
        self.assertEqual(
            self.system_info.format()['os_type'], 'Darwin-11.4.2-x86-64bit')
        self.assertEqual(self.system_info.format()['memory_mb'], '1024')
        self.assertEqual(self.system_info.format()['architecture'], 'x86_64')

    def test_new_system_info_empty_obj(self):
        self.system_info = SystemInfo()
        self.assertTrue('cpu_cores' in self.system_info.format())
        self.assertTrue('disk_gb' in self.system_info.format())
        self.assertTrue('os_type' in self.system_info.format())
        self.assertTrue('memory_mb' in self.system_info.format())
        self.assertTrue('architecture' in self.system_info.format())


class WhenTestingWorkerConfigurationObject(unittest.TestCase):
    def test_worker_configuration(self):
        self.worker_config = WorkerConfiguration(
            "correlation",
            "meniscus.personas.worker.correlation",
            "94d6176b-9188-4409-8648-7374d0326e6b",
            "8cc3b103-9b23-4e1c-afb1-8c5973621b55",
            "http://172.22.15.25:8080/v1")
        self.assertEqual(self.worker_config.format()['personality'],
                         'correlation')
        self.assertEqual(self.worker_config.format()['personality_module'],
                         'meniscus.personas.worker.correlation')
        self.assertEqual(self.worker_config.format()['worker_token'],
                         '94d6176b-9188-4409-8648-7374d0326e6b')
        self.assertEqual(self.worker_config.format()['worker_id'],
                         '8cc3b103-9b23-4e1c-afb1-8c5973621b55')
        self.assertEqual(self.worker_config.format()['coordinator_uri'],
                         'http://172.22.15.25:8080/v1')


if __name__ == '__main__':
    unittest.main()