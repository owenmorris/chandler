#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


# List of modules/packages that are usable as "APIs" by scripting and
# development tools
# 

# When you uncomment this, make sure you list EVERYTHING that is supposed to be
# public. Otherwise things like epydoc think that everything that is not listed
# is private and will not provide documentation for it.
#__all__ = ['startup']

class ChandlerException(Exception):
    __slots__ = ['message', "exception", 'debugMessage']

    def __init__(self, message, exception=None, debugMessage=None):
        assert message is not None

        self.message = unicode(message)
        self.debugMessage = debugMessage
        self.exception = exception

    def __str__(self):
        if self.debugMessage is not None:
            return self.debugMessage

        return self.message.encode("utf-8")

    def __unicode__(self):
        return self.message

from preferences import Preferences
