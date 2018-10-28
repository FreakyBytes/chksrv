#!/usr/bin/env python3

from setuptools import setup

with open('README.rst', 'r') as fh:
    long_description = fh.read()

setup(
    name='chksrv',
    version='0.1.0',
    description='A tool to probe and check the health of services',
    long_description=long_description,
    long_description_content_type="text/rst",
    url='https://git.hel.freakybytes.net/martin/chksrv',
    author='Martin Peters',
    author_email='',
    packages=[
        'chksrv',
        'chksrv.checks'
    ],
    install_requires=[
        'docopt~=0.6'
    ],
    entry_points='''
        [console_scripts]
        chksrv=chksrv.cli:run
    ''',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring',
        'Topic :: Utilities',
    ]
)
