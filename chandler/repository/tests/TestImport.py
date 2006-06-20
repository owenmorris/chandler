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
Test importing of items across views and null repository view
"""

import unittest, os

from repository.item.Item import Item
from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.util.Path import Path
from repository.persistence.RepositoryView import NullRepositoryView

nv = NullRepositoryView()


class TestImport(RepositoryTestCase):
    """ Test importItem """

    def setUp(self):

        super(TestImport, self).setUp()

        nv.closeView()
        nv.openView()

    def _loadCG(self):

        view = self.rep.view
        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')
        view.loadPack(cineguidePack)
        self.kh = view.findPath('//CineGuide/KHepburn')
        self.kh.movies.addIndex('t', 'attribute', attribute='title')
        view.commit()

    def _setCopyExport(self, item):
        
        item._status |= Item.COPYEXPORT
        for child in item.iterChildren():
            self._setCopyExport(child)

    def _unsetCopyExport(self, item):
        
        item._status &= ~Item.COPYEXPORT
        for child in item.iterChildren():
            self._unsetCopyExport(child)

    def testImport(self):

        #self._unsetCopyExport(view.findPath('//Schema/Core/Parcel'))
        #self._unsetCopyExport(view.findPath('//Schema/Core/Manager'))

        self._loadCG()
        nv.clear()
        view = self.rep.view
        nv.importItem(self.kh)
        nv.importItem(view['Packs'])
        nv.importItem(view['parcels'])

        self.assert_(self.kh.itsView is nv)
        self.assert_(self.kh.itsParent.itsView is nv)
        self.assert_(self.kh.itsKind.itsView is nv)

        self.assert_(view.check())
        self.assert_(nv.check())

    def testCreate(self):

        #self._unsetCopyExport(view.findPath('//Schema/Core/Parcel'))
        #self._unsetCopyExport(view.findPath('//Schema/Core/Manager'))

        self._loadCG()
        nv.clear()
        view = self.rep.view
        nv.importItem(self.kh)
        nv.importItem(view['Packs'])
        nv.importItem(view['parcels'])

        m1 = self.kh.movies.first()
        m9 = m1.itsKind.newItem('m9', self.kh.itsParent)
        m9.title = 'ZZ'
        m9.director = m1.director
        self.assert_(m9.itsView is self.kh.itsView)
        self.assert_(self.kh.itsView is nv)

        kh = view.findPath('//CineGuide/KHepburn')
        self.assert_(kh.itsView is view)
        self.assert_(kh.itsView is not nv)

        kh.movies.append(m9)
        self.assert_(m9.itsView is kh.itsView)
        self.assert_(m9.itsView is view)
        self.assert_(m9.itsView is not nv)
        self.assert_(kh.movies.lastInIndex('t') is m9)

        self.assert_(view.check())
        self.assert_(nv.check())

    def testImportWithCopy(self):

        def mkdir(parent, name, child):
            if child is not None:
                return child
            return Item(name, parent, None)

        cineguidePack = os.path.join(self.testdir, 'data', 'packs',
                                     'cineguide.pack')

        view = self.rep.view

        nv.loadPack(self.chandlerPack)
        nv.loadPack(cineguidePack)
        nv.findPath('//CineGuide/KHepburn').movies.addIndex('n', 'numeric')
        nv.findPath('//CineGuide/KHepburn').movies.addIndex('t', 'attribute',
                                                            attribute='title')
        self._setCopyExport(nv['Schema'])
        self._unsetCopyExport(nv['Schema']['Core']['items'])

        view.walk(Path('//Schema/CineGuide/Kinds'), mkdir)
        view.walk(Path('//Schema/CineGuide/Attributes'), mkdir)
        view.walk(Path('//Schema/CineGuide/Types'), mkdir)
        view.commit()

        view.importItem(nv.findPath('//CineGuide/KHepburn'))

        self.assert_(view.check())
        self.assert_(nv.check())

        view.commit()

        self._reopenRepository()
        self.assert_(self.rep.view.check())


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
