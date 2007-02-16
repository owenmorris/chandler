#   Copyright (c) 2005-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


__all__ = [
    'ChandlerServerHandle',
    'WebDAVTester',
    'checkAccess',
    'createCosmoAccount',
    'CANT_CONNECT',
    'NO_ACCESS',
    'READ_ONLY',
    'READ_WRITE',
    'IGNORE',
]

import zanshin.webdav
import zanshin.util
import zanshin.http

import M2Crypto.BIO
import M2Crypto.SSL.Checker
import chandlerdb
import twisted.internet.error as error
from twisted.internet import reactor

import application.Globals as Globals
import application.Utility as Utility
from osaf.framework.certstore import ssl
from osaf import messages
import threading
import version
from i18n import ChandlerMessageFactory as _
from osaf.mail.utils import displayIgnoreSSLErrorDialog, \
                            displaySSLCertDialog, \
                            callMethodInUIThread


class ChandlerServerHandle(zanshin.webdav.ServerHandle):
    def __init__(self, host=None, port=None, username=None, password=None,
                 useSSL=False, repositoryView=None):
        
        self.resourcesByPath = {}   # Caches resources indexed by path

        self.factory = ChandlerHTTPClientFactory()
        self.factory.protocol = zanshin.webdav.WebDAVProtocol
        self.factory.startTLS = useSSL
        self.factory.host = host
        self.factory.port = port
        self.factory.username = username
        self.factory.password = password
        self.factory.retries = zanshin.webdav.DEFAULT_RETRIES
        self.factory.repositoryView = repositoryView

        #self.factory.extraHeaders = { 'Connection' : "close" }

        self.factory.extraHeaders = { 'User-Agent' : Utility.getUserAgent() }

        self.factory.logging = True

    def addRequest(self, request):
        # Make all requests going through this ServerHandle have a
        # 5 minute timeout
        request.timeout = 5 * 60 # seconds
        return super(ChandlerServerHandle, self).addRequest(request)

    def blockUntil(self, callable, *args, **keywds):
        # Since there can be several errors in a connection, we must keep 
        # trying until we either get a successful connection or the user 
        # decides to cancel/disconnect, or there is an error we don't know 
        # how to deal with.
        while True:
            try:
                return zanshin.util.blockUntil(callable, *args, **keywds)
            except Utility.CertificateVerificationError, err:
                assert err.args[1] == 'certificate verify failed'
    
                # Reason why verification failed is stored in err.args[0], see
                # codes at http://www.openssl.org/docs/apps/verify.html#DIAGNOSTICS
    
                retry = (lambda: setattr(self, '_retry', True))
    
                if err.args[0] in ssl.unknown_issuer:
                    handler = lambda: ssl.askTrustServerCertificate(
                        Globals.wxApplication.UIRepositoryView,
                        err.untrustedCertificates[0], 
                        retry)
                else:
                    handler = lambda: ssl.askIgnoreSSLError(
                        err.untrustedCertificates[0], 
                        err.args[0], 
                        retry)
    
                self._handleSSLError(handler, err, callable, *args, **keywds)
                        
            except M2Crypto.SSL.Checker.WrongHost, err:
                retry = (lambda: setattr(self, '_retry', True))
    
                handler = lambda: ssl.askIgnoreSSLError(
                    err.pem, 
                    messages.SSL_HOST_MISMATCH % {'expectedHost': err.expectedHost, 'actualHost': err.actualHost},
                    retry)
                self._handleSSLError(handler, err, callable, *args, **keywds)
    
            except M2Crypto.BIO.BIOError, error:
                # Translate the mysterious M2Crypto.BIO.BIOError
                raise error.SSLError(error)

    def _handleSSLError(self, handler, err, callable, *args, **keywds):
        self._reconnect = False

        if Globals.wxApplication is not None: # test framework has no wxApplication
            handler()
            
        if hasattr(self, '_retry'):
            del self._retry
        else:
            raise err
        


