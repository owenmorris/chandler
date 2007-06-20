#   Copyright (c) 2007 Open Source Applications Foundation
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

from i18n import ChandlerMessageFactory as _m_
from application import schema

from chandlerdb.schema.c import CAttribute
from repository.schema.Types import UString


class LocalizableString(UString):
    __metaclass__ = schema.TypeClass

    def getFlags(self):
        return CAttribute.PURE

    def makeValue(self, data):
        return _m_(unicode(data))

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):
        return offset+1, _m_(data[offset])
