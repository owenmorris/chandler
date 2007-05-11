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
"""

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
        view = self.view
        kind = view.findPath('//Schema/Core/Kind')
        itemKind = view.findPath('//Schema/Core/Item')
        attrKind = itemKind.itsParent['Attribute']

        # blockKind has a 'blocks' reference collection, and an inverse 'blockParent'
        blockKind = kind.newItem('Block', view)
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
        eventKind = kind.newItem('Event', view)
        notifyBlock = Attribute('notify', eventKind, attrKind)
        notifyBlock.cardinality = 'single'
        notifyBlock.copyPolicy = currentPolicy
        eventKind.addValue('attributes',
                          notifyBlock, alias='notify')

        return (blockKind, eventKind)

    def testDeepCopyRef(self):
        # create some blocks to work with
        view = self.view
        blockKind, eventKind = self._createBlockAndEventKinds('list')
        aBlock = blockKind.newItem('aBlock', view)
        eggsBlock = blockKind.newItem('eggs', view)
        
        # link up aBlock with eggsBlock
        aBlock.blocks = []
        aBlock.blocks.append(eggsBlock, alias='eggs')
        self.assert_(aBlock.blocks.getByAlias('eggs') is eggsBlock)
        self.assert_(aBlock is eggsBlock.blockParent)

        # create the spamEvent, which points to aBlock, 
        # and is pointed to by eggsBlock.
        spamEvent = eventKind.newItem('spamEvent', view)
        spamEvent.notify = aBlock
        eggsBlock.event = spamEvent

        # Now copy the whole thing, by starting at aBlock
        # Currently using Item.copy():
        # def copy(self, name=None, parent=None, copies=None, copyPolicy=None):
        cloneBlock = aBlock.copy(name = 'cloneBlock', 
                                 parent = view,
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
