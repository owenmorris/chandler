Index: twisted/internet/m2ssl.py
===================================================================
--- twisted/internet/m2ssl.py	(revision 0)
+++ twisted/internet/m2ssl.py	(revision 0)
@@ -0,0 +1,134 @@
+# Twisted, the Framework of Your Internet
+# Copyright (C) 2001 Matthew W. Lefkowitz
+#
+# This library is free software; you can redistribute it and/or
+# modify it under the terms of version 2.1 of the GNU Lesser General Public
+# License as published by the Free Software Foundation.
+#
+# This library is distributed in the hope that it will be useful,
+# but WITHOUT ANY WARRANTY; without even the implied warranty of
+# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
+# Lesser General Public License for more details.
+#
+# You should have received a copy of the GNU Lesser General Public
+# License along with this library; if not, write to the Free Software
+# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
+
+"""Adapters for M2Crypto's SSL.Connection and SSL.Context
+
+Requires M2Crypto (http://sandbox.rulemaker.net/ngps/m2/).
+To use M2Crypto, set the optional 'useM2' parameter to True when creating
+the SSL context factories (see twisted.internet.ssl).
+
+API Stability: unstable
+
+Author: U{Heikki Toivonen<mailto:heikki@osafoundation.org>}
+"""
+
+# Import with different names so that we can call the base class methods.
+from M2Crypto.SSL import Connection as M2Connection
+from M2Crypto.SSL import Context as M2Context
+
+class Connection(M2Connection):
+    """
+    A connection object modelled after PyOpenSSL's Connection object that
+    Twisted is used to. Only provides methods that Twisted actually uses,
+    and which need to be different from the normal
+    M2Crypto.SSL.Connection object.
+
+    Documentation for M2Crypto's Connection object is here:
+    http://sandbox.rulemaker.net/ngps/Dist/api/public/M2Crypto.SSL.Connection.Connection-class.html
+
+    Documentation for PyOpenSSL's Connection object is here:
+    http://pyopenssl.sourceforge.net/pyOpenSSL.html/openssl-connection.html
+    """
+
+    def close(self):
+        # M2Crypto.SSL.Connection has a different close().
+        self.socket.close()
+
+    def shutdown(self, how=2):
+        # M2Crypto.SSL.Connection has a different shutdown().
+        M2Connection.close(self)
+
+    def sock_shutdown(self, how):
+        # M2Crypto.SSL.Connection does not have this method.
+        self.socket.shutdown(how)
+
+    def connect_ex(self, addr):
+        # M2Crypto.SSL.Connection does not have this method.
+        # Not sure if this method is actually used.
+        ret = self.socket.connect_ex(addr)
+        if ret == 0:
+            self.addr = addr
+            self.set_connect_state()
+        return ret
+
+    def get_peer_certificate(self):
+        # M2Crypto.SSL.Connection has a differently named method.
+        return self.get_peer_cert()
+
+    def __getattr__(self, name):
+        # If this object does not have the attribute asked for, we try
+        # to delegate to socket, and fail if the socket does not have
+        # the attribute. M2Crypto.SSL.Connection() does not do this.
+        # Not sure if this method is actually used.
+        if hasattr(self.socket, name):
+            return self.socket.__dict__[name]
+        raise AttributeError
+
+    def set_connect_state(self):
+        # Need to do extra work to setup internal state.
+        self.setup_ssl()
+        M2Connection.set_connect_state(self)
+        self.connect_ssl()
+
+    def set_accept_state(self):
+        # Need to do extra work to setup internal state.
+        self.setup_ssl()
+        M2Connection.set_accept_state(self)
+        self.accept_ssl()
+
+    def accept(self):
+        # Need to create this Connection object.
+        sock, addr = self.socket.accept()
+        ssl = Connection(self.ctx, sock)
+        ssl.addr = addr
+        ssl.set_accept_state()
+        return ssl, addr
+
+    def send(self, data):
+        # M2Crypto.SSL.Connection.send() raises exception with empty data.
+        if not data:
+            return 0
+        return self._write_bio(data)
+
+
+class Context(M2Context):
+    """
+    A context object modelled after PyOpenSSL's Context object that
+    Twisted is used to. Only provides methods that Twisted actually uses,
+    and which need to be different from the normal
+    M2Crypto.SSL.Context object.
+    
+    Documentation for M2Crypto's Context object is here:
+    http://sandbox.rulemaker.net/ngps/Dist/api/public/M2Crypto.SSL.Context.Context-class.html
+
+    Documentation for PyOpenSSL's Context object is here:
+    http://pyopenssl.sourceforge.net/pyOpenSSL.html/openssl-context.html
+    """
+
+    def __init__(self, protocol='sslv23'):
+        if (protocol == 1):
+            protocol = 'sslv2'
+        elif (protocol == 2):
+            protocol = 'sslv3'
+        elif (protocol == 3):
+            protocol = 'sslv23'
+        elif (protocol == 4):
+            protocol = 'tlsv1'
+            
+        M2Context.__init__(self, protocol)
+
+
+__all__ = ["Connection", "Context"]
Index: twisted/internet/ssl.py
===================================================================
--- twisted/internet/ssl.py	(revision 11245)
+++ twisted/internet/ssl.py	(working copy)
@@ -15,8 +15,13 @@
 # License along with this library; if not, write to the Free Software
 # Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 
