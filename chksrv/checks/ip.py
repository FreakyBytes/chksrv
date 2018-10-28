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
chksrv - Internet Protocol Check Module - includes TCP, UDP, ICMP-Ping.
"""

import typing
import logging

import socket

from . import BaseCheck, start_timer, stop_timer


class TcpCheck(BaseCheck):

    log = logging.getLogger('TCP')
    default_options = {
        'ipv6': 'prefer',
        'timeout': 10,
    }

    def __init__(self, host, port, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = int(port)

    def run(self):
        sock = self.get_connection()
        self.close_connection(sock)

        self.results['success'] = self.results['tcp.success'] is True

    def get_connection(self):
        return self._connect_socket(retry=False)

    def close_connection(self, sock: typing.Type[socket.socket]):
        if sock:
            timer = start_timer()
            sock.shutdown(socket.SHUT_RDWR)
            self.results['tcp.shutdown.time.perf'], self.results['tcp.shutdown.time.process'] = stop_timer(*timer)

            sock.close()

    def _connect_socket(self, retry=False):
        ipv6 = self.options['ipv6'].lower() if isinstance(self.options['ipv6'], str) else self.options['ipv6']
        do_retry = True if ipv6 in ('prefer', 'fallback') else False

        try:
            if ipv6 is True or (ipv6 == 'prefer' and retry is False) or (ipv6 == 'fallback' and retry is True):
                self.log.info("Build IPv6 TCP socket")
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                self.results['tcp.ipv6'] = True
            else:
                self.log.info("Build IPv4 TCP socket")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.results['tcp.ipv6'] = False

            sock.setblocking(True)
            sock.settimeout(self.options['timeout'])

        except OSError as e:
            self.log.error(f"Error creating socket: {e.strerror}", exc_info=False)
            if not retry and do_retry:
                self.log.info("Retry socket creation", exc_info=False)
                return self._connect_socket(retry=True)
            else:
                self.results['tcp.success'] = False
                return None

        try:
            self.log.info(f"Try connecting to {self.host} {self.port}")

            time = start_timer()

            sock.connect((self.host, self.port))

            self.results['tcp.con.time.perf'], self.results['tcp.con.time.process'] = stop_timer(*time)
            self.results['tcp.success'] = True

            self.log.info("Connection successfull")

            return sock

        except OSError as e:
            self.log.exception(f"Error while connecting to {self.host} {self.port}: {e.strerror}", exc_info=False)
            if not retry and do_retry:
                self.log.info("Retry socket connection", exc_info=False)
                return self._connect_socket(retry=True)
            else:
                self.results['tcp.success'] = False
                return None


class IcmpPingCheck(BaseCheck):
    pass
