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
Unit tests for Aliases
"""

import os, unittest
from datetime import datetime

from chandlerdb.util.RepositoryTestCase import RepositoryTestCase
from chandlerdb.schema.Attribute import Attribute
from chandlerdb.util.Path import Path


class AliasTest(RepositoryTestCase):
    """ Test Aliases """

    def setUp(self):
        super(AliasTest, self).setUp()

        view = self.view

        self.kind = view.findPath(self._KIND_KIND)
        self.itemKind = view.findPath(self._ITEM_KIND)
        self.attrKind = self.itemKind.itsParent['Attribute']
        self.newKind = self.kind.newItem('newKind', view)
        self.typeKind = view.findPath('//Schema/Core/Type')

        self.aliasKind = view.findPath('//Schema/Core/Alias')

        self.alias = self.aliasKind.newItem('alias', view)

        self.dateTimeType = view.findPath('//Schema/Core/DateTime')
        self.alias.addValue('types',self.dateTimeType)

        self.intType = view.findPath('//Schema/Core/Integer')
        self.alias.addValue('types',self.intType)

        self.dateTimeString = '2004-01-08 12:34:56-0800'
        self.dateTime = datetime(2004, 1, 8, 12, 34, 56,
                                 tzinfo=view.tzinfo.getInstance('US/Pacific'))

    def testIsAlias(self):

        self.assert_(self.alias.isAlias())
        self.assert_(not self.dateTimeType.isAlias())
        self.assert_(not self.intType.isAlias())

    def testType(self):

        self.assert_(self.alias.type(1.43) is None)
        self.assert_(self.alias.type(2.4+8j) is None)
        self.assert_(self.alias.type(True) is None)
        self.assert_(self.alias.type(self.alias.itsUUID) is None)

        self.assert_(self.alias.type(12) is not None)
        self.assert_(self.alias.type(self.dateTime) is not None)

    def testRecognizes(self):

        self.assert_(not self.alias.recognizes(1.43))
        self.assert_(not self.alias.recognizes(2.4+8j))
        self.assert_(not self.alias.recognizes(True))
        self.assert_(not self.alias.recognizes(self.alias.itsUUID))

        self.assert_(self.alias.recognizes(12))
        self.assert_(self.alias.recognizes(self.dateTime))


if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
        
