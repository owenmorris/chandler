"""
@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm

Low level Access Control List (ACL) API for WebDAV.

One could construct an ACL object like this, starting with ACE:

>>> allACE = ACE(principal='all', deny=(), grant=('read', 'DAV:'))
>>> allACE.grant('write', 'http://www.xythos.com/namespaces/StorageServer/acl/')
>>> print allACE
<D:ace>
<D:principal><D:all/></D:principal>
<D:grant>
<D:privilege><D:read/></D:privilege>
<D:privilege><ns-1:write/></D:privilege>
</D:grant>
</D:ace>
<BLANKLINE>

Then creating the actual ACL by passing in the ACE:
    
>>> aclObj = ACL(acl=[allACE])
>>> print aclObj
<D:acl xmlns:D="DAV:" xmlns:ns-1="http://www.xythos.com/namespaces/StorageServer/acl/" >
<D:ace>
<D:principal><D:all/></D:principal>
<D:grant>
<D:privilege><D:read/></D:privilege>
<D:privilege><ns-1:write/></D:privilege>
</D:grant>
</D:ace>
</D:acl>

Let's play with the ACE object some more:

>>> allACE.deny('yawn', 'http://www.example.com/namespaces/acl/')
>>> print allACE
<D:ace>
<D:principal><D:all/></D:principal>
<D:deny><D:privilege><ns-1:yawn/></D:privilege>
</D:deny>
<D:grant>
<D:privilege><D:read/></D:privilege>
<D:privilege><ns-1:write/></D:privilege>
</D:grant>
</D:ace>
<BLANKLINE>
>>> print allACE._deny.privileges['yawn']
['ns-1', 'http://www.example.com/namespaces/acl/']
>>> allACE.deny('yawn', 'http://www.example.com/namespaces/fooledya/acl/')
>>> print allACE
<D:ace>
<D:principal><D:all/></D:principal>
<D:deny><D:privilege><ns-2:yawn/></D:privilege>
</D:deny>
<D:grant>
<D:privilege><D:read/></D:privilege>
<D:privilege><ns-1:write/></D:privilege>
</D:grant>
</D:ace>
<BLANKLINE>
>>> print allACE._deny.privileges['yawn']
['ns-2', 'http://www.example.com/namespaces/fooledya/acl/']
>>> allACE.protected = True
>>> print allACE
<BLANKLINE>
>>> allACE.protected = False
>>> print allACE
<D:ace>
<D:principal><D:all/></D:principal>
<D:deny><D:privilege><ns-2:yawn/></D:privilege>
</D:deny>
<D:grant>
<D:privilege><D:read/></D:privilege>
<D:privilege><ns-1:write/></D:privilege>
</D:grant>
</D:ace>
<BLANKLINE>
>>> allACE._deny = _Deny(())
>>> print allACE
<D:ace>
<D:principal><D:all/></D:principal>
<D:grant>
<D:privilege><D:read/></D:privilege>
<D:privilege><ns-1:write/></D:privilege>
</D:grant>
</D:ace>
<BLANKLINE>

You can also modify the ACL object:

>>> aclObj.add(allACE)
Traceback (most recent call last):
  File "<stdin>", line 1, in ?
  File "acl.py", line 95, in add
    raise ValueError, 'ace already added'
ValueError: ace already added
>>> dummyACE = ACE(principal='http://example.com/users/dummy', deny=(), grant=('read', 'DAV:'))
>>> aclObj.add(dummyACE)
>>> print aclObj
<D:acl xmlns:D="DAV:" xmlns:ns-1="http://www.xythos.com/namespaces/StorageServer/acl/" >
<D:ace>
<D:principal><D:all/></D:principal>
<D:grant>
<D:privilege><D:read/></D:privilege>
<D:privilege><ns-1:write/></D:privilege>
</D:grant>
</D:ace>
<D:ace>
<D:principal><D:href>http://example.com/users/dummy</D:href></D:principal>
<D:grant>
<D:privilege><D:read/></D:privilege>
</D:grant>
</D:ace>
</D:acl>
>>> aclObj.remove(dummyACE)
>>> aclObj.remove(dummyACE)
Traceback (most recent call last):
  File "<stdin>", line 1, in ?
  File "acl.py", line 99, in remove
    self.acl.remove(ace)
ValueError: list.remove(x): x not in list
>>> print aclObj
<D:acl xmlns:D="DAV:" xmlns:ns-1="http://www.xythos.com/namespaces/StorageServer/acl/" >
<D:ace>
<D:principal><D:all/></D:principal>
<D:grant>
<D:privilege><D:read/></D:privilege>
<D:privilege><ns-1:write/></D:privilege>
</D:grant>
</D:ace>
</D:acl>

The handiest way to get an ACL object is to parse it from the XML returned
by the server:

>>> parsedACL = parse(str(aclObj))
>>> print str(parsedACL) == str(aclObj)
True

Let's parse real life XML now:

>>> xml = ['<?xml version="1.0" encoding="utf-8" ?>']
>>> xml += ['<D:multistatus xmlns:D="DAV:" xmlns:XS="http://www.w3.org/2001/XMLSchema" xmlns:XSI="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/">']
>>> xml += ['<D:response>']
>>> xml += ['<D:href>https://www.sharemation.com/heikki2/hello.txt</D:href>']
>>> xml += ['     <D:propstat>']
>>> xml += ['        <D:prop>']
>>> xml += ['']
>>> xml += ['<D:acl xmlns:XA="http://www.xythos.com/namespaces/StorageServer/acl/">']
>>> xml += ['']
>>> xml += ['<D:ace>']
>>> xml += ['  <D:principal>']
>>> xml += ['    <D:property><D:owner/></D:property>']
>>> xml += ['  </D:principal>']
>>> xml += ['  <D:grant>']
>>> xml += ['    <D:privilege><D:read/></D:privilege>']
>>> xml += ['    <D:privilege><XA:permissions/></D:privilege>']
>>> xml += ['  </D:grant>']
>>> xml += ['  <D:protected/>']
>>> xml += ['</D:ace>']
>>> xml += ['']
>>> xml += ['<D:ace>']
>>> xml += ['  <D:principal>']
>>> xml += ['    <D:property><D:owner/></D:property>']
>>> xml += ['  </D:principal>']
>>> xml += ['  <D:grant>']
>>> xml += ['    <D:privilege><XA:write/></D:privilege>']
>>> xml += ['    <D:privilege><XA:delete/></D:privilege>']
>>> xml += ['  </D:grant>']
>>> xml += ['</D:ace>']
>>> xml += ['']
>>> xml += ['<D:ace>']
>>> xml += ['  <D:principal>']
>>> xml += ['    <D:all/>']
>>> xml += ['  </D:principal>']
>>> xml += ['  <D:grant/>']
>>> xml += ['</D:ace>']
>>> xml += ['']
>>> xml += ['</D:acl>']
>>> xml += ['']
>>> xml += ['      </D:prop>']
>>> xml += ['       <D:status>HTTP/1.1 200 OK</D:status>']
>>> xml += ['     </D:propstat>']
>>> xml += ['</D:response>']
>>> xml += ['</D:multistatus>']
>>> xml = '\\n'.join(xml)
>>> realACL = parse(xml)
>>> print len(realACL.acl), realACL.acl[0].protected
3 True
>>> print realACL
<D:acl xmlns:D="DAV:" xmlns:ns-1="http://www.xythos.com/namespaces/StorageServer/acl/" >
<D:ace>
<D:principal><D:owner/></D:principal>
<D:grant>
<D:privilege><ns-1:write/></D:privilege>
<D:privilege><ns-1:delete/></D:privilege>
</D:grant>
</D:ace>
<D:ace>
<D:principal><D:all/></D:principal>
</D:ace>
</D:acl>

TODO:
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
"""

