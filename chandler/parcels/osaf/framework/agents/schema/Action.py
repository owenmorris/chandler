__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import os.path
import sys

from wxPython.wx import *


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

    def NeedsConfirmation(self):
        """
          if the confirmFlag is True, we require that the user confirms the action
        """
        if self.hasAttributeValue('confirmFlag'):
            return self.confirmFlag
        
        return False
    
    def GetName(self):
        return self.GetItemName()

    def _ImportClasses(self, importPaths):
        '''
          utility routine to load a list of imported modules and classes
        '''
        importList = importPaths.split(',')
        for moduleName in importList:
            className = moduleName.split('.')[-1]      
            __import__(moduleName, {}, {}, className)
        
    def Execute(self, agent, notification):
        '''
          perform an action according to the action type.
          FIXME:  right now we run the scripts in the current context, so they can access the parameters.
          Probably, we should construct and pass in a context to protect us from side-effects
        '''
        result = None
        script = self.actionScript
        actionType = self.actionType
        data = notification.GetData()
        
        # set up an optional value to be used by the script
        if self.hasAttributeValue('actionValue'):
            actionValue = self.actionValue
        else:
            actionValue = None
        
        # load list of imported classes if necessary
        if self.hasAttributeValue('actionImports'):
            self._ImportClasses(self.actionImports)
        
        # execute the script according to the action type
        try:
            if actionType == 'script': 
                scriptPath = os.path.join("application", "agents", "scripts", script)
                execfile(scriptPath)
            elif actionType == 'expression':
                result = eval(script)
            elif actionType == 'inline':
                exec script
            elif actionType == 'classmethod':
                (moduleName, className, methodName) = script.split(':')
                classObject = getattr(__import__(moduleName, {}, {}, className), className)
                methodObject = getattr(classObject, methodName)
                instance = classObject()
                result = methodObject(instance)
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
    def __init__(self, action, agent, needConfirm, notification):
        self.action = action
        self.agent = agent
        self.needConfirm = needConfirm
        self.notification = notification
    
    def _GetPermissionMessage(self):
        if self.action.hasAttributeValue('actionPermissionRequest'):
            message = self.action.actionPermissionRequest
        else:
            message = _('Agent [agentname] needs your permission.  Do you grant it?')
           
        message = message.replace('[agentname]', self.agent.GetName())
        return message
    
    def Execute(self):
        if self.needConfirm:
            application = self.agent.agentManager.application
            message = self._GetPermissionMessage()
            confirmDialog = wxMessageDialog(application.wxMainFrame, message, _("Confirm Action"), wxYES_NO | wxICON_QUESTION)
                        
            result = confirmDialog.ShowModal()
            confirmDialog.Destroy()
       
            if result != wxID_YES:
                return False
            
             
        result = self.action.Execute(self.agent, self.notification)
        
        
