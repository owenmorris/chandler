
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class SingleRef(object):

    __slots__ = "_uuid"

    def __init__(self, uuid):

        super(SingleRef, self).__init__()
        self._uuid = uuid

    def __str__(self):

        return self._uuid.str64()

    def __repr__(self):

        return "<ref: %s>" %(self._uuid.str16())

    def __getstate__(self):

        return self._uuid._uuid

    def __setstate__(self, state):

        self._uuid = UUID(state)
    
    def getUUID(self):

        return self._uuid

    def __cmp__(self, other):

        if not isinstance(other, SingleRef):
            raise TypeError, type(other)
        
        return self._uuid.__cmp__(other._uuid)
