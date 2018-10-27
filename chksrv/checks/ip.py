"""
chksrv - Internet Protocol Check Module - includes TCP, UDP, ICMP-Ping.
"""

import typing
import logging

import socket
import time

from . import BaseCheck


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

    def get_connection(self):
        return self._connect_socket(retry=False)

    def close_connection(self, sock: typing.Type[socket.socket]):
        if sock:
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

            time_perf = time.perf_counter()
            time_proc = time.process_time()

            sock.connect((self.host, self.port))

            time_proc = time.process_time() - time_proc
            time_perf = time.perf_counter() - time_perf

            self.results['tcp.con_time.process'] = time_proc
            self.results['tcp.con_time.perf']  = time_perf
            self.results['tcp.success'] = True

            return sock

        except OSError as e:
            self.log.exception(f"Error while connection to {self.host} {self.port}: {e.strerror}", exc_info=False)
            if not retry and do_retry:
                self.log.info("Retry socket connection", exc_info=False)
                return self._connect_socket(retry=True)
            else:
                self.results['tcp.success'] = False
                return None


class IcmpPingCheck(BaseCheck):
    pass
