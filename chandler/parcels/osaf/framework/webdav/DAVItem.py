import application.Globals as Globals

import davlib
import httplib
import libxml2

class BadItem(Exception):
    pass

"""
What I want this class to be able to do is keep track of the DAV properties
in XML that I can use to proppatch as well as check/merge against when doing
a propfind.  If I can store all that data here in one place, life will be
grand.  Merging can be done by diffing the current XML tree against the
incoming one.  If you have local changes, once merged the resulting XML can
be sent back to the server to sync it up.

Currently it is read-only.  Soon it will be read-write.
"""

class DAVItem(object):
    """ utility class that represents an item from a webdav server """
    def __init__(self, dav):
        super(DAVItem, self).__init__()

        self.dav = dav
        self.doc = self._allprop(unicode(dav.url))

    def _allprop(self, url, depth = 0):
        """ Fetch all the properties of a resource """
        body = davlib.XML_DOC_HEADER + \
               '<D:propfind xmlns:D="DAV:">' + \
               '<D:allprop/><D:getetag/><D:getlastmodified/>' + \
               '</D:propfind>'

        # In order to get see if the etag matches something, we need
        # to first fetch the item, get its uuid and getetag properties.
        # At that point we can look it up in the itemMap and see if we
        # already have it, and then match the etag associated with that.
        #
        # for now, lets just fetch all the properties and match the etag
        # later.
        #
        # we could also make the get code smarter by allowing you to "get"
        # an item that was already shared (and hence has a url and an etag
        # already.  This might be the best solution.
        r = self.dav.newConnection().propfind(url, body, depth)

        xmlgoop = r.read()
        print url
        print xmlgoop

        doc = libxml2.parseDoc(xmlgoop)

        return doc

    def _getKind(self):
        value = self._getAttribute('kind', '//core')
        if not value:
            raise BadItem, 'Unable to find a kind at %s' % (self.dav.url)

        return Globals.repository.findPath(value)

    def _getUUID(self):
        value = self._getAttribute('uuid', '//core')
        if not value:
            raise BadItem, 'Unable to find a uuid at %s' % (self.dav.url)

        from repository.util.UUID import UUID
        return UUID(value)

    def _getETag(self):
        return self._getAttribute('getetag', 'DAV:')

    def _getLastModified(self):
        return self._getAttribute('getlastmodified', 'DAV:')

    def getAttribute(self, attr):
        """ takes an Attribute argument """
        attrname = attr.itsName
        
        attrns = str(attr.itsPath[0:-1])
        return self._getAttribute(attrname, attrns)

    def _getAttribute(self, attr, attrns):
        ctxt = self.doc.xpathNewContext()
        ctxt.xpathRegisterNs('D', 'DAV:')
        ctxt.xpathRegisterNs('O', attrns)

        xp = '/D:multistatus/D:response/D:propstat/D:prop/O:' + attr
        try:
            node = ctxt.xpathEval(xp)[0]
        except IndexError:
            return None

        # Do I need to free the context?

        return node.content

    #def __getattr__(self, name):

    itsKind = property(_getKind)
    itsUUID = property(_getUUID)
    etag = property(_getETag)
    lastModified = property(_getLastModified)
