"""
chksrv - Base Check Module.
"""

import typing


class BaseCheck(object):
    """chksrv - BaseCheck class."""

    def __init__(self, params: typing.Dict[str, typing.Any]):
        self.params = params