__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import httplib
import socket
import mimetypes
import base64
import libxml2
import urlparse
import logging
import application.Globals as Globals
import crypto.ssl as ssl
import chandlerdb.util.uuid

logger = logging.getLogger('WebDAV')
logger.setLevel(logging.INFO)

XML_CONTENT_TYPE = 'text/xml; charset="utf-8"'
XML_DOC_HEADER = '<?xml version="1.0" encoding="utf-8"?>'

DEFAULT_RETRIES = 3

class Client(object):

    def __init__(self, host, port=80, username=None, password=None,
     useSSL=False, ctx=None, retries=DEFAULT_RETRIES, repositoryView=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.useSSL = useSSL
        self.ctx = ctx
        self.conn = None
        self.retries = retries
        self.view = repositoryView

    def connect(self, host=None, port=None):
        logger.debug("Opening connection")

        if self.useSSL:
            if self.ctx is None:
                self.ctx = Globals.crypto.getSSLContext(repositoryView=self.view)
            self.conn = ssl.HTTPSConnection(self.host,
                                            self.port,
                                            ssl_context=self.ctx)
        else:
            if host and port:
                # We've been redirected
                self.conn = httplib.HTTPConnection(host, port)
            else:
                self.conn = httplib.HTTPConnection(self.host, self.port)

        self.conn.debuglevel = 0
        try:
            logger.debug("Connecting to %s" % self.host)
            self.conn.connect()
        except socket.gaierror, err:
            # @@@MOR can these exceptions mean anything else?
            message = "Unknown host %s" % self.host
            raise ConnectionError(message=message)
        except socket.herror, err:
            message = "Unknown host %s" % self.host
            raise ConnectionError(message=message)
        except socket.error, err:
            message = "Socket error: %s" % \
                      (" ".join(map(lambda x : str(x), err.args)))
            raise ConnectionError(message=message)

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

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

    def options(self, url, extraHeaders={ }):
        return self._request('OPTIONS', url, extraHeaders=extraHeaders)

    def delete(self, url, extraHeaders={ }):
        return self._request('DELETE', url, extraHeaders=extraHeaders)

    def propfind(self, url, body=None, depth=None, extraHeaders={ }):
        extraHeaders = extraHeaders.copy()
        extraHeaders['Content-Type'] = XML_CONTENT_TYPE
        if body is None: # by default, ask for etags
            body = "%s\n<D:propfind xmlns:D=\"DAV:\"><D:prop><D:getetag/></D:prop></D:propfind>" % XML_DOC_HEADER
        if depth is not None:
            extraHeaders['Depth'] = str(depth)
        return self._request('PROPFIND', url, body, extraHeaders=extraHeaders)

    def ls(self, url, extraHeaders={ }, ignoreCollections=True):
        # A helper method which parses a PROPFIND response and returns a
        # list of (path, etag) tuples, providing an easy way to get the
        # contents of a collection

        resources = []
        resp = self.propfind(url, depth=1, extraHeaders=extraHeaders)
        if resp.status != httplib.MULTI_STATUS:
            raise WebDAVException(status=resp.status)

        # Parse the propfind, pulling out the URLs for each child along
        # with their ETAGs, and storing them in the resourceList dictionary:
        text = resp.read()
        # @@@ Hack to avoid libxml2 complaints: (maybe fixed 1/19/2005)
        text = text.replace('="DAV:"', '="http://osafoundation.org/dav"')
        try:
            doc = libxml2.parseDoc(text)
        except:
            logging.error("Parsing response failed: %s" % text)
            raise

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
                    if path:
                        if not ignoreCollections or not path.endswith("/"):
                            resources.append( (path, etag) )
            node = node.next
        doc.freeDoc()
        return resources

    def getacl(self, url, extraHeaders={ }):
        # Strictly speaking this method is not needed, you could use
        # propfind, or getprops.
        body = XML_DOC_HEADER + \
               '<D:propfind xmlns:D="DAV:"><D:prop><D:acl/></D:prop></D:propfind>'
        return self.propfind(url, body, extraHeaders=extraHeaders)

    def setacl(self, url, acl, extraHeaders={ }):
        # url is the resource who's acl we are changing
        # acl is an ACL object that sets the actual ACL
        body = XML_DOC_HEADER + str(acl)
        headers = extraHeaders.copy()
        headers['Content-Type'] = XML_CONTENT_TYPE
        return self._request('ACL', url, body, headers)

    def _request(self, method, url, body=None, extraHeaders={ }):
        logger.debug("_request: %s %s" % (method, url))

        closeWhenFinished = False

        if self.conn is None:
            self.connect()

        if self.username:
            auth = 'Basic ' + \
             base64.encodestring(self.username + ':' + self.password).strip()
            extraHeaders = extraHeaders.copy()
            extraHeaders['Authorization'] = auth

        triesLeft = self.retries
        while triesLeft > 0:
            logger.debug("%d tries left" % triesLeft)
            triesLeft -= 1

            try:
                logger.debug("Sending request: %s %s" % (method, url))
                self.conn.request(method, url, body, extraHeaders)
            except httplib.CannotSendRequest:
                logger.debug("Got CannotSendRequest")
                self.connect()
                continue
            except socket.error, e:
                logger.debug("Got socket error: %s" % e)
                self.connect()
                continue

            try:
                response = self.conn.getresponse()
            except httplib.BadStatusLine, e:
                if not e.line:
                    # This condition means the server closed a keepalive
                    # connection.  Reopen.
                    logger.debug("Server closed keepalive connection")
                    self.connect()
                    continue
                else:
                    # We must have gotten a garbled status line
                    raise
            except socket.error, e:
                logger.debug("Got socket error: %s" % e)
                self.connect()
                continue

            # Check for HTTP redirects (30X codes)
            if response.status in (httplib.MOVED_PERMANENTLY, httplib.FOUND,
             httplib.SEE_OTHER, httplib.TEMPORARY_REDIRECT):
                response.read() # Always need to read each response
                newurl = response.getheader('Location')
                # Make sure server isn't redirecting us somewhere else, since
                # bad things can happen:
                old = urlparse.urlsplit(url)
                new = urlparse.urlsplit(newurl)
                if method in ('GET', 'HEAD', 'OPTIONS') or \
                  (old[0] == new[0] and old[1] == new[1]):
                    url = newurl
                    closeWhenFinished = True
                    logger.debug("Redirecting to: %s" % url)

                    # Examine the redirected URL for new host and port
                    host = new[1]
                    port = self.port
                    if host.find(':') != -1:
                        (host, port) = host.split(':')
                        port = int(port)
                    self.connect(host=host, port=port)
                    continue
                else:
                    logger.debug("Illegal redirect: %s to %s" % (url, newurl))
                    message = "Illegal redirect: %s to %s" % (url, newurl)
                    raise IllegalRedirect(message=message)

            if closeWhenFinished:
                self.conn = None

            return response

        # After the retries, we didn't succeed.
        # @@@MOR What sort of exceptions do we want to raise here?
        raise ConnectionError()

class WebDAVException(Exception):
    def __init__(self, status=None, message=None):
        self.status = status
        self.message = message

class ConnectionError(WebDAVException):
    pass

class NotFound(WebDAVException):
    pass

class NotAuthorized(WebDAVException):
    pass

class IllegalRedirect(WebDAVException):
    pass


# ----------------------------------------------------------------------------


CANT_CONNECT = -1
NO_ACCESS    = 0
READ_ONLY    = 1
READ_WRITE   = 2

def checkAccess(host, port=80, useSSL=False, username=None, password=None,
                path=None):
    """ Check the permissions for a webdav account by reading and writing
        to that server.

    Returns a tuple (result code, reason), where result code indicates the
    level of permissions:  CANT_CONNECT, NO_ACCESS, READ_ONLY, READ_WRITE.
    CANT_CONNECT will be accompanied by a "reason" string that was provided
    from the socket layer.  NO_ACCESS and READ_ONLY will be accompanied by
    an HTTP status code.  READ_WRITE will have a "reason" of None.
    """

    client = Client(host, port, username, password, useSSL)

    # Make sure path begins/ends with /
    path = path.strip("/")
    if path == "":
        path = "/"
    else:
        path = "/" + path + "/"

    portString = ""
    if useSSL:
        scheme = "https"
        if port != 443:
            portString = ":%d" % port
    else:
        scheme = "http"
        if port != 80:
            portString = ":%d" % port

    url = "%s://%s%s%s" % (scheme, host, portString, path)
    try:
        response = client.propfind(url, depth=0)
        body = response.read()
    except ConnectionError, err:
        return (CANT_CONNECT, err.message)

    status = response.status
    # print "PROPFIND:", url, status
    if status < 200 or status >= 300: # failed to read
        return (NO_ACCESS, status)

    tries = 10
    urlToTest = None
    while tries > 0:
        # Random string to use for trying a put
        uuid = chandlerdb.util.uuid.UUID()
        url = "%s://%s%s%s%s.tmp" % (scheme, host, portString, path, uuid)
        response = client.propfind(url, depth=0)
        body = response.read()
        status = response.status
        # print "PROPFIND:", url, status
        if status == httplib.NOT_FOUND:
            urlToTest = url
            break
        tries -= 1

    if urlToTest is None:
        return -1

    response = client.put(urlToTest, "Write access test")
    body = response.read()
    status = response.status
    # print "PUT:", url, status
    if status >= 200 and status < 300: # successful put
        writeSuccess = True
        # remove it
        response = client.delete(urlToTest)
        body = response.read()
        status = response.status
        # print "DELETE:", url, status
        deleteSuccess = status >= 200 and status < 300 # successful delete
        # @@@MOR If we can't delete after the put, what does that mean?
        return (READ_WRITE, None)
    else:
        return (READ_ONLY, status)
