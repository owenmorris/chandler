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

"""
A base class for repository testing
"""

from unittest import TestCase
import logging, os, sys

from repository.persistence.DBRepository import DBRepository
from repository.util.Path import Path
from application.Parcel import Manager as ParcelManager
from application import schema

class RepositoryTestCase(TestCase):

    logLevel = logging.WARNING      # a nice quiet default

    def _setup(self, ramdb=True):
        self.rootdir = os.environ['CHANDLERHOME']
        self.chandlerPack = os.path.join(self.rootdir, 'repository',
                                         'packs', 'chandler.pack')

        handler = \
         logging.FileHandler(os.path.join(self.rootdir,'chandler.log'))
        formatter = \
         logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.addHandler(handler)

        self.ramdb = ramdb

    def _openRepository(self, ramdb=True):
        preloadedRepositoryPath = os.path.join(self.testdir, '__preloaded_repository__')
        self.rep = DBRepository(os.path.join(self.testdir, '__repository__'))

        if os.path.exists(preloadedRepositoryPath):
            self.ramdb = False
            self.rep.open(ramdb=False,
                          restore=preloadedRepositoryPath,
                          refcounted=True)
            self.rep.logger.setLevel(self.logLevel)
            self.rep.logger.info('Using preloaded repository')
        else:
            self.rep.create(ramdb=self.ramdb,
                            refcounted=True)
            self.rep.logger.setLevel(self.logLevel)
            self.rep.view.loadPack(self.chandlerPack)
            self.rep.view.commit()

        view = self.rep.view

        self.manager = \
            ParcelManager.get(view, [os.path.join(self.rootdir, 'parcels')])

    def setUp(self, ramdb=True):
        self._setup(ramdb)

        self.testdir = os.path.join(self.rootdir, 'repository',
                                    'tests')
        self._openRepository(ramdb)

    def tearDown(self):
        self.rep.close()
        self.rep.logger.debug('RAMDB = %s', self.ramdb)
        if not self.ramdb:
            self.rep.delete()

    def _reopenRepository(self):
        self.rep.view.commit()

        if self.ramdb:
            self.rep.view.closeView()
            self.rep.view.openView()
        else:
            self.rep.close()
            self.rep = DBRepository(os.path.join(self.testdir,
                                                 '__repository__'))
            self.rep.open()

        self.manager = \
         ParcelManager.get(self.rep.view, \
         path=[os.path.join(self.rootdir, 'parcels')])

    def _find(self, path):
        return self.rep.view.findPath(path)

    def loadParcel(self, namespace):
        self.loadParcels([namespace])

    def loadParcels(self, namespaces=None):
        self.manager.loadParcels(namespaces)

    _KIND_KIND = Path("//Schema/Core/Kind")
    _ITEM_KIND = Path("//Schema/Core/Item")

    # Repository specific assertions
    def assertIsRoot(self, item):
        self.assert_(item in list(self.rep.view.iterRoots()))

    def assertItemPathEqual(self, item, string):
        self.assertEqual(str(item.itsPath), string)
