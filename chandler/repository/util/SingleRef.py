
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class SingleRef(object):
    """
    Wraps a L{UUID<chandlerdb.util.uuid.UUID>} to form a uni-directional
    reference to an item.

    Direct use of this type is not necessary since setting an item as a value
    into an attribute not setup for bi-directional references causes a value
    of this type to be set instead. Similarly, instead of returning a value
    of this type, the data model returns the referenced item.
    """

    __slots__ = "_uuid"

    def __init__(self, uuid):

        super(SingleRef, self).__init__()
        self._uuid = uuid

    def __str__(self):

        return str(self._uuid)

    def __repr__(self):

        return "<ref: %s>" %(self._uuid.str16())

    def __getstate__(self):

        return self._uuid._uuid

    def __setstate__(self, state):

        self._uuid = UUID(state)
    
    def __getUUID(self):

        return self._uuid

    def __hash__(self):

        return hash(self._uuid)

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

    itsUUID = property(__getUUID)
    
