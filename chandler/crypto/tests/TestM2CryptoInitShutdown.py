"""
Unit test for M2Crypto startup and shutdown. When this works we know
we have the OpenSSL libraries and M2Crypto installed and almost certainly
working properly.

@copyright = Copyright (c) 2004 Open Source Applications Foundation
@license   = http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import unittest
import os, sys
import application.Globals as Globals
from crypto import Crypto


class InitShutdown(unittest.TestCase):
    def setUp(self):
        pathComponents = sys.modules['application'].__file__.split(os.sep)
        assert len(pathComponents) > 3
    
        chandlerDir = os.sep.join(pathComponents[0:-2])
      
        Globals.crypto = Crypto.Crypto(chandlerDir)
        Globals.crypto.init()        

    def tearDown(self):
        Globals.crypto.shutdown()

    def testAll(self):
        pass # setUp() and tearDown() do our test for us


if __name__ == "__main__":
    unittest.main()
