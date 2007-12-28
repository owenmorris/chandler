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

from i18n import MessageFactory, Message
from application import schema

from chandlerdb.schema.c import CAttribute
from chandlerdb.persistence.c import Record
from chandlerdb.schema.Types import UString

STRING  = 0
LSTRING = 1


class LocalizableString(UString):
    __metaclass__ = schema.TypeClass

    def getFlags(self):
        return CAttribute.PURE

    def recognizes(self, value):
        res = type(value) is Message

        if res:
            return True

        return super(LocalizableString, self).recognizes(value)


    def getImplementationType(self):
        return Message

    def writeValue(self, itemWriter, record, item, version, value, withSchema):

        if type(value) == unicode or type(value) ==  str:
            record += (Record.BYTE, STRING,
                       Record.STRING, value)

        else:
            record += (Record.BYTE, LSTRING,
                       Record.STRING, value.project,
                       Record.STRING, value.catalog_name,
                       Record.STRING, value.msgid)
        return 0

    def readValue(self, itemReader, offset, data, withSchema, view, name,
                  afterLoadHooks):

        type = data[offset]

        if type == LSTRING:
            project, catalog_name, msgid = data[offset+1:offset+4]
            return offset+4, MessageFactory(project, catalog_name)(msgid)
        else:
            value = data[offset+1]
            return offset+2, value