-"""SSL transport. Requires PyOpenSSL (http://pyopenssl.sf.net).
+"""SSL transport.
 
+Requires PyOpenSSL (http://pyopenssl.sf.net) or alternatively
+M2Crypto (http://sandbox.rulemaker.net/ngps/m2/). PyOpenSSL is the default.
+To use M2Crypto, set the optional 'useM2' parameter to True when creating
+the context factory.
+
 SSL connections require a ContextFactory so they can create SSL contexts.
 End users should only use the ContextFactory classes directly - for SSL
 connections use the reactor.connectSSL/listenSSL and so on, as documented
@@ -44,7 +49,27 @@
 supported = False
 
 # System imports
-from OpenSSL import SSL
+
+# Tricks that enable us to import both PyOpenSSL and M2Crypto.
+try:
+    from OpenSSL import SSL
+    import OpenSSL
+except:
+    SSL = None
+
+try:
+    import m2ssl
+    if not SSL:
+        from M2Crypto import SSL
+        SSL.SSLv2_METHOD  = 'sslv2'        
+        SSL.SSLv23_METHOD = 'sslv23'
+        SSL.SSLv3_METHOD  = 'sslv3'
+        SSL.TLSv1_METHOD  = 'tlsv1'
+except:
+    if not SSL:
+        raise
+
+
 import socket
 from zope.interface import implements, implementsOnly, implementedBy
 
@@ -60,6 +85,7 @@
     """A factory for SSL context objects, for server SSL connections."""
 
     isClient = 0
+    useM2    = 0
 
     def getContext(self):
         """Return a SSL.Context object. override in subclasses."""
@@ -69,16 +95,23 @@
 class DefaultOpenSSLContextFactory(ContextFactory):
 
     def __init__(self, privateKeyFileName, certificateFileName,
-                 sslmethod=SSL.SSLv23_METHOD):
+                 sslmethod=SSL.SSLv23_METHOD, useM2=0):
         self.privateKeyFileName = privateKeyFileName
         self.certificateFileName = certificateFileName
         self.sslmethod = sslmethod
+        self.useM2 = useM2
         self.cacheContext()
 
     def cacheContext(self):
-        ctx = SSL.Context(self.sslmethod)
-        ctx.use_certificate_file(self.certificateFileName)
-        ctx.use_privatekey_file(self.privateKeyFileName)
+        if self.useM2:
+            ctx = m2ssl.Context(self.sslmethod)
+            ctx.load_cert(self.certificateFileName, self.privateKeyFileName)
+        else:
+            if OpenSSL.SSL != SSL:
+                raise Exception, 'Using wrong SSL implementation'
+            ctx = SSL.Context(self.sslmethod)
+            ctx.use_certificate_file(self.certificateFileName)
+            ctx.use_privatekey_file(self.privateKeyFileName)
         self._context = ctx
 
     def __getstate__(self):
@@ -100,9 +133,17 @@
     """A context factory for SSL clients."""
 
     isClient = 1
-    method = SSL.SSLv3_METHOD
+    useM2    = 0
+    method   = SSL.SSLv3_METHOD
 
+    def __init__(self, useM2=0):
+        self.useM2 = useM2
+
     def getContext(self):
+        if self.useM2:
+            return m2ssl.Context(self.method)
+        if OpenSSL.SSL != SSL:
+            raise Exception, 'Using wrong SSL implementation'
         return SSL.Context(self.method)
 
 
@@ -161,16 +202,23 @@
         tcp.Port.__init__(self, port, factory, backlog, interface, reactor)
         self.ctxFactory = ctxFactory
 
+    def _useM2(self):
+        return hasattr(self.ctxFactory, 'useM2') and self.ctxFactory.useM2
+
     def createInternetSocket(self):
         """(internal) create an SSL socket
         """
         sock = tcp.Port.createInternetSocket(self)
+        if self._useM2():
+            return m2ssl.Connection(self.ctxFactory.getContext(), sock)
+        if OpenSSL.SSL != SSL:
+            raise Exception, 'Using wrong SSL implementation'
         return SSL.Connection(self.ctxFactory.getContext(), sock)
 
     def _preMakeConnection(self, transport):
         # *Don't* call startTLS here
         # The transport already has the SSL.Connection object from above
-        transport._startTLS()
+        transport._startTLS(self._useM2())
         return tcp.Port._preMakeConnection(self, transport)
 
 
Index: twisted/internet/abstract.py
===================================================================
--- twisted/internet/abstract.py	(revision 11245)
+++ twisted/internet/abstract.py	(working copy)
@@ -144,7 +144,13 @@
             return
         if data:
             if (not self.dataBuffer) and (self.producer is None):
-                l = self.writeSomeData(data)
+                # XXX Terrible hack to make M2Crypto SSL handshake work with
+                # XXX newly started server
+                l = -1
+                while l < 0:
+                    l = self.writeSomeData(data)
+                    if l < 0:
+                        print '***retrying write - FIXME!***'
                 if l == len(data):
                     # all data was sent, our work here is done
                     return
Index: twisted/internet/tcp.py
===================================================================
--- twisted/internet/tcp.py	(revision 11245)
+++ twisted/internet/tcp.py	(working copy)
@@ -40,11 +40,31 @@
     fcntl = None
 from zope.interface import implements, classImplements
 
+# Tricks that enable us to import both PyOpenSSL and M2Crypto.
 try:
     from OpenSSL import SSL
+    import OpenSSL
+    # Dummies, not used for anything with PyOpenSSL
+    class DummyPyOpenSSLError(Exception): pass
+    SSL.SSLError = DummyPyOpenSSLError
 except ImportError:
     SSL = None
 
+try:
+    import m2ssl
+    if not SSL:
+        from M2Crypto import SSL
+        # Dummies, not used for anything with M2Crypto
+        class DummyM2CryptoError(Exception): pass
+        SSL.SysCallError = SSL.WantReadError = SSL.WantWriteError = SSL.ZeroReturnError = SSL.Error = DummyM2CryptoError
+    else:
+        # Don't want to import all of M2Crypto.SSL and stomp over PyOpenSSL
+        from M2Crypto.SSL import SSLError
+        SSL.SSLError = SSLError
+except:
+    pass
+
+
 if os.name == 'nt':
     # we hardcode these since windows actually wants e.g.
     # WSAEALREADY rather than EALREADY. Possibly we should
@@ -115,6 +135,9 @@
         except SSL.Error:
             log.err()
             return main.CONNECTION_LOST
+        except SSL.SSLError:
+            log.err()
+            return main.CONNECTION_LOST
 
     def loseConnection(self):
         Connection.loseConnection(self)
@@ -151,6 +174,9 @@
         except SSL.Error:
             log.err()
             return main.CONNECTION_LOST
+        except SSL.SSLError:
+            log.err()
+            return main.CONNECTION_LOST
 
     def _closeSocket(self):
         try:
@@ -204,20 +230,28 @@
         self.socket.setblocking(0)
         self.fileno = skt.fileno
         self.protocol = protocol
+        self.useM2 = 0
 
     if SSL:
-
+        
         def startTLS(self, ctx):
             assert not self.TLS
             self.stopReading()
             self.stopWriting()
-            self._startTLS()
-            self.socket = SSL.Connection(ctx.getContext(), self.socket)
+            useM2 = hasattr(ctx, 'useM2') and ctx.useM2
+            self._startTLS(useM2)
+            if useM2:
+                self.socket = m2ssl.Connection(ctx.getContext(), self.socket)
+            else:
+                if OpenSSL.SSL != SSL:
+                    raise Exception, 'Using wrong SSL implementation'
+                self.socket = SSL.Connection(ctx.getContext(), self.socket)
             self.fileno = self.socket.fileno
             self.startReading()
 
-        def _startTLS(self):
+        def _startTLS(self, useM2):
             self.TLS = 1
+            self.useM2 = useM2
             klass = self.__class__
             class TLSConnection(_TLSMixin, klass):
                 implements(interfaces.ISSLTransport)
@@ -251,6 +285,14 @@
             if retval == -1 and desc == 'Unexpected EOF':
                 return main.CONNECTION_DONE
             raise
+        except SSL.SSLError, m2err:
+            # M2Crypto raises only SSLErrors, but when the value is
+            # 'unexpected eof', we know it is SysCallError
+            if str(m2err) == 'unexpected eof':
+                return main.CONNECTION_DONE
+            raise
+        if data is None and self.useM2:
+            return # M2Crypto told us not to hang up yet!
         if not data:
             return main.CONNECTION_DONE
         return self.protocol.dataReceived(data)
Index: twisted/mail/protocols.py
===================================================================
--- twisted/mail/protocols.py	(revision 11245)
+++ twisted/mail/protocols.py	(working copy)
@@ -221,13 +221,20 @@
     
     This loads a certificate and private key from a specified file.
     """
-    def __init__(self, filename):
+    def __init__(self, filename, useM2=0):
         self.filename = filename
+        self.useM2 = useM2
 
     def getContext(self):
         """Create an SSL context."""
-        from OpenSSL import SSL
-        ctx = SSL.Context(SSL.SSLv23_METHOD)
-        ctx.use_certificate_file(self.filename)
-        ctx.use_privatekey_file(self.filename)
+        if self.useM2:
+            from twisted.internet import m2ssl
+            ctx = m2ssl.Context('sslv23')
+            ctx.load_cert(self.filename)            
+        else:
+            from OpenSSL import SSL
+            ctx = SSL.Context(SSL.SSLv23_METHOD)
+            ctx.use_certificate_file(self.filename)
+            ctx.use_privatekey_file(self.filename)
+            
         return ctx
