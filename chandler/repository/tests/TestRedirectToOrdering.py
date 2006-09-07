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

class RedirectAttributeOrderingTest(RepositoryTestCase.RepositoryTestCase):
    """Test Redirect Attribute Ordering"""
    
    # When we have multiple superKinds, and there is a conflict between
    # more than one attribute with redirectTo aspect, the ordering
    # changes when reloading the repository.

    def setUp(self):

        super(RedirectAttributeOrderingTest, self).setUp()

        view = self.rep.view
        kind = self._find('//Schema/Core/Kind')
        itemKind = self._find('//Schema/Core/Item')
        attrKind = itemKind.itsParent['Attribute']

        # noteKind has a 'creator' string, and a 'who' attribute to 
        #   redirectTo 'creator'
        noteKind = kind.newItem('Note', view)
        creatorAttribute = Attribute('creator', noteKind, attrKind)
        creatorAttribute.cardinality = 'single'
        noteKind.addValue('attributes',
                          creatorAttribute, alias='creator')
        whoAttribute = Attribute('who', noteKind, attrKind)
        whoAttribute.cardinality = 'single'
        whoAttribute.redirectTo = 'creator'
        noteKind.addValue('attributes',
                          whoAttribute, alias='who')

        # taskMixin has a 'participant' string, and a 'who' attribute to 
        #   redirectTo 'participant'
        taskMixin = kind.newItem('TaskMixin', view)
        participantAttribute = Attribute('participant', taskMixin, attrKind)
        participantAttribute.cardinality = 'single'
        taskMixin.addValue('attributes',
                           participantAttribute, alias='participant')
        whoAttribute = Attribute('who', taskMixin, attrKind)
        whoAttribute.cardinality = 'single'
        whoAttribute.redirectTo = 'participant'
        taskMixin.addValue('attributes',
                           whoAttribute, alias='who')

        # taskKind is a Kind with superkinds noteKind and taskMixin
        taskKind = kind.newItem('Task', view)
        taskKind.addValue('superKinds', noteKind)
        taskKind.addValue('superKinds', taskMixin)

        self.noteKind = noteKind.itsUUID
        self.taskMixin = taskMixin.itsUUID
        self.taskKind = taskKind.itsUUID

    def reloadRepositoryItems (self, itemList):
        # remember the set of items given, reload the repository,
        #  and bring the items back to life.
        itemUUIDs = []
        for item in itemList:
            itemUUIDs.append(item.itsUUID)

        view = self.rep.view
        view.commit()
        self._reopenRepository()
        view = self.rep.view
        
        # reincarnate the items
        newList = []
        for uuid in itemUUIDs:
            newList.append(view.find(uuid))
        return newList
        
    def testRedirectTo(self):

        view = self.rep.view
        noteKind = view.find(self.noteKind)
        taskMixin = view.find(self.taskMixin)
        taskKind = view.find(self.taskKind)

        aNote = noteKind.newItem('aNote', view)
        aTaskMixin = taskMixin.newItem('aTaskMixin', view)
        aTask = taskKind.newItem('aTask', view)

        noteWho = 'whoWroteTheNote'
        aNote.who = noteWho
        taskMixinWho = 'whoWroteTheTaskMixin'
        aTaskMixin.who = taskMixinWho
        taskWho = 'whoWroteTheTask'
        aTask.who = taskWho

        print "checking attributes"
        self.assert_(aNote.who == noteWho)
        self.assert_(aNote.creator == noteWho)
        self.assert_(aTaskMixin.who == taskMixinWho)
        self.assert_(aTaskMixin.participant == taskMixinWho)
        self.assert_(aTask.who == taskWho)
        self.assert_(aTask.creator == taskWho)
        view.commit()
        print "Task.who points to " + aTask.getAttributeAspect('who', 'redirectTo')

        items = (aNote, aTaskMixin, aTask)
        aNote, aTaskMixin, aTask = self.reloadRepositoryItems(items)

        self.assert_(aNote.who == noteWho)
        self.assert_(aNote.creator == noteWho)
        self.assert_(aTaskMixin.who == taskMixinWho)
        self.assert_(aTaskMixin.participant == taskMixinWho)

        # test that the creator value is still there
        self.assert_(aTask.creator == taskWho)
        print "Task.who points to " + aTask.getAttributeAspect('who', 'redirectTo')
        self.assert_(aTask.who == taskWho)
        
    def testRearrange(self):

        view = self.rep.view
        taskKind = view.find(self.taskKind)

        aTask = self._find('//aTask')
        if aTask is None:
            aTask = taskKind.newItem('aTask', view)

        redirectTo = aTask.getAttributeAspect('who', 'redirectTo')
        print "who points to", aTask.getAttributeAspect('who', 'redirectTo')
        self.assert_(redirectTo == 'creator', redirectTo)

        # place the last superKind first
        taskKind.superKinds.placeItem(taskKind.superKinds.last(), None)

        redirectTo = aTask.getAttributeAspect('who', 'redirectTo')
        print "who points to", aTask.getAttributeAspect('who', 'redirectTo')
        self.assert_(redirectTo == 'participant', redirectTo)
        
                  
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
     unittest.main()
