"""
Unit test for SSL context, connection and related security checks.

@copyright: Copyright (c) 2004-2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import unittest
import socket
from M2Crypto import SSL
import application.Globals as Globals
import crypto
import TestM2CryptoInitShutdown

# XXX This should not inherit from InitShutdown because that makes us
#     run it's tests too
class TestSSL(TestM2CryptoInitShutdown.InitShutdown):
    
    def testSSL(self):
        if not self.isOnline():
            return

        # Should have a list of these and randomly select to avoid
        # hitting the same sites over and over.
        #site = 'www.verisign.com'
        #fp   = '0FA5B0527BA98FC66276CA166BA22E44A73636C9'
        site = 'www.thawte.com'
        fp   = 'D85FE7EC903564DEFD4BCFF82047726F14C09C31'
        
        ctx = Globals.crypto.getSSLContext()
        conn = SSL.Connection(ctx)

        # We wrap the connect() in try/except and filter some common
        # network errors that are not SSL-related.
        try:
            self.assert_(conn.connect((site, 443)) >= 0)
        except socket.gaierror, e:
            if e.args[0] == 7: #'No address associated with nodename'
                return
            if e.args[0] == -3: #'Temporary failure in name resolution'
                return
            raise

        crypto.ssl.postConnectionCheck(conn, fp, hostCheck=True)

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
