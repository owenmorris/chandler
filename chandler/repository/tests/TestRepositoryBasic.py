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

import os, unittest

from chandlerdb.persistence.c import DBNoSuchFileError
from repository.persistence.RepositoryError import \
    RepositoryOpenDeniedError, RepositoryVersionError
from repository.persistence.DBRepository import DBRepository
import util.timing

class TestRepositoryBasic(unittest.TestCase):
    """ Very basic repository tests """

    def _repositoryExists(self):
        try:
            self.rep.open()
            self.fail()
        except DBNoSuchFileError:
            pass
        except RepositoryOpenDeniedError:
            pass
        except RepositoryVersionError:
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
        util.timing.reset()
        util.timing.begin("repository.TestRepositoryBasic.testCreate")
        self.rep.create()
        self.view = view = self.rep.createView()
        util.timing.end("repository.TestRepositoryBasic.testCreate")
        util.timing.results(verbose=False)
        self.assert_(self.view.check())
        self.assert_(self.rep.isOpen())

    def testDestroy(self):
        """ Create and then delete a repository, verify it doesn't exist """
        self.rep.create()
        self.rep.close()
        self.rep.delete()
        self.assert_(not self._repositoryExists())

    def testLoadPack(self):
        """ Minimal test to ensure that we can load packs
        """
        self.rep.create()
        util.timing.reset()
        util.timing.begin("repository.TestRepositoryBasic.testLoadPack")
        view = self.rep.createView()
        util.timing.end("repository.TestRepositoryBasic.testLoadPack")
        util.timing.results(verbose=False)
        self.assert_(view.check())
    
    def tearDown(self):
        self.rep.close()
        self.rep.delete()

if __name__ == "__main__":
    unittest.main()
