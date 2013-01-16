import os

from pecan.deploy import deploy

directory = os.path.dirname(__file__)
application = deploy('{0}{1}config.py'.format(directory, os.sep))

if __name__ == "__main__":
    application.run()
