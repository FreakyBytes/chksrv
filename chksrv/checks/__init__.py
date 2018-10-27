"""
chksrv - check-service a tool to probe and check the health of services.

Package of available chekcs
"""


from .base import BaseCheck, start_timer, stop_timer
from .ip import TcpCheck, IcmpPingCheck
from .dns import DnsCheck
from .ssl import SslCheck
from .http import HttpCheck