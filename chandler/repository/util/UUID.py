
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import UUIDext


class UUID(object):
    '''Implementation of UUID spec at http://www.ics.uci.edu/pub/ietf/webdav/uuid-guid/draft-leach-uuids-guids-01.txt.

    A UUID is intended to be globally unique in the entire universe.
    It is a 128 bit number.
    UUID objects can be used as dictionary keys and are comparable.'''
    
    def __init__(self, uuid=None):

        super(UUID, self).__init__()

        if uuid is None:
            self._uuid = UUIDext.make()
        else:
            self._uuid = UUIDext.make(uuid)
            if not self._uuid:
                raise ValueError, "Generating UUID from '%s' failed" %(uuid)
            
    def __repr__(self):

        try:
            return UUIDext.toString(self._uuid)
        except AttributeError:
            return super(UUID, self).__repr__()

    def __hash__(self):

        return UUIDext.hash(self._uuid)
    
    def __eq__(self, other):

        return isinstance(other, UUID) and self._uuid == other._uuid

    def __ge__(self, other):

        return self._uuid >= other._uuid

    def __gt__(self, other):

        return self._uuid > other._uuid

    def __le__(self, other):

        return self._uuid <= other._uuid

    def __lt__(self, other):

        return self._uuid < other._uuid

    def __ne__(self, other):

        return self._uuid != other._uuid

    def str16(self):
        '''Return the standard hexadecimal string representation of this UUID.

        This string is in the format abf5678c-9d49-11d7-e690-000393db837c and
        is always 36 characters long.'''

        return UUIDext.toString(self._uuid)

    def str64(self):
        '''Return a shorter base64 encoded string representation of this UUID.

        This string is always 22 characters long and looks like this
        aLRpUOtih7neqg00ejSUdY.'''

        return UUIDext.to64String(self._uuid)


if __name__ == "__main__":
    print UUID().str16()
