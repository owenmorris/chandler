"""
Unit tests for the ordering under mixinKinds of the redirectTo aspect 
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import RepositoryTestCase, os, unittest
from repository.persistence.XMLRefDict import XMLRefDict

from repository.schema.Attribute import Attribute
from repository.util.Path import Path


class RefDictionaryAliasTest(RepositoryTestCase.RepositoryTestCase):
    """Test Ref Dictionary Alias manipulation"""
    
    # When I use the alias feature to add items to a ref dictionary
    # and then rebuild the ref dictionary, subsequent searches
    # return True instead of the Item.

    def _createBlockKind(self, cardinality):
        kind = self._find('//Schema/Core/Kind')
        itemKind = self._find('//Schema/Core/Item')
        attrKind = itemKind.itsParent['Attribute']

        # blockKind has a 'blocks' reference collection, and an inverse 'blockParent'
        blockKind = kind.newItem('Block', self.rep)
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

    def NewXMLRefDict(self, view, item, name, otherName, readOnly):
        # Create an XMLRefDict to initialize the attribute.
        # IS THERE A BETTER WAY TO DO THIS?
        return XMLRefDict(view, item, name, otherName, readOnly)

    def reloadRepositoryItems (self, itemList):
        # remember the set of items given, reload the repository,
        #  and bring the items back to life.
        itemUUIDs = []
        for item in itemList:
            itemUUIDs.append(item.itsUUID)

        self.rep.commit()
        self._reopenRepository()
        
        # reincarnate the items
        newList = []
        for uuid in itemUUIDs:
            newList.append(self.rep.find(uuid))
        return newList
        
    def testRefDictAlias(self):
        # create some blocks to work with
        blockKind = self._createBlockKind('list')
        aBlock = blockKind.newItem('aBlock', self.rep)
        eggsBlock = blockKind.newItem('eggs', self.rep)
        
        # link them up using alias
        aBlock.blocks = self.NewXMLRefDict(self.rep.view, aBlock, 'blocks', 'blockParent', False)
        aBlock.blocks.append(eggsBlock, alias='eggs')
        self.assert_(aBlock.blocks.getByAlias('eggs') is eggsBlock)
        self.assert_(aBlock is eggsBlock.blockParent)

        # change this to True and we fail, unless the bug is fixed
        testWithReload = True

        # reload the repository
        if testWithReload:
            aBlock, eggsBlock = self.reloadRepositoryItems((aBlock, eggsBlock))

        self.assert_(aBlock.blocks.getByAlias('eggs') is eggsBlock)
        self.assert_(aBlock is eggsBlock.blockParent)

        # now remove them all, and see that they are gone
        aBlock.blocks.clear()
        mightBeEggs = aBlock.blocks.getByAlias('eggs')
        print "might-be-eggs is %s, type %s" % (mightBeEggs, type(mightBeEggs))
        # OOPS!  When we reload the repository, we end up
        #  returning True instead of the Item or None!
        self.assert_(aBlock.blocks.getByAlias('eggs') is not True)

                  
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
     unittest.main()
