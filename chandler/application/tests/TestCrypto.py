import unittest, os, sys
from i18n.tests import uw

from application import Utility

class CryptoTestCase(unittest.TestCase):
    def _removePool(self):
        try:
            os.remove(os.path.join(self.path, 'randpool.dat'))
        except OSError:
            pass

    def setUp(self):
        u = uw("profileDir_")
        self.path = os.path.join(os.path.dirname(__file__),
                                 u.encode('utf8'))

        try:
            os.makedirs(self.path)
        except OSError:
            pass

        self._removePool()

    def tearDown(self):
        self._removePool()

        try:
            os.rmdir(self.path)
        except OSError:
            pass

    def testCrypto(self):
        # First time there should not be anything, so load and save 0
        r = Utility.initCrypto(self.path)
        self.assert_(r == 0, 'First time crypto init should return 0, got %d' % r)
        r = Utility.stopCrypto(self.path)
        self.assert_(r == 0, 'First time crypto stop should return 0, got %d' % r)

        # Trick us into thinking we have initialized entropy
        from osaf.framework.certstore import utils
        utils.entropyInitialized = True

        # Now we should save 1k on stop, after that loading and saving 1k
        r = Utility.initCrypto(self.path)
        self.assert_(r == 0, 'Entropy initialized, crypto init should return 0 first time, got %d' % r)
        
        # Note: the most likely reason why these would fail is if the entropy
        # file was not created, for example if we failed to create the
        # directory in setUp()
        r = Utility.stopCrypto(self.path)
        self.assert_(r == 1024, 'Entropy initialized, should save 1024 entropy first time, got %d' % r)
        r = Utility.initCrypto(self.path)
        self.assert_(r == 1024, 'Entropy initialized, should load 1024 entropy, got %d' % r)
        r = Utility.stopCrypto(self.path)
        self.assert_(r == 1024, 'Entropy initialized, should save 1024 entropy, got %d' % r)


if __name__=='__main__':
    unittest.main()
