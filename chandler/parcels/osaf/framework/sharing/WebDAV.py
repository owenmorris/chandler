__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import httplib
import mimetypes
import base64
import libxml2
import urlparse
import crypto.ssl as ssl
import M2Crypto.httpslib as httpslib

XML_CONTENT_TYPE = 'text/xml; charset="utf-8"'

class Client(object):

    def __init__(self, host, port=80, username=None, password=None,
     useSSL=False, ctx=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.useSSL = useSSL
        self.ctx = ctx
        self.conn = None

    def connect(self):
        if self.useSSL:
            if self.ctx is None:
                self.ctx = ssl.getSSLContext()
            self.conn = httpslib.HTTPSConnection(self.host,
                                                 self.port,
                                                 ssl_context=self.ctx)
        else:
            self.conn = httplib.HTTPConnection(self.host, self.port)

    def mkcol(self, url, extraHeaders={ }):
        return self._request('MKCOL', url, extraHeaders=extraHeaders)

    def get(self, url, extraHeaders={ }):
        return self._request('GET', url, extraHeaders=extraHeaders)

    def put(self, url, body, contentType=None, contentEncoding=None,
     extraHeaders={ }):
        extraHeaders = extraHeaders.copy()
        if not contentType:
            contentType, contentEncoding = mimetypes.guess_type(url)
        if contentType:
            extraHeaders['Content-Type'] = contentType
        if contentEncoding:
            extraHeaders['Content-Encoding'] = contentEncoding
        return self._request('PUT', url, body=body, extraHeaders=extraHeaders)

    def head(self, url, extraHeaders={ }):
        return self._request('HEAD', url, extraHeaders=extraHeaders)

    def delete(self, url, extraHeaders={ }):
        return self._request('DELETE', url, extraHeaders=extraHeaders)

    def propfind(self, url, depth=None, extraHeaders={ }):
        extraHeaders = extraHeaders.copy()
        extraHeaders['Content-Type'] = XML_CONTENT_TYPE
        if depth is not None:
            extraHeaders['Depth'] = str(depth)
        return self._request('PROPFIND', url, extraHeaders=extraHeaders)

    def ls(self, url, extraHeaders={ }):
        # A helper method which parses a PROPFIND response and returns a
        # list of (path, etag) tuples, providing an easy way to get the
        # contents of a collection

        resources = []
        resp = self.propfind(url, depth=1, extraHeaders=extraHeaders)

        # Parse the propfind, pulling out the URLs for each child along
        # with their ETAGs, and storing them in the resourceList dictionary:
        text = resp.read()
        # @@@ Hack to avoid libxml2 complaints:
        text = text.replace('="DAV:"', '="http://osafoundation.org/dav"')
        doc = libxml2.parseDoc(text)
        node = doc.children.children
        while node:
            if node.type == "element":
                if node.name == "response":
                    path = None
                    etag = None
                    child = node.children
                    while child:
                        if child.name == "href":
                            # use only the path portion of the url:
                            path = urlparse.urlparse(child.content)[2]
                        elif child.name == "propstat":
                            gchild = child.children
                            while gchild:
                                if gchild.name == "prop":
                                    ggchild = gchild.children
                                    while ggchild:
                                        if ggchild.name == "getetag":
                                            etag = ggchild.content
                                        ggchild = ggchild.next
                                gchild = gchild.next
                        child = child.next
                    if path and not path.endswith("/"):
                        resources.append( (path, etag) )
            node = node.next
        doc.freeDoc()
        return resources

    def _request(self, method, url, body=None, extraHeaders={ }):
        if self.conn is None:
            self.connect()

        if self.username:
            auth = 'Basic ' + \
             base64.encodestring(self.username + ':' + self.password).strip()
            extraHeaders = extraHeaders.copy()
            extraHeaders['Authorization'] = auth
        self.conn.request(method, url, body, extraHeaders)
        return self.conn.getresponse()

