"""
Unit test for SSL context, connection and related security checks.

@copyright: Copyright (c) 2004-2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import unittest
import socket, sys, os
import M2Crypto.SSL as SSL
import crypto
import crypto.ssl as ssl

import repository.tests.RepositoryTestCase as RepositoryTestCase

class TestSSL(RepositoryTestCase.RepositoryTestCase):
    def setUp(self):
        #XXX Same as TestCryptoStartupShutdown.InitShutdown.setUp
        pathComponents = sys.modules['crypto'].__file__.split(os.sep)
        assert len(pathComponents) > 3
        chandlerDir = os.sep.join(pathComponents[0:-2])
        self.profileDir = os.path.join(chandlerDir, 'crypto')
        crypto.startup(self.profileDir)        

        super(TestSSL, self)._setup()
        self.testdir = os.path.join(chandlerDir, 'crypto', 'tests')
        super(TestSSL, self)._openRepository()

        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/certstore")
        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/certstore/schema")

    def tearDown(self):
        super(TestSSL, self).tearDown()
        
        #XXX Same as TestCryptoStartupShutdown.InitShutdown.tearDown
        crypto.shutdown(self.profileDir)
    
    def testSSL(self):
        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/certstore/data")

        # Should have a list of these and randomly select to avoid
        # hitting the same sites over and over.
        #site = 'www.verisign.com'
        site = 'www.thawte.com'
        
        ctx = ssl.getContext(self.rep.view)
        socket.setdefaulttimeout(20)
        conn = SSL.Connection(ctx)

        if socket.getdefaulttimeout() is not None:
            # A workaround for M2Crypto bug 2341. If Chandler
            # unit tests are run with run_tests.py, the feedparser
            # calls socket.setdefaulttimeout() which will break
            # this test case. But since we are just testing to make
            # sure that:
            #   1) SSL certificate verification works and
            #   2) post connection check works
            # we can safely force this test to run in blocking mode.
            #
            # Also, the SSL.Connection code is not used in Chandler.
            # In Chandler we use TwistedProtocolWrapper, which
            # works even when socket.setdefaulttimeout() has been
            # called. 
            # XXX We should really test it here, but we first need
            # XXX to figure out how to run these kinds of twisted tests
            # XXX because reactor.run()/stop() can be called only once
            # XXX in a program.
            conn.setblocking(1)
            
        if not self.isOnline():
            return
            
        # We wrap the connect() in try/except and filter some common
        # network errors that are not SSL-related.
        try:
            assert conn.connect((site, 443)) >= 0
        except socket.gaierror, e:
            if e.args[0] == 7: #'No address associated with nodename'
                return
            if e.args[0] == -3: #'Temporary failure in name resolution'
                return
            raise

        ssl.postConnectionCheck(conn.get_peer_cert(), site)

        conn.clear()

    def isOnline(self):
        try:
            socket.gethostbyname('www.osafoundation.org')
            return True
        except:
            return False

        
if __name__ == "__main__":
    unittest.main()
