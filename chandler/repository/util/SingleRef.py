
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

    def __eq__(self, other):

        return isinstance(other, SingleRef) and self._uuid.__eq__(other._uuid)

    def __ge__(self, other):

        return isinstance(other, SingleRef) and self._uuid.__ge__(other._uuid)

    def __gt__(self, other):

        return isinstance(other, SingleRef) and self._uuid.__gt__(other._uuid)

    def __le__(self, other):

        return isinstance(other, SingleRef) and self._uuid.__le__(other._uuid)

    def __lt__(self, other):

        return isinstance(other, SingleRef) and self._uuid.__lt__(other._uuid)

    def __ne__(self, other):

        return isinstance(other, SingleRef) and self._uuid.__ne__(other._uuid)
