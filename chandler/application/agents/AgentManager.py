__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os.path
import os
import xml.sax.handler

from Agent import *
from model.AgentItem import *
from model.Instruction import *
from model.Repertoire import *
from model.Condition import *
from model.Action import *

"""
The AgentManager Class is responsible for loading agents from the repository and launching them at
start-up.  It maintains a directory of agents and allows callers to manipulate them
"""

class AgentManager:
    
    def __init__(self, application):
        """
           initialize data structures then load the agents
        """     
        self.application = application
        self.notificationManager = application.model.notificationManager

        self.debugMode = False

        self.agentMap = {}
        self.activeAgents = {}
        self.notificationHandledStatus = {}
        
        self._LoadAgents()
        self._CheckForNewAgents()
                
    def _LoadAgents(self):
        """
          Iterate through the agentItem in the repository and create their dynamic counterparts
        """
        itemList = self.application.repository.find("//Agents")
        if itemList == None:
            return
        
        for agentItem in itemList:
            if isinstance(agentItem, AgentItem):
                # GetAgentFromItems takes care of registering the new agent
                agent = self.GetAgentFromItem(agentItem)
    
    def _CheckForNewAgents(self):
        """
          Iterate through the agent directory inspecting agent definition xml files, and install
          the associated agent item when appropriate.
        """ 
        agent_directory = 'application/agents/test_agents'
        for filename in os.listdir(agent_directory):
           if filename[-4:] == '.xml':
               agent_path = os.path.join (agent_directory, filename)
               if not self.IsInstalled(agent_path):
                   agentItem = self.AddAgentFromFile(agent_path)
           
                   if agentItem != None:
                       agent = self.GetAgentFromItem(agentItem)
    
    def IsInstalled(self, filePath):
        """
           return True if the agent definition file referenced by the passed-in path
           is already installed, and False if it's not
        """
        for item in self.agentMap.keys():
            if filePath == item.sourceFile:
                return True
        return False
    
    def UnInstall(self, filePath):
        """
           uninstall the agent referenced by the passed-in path
           FIXME: this isn't implemented yet
        """
        if self.IsInstalled(filePath):
            pass
        
    def AddAgentFromFile(self, filePath):
        """
           Create an agent item in the repository from the passed-in xml file,
           and then load it.
        """
        parser = xml.sax.make_parser()
        handler = AgentXMLFileHandler(self, filePath)
 
        parser.setContentHandler(handler)
        
        try:
            parser.parse(filePath)
            item = handler.agentItem      
        except:
            print "failed to load agent", filePath
            item = None
            
        return item
    
    def AgentMatches(self, agent, name, role, owner):
        """ 
          return True if the passed-in agent matches the passed-in criteria
          FIXME: this isn't implemented yet
        """
        return True
    
    def LookUpAgents(self, name, role, owner):
        """
          return a list of agents that meet the passed-in criteria.  If a parameter is None,
          it's ignored.  Wildcards will be supported eventually, but not yet
        """
        resultAgents = []
        registeredAgents = self.agentMap.values()
        for agent in registeredAgents:
            if self.AgentMatches(name, role, owner):
                resultAgents.append(agent)
                
        return resultAgents
    
    def GetAgentFromItem(self, item):
        if self.agentMap.has_key(item):
            return self.agentMap[item]
        
        agent = Agent(item, self)
        self.Register(agent)
        agent.Resume()
        return agent
    
    def IsRegistered(self, agent):
        return self.agentMap.has_key(agent.model)
    
    def Register(self, agent):
        """
          register an agent with the agent manager
        """
        if not self.IsRegistered(agent):
            self.agentMap[agent.model] = agent
         
            # register with the notification manager and subscribe to notifications
            clientID = agent.GetClientID()
            if not self.notificationManager.IsRegistered(clientID):
                self.notificationManager.Register(clientID)
            
            # subscribe to notifications
            notifications = agent.model.GetActiveNotifications()
            for notification in notifications:    
                  self.notificationManager.Subscribe(notification, clientID)
              
    def Unregister(self, agent):
        """
          unregister an agent from the agent manager
        """
        if self.IsRegistered(agent):           
            # unsubscribe to notifications
            clientID = agent.GetClientID()
            
            notifications = agent.model.GetActiveNotifications()
            for notification in notifications:    
                  self.notificationManager.Unsubscribe(notification, clientID)
            
            del self.agentMap[agent.model]
 
    def Stop(self):
        """
          The stop method is called before quitting to stop the threads associated with the agents
        """
        for agent in self.agentMap.values():
            agent.Suspend()
            self.Unregister(agent)

    def Restart(self):
        """
          Restart all the agents
        """
        for agent in self.agentMap.values():
            self.Register(agent)
            agent.Resume() 

    # the following routines maintain the 'handled' state associated with a notification
    # we will probably have a more elaborate model for coordinating actions between agents
    # soon, but this simple scheme suffices for the original implementation
    
    def GetHandledStatus(self, notification):
        id = notification.GetID()
        if self.notificationHandledStatus.has_key(id):
            return self.notificationHandledStatus[id]
        return False
    
    def SetHandledStatus(self, notification, newStatus):      
        self.notificationHandledStatus[notification.GetID()] = newStatus
        
    def DeleteHandledStatus(self, notification):
        id = notification.GetID()        
        if self.notificationHandledStatus.has_key(id):
            del self.notificationHandledStatus[id]
            
