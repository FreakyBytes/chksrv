chksrv
======

*check-service a tool to probe and check the health of network services*

*chksrv* is a tool intended to be used in conjunction with other tools (e.g. `Minitor <https://git.iamthefij.com/iamthefij/minitor>`_)
to check the health and availability of network services.
One design goal was to provide flexibility of what is checked,
without the need for complex bash scripts and piping. Effectively allowing to
write one check and then validating mulitple measurements afterwards.

Installation
------------

:code:`pip install chksrv`

You need at least Python 3.7 to run *chksrv*.

Usage
-----

.. code::

    Usage:
        chksrv (-h | --help)
        chksrv --version
        chksrv tcp [options] [-p PARAM=VALUE]... [-e EXPR]... HOST PORT
        chksrv ssl [options] [-p PARAM=VALUE]... [-e EXPR]... HOST PORT
        chksrv http [options] [-p PARAM=VALUE]... [-e EXPR]... URL

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

Modules
-------

.. _module-tcp:

TCP
'''

The TCP is one of the most basic check modules.
Its purpose is to try to establish a connection
to a standard TCP listening socket.

Parameters
..........

:ipv6: Specifies the IPv6 behaviour. Possible values:

    - :code:`True` only tries to connect to IPv6
    - :code:`False` only tries to connect to IPv4
    - :code:`'prefer'` tries to connect using IPv6 first,
      and tries IPv4 if this fails (default)
    - :code:`'fallback'` tries to connect using IPv4 first,
      and falls back to IPv6 if this fails

:timeout: Specifies the socket timeout in seconds

Results
.......

:tcp.success: :code:`True` if the socket connect succeded
:tcp.con.time.perf: Fractions of seconds it took to establish
    the socket connection
:tcp.con.time.process: Fractions of seconds of CPU time (system and user)
    the process used to  establish the socket connection
:tcp.ipv6: :code:`True` if the socket was established using IPv6

SSL
'''

The SSL module is based on the TCP module <module-tcp> and layers
a SSL/TLS handshake on top of it, using the Python3 :code:`ssl` library.

*All parameters and results from the TCP module are available in addition*

Parameters
..........

:ssl.use_default_context: If set to :code:`True` the SSL context is created using systems defaults.
    :code:`ssl.protocol` and :code:`ssl.ciphers` will be ignored.
    (default: :code:`'prefer'`)
:ssl.check_hostname: If set to :code:`True` chksrv verifies if the SSL certificate commonName
    matches the connected hostname. (default: :code:`False`)
:ssl.protocol: SSL protocol to use. Possible values:

    - :code:`tls` (default)
    - :code:`sslv2`
    - :code:`sslv3`
    - :code:`tlsv1`
    - :code:`tlsv1.1`
    - :code:`tlsv1.2`

:ssl.ciphers: The cipher suite to use.
    Must be a valid OpenSSL cipher suite string. (default: :code:`ALL`)
:ssl.verify_mode: SSL verify mode. cf. `ssl.VerifyMode <https://docs.python.org/3.7/library/ssl.html#ssl.VerifyMode>`_ (default: :code:`CERT_OPTIONAL`)
:ssl.verify_flags: SSL verify flags. cf. `ssl.VerifyFlags <https://docs.python.org/3.7/library/ssl.html#ssl.VerifyFlags>`_ (default: :code:`VERIFY_DEFAULT`)
:ssl.ca: Directory or file containing x509 certifcates of
    trusted Certificate Authorities. By setting it to :code:`__sys__`
    *chksr* tries to load the system default trusted certificates.

Results
.......

:ssl.success: :code:`True` if the SSL handshake was successful
:ssl.con.cert: Parsed x509 certificate the server used to authenticate itself
:ssl.con.cipher: Negotiated cipher used to this connection
:ssl.con.compression: Compression algorithm for this connection or :code:`None`
:ssl.con.alpn_protocol: ALPN protocol selected during the TLS handshake
    or :code:`None`
:ssl.con.npn_protocol: NPN protocol selected during the SSL/TLS handshake
    or :code:`None`
:ssl.con.ssl_version: Actual SSL protocol version negotiated for this connection
    or :code:`None` if no secure connection was established
:ssl.con.server_hostname: Hostname of the server
:ssl.con.cert.matches_hostname: :code:`True` if the server hostname matches the
    certificate commonName

HTTP
''''

The HTTP module is intended to be used to check web services,
and relies on either the TCP or SSL module to establish
the underlying socket connection. Depending if the URL is
specified with :code:`http://` or :code:`https://`.

Consequently *all parameters from either only the TCP module or both
the TCP and SSL module are available in addition*

Parameters
..........

:http.method: HTTP method of the request. Possible values:

    * :code:`GET` (default)
    * :code:`HEAD`
    * :code:`POST`
    * :code:`PUT`
    * :code:`DELETE`
    * :code:`OPTIONS`
    * :code:`PATCH`
    * :code:`TRACE`

:http.body: Body to attach to the request. (default: :code:`None`)

Results
.......

:http.success: :code:`True` if the HTTP request was successful.
    (Does not evaluate the returned status code)
:http.resp.status: HTTP response status code (numeric)
:http.resp.reason: HTTP response reason (e.g. :code:`Found`)
:http.resp.version: HTTP version
:http.resp.body: HTTP response body
:http.resp.body_length: Actual size of the HTTP response body.
    (Does not read :code:`Content-Length` header)
:http.resp.header.*: Collection of response headers, converted to lower-case snake_case.
    So the header field :code:`Content-Length` is available as
    :code:`http.resp.header.content_length`. If a header field appears multiple
    times in the response header (e.g. :code:`Set-Cookie`) the value
    is provided as list.





