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

import os
from configobj import ConfigObj
from ConfigParser import DuplicateSectionError, NoSectionError
import PyICU

ICUnumberParse = PyICU.NumberFormat.createInstance(PyICU.Locale.getUS()).parse
cfg = None

class AcceptEmptyConfig(ConfigObj):
    # legacy interface to mimic ConfigParser
    # (not a 100% complete)
    def sections(self):
        return self.keys()
    
    def add_section(self, section):
        if self.hasKey(unicode(section)):
            raise DuplicateSectionError
        self[unicode(section)] = {}
    
    def has_section(self, section):
        return self.hasKey(unicode(section))
        
    def options(self, section):
        if self.hasKey(unicode(section)):
            return self[unicode(section)].items()
        return []
    
    def has_option(self, section, option):
        return self.hasKey(unicode(section)) and self[unicode(section)].hasKey(unicode(option))

    def get(self, section, option):
        try:
             entry = self[unicode(section)][unicode(option)]
             if isinstance(entry, list):
                 entry = u", ".join(entry)
             elif not (isinstance(entry, str) or isinstance(entry, unicode)):
                 entry = unicode(entry)
             # hack for color entries
             if entry.startswith(u"rgb"):
                 entry = u"#%s" % entry[3:9]
             return entry
        except:
            return None

    def getint(self, section, option):
        try:
            return self[unicode(section)].as_int(unicode(option))
        except:
            return None

    def getfloat(self, section, option):
        try:
            numberAsString = self[unicode(section)][unicode(option)]
            return ICUnumberParse(numberAsString).getDouble()
        except:
            return None

    def getboolean(self, section, option):
        try:
            return self[unicode(section)].as_bool(unicode(option))
        except:
            return None

    def items(self, section):
        try:
            return self[unicode(section)].items()
        except:
            return []
        
    def set(self, section, option, value):
        if self.hasKey(unicode(section)):
            self[unicode(section)][unicode(option)] = value
        else:
            raise NoSectionError
        
    def remove_option(self, section, option):
        if self.hasKey(unicode(section)):
            if self[unicode(section)].hasKey(unicode(option)):
                del self[unicode(section)][unicode(option)]
                return True
            else:
                return False
        else:
            raise NoSectionError
        
    def remove_section(self, section):
        if self.hasKey(unicode(section)):
            del self[unicode(section)]
            return True
        else:
            return False

def loadConfig():
    global cfg
    cfg = AcceptEmptyConfig(os.path.join(os.path.dirname(__file__), 'styles.conf'), encoding="UTF8")

loadConfig()
