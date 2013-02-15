import meniscus.tests.node.rfc5424_test
import meniscus.tests.api.tenant.resources_test

import unittest

def suite():
    suite = unittest.TestSuite()
    suite.addTest(rfc5424_test.suite())
    suite.addTest(resources_test.suite())

    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())

    def setUp(self):
        pass

    def tearDown(self):
        pass
