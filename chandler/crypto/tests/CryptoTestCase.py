"""
A base class for crypto testing
"""
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from unittest import TestCase
import application.Globals as Globals
from crypto import Crypto

class CryptoTestCase(TestCase):

    def setUp(self):
        Globals.crypto = Crypto.Crypto()
        Globals.crypto.init()        

    def tearDown(self):
        Globals.crypto.shutdown()
