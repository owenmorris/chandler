"""
Test Certstore

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import unittest
import time
import M2Crypto.X509 as X509
import repository.tests.RepositoryTestCase as RepositoryTestCase
import repository.query.Query as Query
import osaf.framework.certstore.certificate as certificate

class CertificateStoreTestCase(RepositoryTestCase.RepositoryTestCase):
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
    pemUnsupported = '''-----BEGIN CERTIFICATE-----
MIIDnjCCAwegAwIBAgIQK2jUo0aexTsoCas4XX8nIDANBgkqhkiG9w0BAQUFADBf
MQswCQYDVQQGEwJVUzEXMBUGA1UEChMOVmVyaVNpZ24sIEluYy4xNzA1BgNVBAsT
LkNsYXNzIDEgUHVibGljIFByaW1hcnkgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkw
HhcNMDAwODA0MDAwMDAwWhcNMDQwODAzMjM1OTU5WjCBpzEXMBUGA1UEChMOVmVy
aVNpZ24sIEluYy4xHzAdBgNVBAsTFlZlcmlTaWduIFRydXN0IE5ldHdvcmsxOzA5
BgNVBAsTMlRlcm1zIG9mIHVzZSBhdCBodHRwczovL3d3dy52ZXJpc2lnbi5jb20v
UlBBIChjKTAwMS4wLAYDVQQDEyVDbGFzcyAxIFB1YmxpYyBQcmltYXJ5IE9DU1Ag
UmVzcG9uZGVyMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC57V56Ondfzl86
UvzNZPdxtW9qlsZZklWUXS9bLsER6iaKy6eBPPZaRN56Ey/9WlHZezcmSsAnPwQD
albBgyzhb1upVFAkSsYuekyhWzdUJCExH6F4GHansXDaItBq/gdiQMb39pt9DAa4
S8co5GYjhFHvRreT2IEzy+U2rMboBQIDAQABo4IBEDCCAQwwIAYDVR0RBBkwF6QV
MBMxETAPBgNVBAMTCE9DU1AgMS0xMDEGA1UdHwQqMCgwJqAkoCKGIGh0dHA6Ly9j
cmwudmVyaXNpZ24uY29tL3BjYTEuY3JsMBMGA1UdJQQMMAoGCCsGAQUFBwMJMEIG
CCsGAQUFBwEBBDYwNDAyBggrBgEFBQcwAaYmFiRodHRwOi8vb2NzcC52ZXJpc2ln
bi5jb20vb2NzcC9zdGF0dXMwRAYDVR0gBD0wOzA5BgtghkgBhvhFAQcBATAqMCgG
CCsGAQUFBwIBFhxodHRwczovL3d3dy52ZXJpc2lnbi5jb20vUlBBMAkGA1UdEwQC
MAAwCwYDVR0PBAQDAgeAMA0GCSqGSIb3DQEBBQUAA4GBAHCQ3bjkvlMXfH8C6dX3
i5mTMWCNfuZgayTvYKzSzpHegG0JpNO4OOVEynJeDS3Bd5y9LAN4KY2kpXeH9fEr
Jq3MB2w6VFoo4AnzTQoEytRYaQuns/XdAaXn3PAfusFdkI2z6k/BEVmXarIrE7Ha
rZehs7GgIFvKMquNzxPwHynD
-----END CERTIFICATE-----'''
    pemMultiple = '%s\n%s' % (pemSite, pemRoot)

    def disabled_testPreloadedCertificates(self):
        # XXX This test does not work right, verify fails in certain situations
        self.loadParcel("parcel:osaf.framework.certstore.data")
        
        qString = u'for i in "//parcels/osaf/framework/certstore/Certificate" where i.type == "root"'
        
        qName = 'rootCertsQuery'
        q = self.rep.view.findPath('//Queries/%s' %(qName))
        if q is None:
            p = self.rep.view.findPath('//Queries')
            k = self.rep.view.findPath('//Schema/Core/Query')
            q = Query.Query(qName, p, k, qString)
            
        now = time.gmtime()
        format = '%b %d %H:%M:%S %Y %Z'

        for cert in q:
            print cert.subjectCommonName
            x509 = cert.asX509()
            self.assertTrue(x509.verify())
                
            # verify() should have caught bad times, but just in case:
            before = x509.get_not_before()
            after = x509.get_not_after()
            try:
                assert time.strptime(str(before), format) < now, before
                assert now < time.strptime(str(after), format), after
            except ValueError:
                raise ValueError, 'bad time value in ' + cert.subjectCommonName
        
            self.assertTrue(len(cert.subjectCommonName) > 0)
            self.assertTrue(cert.type == 'root')
            self.assertTrue(cert.trust == certificate.TRUST_AUTHENTICITY | certificate.TRUST_SITE)
            self.assertTrue(cert.fingerprintAlgorithm == 'sha1')
            self.assertTrue(len(cert.fingerprint) > 3)
            self.assertTrue(cert.asTextAsString()[:12] == 'Certificate:')            
    
    def _importAndFind(self, pem, trust):
        x509 = X509.load_cert_string(pem)
        fingerprint = certificate._fingerprint(x509)
        certificate._importCertificate(x509,
                                      fingerprint,
                                      trust,
                                      self.rep.view)
        
        qString = u'for i in "//parcels/osaf/framework/certstore/Certificate" where i.fingerprint == "%s"' % fingerprint
        
        qName = 'fpCertQuery' + fingerprint
        q = self.rep.view.findPath('//Queries/%s' %(qName))
        if q is None:
            p = self.rep.view.findPath('//Queries')
            k = self.rep.view.findPath('//Schema/Core/Query')
            q = Query.Query(qName, p, k, qString)
            
        assert len(q) == 1
        
        for cert in q: #q[0] does not seem to work
            return cert
    
    def testImportSiteCertificate(self):
        trust = certificate.TRUST_AUTHENTICITY
        cert = self._importAndFind(self.pemSite, trust)

        x509 = cert.asX509()

        x509Issuer = X509.load_cert_string(self.pemRoot)
        issuerPublicKey = x509Issuer.get_pubkey()
        assert x509.verify(issuerPublicKey)
        
        assert x509.as_pem()[:-1] == self.pemSite
        assert x509.get_subject().CN == 'bugzilla.osafoundation.org'
        
        assert cert.fingerprint == '0xFF8013055AAE612AD79C347F06D1B83F93DEB664L'
        assert cert.trust == trust
        assert cert.type == 'site'
        assert cert.subjectCommonName == 'bugzilla.osafoundation.org'

    def testImportRootCertificate(self):
        trust = certificate.TRUST_AUTHENTICITY | certificate.TRUST_SITE
        cert = self._importAndFind(self.pemRoot, trust)

        x509 = cert.asX509()
        assert x509.verify()
        assert x509.as_pem()[:-1] == self.pemRoot
        assert x509.get_subject().CN == 'OSAF CA'
        
        assert cert.fingerprint == '0xADACC622C85DF4C2AE471A81EDA1BD28379A6FA9L'
        assert cert.trust == trust
        assert cert.type == 'root'
        assert cert.subjectCommonName == 'OSAF CA'
        
    def testImportUnsupportedCertificate(self):
        trust = certificate.TRUST_AUTHENTICITY
        self.assertRaises(Exception, self._importAndFind, self.pemUnsupported, trust)
        
    def testImportMultipleCertificate(self):
        # XXX I would like to make it so that attempting to import when
        # XXX there are several certificates would be an error, but right now
        # XXX the system seems to load the first certificate in such a case.
        # XXX Need to investigate more what OpenSSL does and if there is any
        # XXX way to change this.
        #trust = certificate.TRUST_AUTHENTICITY
        #cert = self._importAndFind(self.pemMultiple, trust)
        pass

    def setUp(self):
        super(CertificateStoreTestCase, self).setUp()
        self.loadParcel("parcel:osaf.framework.certstore")
        
if __name__ == "__main__":
    unittest.main()
