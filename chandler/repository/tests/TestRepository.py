"""
Basic Unit tests for Chandler repository
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

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
        view = self.rep.view
        self.assert_(view.hasRoot('Schema'))
        self.assert_(view.hasRoot('Packs'))
        pass

    def testGetRoot(self):

        view = self.rep.view
        root = view.getRoot('Packs')
        #TODO these should use UUID's
        self.assert_(root.itsName == 'Packs')
    
        root = view['Packs']
        self.assert_(root.itsName == 'Packs')
    
    def testIterRoots(self):
        """ Make sure the roots of the repository are correct"""

        # (The parcel manager sticks the //parcels root in there)
        view = self.rep.view
        for root in view.iterRoots():
            self.assert_(root.itsName in ['Schema', 'Packs', 'parcels', 'Queries', 'userdata'])

    def testWalk(self):
        def callme(self, path, x):
            print path
            print x.itsName

        view = self.rep.view
        view.walk(Path('//Schema/Core/Parcel'), callme)
#TODO what's a resonable test here?
        pass

    def testFind(self):
        """ Make sure we can run find """
        util.timing.reset()
        util.timing.begin("repository.tests.TestRepository.testFind")
        view = self.rep.view
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
        view = self.rep.view
        self.assert_(view.check())

    def testGetUUID(self):
        #TODO -- can't rely on UUID to be the same
        view = self.rep.view
        self.assert_(view.itsUUID is not None)

if __name__ == "__main__":
    unittest.main()
