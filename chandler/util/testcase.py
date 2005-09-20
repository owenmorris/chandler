from application import Utility, Globals
import unittest, sys, os
from repository.persistence.RepositoryView import NullRepositoryView

# This test class is a possible replacement for RepositoryTestCase, and it
# makes use of Utility.py startup helper methods.  I'm trying it out for a
# while to iron out the wrinkles, and if it works, perhaps we could migrate
# other tests to use it.  So far sharing/tests/TestUIDMap uses it.
# ~morgen

class NRVTestCase(unittest.TestCase):

    def setUp(self):
        Globals.options = Utility.initOptions()
        Globals.chandlerDirectory = Utility.locateChandlerDirectory()
        os.chdir(Globals.chandlerDirectory)
        profileDir = Globals.options.profileDir
        Utility.initLogging(Globals.options)
        self.view = NullRepositoryView()

if __name__ == "__main__":
    unittest.main()
