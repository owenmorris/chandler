"""
Unit tests for Aliases
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import RepositoryTestCase, os, unittest

import repository.schema.Types
import repository.item.PersistentCollections

from datetime import datetime
from PyICU import ICUtzinfo

from repository.schema.Attribute import Attribute
from repository.util.Path import Path
from repository.util.SingleRef import SingleRef


class AliasTest(RepositoryTestCase.RepositoryTestCase):
    """ Test Aliases """

    def setUp(self):
        super(AliasTest, self).setUp()

        self.kind = self._find(self._KIND_KIND)
        self.itemKind = self._find(self._ITEM_KIND)
        self.attrKind = self.itemKind.itsParent['Attribute']
        self.newKind = self.kind.newItem('newKind', self.rep)
        self.typeKind = self._find('//Schema/Core/Type')

        self.aliasKind = self._find('//Schema/Core/Alias')

        self.alias = self.aliasKind.newItem('alias', self.rep)

        self.dateTimeType = self._find('//Schema/Core/DateTime')
        self.alias.addValue('types',self.dateTimeType)

        self.intType = self._find('//Schema/Core/Integer')
        self.alias.addValue('types',self.intType)

        self.dateTimeString = '2004-01-08 12:34:56-0800'
        self.dateTime = datetime(2004, 1, 8, 12, 34, 56,
                                 tzinfo=ICUtzinfo.getInstance('US/Pacific'))

    def testIsAlias(self):
        self.assert_(self.alias.isAlias())
        self.assert_(not self.dateTimeType.isAlias())
        self.assert_(not self.intType.isAlias())

    def testType(self):

        self.assert_(self.alias.type(1.43) is None)
        self.assert_(self.alias.type(2.4+8j) is None)
        #self.assert_(self.alias.type(True) is None) bool is subclass of int
        self.assert_(self.alias.type(self.alias.itsUUID) is None)

        self.assert_(self.alias.type(12) is not None)
        self.assert_(self.alias.type(self.dateTime) is not None)

    def testRecognizes(self):

        self.assert_(not self.alias.recognizes(1.43))
        self.assert_(not self.alias.recognizes(2.4+8j))
        # self.assert_(not self.alias.recognizes(True)) bool is subclass of int
        self.assert_(not self.alias.recognizes(self.alias.itsUUID))

        self.assert_(self.alias.recognizes(12))
        self.assert_(self.alias.recognizes(self.dateTime))
        pass

    def testAliases(self):
        """
        What does this test case actually do ??
        """

#        newKind = self.kind.newItem('newKind', self.rep)
#        print k
#        for a in self.alias.iterAttributeValues():
#            print a
#            a1 =  self.kind.getAttribute(a[0])
#            print a1
#            if a1.hasLocalAttributeValue('types'):
#                print a1.types


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
        
