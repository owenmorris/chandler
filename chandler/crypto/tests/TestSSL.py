"""
Unit test for SSL context, connection and related security checks.

@copyright = Copyright (c) 2004 Open Source Applications Foundation
@license   = http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import unittest
import application.Globals as Globals
from crypto import Crypto
import TestM2CryptoInitShutdown
from M2Crypto import SSL

class TestSSL(TestM2CryptoInitShutdown.InitShutdown):
    
    def testSSL(self):
        if not self.isOnline():
            return
        
        ctx = Globals.crypto.getSSLContext(protocol='sslv3')
        conn = SSL.Connection(ctx)
        self.assert_(conn.connect(('www.verisign.com', 443)) >= 0)

        Globals.crypto.sslPostConnectionCheck(conn, 'FA5B0527BA98FC66276CA166BA22E44A73636C9')

        conn.clear()

    def isOnline(self):
        import socket
        try:
            a = socket.gethostbyname('www.osafoundation.org')
            return True
        except:
            return False

        
if __name__ == "__main__":
    unittest.main()
