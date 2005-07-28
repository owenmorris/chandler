"""
Unit test for SSL context, connection and related security checks.

@copyright: Copyright (c) 2004-2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import unittest
import socket, sys, os
import M2Crypto.SSL as SSL
import M2Crypto.SSL.Checker as Checker
import M2Crypto.X509 as X509
import crypto
import crypto.ssl as ssl

import repository.tests.RepositoryTestCase as RepositoryTestCase

class TestSSL(RepositoryTestCase.RepositoryTestCase):
    def setUp(self):
        #XXX Same as TestCryptoStartupShutdown.InitShutdown.setUp
        pathComponents = sys.modules['crypto'].__file__.split(os.sep)
        assert len(pathComponents) > 3
        chandlerDir = os.sep.join(pathComponents[0:-2])
        self.profileDir = os.path.join(chandlerDir, 'crypto')
        crypto.startup(self.profileDir)        

        super(TestSSL, self)._setup()
        self.testdir = os.path.join(chandlerDir, 'crypto', 'tests')
        super(TestSSL, self)._openRepository()

    def tearDown(self):
        super(TestSSL, self).tearDown()
        
        #XXX Same as TestCryptoStartupShutdown.InitShutdown.tearDown
        crypto.shutdown(self.profileDir)
    
    def testCertificateVerification(self):
        self.loadParcel("parcel:osaf.framework.certstore")
        self.loadParcel("parcel:osaf.framework.certstore.data")

        ctx = ssl.getContext(self.rep.view)
        conn1 = SSL.Connection(ctx)
        conn2 = SSL.Connection(ctx)#XXX Why can't I reuse the connection?

        if socket.getdefaulttimeout() is not None:
            # A workaround for M2Crypto bug 2341. If Chandler
            # unit tests are run with run_tests.py, the feedparser
            # calls socket.setdefaulttimeout() which will break
            # this test case. But since we are just testing to make
            # sure that:
            #   1) SSL certificate verification works and
            #   2) post connection check works
            # we can safely force this test to run in blocking mode.
            #
            # Also, the SSL.Connection code is not used in Chandler.
            # In Chandler we use TwistedProtocolWrapper, which
            # works even when socket.setdefaulttimeout() has been
            # called. 
            # XXX We should really test it here, but we first need
            # XXX to figure out how to run these kinds of twisted tests
            # XXX because reactor.run()/stop() can be called only once
            # XXX in a program.
            conn1.setblocking(1)
            conn2.setblocking(1)
            
        if not self.isOnline():
            return
            
        # We wrap the connect() in try/except and filter some common
        # network errors that are not SSL-related.
        try:
            assert conn1.connect(('www.thawte.com', 443)) >= 0
            conn1.clear()

            self.assertRaises(SSL.SSLError, conn2.connect, ('bugzilla.osafoundation.org', 443))
            conn2.clear()
        except socket.gaierror, e:
            if e.args[0] == 7: #'No address associated with nodename'
                return
            if e.args[0] == -3: #'Temporary failure in name resolution'
                return
            raise

        # postConnectionCheck tested separately

    def testPostConnectionCheck(self):
        pemSite = '''-----BEGIN CERTIFICATE-----
MIID9TCCA16gAwIBAgIBBjANBgkqhkiG9w0BAQQFADCBmjELMAkGA1UEBhMCVVMx
CzAJBgNVBAgTAkNBMRYwFAYDVQQHEw1TYW4gRnJhbmNpc2NvMRowGAYDVQQKExFv
c2Fmb3VuZGF0aW9uLm9yZzELMAkGA1UECxMCQ0ExEDAOBgNVBAMTB09TQUYgQ0Ex
KzApBgkqhkiG9w0BCQEWHGhvc3RtYXN0ZXJAb3NhZm91bmRhdGlvbi5vcmcwHhcN
MDUwNDIwMTgxMTE3WhcNMDYwNDIwMTgxMTE3WjCBuzELMAkGA1UEBhMCVVMxEzAR
BgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28xGjAYBgNV
BAoTEW9zYWZvdW5kYXRpb24ub3JnMREwDwYDVQQLEwhidWd6aWxsYTEjMCEGA1UE
AxMaYnVnemlsbGEub3NhZm91bmRhdGlvbi5vcmcxKzApBgkqhkiG9w0BCQEWHGhv
c3RtYXN0ZXJAb3NhZm91bmRhdGlvbi5vcmcwgZ8wDQYJKoZIhvcNAQEBBQADgY0A
MIGJAoGBAN4CWLF6RZaCDZc6kGijgUSfRDO6JD9Utllr2PCMot07D6oA30XEZKWQ
+9KvvMwt3BEHHWG9ngog2gI/bhk7XvFqsreG35jch/Q0f6fU/dk/Dqz1Q0pYb+j0
d2MwDEDOrV2nJuaQkOur0k/oM38kLjVW849XFNmNEfdhRzPGp8f7AgMBAAGjggEm
MIIBIjAJBgNVHRMEAjAAMCwGCWCGSAGG+EIBDQQfFh1PcGVuU1NMIEdlbmVyYXRl
ZCBDZXJ0aWZpY2F0ZTAdBgNVHQ4EFgQUT7Sg/404L9rptjl3gnAPCKb3EJ0wgccG
A1UdIwSBvzCBvIAUUBSZO/t3VgCaayxM9NxoTcVaB0uhgaCkgZ0wgZoxCzAJBgNV
BAYTAlVTMQswCQYDVQQIEwJDQTEWMBQGA1UEBxMNU2FuIEZyYW5jaXNjbzEaMBgG
A1UEChMRb3NhZm91bmRhdGlvbi5vcmcxCzAJBgNVBAsTAkNBMRAwDgYDVQQDEwdP
U0FGIENBMSswKQYJKoZIhvcNAQkBFhxob3N0bWFzdGVyQG9zYWZvdW5kYXRpb24u
b3JnggEAMA0GCSqGSIb3DQEBBAUAA4GBAK/YvXsGbDLuLUEENZsxppcsi5DZM7wd
lqEfJmSam9E585dsOdZylBrypR2X5RRPgEP2qXUDLXW9WHPwztXMM3s42NT5wX51
QzAXPN7hH0vJ3sbpb84tziV5VkvqDT51+WP4MGrk44oVQEjylxnboMkdtCi08Ts5
QUW4hRYWNNbb
-----END CERTIFICATE-----'''
        x509 = X509.load_cert_string(pemSite)
        
        assert ssl.postConnectionCheck(x509, 'bugzilla.osafoundation.org')
        self.assertRaises(Checker.WrongHost, ssl.postConnectionCheck, x509, 'example.com')
        self.assertRaises(Checker.NoCertificate, ssl.postConnectionCheck, None, 'example.com')

    def isOnline(self):
        try:
            socket.gethostbyname('www.osafoundation.org')
            return True
        except:
            return False

        
if __name__ == "__main__":
    unittest.main()
