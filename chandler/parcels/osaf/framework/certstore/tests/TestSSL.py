#   Copyright (c) 2004-2008 Open Source Applications Foundation
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

"""
Unit test for SSL context, connection and related security checks.
"""

import unittest
import socket, os

import M2Crypto.SSL as SSL
import M2Crypto.SSL.Checker as Checker
import M2Crypto.X509 as X509
import twisted.internet.protocol as protocol
import twisted.protocols.policies as policies

import application.Utility as Utility
from osaf.framework.certstore import ssl, utils, certificate, constants
from osaf.pim.tests import TestDomainModel

class TestSSL(TestDomainModel.DomainModelTestCase):
    def setUp(self):

        self.profileDir = os.path.dirname(__file__)
        Utility.initCrypto(self.profileDir)
        super(TestSSL, self).setUp(testdir=self.profileDir)

        self.loadParcel("osaf.framework.certstore")
        self.loadParcel("osaf.framework.certstore.data")

    def tearDown(self):
        super(TestSSL, self).tearDown()
        Utility.stopCrypto(self.profileDir)

    def testCertificateVerification(self):
        ctx = ssl.getContext(self.view)
        conn1 = SSL.Connection(ctx)
        #conn2 = SSL.Connection(ctx)#XXX Why can't I reuse the connection?

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
            #conn2.setblocking(1)

        if not self.isOnline():
            return

        # We wrap the connect() in try/except and filter some common
        # network errors that are not SSL-related.
        try:
            self.assert_(conn1.connect(('www.thawte.com', 443)) >= 0)
            conn1.clear()

            #self.assertRaises(SSL.SSLError, conn2.connect, ('bugzilla.osafoundation.org', 443))
            #conn2.clear()
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

        factory = protocol.ClientFactory()
        wrapper = ssl.TwistedProtocolWrapper(self.view,
                                             'tlsv1',
                                             factory,
                                             policies.WrappingFactory(factory),
                                             0,
                                             1)

        self.assert_(wrapper.postConnectionVerify(x509, 'bugzilla.osafoundation.org'))
        self.assertRaises(Checker.WrongHost, wrapper.postConnectionVerify, 
                          x509, 'example.com')
        self.assertRaises(Checker.NoCertificate, wrapper.postConnectionVerify, 
                          None, 'example.com')
        
    def testCertificateCache(self):
        pemRoot = '''-----BEGIN CERTIFICATE-----
MIIDpzCCAxCgAwIBAgIBADANBgkqhkiG9w0BAQQFADCBmjELMAkGA1UEBhMCVVMx
CzAJBgNVBAgTAkNBMRYwFAYDVQQHEw1TYW4gRnJhbmNpc2NvMRowGAYDVQQKExFv
c2Fmb3VuZGF0aW9uLm9yZzELMAkGA1UECxMCQ0ExEDAOBgNVBAMTB09TQUYgQ0Ex
KzApBgkqhkiG9w0BCQEWHGhvc3RtYXN0ZXJAb3NhZm91bmRhdGlvbi5vcmcwHhcN
MDQwNjAyMjEzNTIzWhcNMjkwNTI3MjEzNTIzWjCBmjELMAkGA1UEBhMCVVMxCzAJ
BgNVBAgTAkNBMRYwFAYDVQQHEw1TYW4gRnJhbmNpc2NvMRowGAYDVQQKExFvc2Fm
b3VuZGF0aW9uLm9yZzELMAkGA1UECxMCQ0ExEDAOBgNVBAMTB09TQUYgQ0ExKzAp
BgkqhkiG9w0BCQEWHGhvc3RtYXN0ZXJAb3NhZm91bmRhdGlvbi5vcmcwgZ8wDQYJ
KoZIhvcNAQEBBQADgY0AMIGJAoGBAMvKQY9ElPz4UOhYwKPhbHpSzxxGXxQHiOGu
QDV9HuTaTD53cs4xhTau5nLrbqR6qkOpaxgq4+xGZGXwwdrl6vABXGamBAIS8U+C
IoxMZmdi1zNCHpALjrUOr5zG+l5lbxKMzzfbBgz0EvnxdyUW3JzWlFA7gtKwNeq9
8BbIVNIRAgMBAAGjgfowgfcwHQYDVR0OBBYEFFAUmTv7d1YAmmssTPTcaE3FWgdL
MIHHBgNVHSMEgb8wgbyAFFAUmTv7d1YAmmssTPTcaE3FWgdLoYGgpIGdMIGaMQsw
CQYDVQQGEwJVUzELMAkGA1UECBMCQ0ExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28x
GjAYBgNVBAoTEW9zYWZvdW5kYXRpb24ub3JnMQswCQYDVQQLEwJDQTEQMA4GA1UE
AxMHT1NBRiBDQTErMCkGCSqGSIb3DQEJARYcaG9zdG1hc3RlckBvc2Fmb3VuZGF0
aW9uLm9yZ4IBADAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBAUAA4GBAAdPk2l4
bQBw41mQvTLGFVUx89oEqmlW8fMh06/PhNyKPvA+Ip/HL4fl71A8aGYINA2KGQeE
Mi6jbcmKpkTked0C7KzayFkggv/SZtmeibzOjQJbO5WQCRgYuF9t7Rijk7oiAt3U
3rOIG1GsNPeKaSKyc+Bpqd9phY+fPNsZf8b4
-----END CERTIFICATE-----'''
        
        self.assert_(ssl.certificateCache == [], 'cache should start empty')
        ssl.getContext(self.view) # set cache
        self.assert_(ssl.certificateCache != [], 'cache should have an entry after getting a context')
        
        x509 = X509.load_cert_string(pemRoot)
        fingerprint = utils.fingerprint(x509)
        cert = certificate.importCertificate(x509,
                                             fingerprint,
                                             constants.TRUST_AUTHENTICITY | constants.TRUST_SERVER,
                                             self.view)
        self.assert_(ssl.certificateCache == [], 'cache should have been cleared after adding a cert')

        ssl.getContext(self.view) # set cache
        cert.trust = 0
        self.assert_(ssl.certificateCache == [], 'cache should have been cleared after changing cert.trust attribute')

        ssl.getContext(self.view) # set cache
        del cert.trust
        self.assert_(ssl.certificateCache == [], 'cache should have been cleared after deleting cert.trust attribute')

        ssl.getContext(self.view) # set cache
        cert.delete()
        self.assert_(ssl.certificateCache == [], 'cache should have been cleared after removing a cert')

if __name__ == "__main__":
    unittest.main()