class ChandlerHTTPClientFactory(zanshin.http.HTTPClientFactory):
    def _makeConnection(self, timeout):
        if self.logging:
            #_doLog("[Connecting to %s:%s]" % (self.host, self.port))
            pass
            
        if self.startTLS:
            result = ssl.connectSSL(self.host, self.port, self,
                                    self.repositoryView, timeout=timeout)
        else:
            result = reactor.connectTCP(self.host, self.port,
                                        self, timeout=timeout)
            
        self._active = result
        
        return result



# ----------------------------------------------------------------------------

CANT_CONNECT = -1
NO_ACCESS    = 0
READ_ONLY    = 1
READ_WRITE   = 2
IGNORE       = 3

def checkAccess(host, port=80, useSSL=False, username=None, password=None,
                path=None, repositoryView=None):
    """
    Check the permissions for a webdav account by reading and writing
    to that server.

    Returns a tuple (result code, reason), where result code indicates the
    level of permissions: CANT_CONNECT, NO_ACCESS, READ_ONLY, READ_WRITE.

    CANT_CONNECT will be accompanied by a "reason" string that was provided
    from the socket layer.
    
    NO_ACCESS and READ_ONLY will be accompanied by an HTTP status code.

    READ_WRITE will have a "reason" of None.
    """

    handle = ChandlerServerHandle(host=host, port=port, username=username,
                   password=password, useSSL=useSSL,
                   repositoryView=repositoryView)

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
        resourceList = handle.blockUntil(topLevelResource.propfind, depth=1)
    except zanshin.webdav.ConnectionError, err:
        return (CANT_CONNECT, err.message)
    except zanshin.webdav.WebDAVError, err:
        return (NO_ACCESS, err.status)
    except error.SSLError, err:
        return (CANT_CONNECT, err) # Unhandled SSL error
    except M2Crypto.SSL.Checker.WrongHost:
        return (IGNORE, None) # The user cancelled SSL error dialog
    except Utility.CertificateVerificationError:
        return (IGNORE, None) # The user cancelled trust cert/SSL error dialog
    except Exception, err: # Consider any other exception as a connection error
        return (CANT_CONNECT, err)

    try:
        privilege_set = handle.blockUntil(topLevelResource.getPrivileges)
        # cosmo doesn't return anything for getPrivileges, bug 7925, so fall
        # back to other tests if write access isn't available.
        #if not ('read', 'DAV:') in privilege_set.privileges:
            #return (NO_ACCESS, _(u"Current-user-privilege-set not supported or Read not allowed."))
        if ('write', 'DAV:') in privilege_set.privileges:
            return (READ_WRITE, None)
        #else:
            #return (READ_ONLY, None)
    except zanshin.http.HTTPError, err:
        return (CANT_CONNECT, err.message)
    
    # Now, we try to PUT a small test file on the server. If that
    # fails (and a MKCOLL fails), we're going to say the user only has
    # read-only access.
    try:
        tmpResource = handle.getResource(topLevelResource.path + 
                                         unicode(chandlerdb.util.c.UUID()))
        body = "Write access test"
        handle.blockUntil(tmpResource.put, body, checkETag=False,
                          contentType="text/plain")
        # Remove the temporary resource, and ignore failures (since there's
        # not much we can do here, anyway).
        handle.blockUntil(tmpResource.delete)
    except:
        pass
    else:
        return (READ_WRITE, None)
    
    # PUT failed, but servers like Kerio's reject PUTs in the home collection,
    # but accept MKCOLL, so try that
    try:
        child = handle.blockUntil(topLevelResource.createCollection,
                                  unicode(chandlerdb.util.c.UUID()))
        handle.blockUntil(child.delete)
    except zanshin.webdav.WebDAVError, e:
        return (READ_ONLY, e.status)
    except:
        # PUT and MKCOLL failed, give up
        return (READ_ONLY, None)
    else:
        return (READ_WRITE, None)


