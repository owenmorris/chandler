
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class Permission(object):

    READ    = 0x0001
    WRITE   = 0x0002
    REMOVE  = 0x0004
    CHANGE  = 0x0008


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

    def _xmlValue(self, key, generator, mode):

        generator.startElement('acl', { 'name': key })
        for ace in self:
            ace._xmlValue(generator, mode)
        generator.endElement('acl')


class ACE(object):

    def __init__(self, pid, perms, deny=False):

        super(ACE, self).__init__()

        self.pid = pid
        self.perms = perms
        self.deny = deny

    def verify(self, principal, perms):

        if not principal.isMemberOf(self.pid):
            return (0, 0)

        if self.deny:
            return (0, perms & self.perms)
        else:
            return (perms & self.perms, 0)

    def _xmlValue(self, generator, mode):

        attrs = { 'pid': self.pid.str64() }
        if self.deny:
            attrs['deny'] = 'True'
            
        generator.startElement('ace', attrs)
        generator.characters(str(self.perms))
        generator.endElement('ace')
