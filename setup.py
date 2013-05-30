# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='meniscus',
    version='0.1',
    description='',
    author='Project Meniscus',
    author_email='',
    tests_require=[
        "mock",
        "nose",
        "nosexcover",
        "testtools",
        "httpretty",
        "tox",
	"six",
	"ordereddict"
    ],
    install_requires=[
        "falcon",
        "iso8601",
        "wsgiref",
        "uWSGI",
        "pymongo",
        "requests",
        "eventlet",
        "oslo.config",
    ],
    test_suite='nose.collector',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup'])
)
