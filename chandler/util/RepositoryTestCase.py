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
A base class for repository testing Chandler
"""

import os, logging

from chandlerdb.util.RepositoryTestCase import RepositoryTestCase as TestCase
from application.Parcel import Manager as ParcelManager


class RepositoryTestCase(TestCase):

    def _openRepository(self, ramdb=True):

        super(RepositoryTestCase, self)._openRepository(ramdb)
        self.manager = ParcelManager.get(self.view, [os.path.join(self.rootdir,
                                                                  'parcels')])

    def setUp(self, ramdb=True, testdir=None):

        self.rootdir = os.environ['CHANDLERHOME']
        self.chandlerPack = os.path.join(self.rootdir, 'repository',
                                         'packs', 'chandler.pack')
        if testdir is None:
            testdir = os.path.join(self.rootdir, 'test_profile')
        else:
            testdir = os.path.join(self.rootdir, testdir)

        super(RepositoryTestCase, self).setUp(ramdb, testdir)

    def _reopenRepository(self):

        super(RepositoryTestCase, self)._reopenRepository()
        self.manager = ParcelManager.get(self.view, [os.path.join(self.rootdir,
                                                                  'parcels')])

    def loadParcel(self, namespace):
        self.loadParcels([namespace])

    def loadParcels(self, namespaces=None):
        self.manager.loadParcels(namespaces)
