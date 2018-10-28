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
chksrv - HTTP/HTTPS Check Module.
"""

import typing
import logging

import socket
from urllib.parse import urlparse
from http.client import HTTPConnection, HTTPResponse, HTTPException

from . import BaseCheck, TcpCheck, SslCheck, start_timer, stop_timer


DEFAULT_PORT_HTTP = 80
DEFAULT_PORT_HTTPS = 443


class HttpSocketConnection(HTTPConnection):

    def __init__(self, sock, blocksize=8192):
        super().__init__(None, blocksize=blocksize)

        self.sock = sock

    def _get_hostport(self, host, port):
        # just overwrite the original get_hostport method, since it
        # isn't required when only the socket is supplied and just causes
        # issues
        return (host, port)

    def connect(self):
        # socket already provided
        pass


class HttpCheck(BaseCheck):

    log = logging.getLogger('HTTP')
    default_options = {
        **SslCheck.default_options,
        'http.method': 'GET',
        'http.body': None,
    }

    def __init__(self, url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.url = url
        self.use_ssl, self.host, self.port, self.path = self._parse_url(url)
        if self.use_ssl:
            self.subtask = SslCheck(self.host, self.port, options=self.options)
        else:
            self.subtask = TcpCheck(self.host, self.port, options=self.options)

    def run(self):
        con = self.get_connection()
        self.close_connection(con)

        self.results['success'] = self.results.get('tcp.success', False) is True and \
                                    (self.results.get('ssl.success') is True or not self.use_ssl) and \
                                    self.results.get('http.success', False) is True

    def get_connection(self):
        self.log.info("Get connection using sub-check task")

        sock = self.subtask.get_connection()
        self.results.update(self.subtask.results)

        if sock:
            self.log.info("Initiate HTTP connection using socket")
            con = HttpSocketConnection(sock)
            # con.set_debuglevel(logging.root.level)
            self._send_request(con)

            return con
        else:
           self.results['http.success'] = False
           self.log.error("Failed to establish socket")
           return None

    def close_connection(self, con: HttpSocketConnection):
        if con:
            con.close()

    def _parse_url(self, url):
        url = urlparse(url)

        if url.scheme.lower() not in ('http', 'https'):
            self.log.error(f"Unknown URL scheme: {url.scheme}")
            raise ValueError("The HTTP check module only accepts URLs with HTTP or HTTPS scheme")

        use_ssl = True if url.scheme.lower() == 'https' else False
        host = url.hostname
        port = url.port or (DEFAULT_PORT_HTTPS if use_ssl else DEFAULT_PORT_HTTP)
        path = url.path + (f'?{url.query}' if url.query else '')

        return use_ssl, host, port, path

    def _send_request(self, con: HttpSocketConnection):

        self.log.info("Prepare HTTP request")

        # iterate over options beginning with http.header.
        additional_headers = {}
        for key, value in filter(lambda item: item[0].startswith('http.header.'), self.options.items()):
            header_name = key[len('http.header.')]
            additional_headers[header_name] = value
            self.log.debug(f"Found additional header: {header_name}: {value}")

        try:
            self.log.info("Send HTTP request")

            timer = start_timer()

            con.request(
                self.options['http.method'],
                self.url,
                body=self.options['http.body'] or None,
                headers=additional_headers,
            )

            self.results['http.con.time.perf'], self.results['http.con.time.process'] = stop_timer(*timer)
            resp = con.getresponse()
            self.results['http.resp.time.perf'], self.results['http.resp.time.process'] = stop_timer(*timer)

            self._update_results(resp, True)
            self.log.info(f"HTTP request finished. Status {resp.status} {resp.reason}")

            return con

        except HTTPException as e:
            self._update_results(resp, False)
            self.log.error(f"HTTP request failed: {', '.join(e.args)}", exc_info=False)
            return None

    def _update_results(self, resp: HTTPResponse, success: bool):
        self.results['http.success'] = success
        self.results['http.resp.status'] = resp.status
        self.results['http.resp.reason'] = resp.reason
        self.results['http.resp.version'] = resp.version

        body = resp.read()
        self.results['http.resp.body'] = body
        self.results['http.resp.body_length'] = len(body)

        for key, value in resp.getheaders():
            key = 'http.resp.header.' + key.replace(' ', '_').replace('-', '_').lower()
            if key in self.results:
                # make it a list
                if isinstance(self.results[key], list):
                    self.results[key].append(value)
                else:
                    self.results[key] = [self.results[key], value]
            else:
                self.results[key] = value
            self.log.debug(f"Found response header: {key}: {value}")
