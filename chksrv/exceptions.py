"""
chksrv - check-service a tool to probe and check the health of services.

Exceptions
"""

class ChksrvBaseException(BaseException):
    pass


class ChksrvConfigException(ChksrvBaseException):
    pass