# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name = 'meniscus',
    version = '0.1',
    description = 'Application event logging at scale',
    author = 'John Hopper',
    author_email = 'john.hopper@rackspace.com',
    install_requires = [
        "pecan",
    ],
    test_suite = 'laas',
    zip_safe = False,
    include_package_data = True,
    packages = find_packages(exclude=['ez_setup'])
)
