"""
Unit tests for the ordering under mixinKinds of the redirectTo aspect 
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

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

        kind = self._find('//Schema/Core/Kind')
        itemKind = self._find('//Schema/Core/Item')
        attrKind = itemKind.itsParent['Attribute']

        # noteKind has a 'creator' string, and a 'who' attribute to 
        #   redirectTo 'creator'
        noteKind = kind.newItem('Note', self.rep)
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
        taskMixin = kind.newItem('TaskMixin', self.rep)
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
        taskKind = kind.newItem('Task', self.rep)
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

        self.rep.commit()
        self._reopenRepository()
        
        # reincarnate the items
        newList = []
        for uuid in itemUUIDs:
            newList.append(self.rep.find(uuid))
        return newList
        
    def testRedirectTo(self):

        noteKind = self.rep.find(self.noteKind)
        taskMixin = self.rep.find(self.taskMixin)
        taskKind = self.rep.find(self.taskKind)

        aNote = noteKind.newItem('aNote', self.rep)
        aTaskMixin = taskMixin.newItem('aTaskMixin', self.rep)
        aTask = taskKind.newItem('aTask', self.rep)

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
        self.rep.commit()
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

        taskKind = self.rep.find(self.taskKind)

        aTask = self._find('//aTask')
        if aTask is None:
            aTask = taskKind.newItem('aTask', self.rep)

        redirectTo = aTask.getAttributeAspect('who', 'redirectTo')
        print "who points to", aTask.getAttributeAspect('who', 'redirectTo')
        self.assert_(redirectTo == 'creator', redirectTo)

        # place the last superKind first
        taskKind.superKinds.placeItem(taskKind.superKinds.last(), None)
        # flush kind caches after re-arranging superKinds
        taskKind.flushCaches('superKinds')

        redirectTo = aTask.getAttributeAspect('who', 'redirectTo')
        print "who points to", aTask.getAttributeAspect('who', 'redirectTo')
        self.assert_(redirectTo == 'participant', redirectTo)
        
                  
if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
     unittest.main()
