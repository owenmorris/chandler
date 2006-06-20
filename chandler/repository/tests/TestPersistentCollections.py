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
Unit tests for persistent collections
"""

import unittest, os

from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.item.PersistentCollections import \
     PersistentList, PersistentDict, PersistentTuple, PersistentSet


class TestPersistentCollections(RepositoryTestCase):
    """
    Test Persistent Collections
    """

    def setUp(self):

        super(TestPersistentCollections, self).setUp()
        view = self.rep.view

        collectionsPack = os.path.join(self.testdir, 'data', 'packs',
                                       'collections.pack')
        view.loadPack(collectionsPack)
        self.kind = view.findPath('//Schema/Collections/Kinds/Collections')
        self.root = view.findPath('//Collections')
        view.commit()

    def testXML(self):

        view = self.rep.view
        strings = view.findPath('//Collections/Strings')

        value = strings.listOfStrings
        self.assert_(len(value) == 2)
        self.assert_(value == ['a string in a list',
                               'another string in a list'])

        value = strings.dictOfStrings
        self.assert_(len(value) == 2)
        self.assert_(value['a'] == 'a string in a dict')
        self.assert_(value['another'] == 'another string in a dict')
        
        value = strings.setOfStrings
        self.assert_(len(value) == 2)
        self.assert_('a string in a set' in value)
        self.assert_('another string in a set' in value)

        value = strings.anything[0]
        self.assert_(value[0] == 'a string')
        self.assert_(isinstance(value[1], list))
        self.assert_(value[1][1] == 2.5)
        self.assert_(isinstance(value[2], dict))
        self.assert_(value[2]['one'] == 2.5)
        self.assert_(isinstance(value[3], set))
        self.assert_(2.5 in value[3])
        
    def _testList(self, item, values):

        self.assert_(item.list is not values)
        self.assert_(item.list != values, "items are stored as SingleRefs")
        self.assert_(len(item.list) == len(values))
        self.assert_(type(item.list) is PersistentList)

        for v in item.list:
            if not isinstance(v, list):
                self.assert_(v in values, v)
            else:
                self.assert_(type(v) is not list)
                self.assert_(type(v) is PersistentList)

        self.assert_(item in item.list)
        self.assert_(item in item.list[5])
        self.assert_(4 in item.list)
        self.assert_(5 in item.list[5])
        self.assert_(item.list.index(item) == 4)
        self.assert_(item.list.count(item) == 1)

        view = self.rep.view
        view.check()

    def testList(self):

        item = self.kind.newItem('foo', self.root);
        values = [1, 2, 3, 4, item, [item, 5]]
        item.list = values
        self._testList(item, values)

    def testListWithCommit(self):

        item = self.kind.newItem('foo', self.root);
        values = [1, 2, 3, 4, item, [item, 5]]
        item.list = values
        self._testList(item, values)

        self._reopenRepository()
        view = self.rep.view
        item = view.findPath('//Collections/foo')
        values = [1, 2, 3, 4, item, [item, 5]]
        self._testList(item, values)

    def _testDictionary(self, item, values):

        self.assert_(item.dictionary is not values)
        self.assert_(item.dictionary != values,
                     "items are stored as SingleRefs")
        self.assert_(len(item.dictionary) == len(values))
        self.assert_(type(item.dictionary) is PersistentDict)

        for k, v in item.dictionary.iteritems():
            if not isinstance(v, list):
                self.assert_(k in values, k)
            else:
                self.assert_(type(v) is not list)
                self.assert_(type(v) is PersistentList)

        self.assert_(item in item.dictionary.values())
        self.assert_(item in item.dictionary['list'])
        self.assert_('b' in item.dictionary)
        self.assert_(2 in item.dictionary['list'])

        view = self.rep.view
        view.check()

    def testDictionary(self):

        item = self.kind.newItem('foo', self.root);
        values = {'a': 1, 'b': 2, 'c': 3, 'i': item, 'list': [item, 2]}
        item.dictionary = values
        self._testDictionary(item, values)

    def testDictionaryWithCommit(self):

        item = self.kind.newItem('foo', self.root);
        values = {'a': 1, 'b': 2, 'c': 3, 'i': item, 'list': [item, 2]}
        item.dictionary = values
        self._testDictionary(item, values)

        self._reopenRepository()
        view = self.rep.view
        item = view.findPath('//Collections/foo')
        values = {'a': 1, 'b': 2, 'c': 3, 'i': item, 'list': [item, 2]}
        self._testDictionary(item, values)

    def _testTuple(self, item, values):

        self.assert_(item.tuple is not values)
        self.assert_(item.tuple != values, "items are stored as SingleRefs")
        self.assert_(len(item.tuple) == len(values))

        for v in item.tuple:
            if not isinstance(v, tuple):
                self.assert_(v in values, v)
            else:
                self.assert_(type(v) is not tuple)
                self.assert_(type(v) is PersistentTuple)

        self.assert_(item in item.tuple)
        self.assert_(item in item.tuple[5])
        self.assert_(4 in item.tuple)
        self.assert_(5 in item.tuple[5])

        view = self.rep.view
        view.check()

    def testTuple(self):

        item = self.kind.newItem('foo', self.root);
        values = (1, 2, 3, 4, item, (item, 5))
        item.tuple = values
        self._testTuple(item, values)

    def testTupleWithCommit(self):

        item = self.kind.newItem('foo', self.root);
        values = (1, 2, 3, 4, item, (item, 5))
        item.tuple = values
        self._testTuple(item, values)

        self._reopenRepository()
        view = self.rep.view
        item = view.findPath('//Collections/foo')
        values = (1, 2, 3, 4, item, (item, 5))
        self._testTuple(item, values)

    def _testSet(self, item, values):

        self.assert_(item.set is not values)
        self.assert_(item.set != values, "items are stored as SingleRefs")
        self.assert_(len(item.set) == len(values))

        for v in item.set:
            if not isinstance(v, tuple):
                self.assert_(v in values, v)
            else:
                self.assert_(type(v) is not tuple)
                self.assert_(type(v) is PersistentTuple)

        self.assert_(item in item.set)
        self.assert_(4 in item.set)

        view = self.rep.view
        view.check()

    def testSet(self):

        item = self.kind.newItem('foo', self.root);
        values = set((1, 2, 3, 4, item, (item, 5)))
        item.set = values
        self._testSet(item, values)

    def testSetWithCommit(self):

        item = self.kind.newItem('foo', self.root);
        values = set((1, 2, 3, 4, item, (item, 5)))
        item.set = values
        self._testSet(item, values)

        self._reopenRepository()
        view = self.rep.view
        item = view.findPath('//Collections/foo')
        values = set((1, 2, 3, 4, item, (item, 5)))
        self._testSet(item, values)
       
                  
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
     unittest.main()
