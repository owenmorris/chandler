"""
Unit tests Password class
"""

__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest
from unittest import TestCase
import crypto.tests.CryptoTestCase as CryptoTestCase
import crypto.Password as Password

class PasswordTest(TestCase):

    def testEmptyPassword(self):
        p = Password.Password()
        self.assert_(isinstance(p, Password.Password))
        self.assert_(str(p) == '')
        p.clear()

    def testPassword(self):
        pw = 'mypass'
        p = Password.Password(pw)
        self.assert_(isinstance(p, Password.Password))
        self.assert_(str(p) == pw)
        p.clear()
        self.assert_(str(p) == '')
        p.set(pw)
        self.assert_(str(p) == pw)
        p.set(pw + pw)
        self.assert_(str(p) == (pw + pw))

    def testTypeError(self):
        pw = ['mypass']
        try:
            p = Password.Password(pw)
            raise Exception, 'should not be able to use non strings as password'
        except TypeError:
            pass

        p = Password.Password()
        try:
            p.set(pw)
            raise Exception, 'should not be able to use non strings as password'
        except TypeError:
            pass

        
if __name__ == "__main__":
    unittest.main()
