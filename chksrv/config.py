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
chksrv - config helper classes.
"""

import typing
from datetime import date, time, datetime


def parse_option_value(value: str):
    """Takes a string option value and tries to cast it to a more fitting type."""

    if value.lower() in ('true', 'yes', 'y'):
        return True
    elif value.lower() in ('false', 'no', 'n'):
        return False

    for fct in (int, float, complex, date.fromisoformat, time.fromisoformat, datetime.fromisoformat):
        try:
            return fct(value)
        except ValueError:
            pass

    return value


class OptionDict(dict):
    """OptionsDict extends the build in Python dict, but takes a dict of default values."""

    def __init__(self, defaults={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._defaults = defaults

    def __missing__(self, key):
        return self._defaults[key]
