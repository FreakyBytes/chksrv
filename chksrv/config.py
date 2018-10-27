"""
chksrv - config helper classes.
"""


class OptionDict(dict):
    """OptionsDict extends the build in Python dict, but takes a dict of default values."""

    def __init__(self, defaults={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._defaults = defaults

    def __missing__(self, key):
        return self._defaults[key]