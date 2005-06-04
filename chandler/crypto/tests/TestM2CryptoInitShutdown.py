"""
Unit test for M2Crypto startup and shutdown. When this works we know
we have the OpenSSL libraries and M2Crypto installed and almost certainly
working properly.

@copyright: Copyright (c) 2004-2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import unittest, os, sys
import crypto

class InitShutdown(unittest.TestCase):
    def setUp(self):
        pathComponents = sys.modules['crypto'].__file__.split(os.sep)
        assert len(pathComponents) > 3
        chandlerDir = os.sep.join(pathComponents[0:-2])
        self.profileDir = os.path.join(chandlerDir, 'crypto')
        crypto.startup(self.profileDir)        

    def tearDown(self):
        crypto.shutdown(self.profileDir)

    def testAll(self):
        pass # setUp() and tearDown() do our test for us


if __name__ == "__main__":
    unittest.main()
