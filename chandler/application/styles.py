"""
This is an experiment in light weight "styles", i.e., configuration read
from a file, with the aim of making it easy for the design team to tweak
graphical details without mucking about in Python.

This approach is intended to be complementary to persisting layout details that
can be changed by users in the course of using chandler.
"""

import ConfigParser, os

cfg = None

class AcceptEmptyConfig(ConfigParser.SafeConfigParser):
    def get(self, *args, **kwargs):
        try:
            return ConfigParser.SafeConfigParser.get(self, *args, **kwargs)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None

def loadConfig():
    global cfg
    cfg = AcceptEmptyConfig()
    cfg.read(os.path.join(os.path.dirname(__file__), 'styles.conf'))

loadConfig()