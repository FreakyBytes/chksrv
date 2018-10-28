"""
chksrv - Exceptions.
"""

class ChksrvBaseException(BaseException):
    pass


class ChksrvConfigException(ChksrvBaseException):
    pass


class ChksrvNotReadyError(ChksrvBaseException):
    pass