"""
Unit tests for kinds
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import RepositoryTestCase, os, unittest

from repository.item.Item import Item
from repository.schema.Attribute import Attribute
from repository.schema.Kind import Kind

class KindTest(RepositoryTestCase.RepositoryTestCase):
    """ Test Kinds  """

    def setUp(self):
        super(KindTest, self).setUp()

        self.kind = self._find("//Schema/Core/Kind")
        self.itemKind = self._find("//Schema/Core/Item")
        self.attrKind = self.itemKind.itsParent['Attribute']

        self.kind1 = self.kind.newItem('kind1',self.rep)
        self.kind1Attr1 = Attribute('k1a1', self.rep, self.attrKind)
        self.kind1Attr1.cardinality = 'list'
        self.kind1Attr1.otherName = 'owner'
        self.kind1.addValue('attributes', self.kind1Attr1, alias='k1a1')

        kind1Attr1Bad = Attribute('k1a1bad', self.kind1, self.attrKind)
        kind1Attr1Bad.cardinality = 'list'
        kind1Attr1Bad.otherName = 'owner'
        self.kind1.addValue('attribute', kind1Attr1Bad, alias='k1a1bad')
        
        self.kind2 = self.kind.newItem('kind2', self.kind1)

    
    def testBasic(self):
        """ Test basic Kind methods """
        kindClass = self.kind.getItemClass()
        itemKindClass = self.itemKind.getItemClass()
        self.assertEquals(kindClass.__name__,"Kind")
        self.assertEquals(itemKindClass.__name__,"Item")

    def testResolve(self):
        """ Test child attribute and aliased attribute resolution """
        # resolve a non-child, non aliased attribute
        self.assert_(self.kind1.resolve('attributes') is None)
        # resolve a non existent attribute
        self.assert_(self.kind1.resolve('bogus') is None)

        # resolve a child non attribute
        self.assertEquals(self.kind1.resolve('kind2'), self.kind2.itsUUID)

        # resolve an attribute (alias)
        self.assert_(self.kind1.resolve('k1a1') is self.kind1Attr1.itsUUID)

    def testGetAttribute(self):
        """ Test getAttribute and has Attribute """
        
        # an attribute that is a child but not on the atts list should
        # not be returned
        self.assert_(self.kind1.getAttribute('k1a1bad') is None)
        self.assert_(not self.kind1.hasAttribute('k1a1bad'))

        # basic getAttribute and hasAttribute
        self.assert_(self.kind1.hasAttribute('k1a1'))
        self.assert_(self.kind1.getAttribute('k1a1') is self.kind1Attr1)

        # add an inherited attribute, kind2 inherits from kind1
        self.kind2.addValue('superKinds', self.kind1)

        # retreive an inherited attribute
        self.assert_(self.kind2.hasAttribute('k1a1'))
        self.assert_(self.kind2.getAttribute('k1a1') is not None)

    def testIsAlias(self):
        """ A kind is not an alias """
        self.assert_(not self.kind1.isAlias())
    
    def testIsSubKindOf(self):
        """ Test IsSubKindOf on multiple super kinds """
        # make kind2 a subkind of kind1
        self.kind2.addValue('superKinds', self.kind1)
        self.assert_(self.kind2.isSubKindOf(self.itemKind))
        self.assert_(self.kind2.isSubKindOf(self.kind1))


    def testToXML(self):
        """ Non  realistic test of to XML """
        xml = self.kind.toXML()
        self.failIf(xml is None)
        
    def testRekinding(self):
        # rekind an item
        # re super kind a kind
        # we do this in TestReferenceAttributes.py but should do it for real here
        #@@@TODO we need to define what it means to rekind first

#         self.kind2.addValue('superKinds', self.kind1)

#         item = self.kind2.newItem('item', self.rep)
#         item.setValue('k1a1','value')
#         self.assertEquals(len(item.k1a1),1)

#         newKind = self.kind.newItem('newKind', self.rep)
#         item.itsKind = newKind
#         self.assert_('value' in item.k1a1)

#         newSuperKind = self.kind.newItem('newSuperKind', self.rep)

        pass
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
        
