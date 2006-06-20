#   Copyright (c) 2004-2006 Open Source Applications Foundation
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
Unit tests for the ordering under mixinKinds of the redirectTo aspect 
"""

import RepositoryTestCase, os, unittest

from repository.schema.Attribute import Attribute
from repository.util.Path import Path


class RefListAliasTest(RepositoryTestCase.RepositoryTestCase):
    """Test Ref Dictionary Alias manipulation"""
    
    # When I use the alias feature to add items to a ref dictionary
    # and then rebuild the ref dictionary, subsequent searches
    # return True instead of the Item.

    def _createBlockKind(self, cardinality):
        view = self.rep.view
        kind = self._find('//Schema/Core/Kind')
        itemKind = self._find('//Schema/Core/Item')
        attrKind = itemKind.itsParent['Attribute']

        # blockKind has a 'blocks' reference collection, and an inverse 'blockParent'
        blockKind = kind.newItem('Block', view)
        blocksAttribute = Attribute('blocks', blockKind, attrKind)
        blocksAttribute.cardinality = cardinality
        blocksAttribute.otherName = 'blockParent'
        blockKind.addValue('attributes',
                           blocksAttribute, alias='blocks')
        blockParentAttribute = Attribute('blockParent', blockKind, attrKind)
        blockParentAttribute.cardinality = 'single'
        blockParentAttribute.otherName = 'blocks'
        blockKind.addValue('attributes',
                           blockParentAttribute, alias='blockParent')
        return blockKind

    def reloadRepositoryItems (self, itemList):
        # remember the set of items given, reload the repository,
        #  and bring the items back to life.
        itemUUIDs = []
        for item in itemList:
            itemUUIDs.append(item.itsUUID)

        self.rep.view.commit()
        self._reopenRepository()
        view = self.rep.view
        
        # reincarnate the items
        newList = []
        for uuid in itemUUIDs:
            newList.append(view.find(uuid))
        return newList
        
    def testRefListAlias(self):
        view = self.rep.view
        # create some blocks to work with
        blockKind = self._createBlockKind('list')
        aBlock = blockKind.newItem('aBlock', view)
        eggsBlock = blockKind.newItem('eggs', view)
        
        # link them up using alias
        aBlock.blocks = []
        aBlock.blocks.append(eggsBlock, alias='eggs')
        self.assert_(aBlock.blocks.getByAlias('eggs') is eggsBlock)
        self.assert_(aBlock is eggsBlock.blockParent)

        # reload the repository
        aBlock, eggsBlock = self.reloadRepositoryItems((aBlock, eggsBlock))

        self.assert_(aBlock.blocks.getByAlias('eggs') is eggsBlock)
        self.assert_(aBlock is eggsBlock.blockParent)

        # now remove them all, and see that they are gone
        aBlock.blocks.clear()
        mightBeEggs = aBlock.blocks.getByAlias('eggs')
        # OOPS!  When we reload the repository, we end up
        #  returning True instead of the Item or None!
        self.assert_(aBlock.blocks.getByAlias('eggs') is not True)

                  
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
     unittest.main()
