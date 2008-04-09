#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
import pkg_resources

from application import Utility, Globals
from chandlerdb.util.c import Default
from chandlerdb.persistence.RepositoryView import NullRepositoryView
from chandlerdb.item.Item import Item

# This test class is a possible replacement for RepositoryTestCase, and it
# makes use of Utility.py startup helper methods.  I'm trying it out for a
# while to iron out the wrinkles, and if it works, perhaps we could migrate
# other tests to use it.  So far sharing/tests/TestUIDMap uses it.
# ~morgen

class BaseTestCase(unittest.TestCase):

    def getTestResourcePath(self, filename):
        """
        Find the file with filename in the same directory as C{self}'s
        python module. Used to locate test data (like, files to import,
        etc). Returns a C{unicode} object (not C{str}).
        """
        path = pkg_resources.resource_filename(self.__class__.__module__,
                                               filename)
        # path is a str here, so convert it to unicode
        if not isinstance(path, unicode):
            path = unicode(path, sys.getfilesystemencoding())
        return path

class NRVTestCase(BaseTestCase):

    def setUp(self):
        Globals.options = Utility.initOptions()
        Utility.initLogging(Globals.options)
        self.view = NullRepositoryView()
        Utility.initTimezone(Globals.options, self.view)

class SingleRepositoryTestCase(BaseTestCase):

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

class SharedSandboxTestCase(SingleRepositoryTestCase):
    """
    This test case class uses a single repository view, which is left
    in place across invocation of individual tests. At the start of each
    test case (i.e. in C{setUp}) an Item is created at the path '//sandbox',
    and this is destroyed afterwards (i.e. in C{tearDown}). This means that
    if you specify itsParent=self.sandbox when creating persistent items
    in your test code, these items will be cleaned up after each test.
    
    @ivar sandbox: The poarent for items you want cleaned up in the test
    @type sandbox: C{Item}
    """

    view = None

    def setUp(self):
        if SharedSandboxTestCase.view is None:
            super(SharedSandboxTestCase,self).setUp()
            SharedSandboxTestCase.view = self.view
            del self.view
            
        self.sandbox = Item("sandbox", SharedSandboxTestCase.view, None)
        
    def tearDown(self):
        self.sandbox.delete(recursive=True)
        self.sandbox.itsView.commit()
        self.sandbox = None
        
    def reopenRepository(self):
        self.view = self.sandbox.itsView
        path = self.sandbox.itsPath
        super(SharedSandboxTestCase, self).reopenRepository()
        self.sandbox = self.view.findPath(path)
        del self.view

class DualRepositoryTestCase(BaseTestCase):

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
