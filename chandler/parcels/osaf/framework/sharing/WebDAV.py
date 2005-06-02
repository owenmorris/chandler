__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from twisted.internet.error import TimeoutError, UserError, DNSLookupError
from twisted.internet.defer import Deferred
from twisted.internet import reactor
from twisted.python.failure import Failure
import zanshin.webdav
from zanshin.http import Request, ConnectionError
from twisted.web.http import NOT_FOUND
from zanshin.tests.util import runTestSynchronously as blockUntil

import logging
from repository.persistence.RepositoryViewManager import AbstractRepositoryViewManager
import application.Globals as Globals
import crypto.ssl as ssl
import chandlerdb.util.uuid

logger = logging.getLogger('WebDAV')
logger.setLevel(logging.INFO)

class ChandlerServerHandle(zanshin.webdav.ServerHandle):
    """
    Subclass of zanshin.webdav.ServerHandle that can access
    the repository (needed to plug in to Chandler crypto's
    certificate verification).
    """
    def __init__(self, host=None, port=None, username=None, password=None,
        useSSL=False, repositoryView=None):
        
        super(ChandlerServerHandle, self).__init__(host=host, port=port,
            username=username, password=password, useSSL=useSSL)
            
        if useSSL and repositoryView != None and \
            not hasattr(self.factory, "wrappingFactory"):
            
            self.factory.startTLS = True # Starts SSL immediately.
            self.factory.wrappingFactory = TLSWrappingFactory(self.factory)
            self.factory.wrappingFactory.protocol = TLSProtocolWrapper

            if self.factory.sslContextFactory == None:
                self.factory.getContext = lambda: \
                    Globals.crypto.getSSLContext(repositoryView=repositoryView)



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

    handle = ChandlerServerHandle(host=host, port=port, username=username,
                   password=password, useSSL=useSSL)

    # Make sure path begins/ends with /
    path = path.strip("/")
    if path == "":
        path = "/"
    else:
        path = "/" + path + "/"

    # Get the C{Resource} object associated with the specified
    # path
    topLevelResource = handle.getResource(path)

    # Now, try to list all the child resources of the top level.
    # This may lead to auth errors (mistyped username/password)
    # or other failures (e.g., nonexistent path, mistyped
    # host).
    try:
        resourceList = blockUntil(topLevelResource.propfind, depth=1)
    except ConnectionError, err:
        return (CANT_CONNECT, err.message)
    except zanshin.webdav.WebDAVError, err:
        return (NO_ACCESS, err.status)
        
    
    # Unique the child names returned by the server. (Note that
    # collection subresources will have a name that ends in '/').
    # We're doing this so that we can try a PUT below to a (hopefully
    # nonexistent) path.
    childNames = set([])
    
    for child in resourceList:
        if child is not topLevelResource:
            childPath = child.path
            if childPath and childPath[-1] == '/':
                childPath = childPath[:-1]
            childComponents = childPath.split('/')
            if len(childComponents):
                childNames.add(childComponents[-1])

    # Try to figure out a unique path (although the odds of
    # even more than one try being needs are probably negligible)..
    tries = 10
    testFilename = unicode(chandlerdb.util.uuid.UUID())
    
    # Random string to use for trying a put
    while testFilename in childNames:
        tries -= 1

        if numTries == 0:
            # @@@ [grant] This can't be right, but it's what was in the
            # original (pre-zanshin) code.
            return -1

            testFilename = chandlerdb.util.uuid.UUID()
    
    # Now, we try to PUT a small test file on the server. If that
    # fails, we're going to say the user only has read-only access.
    try:
        tmpResource = blockUntil(topLevelResource.createFile, testFilename,
                                     body='Write access test')
    except zanshin.webdav.WebDAVError, e:
        return (READ_ONLY, e.status)
        
    # Remove the temporary resource, and ignore failures (since there's
    # not much we can do here, anyway).
    try:
        blockUntil(tmpResource.delete)
    except:
        pass
        
    # Success!
    return (READ_WRITE, None)