class AgentXMLFileHandler(xml.sax.handler.ContentHandler):
    """
      Here's the xml parser class that receives the agent definition file as an XML SAX stream,
      and creates an agentItem from it, that is returned in the handler's agentItem field.
    """
    def __init__(self, agentManager, filePath):
        self.agentManager = agentManager
        self.filePath = filePath
        
        self.agentItem = None
        self.currentItem = None
        self.lastContainer = None
        self.inRepertoire = False
        
        self.buffer = ""
        
    def _GetOptionalAttribute(self, attributeName, attributeDict):
        """
           utility routine to return an optional attribute from the passed-in
           attribute name and dictionary
        """
        if attributeDict.has_key(attributeName):
            return attributeDict[attributeName]
                                               
        return None
    
    def _MakeItem(self, moduleName, agentName):
        """
           magic utility routine that makes a new item dynamically, with the passed in moduleName
        """
        className = moduleName.split('.')[-1]      
        classObject = getattr(__import__(moduleName, {}, {}, className), className)
                
        repository = self.agentManager.application.repository
        container = repository.find("//Agents")
        kind = repository.find("//Schema/AgentsSchema/" + className)              
        return classObject(agentName, container, kind)
          
    def startElement(self, name, attributes):
        self.buffer = ""
        repository = self.agentManager.application.repository
        
        if name == 'agent':
            agentName = self._GetOptionalAttribute('name', attributes)
            
            # if a class is specified, we have to import it on the fly
            if attributes.has_key('class'):
                moduleName = attributes['class']
                self.agentItem = self._MakeItem(moduleName, agentName) 
            # otherwise we use the Item class
            else:
                agentFactory = AgentItemFactory(repository)
                self.agentItem = agentFactory.NewItem(agentName)
            
            self.currentItem = self.agentItem
            
            if agentName != None:
                self.agentItem.agentName = agentName                                           
        
        elif name == 'attribute':
            self.attributeName = attributes['name']
        
        elif name == 'instruction':
            self.inRepertoire = False
            
            enabledText = self._GetOptionalAttribute('enabled', attributes)
            enabledFlag = enabledText == 'True'
            instructionFactory = InstructionFactory(repository) 
            self.currentItem = instructionFactory.NewItem()
            self.currentItem.setAttributeValue('enabled', enabledFlag)
            self.lastContainer = self.currentItem
            
            self.agentItem.AddInstruction(self.currentItem)
        
        elif name == 'repertoire':
            self.inRepertoire = True
            
            repertoireName = self._GetOptionalAttribute('name', attributes)
            repertoireFactory = RepertoireFactory(repository) 
            self.currentItem = repertoireFactory.NewItem(repertoireName)
            self.lastContainer = self.currentItem
            self.agentItem.SetRepertoire(self.currentItem)
            
        elif name == 'condition':
            conditionName = self._GetOptionalAttribute('name', attributes)
            
            conditionFactory = ConditionFactory(repository)
            self.currentItem = conditionFactory.NewItem(conditionName)
                        
            self.lastContainer.AddCondition(self.currentItem) 
            
        elif name == 'action':
            actionName = self._GetOptionalAttribute('name', attributes)
            
            # if a classname is specified, make the item dynamically
            if attributes.has_key('class'):
                moduleName = attributes['class']
                self.currentItem = self._MakeItem(moduleName, actionName) 
            else:     
                actionFactory = ActionFactory(repository)
                self.currentItem = actionFactory.NewItem(actionName)
            
            if actionName != None:
                self.currentItem.setAttributeValue('actionName', actionName)
            
            self.lastContainer.AddAction(self.currentItem)                                                     
            
    def characters(self, data):
        self.buffer += data
                                
    def endElement(self, name):
        if name == 'attribute':
            value = self.buffer
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
                
            self.currentItem.setAttributeValue(self.attributeName, value)
        elif name == 'agent':
            self.agentItem.setAttributeValue('sourceFile', self.filePath)
            
