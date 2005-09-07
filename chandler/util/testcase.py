from application import Utility, Globals
import unittest, sys, os

# This test class is a possible replacement for RepositoryTestCase, and it
# makes use of Utility.py startup helper methods.  I'm trying it out for a
# while to iron out the wrinkles, and if it works, perhaps we could migrate
# other tests to use it.  So far sharing/tests/TestUIDMap uses it.
# ~morgen

class ChandlerTestCase(unittest.TestCase):

    parcels = [] # Default: load all parcels

    def setUp(self):
        global parcels

        Globals.options = Utility.initOptions()
        Globals.options.create = True
        Globals.options.ramdb = True
        Globals.chandlerDirectory = Utility.locateChandlerDirectory()
        os.chdir(Globals.chandlerDirectory)
        profileDir = Globals.options.profileDir
        Utility.initLogging(Globals.options)
        parcelPath = Utility.initParcelEnv(Globals.chandlerDirectory,
                                           Globals.options.parcelPath)
        self.view = Utility.initRepository(None, Globals.options)
        Utility.initCrypto(Globals.options.profileDir)
        Utility.initParcels(self.view, parcelPath, self.parcels)

if __name__ == "__main__":
    unittest.main()
