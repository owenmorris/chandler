"""
Basic Unit tests for Chandler repository
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest

from bsddb.db import DBNoSuchFileError
from repository.persistence.RepositoryError import RepositoryOpenDeniedError
from repository.persistence.DBRepository import DBRepository
import tools.timing

class BasicRepositoryTest(unittest.TestCase):
    """ Very basic repository tests """

    def _repositoryExists(self):
        try:
            self.rep.open()
            self.fail()
        except DBNoSuchFileError:
            pass
        except RepositoryOpenDeniedError:
            pass

    def setUp(self):
        self.rootdir = os.environ['CHANDLERHOME']
        self.testdir = os.path.join(self.rootdir, 'repository',
                                    'tests')
        self.rep = DBRepository(os.path.join(self.testdir, '__repository__'))

    def testNonExistent(self):
        """ The repository should not exist at this point """
        self.assert_(not self._repositoryExists())

    def testCreate(self):
        """ Create a repository and make sure it is open """
        tools.timing.reset()
        tools.timing.begin("repository.TestRepositoryBasic.testCreate")
        self.rep.create()
        tools.timing.end("repository.TestRepositoryBasic.testCreate")
        tools.timing.results(verbose=False)
        self.assert_(self.rep.check())
        self.assert_(self.rep.isOpen())

    def testDestroy(self):
        """ Create and then delete a repository, verify it doesn't exist """
        self.rep.create()
        self.rep.close()
        self.rep.delete()
        self.assert_(not self._repositoryExists())

    def testLoadPack(self):
        """ Minimal test to ensure that we can load packs
TODO is there more pack testing we need to do?
        """
        self.rep.create()
        self.assert_(self.rep.check())
        schemaPack = os.path.join(self.rootdir, 'repository',
                                  'packs', 'schema.pack')
        tools.timing.reset()
        tools.timing.begin("repository.TestRepositoryBasic.testLoadPack")
        self.rep.loadPack(schemaPack)
        tools.timing.end("repository.TestRepositoryBasic.testLoadPack")
        tools.timing.results(verbose=False)
        self.assert_(self.rep.check())
    
    def tearDown(self):
        self.rep.close()
        self.rep.delete()

if __name__ == "__main__":
    unittest.main()
