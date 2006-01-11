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
        profileDir = Globals.options.profileDir
        Utility.initLogging(Globals.options)
        self.view = NullRepositoryView()

class SingleRepositoryTestCase(unittest.TestCase):

    def setUp(self):
        Globals.options = Utility.initOptions()
        Globals.options.ramdb = True
        profileDir = Globals.options.profileDir
        Utility.initLogging(Globals.options)
        self.view = Utility.initRepository("", Globals.options, True)

class DualRepositoryTestCase(unittest.TestCase):

    def setUp(self):
        Globals.options = Utility.initOptions()
        Globals.options.ramdb = True
        profileDir = Globals.options.profileDir
        Utility.initLogging(Globals.options)
        self.views = []
        for i in xrange(2):
            view = Utility.initRepository("", Globals.options, True)
            view.name = "test_view_%d" % i
            self.views.append(view)


if __name__ == "__main__":
    unittest.main()
