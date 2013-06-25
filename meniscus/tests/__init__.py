import unittest

import meniscus.tests.config_test
import meniscus.tests.api.normalization.drivers.rfc5424_test
import meniscus.tests.api.tenant.resources_test
import meniscus.tests.data.datastore.handler_test
import meniscus.tests.data.adapters.mongodb_test
import meniscus.tests.ext.plugin_test


def suite():
    suite = unittest.TestSuite()
    suite.addTest(rfc5424_test.suite())
    suite.addTest(resources_test.suite())
    suite.addTest(config_test.suite())
    suite.addTest(handler_test.suite())
    suite.addTest(mongodb_test.suite())
    suite.addTest(plugin_test.suite())

    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