def createCosmoAccount(host, port=80, useSSL=False,
    admin="root", adminpw="cosmo",
    username="username", password="password",
    firstName="First", lastName="Last",
    email="user@example.com", repositoryView=None):

    body = """<?xml version="1.0" encoding="utf-8" ?>
<user xmlns="http://osafoundation.org/cosmo">
  <username>%s</username>
  <password>%s</password>
  <firstName>%s</firstName>
  <lastName>%s</lastName>
  <email>%s</email>
</user>
""" % (username, password, firstName, lastName, email)

    handle = ChandlerServerHandle(host=host, port=port, username=admin,
                   password=adminpw, useSSL=useSSL,
                   repositoryView=repositoryView)

    resource = handle.getResource("/api/user/%s" % username)
    try:
        handle.blockUntil(resource.put, body, checkETag=False,
                          contentType="text/xml; charset='utf-8'")
    except zanshin.http.HTTPError, e:
        pass # ignore these for now, since we'll always get a 501 on the
             # followup PROPFIND

class TestChandlerServerHandle(ChandlerServerHandle):
    def __init__(self, host=None, port=None, username=None, password=None,
                 useSSL=False, repositoryView=None, reconnect=None,
                 callback=None):

        super(TestChandlerServerHandle, self).__init__(host, port, username,
                                                        password, useSSL,
                                                        repositoryView)
        self.reconnect = reconnect
        self.callback = callback

    def execCommand(self, callable, *args, **keywds):
        try:
            result =  zanshin.util.blockUntil(callable, *args, **keywds)
            return (1, result)

        except Utility.CertificateVerificationError, err:
            assert err.args[1] == 'certificate verify failed'

            # Reason why verification failed is stored in err.args[0], see
            # codes at http://www.openssl.org/docs/apps/verify.html#DIAGNOSTICS
            try:
                result = (2, None)
                # Send the message to destroy the progress dialog first. This needs
                # to be done in this order on Linux because otherwise killing
                # the progress dialog will also kill the SSL error dialog.
                # Weird, huh? Welcome to the world of wx...
                callMethodInUIThread(self.callback, result)
                if err.args[0] in ssl.unknown_issuer:
                    displaySSLCertDialog(err.untrustedCertificates[0], self.reconnect)
                else:
                    displayIgnoreSSLErrorDialog(err.untrustedCertificates[0],
                                                err.args[0], self.reconnect)

                return result
            except Exception, e:
                # There is a bug in the M2Crypto code which needs
                # to be fixed.
                log.exception('This should not happen')
                return (0, (CANT_CONNECT, _(u"Error in SSL Layer")))

        except M2Crypto.SSL.Checker.WrongHost, err:
            result = (2, None)
            # Send the message to destroy the progress dialog first. This needs
            # to be done in this order on Linux because otherwise killing
            # the progress dialog will also kill the SSL error dialog.
            # Weird, huh? Welcome to the world of wx...
            callMethodInUIThread(self.callback, result)
            ssl.askIgnoreSSLError( err.pem,
                    messages.SSL_HOST_MISMATCH % \
                      {'expectedHost': err.expectedHost,
                       'actualHost': err.actualHost},
                       self.reconnect)

            return result

        except M2Crypto.BIO.BIOError, error:
            return (0, (CANT_CONNECT, str(err)))

        except zanshin.webdav.ConnectionError, err:
            return (0, (CANT_CONNECT, err.message))

        except zanshin.webdav.WebDAVError, err:
            return (0, (NO_ACCESS, err.status))

        except error.SSLError, err:
            return (0, (CANT_CONNECT, err)) # Unhandled SSL error

        except Exception, err: # Consider any other exception as a connection error
            return (0, (CANT_CONNECT, err))


