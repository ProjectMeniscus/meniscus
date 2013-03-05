import os
import unittest
import tempfile
import importlib
import shutil

from meniscus.ext.plugin import plug_into


def suite():
    suite = unittest.TestSuite()
    suite.addTest(WhenLoading())

    return suite


PLUGIN_PY = """
def perform_operation(msg):
    return True, msg

"""


class WhenLoading(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp('testing_lib')
        self.tmp_lib = os.path.join(self.tmp_dir, 'test')
        os.mkdir(self.tmp_lib)

        self.plugin_file = os.path.join(self.tmp_lib, 'plugin.py')

        output = open(self.plugin_file, 'w')
        output.write(PLUGIN_PY)
        output.close()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_loading(self):
        plug_into(self.tmp_dir)

        plugin_mod = importlib.import_module('test.plugin')
        must_be_true, msg = plugin_mod.perform_operation('test')

        self.assertTrue(must_be_true)
        self.assertEqual('test', msg)


if __name__ == '__main__':
    unittest.main()
