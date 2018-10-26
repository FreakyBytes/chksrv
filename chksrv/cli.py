#!/usr/bin/env pyhton3
"""
chksrv - check-service a tool to probe and check the health of services.

Usage:
    chksrv (-h | --help)
    chksrv --version
    chksrv http [options] [-p PARAM=VALUE]... [-e EXPR]... URL
    chksrv ping [options] [-p PARAM=VALUE]... [-e EXPR]... HOST
    chksrv dns [options] [-p PARAM=VALUE]... [-e EXPR]... DOMAIN

Options:
    -h --help                     Show this screen.
    --version                     Show version.
    -p --parameter PARAM=VALUE    Defines a parameter.
    -e --expects EXPR             Defines an expection expression.
    -r --retry RETRY              Defines the amount of retries [default: 3].
    --timeout TIMEOUT             Defines a timeout for one try in seconds [default: 10].
"""

import typing
import sys
import logging
from docopt import docopt


log = logging.getLogger('CLI')


def setup_logging(level=logging.WARN, logfile=None) -> None:
    log_root = logging.getLogger()
    log_root.setLevel(level)
    # log_format = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    log_format = logging.Formatter('{asctime} {name: <12} {levelname: <8} {message}', style='{')

    # setting up logging to file
    if logfile:
        log_file_handler = logging.FileHandler(logfile)
        log_file_handler.setFormatter(log_format)
        log_root.addHandler(log_file_handler)

    # setting up logging to stdout
    log_stream_handler = logging.StreamHandler(sys.stdout)
    log_stream_handler.setFormatter(log_format)
    log_root.addHandler(log_stream_handler)


def run():
    setup_logging()
    args = docopt(__doc__)
    
    print(args)
