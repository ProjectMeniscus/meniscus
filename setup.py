# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
    from setuptools.command import easy_install
except ImportError:
    from setuptools import setup, find_packages
    from setuptools.command import easy_install


def read(relative):
    contents = open(relative, 'r').read()
    return [l for l in contents.split('\n') if l != '']

setup(
    name='meniscus',
    version='0.1',
    description='',
    author='Project Meniscus',
    author_email='',
    tests_require=read('./tools/test-requires'),
    install_requires=read('./tools/pip-requires'),
    test_suite='nose.collector',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup'])
)
