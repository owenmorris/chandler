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
A base class for repository testing
"""

import os, logging
from unittest import TestCase

from chandlerdb.persistence.DBRepository import DBRepository
from chandlerdb.util.Path import Path


class RepositoryTestCase(TestCase):

    logLevel = logging.WARNING      # a nice quiet default

    def _openRepository(self, ramdb=True):

        self.rep = DBRepository(os.path.join(self.testdir, '__repository__'))

        self.rep.create(ramdb=self.ramdb, refcounted=True)
        self.rep.logger.setLevel(self.logLevel)

        self.view = view = self.rep.createView("Test")
        view.commit()

    def setUp(self, ramdb=True, testdir='tests'):

        self.ramdb = ramdb
        self.testdir = testdir
        self._openRepository(ramdb)

    def tearDown(self):
        self.rep.close()
        self.rep.logger.debug('RAMDB = %s', self.ramdb)
        if not self.ramdb:
            self.rep.delete()

    def _reopenRepository(self):
        view = self.view
        view.commit()

        if self.ramdb:
            view.closeView()
            view.openView()
        else:
            dbHome = self.rep.dbHome
            self.rep.close()
            self.rep = DBRepository(dbHome)
            self.rep.open()
            self.view = view = self.rep.createView("Test")

    def loadCineguide(self, view, commit=True):

        view.loadPack('data/packs/cineguide.pack', package='tests')
        if commit:
            view.commit()

    def loadCollections(self, view, commit=True):

        view.loadPack('data/packs/collections.pack', package='tests')
        if commit:
            view.commit()
        
    _KIND_KIND = Path("//Schema/Core/Kind")
    _ITEM_KIND = Path("//Schema/Core/Item")

    # Repository specific assertions
    def assertIsRoot(self, item):
        self.assert_(item in list(item.itsView.iterRoots()))

    def assertItemPathEqual(self, item, string):
        self.assertEqual(str(item.itsPath), string)

    def setLoggerLevel(self, level):
        current = self.rep.logger.level
        self.rep.logger.setLevel(level)
        return current
