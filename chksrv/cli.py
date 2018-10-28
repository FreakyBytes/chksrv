#!/usr/bin/env pyhton3
# chksrv
# Copyright (C) 2018  Martin Peters

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
chksrv - check-service a tool to probe and check the health of network services.

Usage:
    chksrv (-h | --help)
    chksrv --version
    chksrv tcp [options] [-p PARAM=VALUE]... [-e EXPR]... HOST PORT
    chksrv ssl [options] [-p PARAM=VALUE]... [-e EXPR]... HOST PORT
    chksrv http [options] [-p PARAM=VALUE]... [-e EXPR]... URL
    chksrv ping [options] [-p PARAM=VALUE]... [-e EXPR]... HOST
    chksrv dns [options] [-p PARAM=VALUE]... [-e EXPR]... DOMAIN

Options:
    -h --help                     Show this screen.
    --version                     Show version.
    -v --verbose                  Increases verbosity.
    -l --log-level LEVEL          Defines the log verbosity [default: WARN].
    --log-file FILE               Stores all log output in a file.
    -p --parameter PARAM=VALUE    Defines a parameter.
    -e --expects EXPR             Defines an expection expression.
    -r --retry RETRY              Defines the amount of retries [default: 3].
    --timeout TIMEOUT             Defines a timeout for one try in seconds [default: 10].
"""

import typing
import sys
import os
import logging
import re

from docopt import docopt

from chksrv import exceptions
from chksrv.config import parse_option_value
from chksrv import checks
from chksrv.runner import Runner


log = logging.getLogger('CLI')


def get_version():
    from pkg_resources import get_distribution, DistributionNotFound

    try:
        dist = get_distribution('chksrv')
        dist_loc = os.path.normcase(dist.location)
        here = os.path.normcase(__file__)
        if not here.startswith(os.path.join(dist_loc, 'chksrv')):
            # not installed, but another version of chksrv is
            raise DistributionNotFound
    except DistributionNotFound:
        return "n/a"
    else:
        return dist.version


def setup_logging(level=logging.WARN, logfile=None) -> None:
    log_root = logging.getLogger()
    log_root.setLevel(level)
    log_format = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

    # setting up logging to file
    if logfile:
        log_file_handler = logging.FileHandler(logfile)
        log_file_handler.setFormatter(log_format)
        log_root.addHandler(log_file_handler)

    # setting up logging to stdout
    log_stream_handler = logging.StreamHandler(sys.stdout)
    log_stream_handler.setFormatter(log_format)
    log_root.addHandler(log_stream_handler)


def parse_type(args: typing.Dict[str, typing.Any]) -> str:
    types = ('tcp', 'ssl', 'http', 'ping', 'dns')
    result = None

    for t in types:
        b = args.get(t, False)
        if b is True and result is None:
            result = t
        elif b is True and result is not None:
            raise exceptions.ChksrvConfigException("Multiple check types are configure.")

    if result is None:
        raise exceptions.ChksrvConfigException("No check type is configured.")

    return result.lower()


def parse_options(param_list: typing.List[str]) -> typing.Dict[str, typing.Any]:
    regex = re.compile(r'^(?P<name>[a-z][a-z0-9\-\_\.]+)\=(?P<value>.+)$')

    log.debug("Parse parameter")
    params = {}
    for p in param_list:
        match = regex.match(p)
        if not match:
            log.error(f"Cannot parse parameter '{p}'. Please ensure parameter are passed in the formate NAME=VALUE")
            continue

        name = match.group('name').lower()
        value = parse_option_value(match.group('value'))

        if name in params:
            log.warn(f"Parameter '{name}' was already defined with value '{params[name]}'. Now overwriting with '{value}'")

        params[name] = value
        log.debug(f"Found parameter '{name} = {value}'")

    return params

def parse_loglevel(args):
    level_map = {
        'CRITICAL': 50,
        'FATAL': 50,
        'ERROR': 40,
        'WARNING': 30,
        'WARN': 30,
        'INFO': 20,
        'DEBUG': 10,
        'TRACE': 10,
    }

    level_name = args.get('--log-level', 'WARN').upper()
    level = level_map.get(level_name, None)
    if not level:
        try:
            level = int(level_name)
        except:
            level = level_map['WARN']

    if args.get('--verbose', False):
        level = level - 10

    return max(0, level)


def run():
    args = docopt(__doc__)

    if args['--version']:
        print(f"chksrv version {get_version()}")
        return

    setup_logging(parse_loglevel(args), args.get('--log-file', None))
    log.info("Start chksrv")

    chk_type = parse_type(args)
    log.info(f"Check type {chk_type}")
    options = parse_options(args.get('--parameter', []))

    if chk_type == 'tcp':
        chk = checks.TcpCheck(args['HOST'], int(args['PORT']), options=options)
    elif chk_type == 'ssl':
        chk = checks.SslCheck(args['HOST'], int(args['PORT']), options=options)
    elif chk_type == 'http':
        chk = checks.HttpCheck(args['URL'], options=options)
    else:
        log.error(f"Not implemented check type {chk_type}")
        sys.exit(2)

    runner = Runner(chk, args['--expects'], options)
    runner.run()

    if runner and runner.results:
        from pprint import pprint
        pprint(runner.results)

    if runner.success:
        log.info("Check succeded")
    else:
        log.info("Check failed")

    sys.exit(0 if runner.success is True else 1)
