"""
Basic Unit tests for Chandler repository
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from bsddb.db import DBNoSuchFileError
from repository.persistence.XMLRepository import XMLRepository
from repository.schema.DomainSchemaLoader import DomainSchemaLoader

class RepositoryTest(unittest.TestCase):
    """ Very basic repository tests """

    def _repositoryExists(self):
        try:
            self.rep.open()
            self.fail()
        except DBNoSuchFileError:
            self.assert_(True)

    def setUp(self):
        self.rootdir = os.environ['CHANDLERDIR']
        self.rep = XMLRepository('RepositoryUnitTest-Repository')
        self.rep.create()
        schemaPack = os.path.join(self.rootdir, 'repository', 'packs', 'schema.pack')
        self.rep.loadPack(schemaPack)
        self.loader = DomainSchemaLoader(self.rep)

    def testCommit(self):
        pass

    def testHasRoot(self):
        self.assert_(self.rep.hasRoot('Schema'))
        self.assert_(self.rep.hasRoot('Packs'))
        pass

    def testGetRoot(self):
        root = self.rep.getRoot('Packs')
        #TODO these should use UUID's
        self.assert_(root.getItemName() == 'Packs')
    
    def testGetRoots(self):
        """ Make sure the roots of the repository are correct"""
        roots = self.rep.getRoots()
        schema = roots[0]
        packs = roots[1]
        #TODO these should use UUID's
        self.assert_(schema.getItemName() == 'Schema')
        self.assert_(packs.getItemName() == 'Packs')

    def testWalk(self):
        def callme(self, path, x):
            print path
            print x.getItemName()

        self.rep.walk('//Schema/Core/Parcel', callme)
#TODO what's a resonable test here?
        pass

    def testFind(self):
        """ Make sure we can run find """
        kind = self.rep.find('//Schema/Core/Kind')
        self.assert_(kind is not None)
        #TODO should check UUID
        pass

#    def testDir(self):
#        #TODO NOOP because it prints
#        pass

    def testCheck(self):
        self.assert_(self.rep.check())

    def testGetUUID(self):
        #TODO -- can't rely on UUID to be the same
        self.assert_(self.rep.getUUID() is not None)

    def tearDown(self):
        self.rep.close()
        self.rep.delete()

if __name__ == "__main__":
    unittest.main()
