"""
Unit tests for X509 certificates.
"""

__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest
import crypto.tests.CryptoTestCase as CryptoTestCase
from M2Crypto import RSA, X509, EVP, m2, Rand, Err

class X509(CryptoTestCase.CryptoTestCase):
    def testRSAKeyGeneration(self):
        self.assert_(isinstance(RSA.gen_key(2048, m2.RSA_F4), RSA.RSA))

if __name__ == "__main__":
    unittest.main()
