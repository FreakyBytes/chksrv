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
chksrv - SSL/TLS Check Module.
"""

import typing
import logging

import os
import socket
import ssl

from . import TcpCheck, start_timer, stop_timer


PROTOCOL_MAP = {
    'tls': ssl.PROTOCOL_TLS,
    'sslv2': ssl.PROTOCOL_SSLv2 if ssl.HAS_SSLv2 else ssl.PROTOCOL_TLS,
    'sslv3': ssl.PROTOCOL_SSLv3 if ssl.HAS_SSLv3 else ssl.PROTOCOL_TLS,
    'tlsv1': ssl.PROTOCOL_TLSv1 if ssl.HAS_TLSv1 else ssl.PROTOCOL_TLS,
    'tlsv1.1': ssl.PROTOCOL_TLSv1_1 if ssl.HAS_TLSv1_1 else ssl.PROTOCOL_TLS,
    'tlsv1.2': ssl.PROTOCOL_TLSv1_2 if ssl.HAS_TLSv1_2 else ssl.PROTOCOL_TLS,
}


class SslCheck(TcpCheck):

    log = logging.getLogger('SSL')
    default_options = {
        **TcpCheck.default_options,
        'ssl.use_default_context': True,
        'ssl.protocol': 'TLS',
        'ssl.ciphers': 'ALL',
        'ssl.check_hostname': False,
        'ssl.verify_mode': 'CERT_OPTIONAL',
        'ssl.verify_flags': 'VERIFY_DEFAULT',
        'ssl.ca': '__sys__',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self):
        sock = self.get_connection()
        self.close_connection(sock)

        self.results['success'] = self.results['tcp.success'] is True and self.results['ssl.success'] is True

    def get_connection(self):
        self.log.info(f"SSL library: {ssl.OPENSSL_VERSION} ({'.'.join(map(str, ssl.OPENSSL_VERSION_INFO))})")
        context = self._get_context()

        sock = self._connect_socket(retry=False)
        if sock:
            ssock = self._wrap_socket(sock, context)
            return ssock
        else:
            self.results['ssl.success'] = False
            self.log.error("Failed to establish socket")
            return None

    def close_connection(self, ssock: ssl.SSLSocket):
        if ssock:
            timer = start_timer()
            ssock.shutdown(socket.SHUT_RDWR)
            self.results['ssl.shutdown.time.perf'], self.results['ssl.shutdown.time.process'] = stop_timer(*timer)

            ssock.close()

    def _get_context(self):

        if self.options['ssl.use_default_context'] is True:
            self.log.info("Using system default SSL context")
            context = ssl.create_default_context()
        else:
            self.log.info("Creating SSL context")

            protocol = PROTOCOL_MAP.get(self.options['ssl.protocol'].lower(), ssl.PROTOCOL_TLS)
            context = ssl.SSLContext(protocol)
            context.set_ciphers(self.options['ssl.ciphers'])

        context.check_hostname = bool(self.options['ssl.check_hostname'])
        context.verify_mode = ssl.VerifyMode[self.options['ssl.verify_mode']] or ssl.VerifyMode.CERT_OPTIONAL
        context.verify_flags = ssl.VerifyFlags[self.options['ssl.verify_flags']] or ssl.VerifyFlags.VERIFY_DEFAULT

        self.log.debug(f"SSL verify mode: {str(context.verify_mode)}")
        self.log.debug(f"SSL verify flags: {str(context.verify_flags)}")

        ca_path = self.options['ssl.ca']
        if ca_path in ('__sys__', None):
            self.log.info("Load system Certificate Authorities")
            context.set_default_verify_paths()
            context.load_default_certs()

        elif os.path.isfile(ca_path) and os.path.exists(ca_path):
            self.log.info(f"Load CA file: {ca_path}")
            context.load_verify_locations(cafile=ca_path)

        elif os.path.isdir(ca_path) and os.path.exists(ca_path):
            self.log.info(f"Load load all CAs from directory: {ca_path}")
            context.load_verify_locations(capath=ca_path)

        stats = context.cert_store_stats()
        self.log.info(f"Certificate trust store with: {stats['crl']} CRL, {stats['x509_ca']} x509 CAs, {stats['x509']} other x509 certs")

        return context

    def _wrap_socket(self, sock: socket.socket, context: ssl.SSLContext) -> ssl.SSLSocket:
        ssock = context.wrap_socket(sock, server_side=False, do_handshake_on_connect=False, server_hostname=self.host)

        try:
            self.log.info("Start SSL handshake")
            timer = start_timer()

            ssock.do_handshake()

            self.results['ssl.handshake.time.perf'], self.results['ssl.handshake.time.process'] = stop_timer(*timer)
            self._update_results(context, ssock, True)

            self.log.info("SSL handshake successfull")

            return ssock

        except ssl.SSLError as e:
            self._update_results(context, ssock, False)
            self.log.error(f"SSL handshake failed: {e.reason}", exc_info=False)
            return None

    def _update_results(self, context: ssl.SSLContext, ssock: ssl.SSLSocket, success: bool):

        self.results['ssl.success'] = success

        cert = ssock.getpeercert() if success else None
        self.results['ssl.con.cert'] = cert
        self.results['ssl.con.cipher'], self.results['ssl.con.protocol'], self.results['ssl.con.secret_bits'] = ssock.cipher() or (None, None, None)
        self.results['ssl.con.compression'] = ssock.compression() or None
        self.results['ssl.con.alpn_protocol'] = ssock.selected_alpn_protocol() or None
        self.results['ssl.con.npn_protocol'] = ssock.selected_npn_protocol() or None
        self.results['ssl.con.ssl_version'] = ssock.version() or None
        self.results['ssl.con.server_hostname'] = ssock.server_hostname or None
        self.results['ssl.con.cert.matches_hostname'] = True if cert is not None and ssl.match_hostname(cert, self.host) else False
