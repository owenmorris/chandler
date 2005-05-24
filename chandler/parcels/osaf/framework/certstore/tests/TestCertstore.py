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
    def testPreloadedCertificates(self):
        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/certstore/data")
        
        qString = u'for i in "//parcels/osaf/framework/certstore/schema/Certificate" where True'
        
        qName = 'allCertsQuery'
        q = self.rep.view.findPath('//Queries/%s' %(qName))
        if q is None:
            p = self.rep.view.findPath('//Queries')
            k = self.rep.view.findPath('//Schema/Core/Query')
            q = Query.Query(qName, p, k, qString)
            
        now = time.gmtime()
        format = '%b %d %H:%M:%S %Y %Z'

        for cert in q:
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
    
    def _testImportCertificate(self):
        # XXX Either this test works or the one above but not both at the
        # XXX same time.
        pemString = '''-----BEGIN CERTIFICATE-----
MIID9DCCA12gAwIBAgIBADANBgkqhkiG9w0BAQQFADCBszELMAkGA1UEBhMCVVMx
EzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNhbiBGcmFuY2lzY28xKzAp
BgNVBAoTIk9wZW4gU291cmNlIEFwcGxpY2F0aW9uIEZvdW5kYXRpb24xCzAJBgNV
BAsTAkNBMRAwDgYDVQQDEwdPU0FGIENBMSswKQYJKoZIhvcNAQkBFhxob3N0bWFz
dGVyQG9zYWZvdW5kYXRpb24ub3JnMB4XDTA0MDIxMDAyMDkxOVoXDTI5MDIwMzAy
MDkxOVowgbMxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlhMRYwFAYD
VQQHEw1TYW4gRnJhbmNpc2NvMSswKQYDVQQKEyJPcGVuIFNvdXJjZSBBcHBsaWNh
dGlvbiBGb3VuZGF0aW9uMQswCQYDVQQLEwJDQTEQMA4GA1UEAxMHT1NBRiBDQTEr
MCkGCSqGSIb3DQEJARYcaG9zdG1hc3RlckBvc2Fmb3VuZGF0aW9uLm9yZzCBnzAN
BgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAua/2CaL1tS+zw0Nd0+8ei4InJGCejGIx
TcLlXKagDIFnA3k3Nte/TLriLfviHl2z1vasSeel1QcGVGMybJRnYxGd5xm+lAyg
mOdM881CDR3O97iiC8E+KPddN8xvfYDSTJt8hY6I+CKpxgYvU0rj31wUiwJK08Wn
6tF4E/QTeDECAwEAAaOCARQwggEQMB0GA1UdDgQWBBQSfrCol47GWBxPPK1Z6j+c
eW+PKjCB4AYDVR0jBIHYMIHVgBQSfrCol47GWBxPPK1Z6j+ceW+PKqGBuaSBtjCB
szELMAkGA1UEBhMCVVMxEzARBgNVBAgTCkNhbGlmb3JuaWExFjAUBgNVBAcTDVNh
biBGcmFuY2lzY28xKzApBgNVBAoTIk9wZW4gU291cmNlIEFwcGxpY2F0aW9uIEZv
dW5kYXRpb24xCzAJBgNVBAsTAkNBMRAwDgYDVQQDEwdPU0FGIENBMSswKQYJKoZI
hvcNAQkBFhxob3N0bWFzdGVyQG9zYWZvdW5kYXRpb24ub3JnggEAMAwGA1UdEwQF
MAMBAf8wDQYJKoZIhvcNAQEEBQADgYEAE7sgxD2I3NLJF/wWw4nPMfwIHL5L/0PG
4I7Etbgp98vFxBKFf5gjKv8mjuec3F2/Xez0k8AP0e951pnvaH1PUpptByiu6nsw
8m7/hUuYJx/0Jkg3jv7u9fmXAgfPvxuGzRSWJItwndODXbjRaPw41NNJ93VEttw5
2ur5kIp9WbA=
-----END CERTIFICATE-----'''
        x509 = X509.load_cert_string(pemString)
        fingerprint = certificate._fingerprint(x509)
        certificate._importCertificate(x509,
                                      fingerprint,
                                      certificate.TRUST_AUTHENTICITY | certificate.TRUST_SITE,
                                      self.rep.view)
        
        qString = u'for i in "//parcels/osaf/framework/certstore/schema/Certificate" where i.fingerprint == "%s"' % fingerprint
        
        qName = 'fpCertQuery' + fingerprint
        q = self.rep.view.findPath('//Queries/%s' %(qName))
        if q is None:
            p = self.rep.view.findPath('//Queries')
            k = self.rep.view.findPath('//Schema/Core/Query')
            q = Query.Query(qName, p, k, qString)
            
        assert len(q) == 1
        
        for cert in q: #q[0] does not seem to work
            x509_rep = cert.asX509()
            assert x509_rep.verify()
            assert x509_rep.as_pem()[:-1] == pemString
            assert cert.fingerprint == fingerprint
            assert cert.trust == certificate.TRUST_AUTHENTICITY | certificate.TRUST_SITE
        

    def setUp(self):
        super(CertificateStoreTestCase, self).setUp()
        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/certstore")
        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/certstore/schema")
        
        
if __name__ == "__main__":
    unittest.main()
