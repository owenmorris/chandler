#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


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
