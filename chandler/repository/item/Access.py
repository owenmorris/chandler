
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class Permission(object):

    READ    = 0x0001
    WRITE   = 0x0002
    REMOVE  = 0x0004


class AccessDeniedError(Exception):
    pass