class WebDAVTester(object):
    def __init__(self, host=None, port=None, path=None, username=None,
                 password=None, useSSL=False, repositoryView=None):

       self.host = host
       self.port = port
       self.path = path
       self.username = username
       self.password = password
       self.useSSL = useSSL
       self.view = repositoryView

       self.cancel  = False

    def cancelLastRequest(self):
        self.cancel = True

    def testAccountSettings(self, callback, reconnect, blocking=False):
        if blocking:
            return self._testAccountSettings(callback, reconnect)

        # don't block the current thread
        t = threading.Thread(target=self._testAccountSettings,
              args=(callback, reconnect))

        t.start()

    def _testAccountSettings(self, callback, reconnect):
        handle = TestChandlerServerHandle(self.host,
                                          self.port,
                                          self.username,
                                          self.password,
                                          self.useSSL,
                                          self.view, reconnect,
                                          callback=callback)

        # Make sure path begins/ends with /
        self.path = self.path.strip("/")

        if self.path == "":
            self.path = "/"
        else:
            self.path = "/" + self.path + "/"

        # Get the C{Resource} object associated with the specified
        # path
        topLevelResource = handle.getResource(self.path)

        statusCode, statusValue = handle.execCommand(
                                        topLevelResource.propfind, depth=1)

        if self.cancel:
            return

        if statusCode != 1:
            return

        childNames = set([])

        for child in statusValue:
            if child is not topLevelResource:
                childPath = child.path

                if childPath and childPath[-1] == '/':
                    childPath = childPath[:-1]

                childComponents = childPath.split('/')

                if len(childComponents):
                    childNames.add(childComponents[-1])

        # Try to figure out a unique path (although the odds of
        # even more than one try being needs are probably negligible)..
        testFilename = unicode(chandlerdb.util.c.UUID())

        # Random string to use for trying a put
        while testFilename in childNames:
            testFilename = unicode(chandlerdb.util.c.UUID())

        # Now, we try to PUT a small test file on the server. If that
        # fails, we're going to say the user only has read-only access.

        tmpResource = handle.getResource(topLevelResource.path + testFilename)

        body = "Write access test"

        statusCode, statusValue = handle.execCommand(tmpResource.put, body, checkETag=False,
                                                    contentType="text/plain")

        if self.cancel:
            return

        if statusCode == 0:
            # No access in this case means read only
            if statusValue[0] == NO_ACCESS:
                return callMethodInUIThread(callback, (1, (READ_ONLY, None)))

            return callMethodInUIThread(callback, (statusCode, statusValue))

        # Remove the temporary resource, and ignore failures (since there's
        # not much we can do here, anyway).
        handle.execCommand(tmpResource.delete)

        if self.cancel:
            return

        # Success!
        return callMethodInUIThread(callback, (1, (READ_WRITE, None)))


class MorsecodeTester(object):
    def __init__(self, host=None, port=None, path=None, username=None,
                 password=None, useSSL=False, repositoryView=None):

       self.host = host
       self.port = port
       self.path = path
       self.username = username
       self.password = password
       self.useSSL = useSSL
       self.view = repositoryView

       self.cancel  = False

    def cancelLastRequest(self):
        self.cancel = True

    def testAccountSettings(self, callback, reconnect, blocking=False):
        if blocking:
            return self._testAccountSettings(callback, reconnect)

        # don't block the current thread
        t = threading.Thread(target=self._testAccountSettings,
              args=(callback, reconnect))

        t.start()

    def _testAccountSettings(self, callback, reconnect):
        handle = TestChandlerServerHandle(self.host,
                                          self.port,
                                          self.username,
                                          self.password,
                                          self.useSSL,
                                          self.view, reconnect,
                                          callback=callback)

        self.path = "/" + self.path.strip("/")
        usdPath = "%s/cmp/user/%s/service" % (self.path, self.username)

        request = zanshin.http.Request("GET", usdPath, { }, None)

        statusCode, result = handle.execCommand(handle.addRequest, request)

        if self.cancel:
            return

        if statusCode != 1:
            return

        if result.status == 200:
            # Success!
            return callMethodInUIThread(callback,
                (1, (READ_WRITE, None)))
        else:
            return callMethodInUIThread(callback,
                (0, (NO_ACCESS, result.status)))
