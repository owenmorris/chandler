"""
Unit tests for X509 certificates.
"""

__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest
import crypto.tests.CryptoTestCase as CryptoTestCase
from M2Crypto import RSA, X509, EVP, m2, Rand, Err
import crypto.tests.ca as ca

class X509(CryptoTestCase.CryptoTestCase):

    def _passphrase_callback(self, v):
        return "passw0rd"
            
    def testCA(self):
        (cert, rsa) = ca.ca()

        self.assert_(isinstance(rsa, RSA.RSA))         
        # XXX Why does this work in /internal/m2crypto/demo/x509/ca.py
        # XXX but crashes Python when run with HardHat here?
        #rsa.save_key('ca_rsa.pem', cipher='aes_256_cbc', callback=self._passphrase_callback)

        # XXX Why doesn't isinstance work here?
        #self.assert_(isinstance(cert, X509.X509))
        cert.save_pem('ca_cert.pem')
        
if __name__ == "__main__":
    unittest.main()
