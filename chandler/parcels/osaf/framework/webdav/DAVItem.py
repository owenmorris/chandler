import application.Globals as Globals

import davlib
import libxml2
import logging

class BadItem(Exception):
    pass

log = logging.getLogger("sharing")
log.setLevel(logging.INFO)

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
        if headersOnly:
            props = '<D:prop>' + \
                    '<O:uuid/><O:kind/><D:getetag/><D:getlastmodified/>' + \
                    '</D:prop>'
        else:
            props = '<D:allprop/><D:getetag/><D:getlastmodified/>'

        body = davlib.XML_DOC_HEADER + \
               '<D:propfind xmlns:D="DAV:" xmlns:O="//core">' + \
               props + \
               '</D:propfind>'

        r = self.dav.getProps(body, 0)

        xmlgoop = r.read()

        log.debug('PROPFIND returned:')
        log.debug(xmlgoop)

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
        # this would be a lot faster if we only allocated a single
        # xpathContext per-DAVItem
        ctxt = self.doc.xpathNewContext()
        ctxt.xpathRegisterNs('D', 'DAV:')
        ctxt.xpathRegisterNs('O', attrns)

        xp = '/D:multistatus/D:response/D:propstat/D:prop/O:' + attr
        try:
            node = ctxt.xpathEval(xp)[0]
            value = node.content
        except IndexError:
            value = None

        ctxt.xpathFreeContext()

        return value

    itsKind = property(_getKind)
    itsUUID = property(_getUUID)
    etag = property(_getETag)
    lastModified = property(_getLastModified)
