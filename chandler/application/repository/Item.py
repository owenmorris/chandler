""" Item.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application.repository.Namespace import chandler, dc
from application.repository.Thing import Thing
from application.repository.KindOfThing import KindOfThing
from application.repository.KindOfThing import AkoThingFactory

from application.repository.Repository import Repository

from mx import DateTime

_attributes = [{ chandler.uri : dc.identifier,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.remoteAddress,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.project,
                 chandler.range : str,
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.status,
                 chandler.range : str,
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.topic,
                 chandler.range : str,
                 chandler.cardinality : None,
                 chandler.required : False,
                 chandler.default : None },
               
               { chandler.uri : chandler.dateCreated,
                 chandler.range : 'DateTime',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None },
                        
               { chandler.uri : chandler.dateModified,
                 chandler.range : 'DateTime',
                 chandler.cardinality : 1,
                 chandler.required : False,
                 chandler.default : None }
               ]

class AkoItemFactory(AkoThingFactory):
    def __init__(self):
        AkoThingFactory.__init__(self, chandler.Item, _attributes)

class Item(Thing):
    def __init__(self, dict=None):
        Thing.__init__(self, dict)
        self.SetAko(AkoItemFactory().GetAko())
        self.SetUri(self.GetUniqueId())
        
    # Convenience methods make chandler attributes accessible
    # via python object attributes

    def IsRemote(self):
        # @@@ Perhaps do some sort of validation
        remoteAddress = self.get(chandler.remoteAddress, None)
        return (remoteAddress != None)
    
    # Items typically are top level objects
    def IsTopLevel(self):
        return 1
    
    def GetRemoteAddress(self):
        return self.GetAttribute(chandler.remoteAddress)
    
    def SetRemoteAddress(self, address):
        self.SetAttribute(chandler.remoteAddress, address)
        
    remoteAddress = property(GetRemoteAddress, SetRemoteAddress)
    
    def GetProjects(self):
        return self.GetAttribute(chandler.project)
    
    def SetProjects(self, projectList):
        """
        """
        if (projectList and 
            not instanceof(projectList, PersistentList)):
            # If we have a simple python list, create
            # a persistent variety for the item.
            projectList = PersistentList(projectList)

        self.SetAttribute(chandler.project, projectList)
        
    def AddProject(self, project):
        projectList = self.GetAttribute(chandler.project)
        projectList.add(project)
        
    def RemoveProject(self, project):
        projectList = self.GetAttribute(chandler.project)
        projectList.remove(project)
        
    def GetDateCreated(self):
        return self.GetAttribute(chandler.dateCreated)
    
    def GetDateModified(self):
        return self.GetAttribute(chandler.dateModified)
    
    projectList = property(GetProjects, SetProjects)
    dateCreated = property(GetDateCreated)
    dateModified = property(GetDateModified)
        

