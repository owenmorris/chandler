__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
Low level Access Control List (ACL) API for WebDAV.

One could construct an ACL object like this, starting with ACE:

>>> allACE = ACE(principal='all', deny=(), grant=('read', 'DAV:'))
>>> allACE.grant('write', 'http://www.xythos.com/namespaces/StorageServer/acl/')
>>> print allACE
<D:ace><D:principal><D:all/></D:principal><D:grant><D:privilege><D:read/></D:privilege><D:privilege><ns-1:write/></D:privilege></D:grant></D:ace>

Then creating the actual ACL by passing in the ACE:
    
>>> acl = ACL(acl=[allACE])
>>> print acl
<D:acl xmlns:D="DAV:" xmlns:ns-1="http://www.xythos.com/namespaces/StorageServer/acl/" ><D:ace><D:principal><D:all/></D:principal><D:grant><D:privilege><D:read/></D:privilege><D:privilege><ns-1:write/></D:privilege></D:grant></D:ace></D:acl>

TODO:
    * Parse ACLs from XML.
    * Complete the API.
    * Might want to rething a more user friendly API.
    * Higher level API:
        - pythonic (raise exceptions on errors, return python objects
          instead of XML etc.)
        - combine WebDAV operations into one call, for example
          when setting ACL we should lock resource
        - add a higher level API to modify ACLs (currently only get and set)
        - read and understand server mappings for ACL, and respond to requests
          in a smart way - for example if want to set read access but there
          is no read per se but it consists of finer graned properties then
          detect and set these automatically
        - figure out protected properties
"""

class ACE(object):
    """
    Access Control Entry consists of all the deny and grant rules for a
    principal. An ACE defines the complete access control definition for a
    single principal.
    """
    def __init__(self, principal, deny=(), grant=()):
        """
        @param principal: Principal name (in DAV: namespace) or URL.
        @param deny:      Tuple of privilege name and privilege namespace
        @param grant:     Tuple of privilege name and privilege namespace
        """
        self._principal = _Principal(principal)
        self._deny  = _Deny(deny)
        self._grant = _Grant(grant)

    def deny(self, privilege, namespace='DAV:'):
        self._deny.add(privilege, namespace)

    def grant(self, privilege, namespace='DAV:'):
        self._grant.add(privilege, namespace)

    def namespaces(self):
        return self._deny.namespaces() + self._grant.namespaces()

    def mapPrefixes(self, map):
        self._deny.mapPrefixes(map)
        self._grant.mapPrefixes(map)

    def __str__(self):
        return '<D:ace>%s%s%s</D:ace>' %(str(self._principal),
                                         str(self._deny),
                                         str(self._grant))

class ACL(object):
    """
    Access Control List (ACL) consists of one of more ACEs. ACL defines all
    the access control definitions for a single resource.
    """
    def __init__(self, acl=[]):
        self.acl = acl

    def add(self, ace):
        self.acl += [ace]

    def __str__(self):
        acl = '<D:acl xmlns:D="DAV:" '
        s = ''
        nsCounter = 1

        namespaces = []
        for ace in self.acl:
            namespaces += ace.namespaces()

        map = {'DAV:': 'D'}
        for namespace in namespaces:
            if not map.has_key(namespace[1]):
                map[namespace[1]] = 'ns-' + str(nsCounter)
                acl += 'xmlns:ns-%d="%s" ' %(nsCounter, namespace[1])
                nsCounter += 1

        for ace in self.acl:
            ace.mapPrefixes(map)
            s += str(ace)

        return '%s>%s</D:acl>' %(acl, s)

class _Principal(object):
    def __init__(self, url):
        """
        Principal.

        @param url: Either principal URL or one of 'all', 'self',
                    'authenticated', 'unauthenticated', 'owner'
        """
        self.url = url

    def __str__(self):
        if self.url in ('all', 'self', 'authenticated', 'unauthenticated',
                        'owner'):
            return '<D:principal><D:%s/></D:principal>' %(self.url)
        else:
            return '<D:principal><D:href>%s</D:href></D:principal>' %(self.url)

class _Privileges(object):
    """
    The set of privileges.
    """
    def __init__(self, privilege=()):
        """
        @param privilege: Privilege is a tuple of privilege name and
                          privilege namespace.
        """
        if privilege is not ():
            if privilege[1] == 'DAV:':
                prefix = 'D'
                self.nsCounter = 0
            else:
                self.nsCounter = 1
                prefix = 'ns-1'
            self.privileges = {privilege[0] : [prefix, privilege[1]]}
        else:
            self.privileges = {}

    def add(self, name, namespace='DAV:'):
        if namespace == 'DAV:':
            prefix = 'D'
        else:
            self.nsCounter += 1
            prefix = 'ns-%d' %(self.nsCounter)
        self.privileges[name] = [prefix, namespace]

    def namespaces(self):
        return self.privileges.values()

    def mapPrefixes(self, map):
        names = self.privileges.keys()
        for name in names:
            if map.has_key(self.privileges[name][1]):
                self.privileges[name][0] = map[self.privileges[name][1]]

    def __str__(self):
        s = ''
        names = self.privileges.keys()
        for name in names:
            s += '<D:privilege><%s:%s/></D:privilege>' %(self.privileges[name][0], name) 
        return s

class _Grant(_Privileges):
    """
    The set of privileges to grant.
    """
    def __str__(self):
        if self.privileges:
            # Why doesn't this work?: super(_Privileges, self).__str__()
            return '<D:grant>%s</D:grant>' %(_Privileges.__str__(self))
        else:
            return ''

class _Deny(_Privileges):
    """
    The set of privileges to deny.
    """
    def __str__(self):
        if self.privileges:
            # Why doesn't this work?: super(_Privileges, self).__str__()
            return '<D:deny>%s</D:deny>' %(_Privileges.__str__(self))
        else:
            return ''

if __name__ == '__main__':
    import doctest
    doctest.testmod()
