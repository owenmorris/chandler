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


from chandlerdb.item.c import isitem, ItemRef
from chandlerdb.util.c import UUID, Nil
from chandlerdb.util.Path import Path


class TypeHandler(object):

    @classmethod
    def typeHandler(cls, view, value):

        try:
            method = getattr(type(value), 'getTypeItem', None)
            if method is not None:
                return method(value, view)
            else:
                for t in cls.typeHandlers[view][type(value)]:
                    if t.recognizes(value):
                        return t
        except KeyError:
            pass

        if isitem(value):
            return cls.typeHandlers[view][ItemRef][0]

        typeKind = cls.typeHandlers[view][None]
        types = typeKind.findTypes(value)
        if types:
            return types[0]
            
        raise TypeError, 'No handler for values of type %s' %(type(value))

    @classmethod
    def makeString(cls, view, value):

        return cls.typeHandler(view, value).makeString(value)

    @classmethod
    def makeValue(cls, view, typeName, data):

        if typeName == 'class':
            return view.classLoader.loadClass(data)
        elif typeName == 'ref':
            return ItemRef(UUID(data), view)

        try:
            return cls.typeDispatch[typeName](data)
        except KeyError:
            raise ValueError, "Unknown type '%s' for data: %s" %(typeName, data)

    @classmethod
    def hashValue(cls, view, value):

        return cls.typeHandler(view, value).hashValue(value)

    @classmethod
    def clear(cls, view):

        try:
            cls.typeHandlers[view].clear()
        except KeyError:
            pass

    typeHandlers = {}
    typeDispatch = {
        'str': str,
        'unicode': unicode,
        'uuid': UUID,
        'path': Path,
        'bool': lambda(data): data != 'False',
        'int': int,
        'long': long,
        'float': float,
        'complex': complex,
        'none': Nil,
    }
