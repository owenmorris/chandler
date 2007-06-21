#   Copyright (c) 2003-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import unittest, sys, os

from application import Utility, Globals
from chandlerdb.util.c import Default
from repository.persistence.RepositoryView import NullRepositoryView

# This test class is a possible replacement for RepositoryTestCase, and it
# makes use of Utility.py startup helper methods.  I'm trying it out for a
# while to iron out the wrinkles, and if it works, perhaps we could migrate
# other tests to use it.  So far sharing/tests/TestUIDMap uses it.
# ~morgen

class NRVTestCase(unittest.TestCase):

    def setUp(self):
        Globals.options = Utility.initOptions()
        Utility.initLogging(Globals.options)
        self.view = NullRepositoryView()
        Utility.initTimezone(Globals.options, self.view)

class SingleRepositoryTestCase(unittest.TestCase):

    def setUp(self):
        Globals.options = Utility.initOptions()
        Globals.options.ramdb = True
        Utility.initLogging(Globals.options)
        self.view = Utility.initRepository("", Globals.options, True)
        Utility.initTimezone(Globals.options, self.view)

    def reopenRepository(self):
        view = self.view
        view.commit()
        view.closeView()
        view.openView(timezone=Default)
        Utility.initTimezone(Globals.options, view)
        

class DualRepositoryTestCase(unittest.TestCase):

    def setUp(self):
        Globals.options = Utility.initOptions()
        Globals.options.ramdb = True
        Utility.initLogging(Globals.options)
        self.views = []
        for i in xrange(2):
            view = Utility.initRepository("", Globals.options, True)
            view.name = "test_view_%d" % i
            self.views.append(view)
            Utility.initTimezone(Globals.options, view)


if __name__ == "__main__":
    unittest.main()
