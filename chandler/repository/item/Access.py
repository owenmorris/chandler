
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class Permission(object):

    DENY    = 0x0001
    READ    = 0x0002
    WRITE   = 0x0004
    REMOVE  = 0x0008
    CHANGE  = 0x0010


class AccessDeniedError(Exception):
    pass


class ACL(list):

    def verify(self, principal, pid, perms):

        grant = deny = 0

        for ace in self:
            on, off = ace.verify(principal, pid, perms)
            grant |= on
            deny |= off

            if grant == perms or deny == perms:
                break

        return grant & ~deny


class ACE(object):

    def __init__(self, pid, perms, deny=False):

        super(ACE, self).__init__()

        self.pid = pid
        self.perms = perms

        if deny:
            self.perms |= Permission.DENY

    def __repr__(self):

        return '<ACE: %s 0x%0.8x>' %(self.pid.str64(), self.perms)

    def verify(self, principal, perms):

        if not principal.isMemberOf(self.pid):
            return (0, 0)

        if self.perms & Permission.DENY:
            return (0, perms & self.perms)
        else:
            return (perms & self.perms, 0)
