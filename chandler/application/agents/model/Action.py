__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import os.path


from model.item.Item import Item

"""
The Action Class is a persistent object containing information about a particular action that can be
executed by an agent, either explictly at the user's request, or automatically, as specified by
a conditional instruction.
"""
class ActionFactory:
    def __init__(self, repository):
        self._container = repository.find("//Agents")
        self._kind = repository.find("//Schema/AgentsSchema/Action")
        self.repository = repository
        
    def NewItem(self, name):
        item = Action(name, self._container, self._kind)
                             
        return item

class Action(Item):

    def __init__(self, name, parent, kind, **_kwds):
        super(Action, self).__init__(name, parent, kind, **_kwds)

    def IsAsynchronous(self):
        """
          return True if the action should be executed asynchronously
        """
        if self.hasAttributeValue('asyncFlag'):
            return self.asyncFlag
        
        return False
    
    def UseWxThread(self):
        """
           by default, actions run on the agent's thread, but they can be deferred to run synchronously
           with the wxWindows.  This means they can safely make wxWindows calls, but they shouldn't be
           time consuming
        """
        if self.hasAttributeValue('wxThreadFlag'):
            return self.wxThreadFlag
        
        return False
    
    def Execute(self, agent, data):
        '''
          perform an action according to the action type.
          FIXME:  right now we run the scripts in the current context, so they can access the parameters.
          Probably, we should construct and pass in a context to protect us from side-effects
        '''
        result = None
        script = self.actionScript
        actionType = self.actionType
                
        # set up an optional value to be used by the script
        if self.hasAttributeValue('actionValue'):
            actionValue = self.actionValue
        else:
            actionValue = None
                
        # execute the script according to the action type
        try:
            if actionType == 'script': 
                scriptPath = os.path.join("application", "agents", "scripts", script)
                execfile(scriptPath)
            elif actionType == 'expression':
                result = eval(script)
            elif actionType == 'inline':
                exec script
            else:
                # FIXME: should probably throw an exception here
                print "unknown action type", agent.GetName(), self.GetName(), self.actionType
        except:
            print "failed to execute action", self.GetName()
        
        return result
    
    def IsCompleted(self):
        return False
    
    def GetCompletionPercentage(self):
        '''
           get the completion percentage of asynchronous actions
        '''
        return 0

    
"""
The DeferredAction class is a simple wrapper for an action that allows an actionto be invoked without 
passing any parameters.
"""
class DeferredAction:
    def __init__(self, action, agent, actionData):
        self.action = action
        self.agent = agent
        self.actionData = actionData
        
    def Execute(self):
        result = self.action.Execute(self.agent, self.actionData)
        
        