import libxml2


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

        """
        The protected flag is true for ACEs that can not be changed.
        """
        self.protected = False

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
        if self.protected:
            return ''
        else:
            return '<D:ace>%s%s%s</D:ace>\n' %(str(self._principal),
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
        if ace in self.acl:
            raise ValueError, 'ace already added'
        self.acl += [ace]

    def remove(self, ace):
        self.acl.remove(ace)

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

        return '%s>\n%s</D:acl>' %(acl, s)


def parse(text):
    """
    Parse XML into ACL object.
    
    @param text: The XML (text) to be parsed into an ACL object.
    """
    # XXX Hack to avoid libxml2 complaints: (maybe fixed 1/19/2005)
    text = text.replace('="DAV:"', '="http://osafoundation.org/dav"')
    try:
        doc = libxml2.parseDoc(text)
        acl = ACL()
        aceNode = _firstACE(doc.children)
        while aceNode:
            if not _isDAVElement(aceNode, 'ace'):
                raise ValueError, 'expected ace, got %s' %(aceNode.name)

            # 1. get principal
            principal = _firstChildElement(aceNode)
            if not _isDAVElement(principal, 'principal'):
                raise ValueError, 'expected principal, got %s' %(principal.name)
            actualPrincipal = _firstChildElement(principal)
            if not _isDAVElement(actualPrincipal):
                raise ValueError, 'actual principal not found'
            if actualPrincipal.name == 'href':
                ace = ACE(actualPrincipal.content)
            else:
                if actualPrincipal.name == 'property':
                    actualPrincipal = _firstChildElement(actualPrincipal)
                    if not _isDAVElement(actualPrincipal):
                        raise ValueError, 'expected property in DAV: ns'

                ace = ACE(actualPrincipal.name)

            # 2. get deny and grant privileges
            node = _nextSiblingElement(principal)
            while node:
                if not _isDAVElement(node):
                    raise ValueError, 'deny or grant expected, wrong namespace'
                if node.name == 'deny':
                    privilege = _firstChildElement(node)
                    while privilege:
                        if not _isDAVElement(privilege, 'privilege'):
                            raise ValueError, 'privilege expected, got %s' %(privilege.name)
                        priv = _firstChildElement(privilege)
                        ace.deny(priv.name,
                                 _translateDAVNamespace(priv.ns().content))
                        privilege = _nextSiblingElement(privilege)
                elif node.name == 'grant':
                    privilege = _firstChildElement(node)
                    while privilege:
                        if not _isDAVElement(privilege, 'privilege'):
                            raise ValueError, 'privilege expected, got %s' %(privilege.name)
                        priv = _firstChildElement(privilege)
                        ace.grant(priv.name,
                                  _translateDAVNamespace(priv.ns().content))
                        privilege = _nextSiblingElement(privilege)
                elif node.name == 'protected':
                    break
                else:
                    raise ValueError, 'deny or grant expected, got %s' %(node.name)
                node = _nextSiblingElement(node)

            # 3. get protected property
            if node and node.name == 'protected':
                ace.protected = True

            acl.add(ace)
            
            aceNode = _nextSiblingElement(aceNode)

        return acl
    finally:
        doc.freeDoc()


def _firstChildElement(node):
    # We need this method because of text nodes (for example whitespace)
    child = node.children
    if not child:
        return None
    
    if child.type == 'element':
        return child
    return _nextSiblingElement(child)


def _nextSiblingElement(node):
    # We need this method because of text nodes (for example whitespace)
    next = node.next
    while next:
        if next.type == 'element':
            return next
        next = next.next
    return None


def _firstACE(node):
    if not node:
        return None

    if  _isDAVElement(node, 'ace'):
        return node

    ret =_firstACE(node.children)
    if ret:
        return ret
    
    return _firstACE(node.next)


# XXX Terrible namespace hacks for DAV: because libxml2 does not like it

def _isDAVElement(node, name=None):
    if node.type != 'element':
        return False
    
    try:
        ns = node.ns().content == 'http://osafoundation.org/dav'
    except treeError:
        return False # There was no namespace
    
    if name is None:
        return ns
    
    return ns and node.name == name


def _translateDAVNamespace(ns):
    if ns == 'http://osafoundation.org/dav':
        return 'DAV:'
    return ns
        

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
            return '\n<D:principal><D:%s/></D:principal>\n' %(self.url)
        else:
            return '\n<D:principal><D:href>%s</D:href></D:principal>\n' %(self.url)


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
            self.nsCounter = 0
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
            s += '<D:privilege><%s:%s/></D:privilege>\n' %(self.privileges[name][0], name) 
        return s


class _Grant(_Privileges):
    """
    The set of privileges to grant.
    """
    def __str__(self):
        if self.privileges:
            return '<D:grant>\n%s</D:grant>\n' %(super(_Grant, self).__str__())
        else:
            return ''


class _Deny(_Privileges):
    """
    The set of privileges to deny.
    """
    def __str__(self):
        if self.privileges:
            return '<D:deny>%s</D:deny>\n' %(super(_Deny, self).__str__())
        else:
            return ''


if __name__ == '__main__':
    import doctest
    libxml2.debugMemory(1)
    doctest.testmod()
    libxml2.cleanupParser()
    if libxml2.debugMemory(1) != 0:
        print '***error***: libxml2 memory leak %d bytes' %(libxml2.debugMemory(1))
        libxml2.dumpMemory()
