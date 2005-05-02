"""
Unit tests for the ordering under mixinKinds of the redirectTo aspect 
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, unittest

from repository.tests.RepositoryTestCase import RepositoryTestCase

from repository.schema.Attribute import Attribute
from repository.util.Path import Path

# constants
currentPolicy = 'cascade'

class TestDeepCopyRef(RepositoryTestCase):
    """Test Deep Copy Reference problem"""
    
    # When I copy a set of cyclical references, one
    # of the links ends up pointing back at the original.

    def _createBlockAndEventKinds(self, cardinality):
        kind = self._find('//Schema/Core/Kind')
        itemKind = self._find('//Schema/Core/Item')
        attrKind = itemKind.itsParent['Attribute']

        # blockKind has a 'blocks' reference collection, and an inverse 'blockParent'
        blockKind = kind.newItem('Block', self.rep)
        blocksAttribute = Attribute('blocks', blockKind, attrKind)
        blocksAttribute.cardinality = cardinality
        blocksAttribute.copyPolicy = currentPolicy
        blocksAttribute.otherName = 'blockParent'
        blockKind.addValue('attributes',
                          blocksAttribute, alias='blocks')
        blockParentAttribute = Attribute('blockParent', blockKind, attrKind)
        blockParentAttribute.cardinality = 'single'
        blockParentAttribute.otherName = 'blocks'
        blockParentAttribute.copyPolicy = currentPolicy
        blockKind.addValue('attributes',
                           blockParentAttribute, alias='blockParent')

        # also has an "event" reference that has no inverse
        eventAttribute = Attribute('event', blockKind, attrKind)
        eventAttribute.cardinality = 'single'
        eventAttribute.copyPolicy = currentPolicy
        blockKind.addValue('attributes',
                           eventAttribute, alias='event')

        # create the event kind, which has a pointer to a Block.
        eventKind = kind.newItem('Event', self.rep)
        notifyBlock = Attribute('notify', eventKind, attrKind)
        notifyBlock.cardinality = 'single'
        notifyBlock.copyPolicy = currentPolicy
        eventKind.addValue('attributes',
                          notifyBlock, alias='notify')

        return (blockKind, eventKind)

    def testDeepCopyRef(self):
        # create some blocks to work with
        blockKind, eventKind = self._createBlockAndEventKinds('list')
        aBlock = blockKind.newItem('aBlock', self.rep)
        eggsBlock = blockKind.newItem('eggs', self.rep)
        
        # link up aBlock with eggsBlock
        aBlock.blocks = []
        aBlock.blocks.append(eggsBlock, alias='eggs')
        self.assert_(aBlock.blocks.getByAlias('eggs') is eggsBlock)
        self.assert_(aBlock is eggsBlock.blockParent)

        # create the spamEvent, which points to aBlock, 
        # and is pointed to by eggsBlock.
        spamEvent = eventKind.newItem('spamEvent', self.rep)
        spamEvent.notify = aBlock
        eggsBlock.event = spamEvent

        # Now copy the whole thing, by starting at aBlock
        # Currently using Item.copy():
        # def copy(self, name=None, parent=None, copies=None, copyPolicy=None):
        cloneBlock = aBlock.copy(name = 'cloneBlock', 
                                 parent = self.rep,
                                 copyPolicy = currentPolicy)

        # check that nothing in the copy points back to the template
        self.assert_(cloneBlock is not aBlock)
        self.assert_(cloneBlock.blocks is not aBlock.blocks)
        eggsCloneBlocks = cloneBlock.blocks
        for eggsClone in eggsCloneBlocks:
            self.assert_(eggsClone is not eggsBlock)
            print 'eggsClone.event is', eggsClone.event
            print 'eggsBlock.event is', eggsBlock.event
            self.assert_(eggsClone.event is not eggsBlock.event)
            self.assert_(eggsClone.event.notify is not eggsBlock.event.notify)

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
     unittest.main()
