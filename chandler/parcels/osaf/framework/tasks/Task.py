__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from Action import Action
from repository.item.Item import Item
import logging, time

class Task(Item):

    def Execute(self):
        #self.getLog().debug('%s / %s' % (agent.getItemDisplayName(), self.getItemDisplayName()))

        result = None

        actions = self.actions
        for action in actions:
            #self.getLog().debug('%s / %s / %s' % (agent.getItemDisplayName(), self.getItemDisplayName(), action.getItemDisplayName()))

            if action.asyncFlag:
                # agent.MakeTask(action, notification)
                pass
            elif action.wxThreadFlag or action.confirmFlag:
                actionProxy = DeferredAction(action.getUUID())

                lock = Globals.wxApplication.PostAsyncEvent(actionProxy.Execute)
                #while lock.locked():
                #    yield 'wait', 1.0
                #yield 'go', 0
                yield 'condition', lock.locked, False
                yield 'condition', None, True
                result = None
            else:
                result = action.Execute(self)

            #self.getLog().debug('%s / %s / %s' % (agent.getItemDisplayName(), self.getItemDisplayName(), 'yielding'))
            yield result
