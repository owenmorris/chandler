import application.Globals as Globals

import davlib
import httplib
import libxml2

import Dav

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
    def __init__(self, dav, headersOnly=False):
        super(DAVItem, self).__init__()

        self.dav = dav
        self.doc = self._getprops(unicode(dav.url), headersOnly)

    def _getprops(self, url, headersOnly=False):
        """ Fetch all the properties of a resource """
        # XXX this doesn't work, but should...
        #        if headersOnly:
        #            props = '<O:uuid/><O:kind/>'
        #        else:
        #            props = '<D:allprop/>'

        body = davlib.XML_DOC_HEADER + \
               '<D:propfind xmlns:D="DAV:" xmlns:O="//core">' + \
               '<D:allprop/><D:getetag/><D:getlastmodified/>' + \
               '</D:propfind>'

        r = self.dav.newConnection().propfind(url, body, 0)

        if r.status == 404:
            raise Dav.NotFound

        xmlgoop = r.read()

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
