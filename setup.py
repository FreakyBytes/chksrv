#!/usr/bin/env python3

from distutils.core import setup

setup(
    name='chksrv',
    version='0.1.0',
    description='A tool to probe and check the health of services',
    author='Martin Peters',
    author_email='',
    packages=[ 'chksrv' ],
    install_requires=[
        'docopt~=0.6'
    ],
    entry_points='''
        [console_scripts]
        chksrv=chksrv.cli:run
    ''',
)
