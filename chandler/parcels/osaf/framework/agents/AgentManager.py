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
        
        self.agentMap = {}
        self.activeAgents = {}
        
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
        """
        if self.IsInstalled(filePath):
            pass
        
    def AddAgentFromFile(self, filePath):
        """
           Create an agent item in the repository from the passed-in xml file,
           and then load it
        """
        parser = xml.sax.make_parser()
        handler = AgentXMLFileHandler(self, filePath)
 
        parser.setContentHandler(handler)
        
        #try:
        parser.parse(filePath)
        item = handler.agentItem
           
        #except:
            #print "failed to load agent", filePath
            #item = None
            
        return item
    
    def AgentMatches(self, agent, name, role, owner):
        """ 
          return True if the passed-in agents matches the passed-in criteria
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
            notificationManager = self.application.model.notificationManager
            notificationManager.Register(clientID)
           
            # subscribe to notifications
            notifications = agent.model.GetActiveNotifications()
            for notification in notifications:    
                  notificationManager.Subscribe(notification, clientID)
              
    def Unregister(self, agent):
        """
          unregister an agent from the agent manager
        """
        if self.IsRegistered(agent):           
            # unsubscribe to notifications
            clientID = agent.GetClientID()
            notificationManager = self.application.model.notificationManager
            
            notifications = agent.model.GetActiveNotifications()
            for notification in notifications:    
                  notificationManager.Unsubscribe(notification, clientID)
            
            del self.agentMap[agent.model]
 
    def Stop(self):
        """
          The stop message is called before quitting to stop the threads associated with the agents
        """
        for agent in self.agentMap.values():
            agent.Suspend()
            self.Unregister(agent)
            
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
        self.lastInstruction = None
        self.buffer = ""
    
    def _GetOptionalAttribute(self, attributeName, attributeDict):
        """
           utility routine to return an optional attribute from the passed-in
           attribute name and dictionary
        """
        if attributeDict.has_key(attributeName):
            return attributeDict[attributeName]
                                               
        return None
    
    def startElement(self, name, attributes):
        self.buffer = ""
        repository = self.agentManager.application.repository
        
        if name == 'agent':
            agentName = self._GetOptionalAttribute('name', attributes)
            agentFactory = AgentItemFactory(repository)
            self.agentItem = agentFactory.NewItem(agentName)
            
            self.currentItem = self.agentItem
            
            if agentName != None:
                self.agentItem.agentName = agentName                                           
        
        elif name == 'attribute':
            self.attributeName = attributes['name']
        
        elif name == 'instruction':
            enabledText = self._GetOptionalAttribute('enabled', attributes)
            enabledFlag = enabledText == 'True'
            instructionFactory = InstructionFactory(repository) 
            self.currentItem = instructionFactory.NewItem()
            self.currentItem.setAttributeValue('enabled', enabledFlag)
            self.lastInstruction = self.currentItem
            
            self.agentItem.AddInstruction(self.currentItem)
            
        elif name == 'condition':
            conditionName = self._GetOptionalAttribute('name', attributes)
            conditionFactory = ConditionFactory(repository)
            self.currentItem = conditionFactory.NewItem(conditionName)
            
            if conditionName != None:
                self.currentItem.setAttributeValue('actionName', conditionName)
            
            self.lastInstruction.SetCondition(self.currentItem) 
            
        elif name == 'action':
            actionName = self._GetOptionalAttribute('name', attributes)
            actionFactory = ActionFactory(repository)
            self.currentItem = actionFactory.NewItem(actionName)
            
            if actionName != None:
                self.currentItem.setAttributeValue('actionName', actionName)
                
            self.lastInstruction.AddAction(self.currentItem)                                                     
   
    def characters(self, data):
        self.buffer += data
                                
    def endElement(self, name):
        if name == 'attribute':
            self.currentItem.setAttributeValue(self.attributeName, self.buffer)
        elif name == 'agent':
            self.agentItem.setAttributeValue('sourceFile', self.filePath)
            