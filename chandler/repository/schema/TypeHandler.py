
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from chandlerdb.util.UUID import UUID
from repository.util.Path import Path
from repository.util.SingleRef import SingleRef
from repository.util.ClassLoader import ClassLoader


class TypeHandler(object):

    def makeValue(cls, typeName, data):

        try:
            return cls.typeDispatch[typeName](data)
        except KeyError:
            raise ValueError, "Unknown type %s for data: %s" %(typeName, data)

    def typeHandler(cls, view, value):

        try:
            for t in cls.typeHandlers[view][type(value)]:
                if t.recognizes(value):
                    return t
        except KeyError:
            pass

        typeKind = cls.typeHandlers[view][None]
        types = typeKind.findTypes(value)
        if types:
            return types[0]
            
        raise TypeError, 'No handler for values of type %s' %(type(value))

    def makeString(cls, view, value):

        return cls.typeHandler(view, value).makeString(value)


    typeHandler = classmethod(typeHandler)
    makeString = classmethod(makeString)
    makeValue = classmethod(makeValue)

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
        'class': lambda(data): ClassLoader.loadClass(data),
        'none': lambda(data): None,
    }
