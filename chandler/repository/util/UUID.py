
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import UUIDext


class UUID(object):
    """
    Implementation of the IETF's U{UUID draft <www.ics.uci.edu/pub/ietf/webdav/uuid-guid/draft-leach-uuids-guids-01.txt>} spec.

    A UUID is intended to be a globally, universally unique 128 bit number.
    UUID objects can be used as dictionary keys and are comparable.
    """

    __slots__ = ("_uuid", "_hash")
    
    def __init__(self, uuid=None):
        """
        Construct a UUID.

        Generate a new UUID when C{uuid} is C{None} or re-construct a UUID
        instance from a string representation or from the 16 bytes
        equivalent to the 128 bit number.

        @param uuid: a 36 or 22 byte string representation of a UUID or 16
        intrinsic bytes, C{None} by default.
        @type uuid: a string
        """

        super(UUID, self).__init__()

        if uuid is None:
            self._uuid = UUIDext.make()
        else:
            self._uuid = UUIDext.make(str(uuid))
            if not self._uuid:
                raise ValueError, "Generating UUID from '%s' failed" %(uuid)

        self._hash = UUIDext.hash(self._uuid)

    def __repr__(self):

        try:
            return '<UUID: %s>' % UUIDext.toString(self._uuid)
        except Exception:
            return super(UUID, self).__repr__()

    def __str__(self):

        try:
            return UUIDext.toString(self._uuid)
        except Exception:
            return super(UUID, self).__str__()

    def __hash__(self):

        return self._hash

    def __getstate__(self):

        return self._uuid

    def __setstate__(self, state):

        self._uuid = state
        self._hash = UUIDext.hash(state)

    def __eq__(self, other):

        return isinstance(other, UUID) and self._uuid == other._uuid

    def __ge__(self, other):

        return isinstance(other, UUID) and self._uuid >= other._uuid

    def __gt__(self, other):

        return isinstance(other, UUID) and self._uuid > other._uuid

    def __le__(self, other):

        return isinstance(other, UUID) and self._uuid <= other._uuid

    def __lt__(self, other):

        return isinstance(other, UUID) and self._uuid < other._uuid

    def __ne__(self, other):

        return isinstance(other, UUID) and self._uuid != other._uuid

    def str16(self):
        """
        Get a standard hexadecimal string representation of this UUID.

        This string is in the format abf5678c-9d49-11d7-e690-000393db837c and
        is 36 characters long.

        @return: a string
        """

        return UUIDext.toString(self._uuid)

    def str64(self):
        """
        Get a shorter base64 encoded string representation of this UUID.

        This string is 22 characters long and looks like this
        aLRpUOtih7neqg00ejSUdY.

        @return: a string
        """

        return UUIDext.to64String(self._uuid)


if __name__ == "__main__":
    print UUID().str16()
