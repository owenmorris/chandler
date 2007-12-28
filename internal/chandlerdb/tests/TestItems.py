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
from cStringIO import StringIO

from chandlerdb.util.RepositoryTestCase import RepositoryTestCase
from chandlerdb.item.Item import Item
from chandlerdb.item.ItemIO import XMLItemWriter
from chandlerdb.util.SAX import XMLPrettyGenerator, XMLGenerator
from chandlerdb.item.RefCollections import RefList
from chandlerdb.schema.Kind import Kind

class ItemsTest(RepositoryTestCase):
    """ Test Items (attributes are tested by other tests)"""

    def testItemParentChild(self):
        """Test basic attribute functionality, focusing on parent-child relationships"""
        view = self.view
        # Test find()
        kind = view.findPath('//Schema/Core/Item')
        self.assert_(kind is not None)

        # Test itsName
        self.assertEquals(kind.itsName, 'Item')

        # Test itsPath
        self.assertEquals(str(kind.itsPath), '//Schema/Core/Item')

        # Test simple item construction
        item = Item('test', view, kind)
        self.assert_(item is not None)
        self.assert_(item.isItemOf(kind))
        self.failIf(item.isRemote())
        self.failIf(item.hasChildren())
        self.assertEquals(item.itsName, 'test')
        self.assertItemPathEqual(item, '//test')
        self.assertEquals(item.refCount(), 0)
        self.assert_(item.isNew())
        self.assert_(item.isDirty())
        self.failIf(item.isDeleted())
        self.failIf(item.isStale())
        self.assertEquals(view, item.itsView)

#TODO test toXML
        out = StringIO()
        generator = XMLPrettyGenerator(XMLGenerator(out))
        itemWriter = XMLItemWriter(generator)
        generator.startDocument()
        itemWriter.writeItem(item, item.getVersion())
        generator.endDocument()
        xml = out.getvalue()
        out.close()

        self.failIf(xml is None)

        # Test to see that item became a respository root
        view.commit()
        roots = list(view.iterRoots())
        self.assert_(item in roots)
        self.failIf(item.isDirty())

        # Test placing children
        child1 = Item('child1', item, kind)
        self.assertEquals(child1.itsName, 'child1')
        self.assertItemPathEqual(child1, '//test/child1')
        self.assert_(item.hasChildren())
        self.assert_(item.hasChild('child1'))
        item.placeChild(child1, None)
        self.assert_(item.hasChild('child1'))
        self.failIf(item.isNew())
        self.assert_(item.isDirty())

        child2 = Item('child2', item, kind)
        self.assertEquals(child2.itsName, 'child2')
        self.assertItemPathEqual(child2, '//test/child2')
        self.assert_(item.hasChildren())
        self.assert_(item.hasChild('child1'))
        self.assert_(item.hasChild('child2'))

        item.placeChild(child2, child1)
        self.assert_(item.hasChild('child2'))
        self.failIf(item.isNew())
        self.assert_(item.isDirty())

        self.assertEqual(item.getItemChild('child1'), child1)
        self.assertEqual(item.getItemChild('child2'), child2)
        self.assertEqual(child1.itsParent, item)
        self.assertEqual(child2.itsParent, item)

        # Test iterating over child items
        iter = item.iterChildren()
        self.assertEqual(item.getItemChild('child1'), iter.next())
        self.assertEqual(item.getItemChild('child2'), iter.next())

#        self.failUnlessRaises(StopIteration, lambda: iter.next())

        # now write what we've done and read it back
        self._reopenRepository()
        view = self.view
        item = view.findPath('//test')
        child1 = item['child1']
        child2 = item['child2']
        self.assertIsRoot(item)
        self.assert_(item.hasChildren())
        self.assert_(item.hasChild('child1'))
        self.assert_(item.hasChild('child2'))

        # Test item renaming, itsName
        kind = view.findPath('//Schema/Core/Item')
        child3 = Item('busted', item, kind)
        self.assertEqual(child3.itsName, 'busted')
        child3.itsName = 'busted'
        self.assertEqual(child3.itsName, 'busted')
        child3.itsName = 'child3'
        self.assertEqual(child3.itsName, 'child3')

        # Test that placing affects iteration order
        item.placeChild(child3, child1)
        iter = item.iterChildren()
        iter.next()
        self.assertEqual(child3, iter.next())
        self.assertItemPathEqual(child3, '//test/child3')
        self.assertIsRoot(child3.itsRoot)

        # Test item movement to same parent
        oldParent = child3.itsParent
        child3.itsParent = child3.itsParent
        self.assertEqual(oldParent, child3.itsParent)
        self.assertItemPathEqual(child3, '//test/child3')
        self.assertIsRoot(child3.itsRoot)
        
        # Test item movement to leaf item
        child3.itsParent = child2
        self.assertEqual(child2, child3.itsParent)
        self.assertItemPathEqual(child3, '//test/child2/child3')
        self.assertIsRoot(child3.itsRoot)

        # now write what we've done and read it back
        self._reopenRepository()
        view = self.view
        item = view.findPath('//test')
        child1 = item['child1']
        child2 = item['child2']
        child3 = child2['child3']

        self.assertEqual(child2, child3.itsParent)
        self.assertItemPathEqual(child3, '//test/child2/child3')
        self.assertIsRoot(child3.itsRoot)

        # Test item movement to root
        child3.itsParent = view
        self.assertIsRoot(child3)
        self.assertItemPathEqual(child3, '//child3')
        self.assertIsRoot(child3.itsRoot)
        
        # now write what we've done and read it back
        self._reopenRepository()
        view = self.view
        item = view.findPath('//test')
        child1 = item['child1']
        child2 = item['child2']
        child3 = view['child3']

        self.assert_(child3 in list(view.iterRoots()))
        self.assertItemPathEqual(child3, '//child3')
        self.assertIsRoot(child3.itsRoot)

    def testAttributeIteration(self):
        """Test iteration over attributes"""
        kind = self.view.findPath('//Schema/Core/Kind')
        self.assert_(kind is not None)

        # Test iterating over literal attributes
        literalAttributeNames = ['classes'] 
        for i in kind.iterAttributeValues(valuesOnly=True):
            self.failUnless(i[0] in literalAttributeNames)

        # Test hasLocalAttributeValue
        for i in literalAttributeNames:
            self.failUnless(kind.hasLocalAttributeValue(i))

        # Test hasTrueAttributeValue
        for i in literalAttributeNames:
            self.failUnless(kind.hasTrueAttributeValue(i), i)

        # Test iterating over reference attributes
        referenceAttributeNames = ['superKinds', 'attributes',
                                   'subKinds', 'extent']
        for i in kind.iterAttributeValues(referencesOnly=True):
            self.failUnless(i[0] in referenceAttributeNames, i[0])
            self.failUnless(isinstance(i[1], RefList) or
                            isinstance(i[1], Item), i[1])

        # Test hasTrueAttributeValue
        for i in referenceAttributeNames:
            self.failUnless(kind.hasTrueAttributeValue(i))


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
