__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

"""
Low level Access Control List (ACL) API for WebDAV.

These two methods can be added to the actual dav object (davlib, WebDAV).

  def getacl(self, url, principal=None):
    # XXX Strictly speaking this method is not needed, you could use propfind,
    #     or getprops
    body = XML_DOC_HEADER + \
           '<D:propfind xmlns:D="DAV:"><D:prop><D:acl/></D:prop></D:propfind>'
    aclResponse = self.propfind(url, body)
    return aclResponse

  def setacl(self, url, acl, extra_hdrs={ }):
    #url is the resource who's acl we are changing
    #acl is an ACL object that sets the actual ACL
    body = XML_DOC_HEADER + str(acl)
    headers = extra_hdrs.copy()
    headers['Content-Type'] = XML_CONTENT_TYPE
    return self._request('ACL', url, body, headers)

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

class Principal:
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

class DenyOrGrant:
    # XXX This could use a better name
    def __init__(self, privileges):
        self.privileges = privileges

    def namespaces(self):
        l = []
        if self.privileges:
            l += self.privileges.namespaces()
        return l

    def mapPrefixes(self, map):
        if self.privileges:
            self.privileges.mapPrefixes(map)

class Grant(DenyOrGrant):
    """
    The set of privileges to grant.
    """
    def __str__(self):
        if self.privileges:
            return '<D:grant>%s</D:grant>' %(str(self.privileges))
        else:
            return ''

class Deny(DenyOrGrant):
    """
    The set of privileges to deny.
    """
    def __str__(self):
        if self.privileges:
            return '<D:deny>%s</D:deny>' %(str(self.privileges))
        else:
            return ''

class Privileges:
    """
    The set of privileges.
    """
    def __init__(self, name, namespace='DAV:'):
        if namespace == 'DAV:':
            prefix = 'D'
            self.nsCounter = 0
        else:
            self.nsCounter = 1
            prefix = 'ns-1'
        self.privileges = {name : [prefix, namespace]}

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
        str = ''
        names = self.privileges.keys()
        for name in names:
            str += '<D:privilege><%s:%s/></D:privilege>' %(self.privileges[name][0], name) 
        return str
    
class ACE:
    """
    Access Control Entry consists of all the deny and grant rules for a
    principal. An ACE defines the complete access control definition for a
    single principal.
    """
    def __init__(self,
                 principal,
                 denyOrGrantList):
        self.aces = {principal: denyOrGrantList}

    def add(self, principal, denyOrGrantList):
        if self.aces.has_key(principal):
            self.aces[principal] = self.aces[principal] + denyOrGrant
        else:
            self.aces[principal] = denyOrGrantList

    def namespaces(self):
        l = []
        principals = self.aces.keys()
        for principal in principals:
            for denyOrGrant in self.aces[principal]:
                l += denyOrGrant.namespaces()

        return l

    def mapPrefixes(self, map):
        principals = self.aces.keys()
        for principal in principals:
            for denyOrGrant in self.aces[principal]:
                denyOrGrant.mapPrefixes(map)

    def __str__(self):
        s = '<D:ace>'
        principals = self.aces.keys()
        for principal in principals:
            s += str(principal)
            for denyOrGrant in self.aces[principal]:
                s += str(denyOrGrant)
                # XXX order deny first

        return s + '</D:ace>'

class ACL:
    """
    Access Control List (ACL) consists of one of more ACEs.

    One could construct an ACL object like this:

        principal = acl.Principal('all')
        privileges = acl.Privileges('read')
        privileges.add('write',
            'http://www.xythos.com/namespaces/StorageServer/acl/')
        grant = acl.Grant(privileges)
        ace = acl.ACE(principal, [grant])
        acl = acl.ACL([ace])
    """
    def __init__(self, acl=[], xml=None):
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
