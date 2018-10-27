"""
chksrv - Base Check Module.
"""

import typing
import logging

from chksrv.config import OptionDict


class BaseCheck(object):
    """chksrv - BaseCheck class."""

    log = logging.getLogger('BASE')
    default_options = {}

    def __init__(self, options: typing.Dict[str, typing.Any] = {}):
        self.options = OptionDict(defaults=self.default_options)
        self.options.update(options)
        self.results = {}  # dict containing all observations from the check

    def run(self):
        """Runs the check, gather information and terminates the connection.
        
        Basically short hand for get_connection() and close_connection()
        """
        raise NotImplementedError()

    def get_connection(self):
        """Establishes the connection and gather information returns the connection object."""
        raise NotImplementedError()

    def close_connection(self, connection):
        """Closes a connection made by this check class."""
        raise NotImplementedError()