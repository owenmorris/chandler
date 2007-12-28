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


from chandlerdb.util.c import _hash, _combine
from chandlerdb.schema.c import CAttribute
from chandlerdb.schema.Types import Type
from chandlerdb.schema.TypeHandler import TypeHandler


class Alias(Type):

    def getImplementationType(self):
        return None

    def isAlias(self):
        return True

    def getFlags(self):

        flags = CAttribute.ALIAS

        if 'types' in self._references:
            for t in self._references['types']:
                flags |= t.getFlags()
        else:
            flags |= CAttribute.PROCESS

        return flags

    def type(self, value):

        if 'types' in self._references:
            for t in self._references['types']:
                if t.recognizes(value):
                    return t
        else:
            return TypeHandler.typeHandler(self.itsView, value)

        return None
        
    def recognizes(self, value):

        if 'types' not in self._references:
            return True
        
        for t in self.types:
            if t.recognizes(value):
                return True

        return False
    
    def typeXML(self, value, generator):

        if 'types' not in self._references:
            super(Alias, self).typeXML(value, generator)
            return

        for t in self.types:
            if t.recognizes(value):
                t.typeXML(value, generator)
                return

        raise TypeError, "value '%s' of type '%s' unrecognized by %s" %(value, type(value), self.itsPath)

    def writeValue(self, itemWriter, record, item, version, value, withSchema):

        if 'types' not in self._references:
            return super(Alias, self).writeValue(itemWriter, record, item,
                                                 version, value, withSchema)

        for t in self.types:
            if t.recognizes(value):
                return t.writeValue(itemWriter, record, item,
                                    version, value, withSchema)

        raise TypeError, "value '%s' of type '%s' unrecognized by %s" %(value, type(value), self.itsPath)

    def hashItem(self):
        """
        Compute a hash value from this aliase's schema.

        The hash value is computed from the aliase's path and types.

        @return: an integer
        """

        hash = _hash(str(self.itsPath))
        if 'types' in self._references:
            for t in self.types:
                hash = _combine(hash, t.hashItem())

        return hash
