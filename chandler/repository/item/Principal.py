
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Item import Item


class Principal(Item):

    def isMemberOf(self, pid):
    
        if pid == self._uuid:
            return True

        principals = self.getAttributeValue('principals', self._references,
                                            None, None)
        if principals:

            if pid in principals:
                return True

            for principal in principals:
                if principal.isMemberOf(pid):
                    return True

        return False
