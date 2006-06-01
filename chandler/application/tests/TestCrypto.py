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
        self.assert_(r == 0, r)
        r = Utility.stopCrypto(self.path)
        self.assert_(r == 0, r)

        # Trick us into thinking we have initialized entropy
        from osaf.framework.certstore import utils
        utils.entropyInitialized = True

        # Now we should save 1k on stop, after that loading and saving 1k
        r = Utility.initCrypto(self.path)
        self.assert_(r == 0, r)
        r = Utility.stopCrypto(self.path)
        self.assert_(r == 1024, r)
        r = Utility.initCrypto(self.path)
        self.assert_(r == 1024, r)
        r = Utility.stopCrypto(self.path)
        self.assert_(r == 1024, r)


if __name__=='__main__':
    unittest.main()
