"""
Basic Unit tests for Chandler repository
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import RepositoryTestCase, os, unittest

from cStringIO import StringIO
from repository.item.Item import Item
from repository.item.ItemIO import XMLItemWriter
from repository.util.SAX import XMLPrettyGenerator, XMLGenerator
from repository.item.RefCollections import RefList
from repository.schema.Kind import Kind

class ItemsTest(RepositoryTestCase.RepositoryTestCase):
    """ Test Items (attributes are tested by other tests)"""

    def testItemParentChild(self):
        """Test basic attribute functionality, focusing on parent-child relationships"""
        # Test find()
        kind = self._find('//Schema/Core/Item')
        self.assert_(kind is not None)

        # Test getItemDisplayName
        self.assertEquals(kind.getItemDisplayName(), 'Item')

        # Test itsPath
        self.assertEquals(str(kind.itsPath), '//Schema/Core/Item')

        # Test simple item construction
        item = Item('test', self.rep, kind)
        self.assert_(item is not None)
        self.assert_(item.isItemOf(kind))
        self.failIf(item.isRemote())
        self.failIf(item.hasChildren())
        self.assertEquals(item.getItemDisplayName(), 'test')
        self.assertItemPathEqual(item, '//test')
        self.assertEquals(item.refCount(), 0)
        self.assert_(item.isNew())
        self.assert_(item.isDirty())
        self.failIf(item.isDeleted())
        self.failIf(item.isStale())
        self.assertEquals(self.rep.view, item.itsView)

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
        self.rep.commit()
        roots = list(self.rep.iterRoots())
        self.assert_(item in roots)
        self.failIf(item.isDirty())

        # Test placing children
        child1 = Item('child1', item, kind)
        self.assertEquals(child1.getItemDisplayName(), 'child1')
        self.assertItemPathEqual(child1, '//test/child1')
        self.assert_(item.hasChildren())
        self.assert_(item.hasChild('child1'))
        item.placeChild(child1, None)
        self.assert_(item.hasChild('child1'))
        self.failIf(item.isNew())
        self.assert_(item.isDirty())

        child2 = Item('child2', item, kind)
        self.assertEquals(child2.getItemDisplayName(), 'child2')
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
        item = self._find('//test')
        child1 = item['child1']
        child2 = item['child2']
        self.assertIsRoot(item)
        self.assert_(item.hasChildren())
        self.assert_(item.hasChild('child1'))
        self.assert_(item.hasChild('child2'))

        # Test item renaming, itsName
        kind = self._find('//Schema/Core/Item')
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
        item = self._find('//test')
        child1 = item['child1']
        child2 = item['child2']
        child3 = child2['child3']

        self.assertEqual(child2, child3.itsParent)
        self.assertItemPathEqual(child3, '//test/child2/child3')
        self.assertIsRoot(child3.itsRoot)

        # Test item movement to root
        child3.itsParent = self.rep
        self.assertIsRoot(child3)
        self.assertItemPathEqual(child3, '//child3')
        self.assertIsRoot(child3.itsRoot)
        
        # now write what we've done and read it back
        self._reopenRepository()
        item = self._find('//test')
        child1 = item['child1']
        child2 = item['child2']
        child3 = self.rep['child3']

        self.assert_(child3 in list(self.rep.iterRoots()))
        self.assertItemPathEqual(child3, '//child3')
        self.assertIsRoot(child3.itsRoot)

    def testAttributeIteration(self):
        """Test iteration over attributes"""
        kind = self._find('//Schema/Core/Kind')
        self.assert_(kind is not None)

        # Test iterating over literal attributes
        literalAttributeNames = ['classes'] 
        for i in kind.iterAttributeValues(valuesOnly=True):
            self.failUnless(i[0] in literalAttributeNames)

        # Test hasLocalAttributeValue
        for i in literalAttributeNames:
            self.failUnless(kind.hasLocalAttributeValue(i))

        # Test iterating over reference attributes
        referenceAttributeNames = ['superKinds', 'attributes', 'clouds',
                                   'inheritedAttributes', 'kindOf', 'ofKind']
        for i in kind.iterAttributeValues(referencesOnly=True):
            self.failUnless(i[0] in referenceAttributeNames, i[0])
            self.failUnless(isinstance(i[1], RefList) or
                            isinstance(i[1], Kind))

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
