__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import wx
from repository.item.Item import Item
import os, os.path, time

"""
The Action Class is a persistent object containing information about a
particular action that can be executed by an agent, either explictly at the
user's request, or automatically, as specified by a conditional instruction.
"""
class Action(Item):
    def IsAsynchronous(self):
        """
          return True if the action should be executed asynchronously
        """
        return self.asyncFlag
        
    def UseWxThread(self):
        """
           by default, actions run on the agent's thread, but they can be
           deferred to run synchronously with the wxWindows.  This means
           they can safely make wxWindows calls, but they shouldn't be
           time consuming
        """
        return self.wxThreadFlag

    def NeedsConfirmation(self):
        """
          if the confirmFlag is True, we require that the user confirms
          the action
        """
        return self.confirmFlag
    
    def GetName(self):
        return self.itsName

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
          FIXME:  right now we run the scripts in the current context, so
          they can access the parameters.  Probably, we should construct
          and pass in a context to protect us from side-effects
        '''
        result = None
        script = self.actionScript
        actionType = self.actionType
        if notification:
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
                print "unknown action type", agent.itsName, self.GetName(), self.actionType
        except:
            print "failed to execute action", self.GetName()

        return result

    def IsCompleted(self):
        # we probably don't need this... whats the difference between complete
        # and waiting to execute?
        return False
    
    def GetCompletionPercentage(self):
        '''
           A number between 0 and 99.  -1 indicates that the completion
           percent is unknown
           get the completion percentage of asynchronous actions
        '''
        return 0


"""
The DeferredAction class is a simple wrapper for an action that allows
an action to be invoked without passing any parameters.
"""
class DeferredAction:
    def __init__(self, actionID):
        self.actionID = actionID

    def _GetPermissionMessage(self, action, agent):
        if action.hasAttributeValue('actionPermissionRequest'):
            message = action.actionPermissionRequest
        else:
            message = _('Agent [agentname] needs your permission.  Do you grant it?')

        message = message.replace('[agentname]', agent.itsName)
        return message

    def Execute(self, agentID, notification):
        repository = Globals.repository

        repository.commit()

        action = repository.find(self.actionID)
        agent = repository.find(agentID)

        if action.NeedsConfirmation():
            message = self._GetPermissionMessage(action, agent)
            # @@@ 25Issue - we no longer use wxMainFrame
            confirmDialog = wx.MessageDialog(Globals.wxMainFrame, message, _("Confirm Action"), wx.YES_NO | wx.ICON_QUESTION)

            result = confirmDialog.ShowModal()
            confirmDialog.Destroy()

            if result != wx.ID_YES:
                return False

        return action.Execute(agent, notification)
