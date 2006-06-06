
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.item.c import isitem
from chandlerdb.util.c import UUID, SingleRef
from repository.util.Path import Path


class TypeHandler(object):

    @classmethod
    def typeHandler(cls, view, value):

        try:
            for t in cls.typeHandlers[view][type(value)]:
                if t.recognizes(value):
                    return t
        except KeyError:
            pass

        if isitem(value):
            return cls.typeHandlers[view][SingleRef][0]

        try:
            typeKind = cls.typeHandlers[view][None]
        except KeyError:
            print type(value), value
            raise
        
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
        'ref': lambda(data): SingleRef(UUID(data)),
        'bool': lambda(data): data != 'False',
        'int': int,
        'long': long,
        'float': float,
        'complex': complex,
        'none': lambda(data): None,
    }
