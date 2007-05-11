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

"""
Basic Unit tests for Chandler repository
"""

import RepositoryTestCase, os, unittest

from repository.util.Path import Path
from chandlerdb.persistence.c import DBNoSuchFileError
import util.timing

class RepositoryTest(RepositoryTestCase.RepositoryTestCase):
    """ Very basic repository tests """

    def _repositoryExists(self):
        try:
            self.rep.open()
            self.fail()
        except DBNoSuchFileError:
            self.assert_(True)

    def testCommit(self):
        pass

    def testHasRoot(self):
        view = self.view
        self.assert_(view.hasRoot('Schema'))
        self.assert_(view.hasRoot('Packs'))
        pass

    def testGetRoot(self):

        view = self.view
        root = view.getRoot('Packs')
        #TODO these should use UUID's
        self.assert_(root.itsName == 'Packs')
    
        root = view['Packs']
        self.assert_(root.itsName == 'Packs')
    
    def testIterRoots(self):
        """ Make sure the roots of the repository are correct"""

        # (The parcel manager sticks the //parcels root in there)
        view = self.view
        for root in view.iterRoots():
            self.assert_(root.itsName in ['Schema', 'Packs', 'parcels', 'Queries', 'userdata'])

    def testWalk(self):
        def callme(self, path, x):
            print path
            print x.itsName

        view = self.view
        view.walk(Path('//Schema/Core/Parcel'), callme)
#TODO what's a resonable test here?
        pass

    def testFind(self):
        """ Make sure we can run find """
        util.timing.reset()
        util.timing.begin("repository.tests.TestRepository.testFind")
        view = self.view
        kind = view.findPath('//Schema/Core/Kind')
        util.timing.end("repository.tests.TestRepository.testFind")
        util.timing.results(verbose=False)

        self.assert_(kind is not None)
        #TODO should check UUID
        pass

#    def testDir(self):
#        #TODO NOOP because it prints
#        pass

    def testCheck(self):
        view = self.view
        self.assert_(view.check())

    def testGetUUID(self):
        #TODO -- can't rely on UUID to be the same
        view = self.view
        self.assert_(view.itsUUID is not None)

if __name__ == "__main__":
    unittest.main()
