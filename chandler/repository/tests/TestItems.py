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
from repository.item.Item import Item

class ItemsTest(unittest.TestCase):
    """ Test Items """

    def setUp(self):
        rootdir = os.environ['CHANDLERDIR']
        schemaPack = os.path.join(rootdir, 'repository', 'packs', 'schema.pack')
        self.rep = XMLRepository('ItemsUnitTest-Repository')
        self.rep.create()
        self.rep.loadPack(schemaPack)
        self.loader = DomainSchemaLoader(self.rep)

    def testCreateItem(self):
        kind = self.rep.find('//Schema/Core/Kind')
        self.assert_(kind is not None)
        self.assertEquals(repr(kind.getItemPath()),'//Schema/Core/Kind')

        item = Item('test', self.rep, kind)
        self.rep.commit()
#        self.rep.close()
#        self.rep.open()
        i = self.rep.getRoots()
        self.assert_(item is not None)
        self.assertEqual(i[0], item)

#        print i[0]
#        print item
#        print item.getItemPath()

        kind = self.rep.find('//Schema/Core/Kind')
#        print kind
        self.assert_(not item.hasChildren())

        child1 = Item('child1', item, kind)
        item.placeChild(child1, None)
        child2 = Item('child2', item, kind)
        item.placeChild(child2, child1)

        self.assert_(item.hasChildren())
        self.assertEqual(item.getItemChild('child1'), child1)
        self.assertEqual(item.getItemChild('child2'), child2)
        self.assertEqual(child1.getItemParent(), item)
        self.assertEqual(child2.getItemParent(), item)

        iter = item.iterChildren()
        self.assertEqual(item.getItemChild('child1'), iter.next())
        self.assertEqual(item.getItemChild('child2'), iter.next())
#TODO        self.failUnlessRaises(StopIteration, iter.next())

        child3 = Item('busted', item, kind)
        self.assertEqual(child3.getItemName(), "busted")

        child3.rename("child3")
        self.assertEqual(child3.getItemName(), "child3")

        item.placeChild(child3, child1)
        iter = item.iterChildren()
        iter.next()
        self.assertEqual(child3, iter.next())

        oldParent = child3.getItemParent()
        child3.move(child3.getItemParent())
        self.assertEqual(oldParent,child3.getItemParent())

        child3.move(child2)
        self.assertEqual(child2,child3.getItemParent())

        child3.move(self.rep)
        print self.rep.getRoots()

    def tearDown(self):
        self.rep.close()
        self.rep.delete()
        pass

if __name__ == "__main__":
    unittest.main()
