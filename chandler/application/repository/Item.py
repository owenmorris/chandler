""" Item.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.repository import Thing, KindOfThing

_attributeTemplates = [{ chandler.uri : dc.identifier,
                          chandler.type : str,
                          chandler.cardinality : 1,
                          chandler.required : false,
                          chandler.default : None },
                        
                        { chandler.uri : dc.subject,
                          chandler.type : str,
                          chandler.cardinality : 1,
                          chandler.required : false,
                          chandler.default : None },
                        
                        { chandler.uri : chandler.project,
                          chandler.type : str,
                          chandler.cardinality : None,
                          chandler.required : false,
                          chandler.default : None },
                        
                        { chandler.uri : chandler.dateCreated,
                          chandler.type : DateTime,
                          chandler.cardinality : 1,
                          chandler.required : false,
                          chandler.default : None },
                        
                        { chandler.uri : chandler.dateModified,
                          chandler.type : DateTime,
                          chandler.cardinality : 1,
                          chandler.required : false,
                          chandler.default : None }
                        ]

akoItem = KindOfThing(chandler.Item, _attributeTemplates)
repository.addThing(akoItem)

class Item(Thing):
    def __init__(self, dict=None):
        Thing.__init__(self, dict)
        self.SetAko(akoItem)
        
    # Convenience methods make chandler attributes accessible
    # via python object attributes
    
    def GetProjects(self):
        return GetAttribute(chandler.project)
    
    def SetProjects(self, projectList):
        """
        """
        if (projectList and 
            not instanceof(projectList, PersistentList)):
            # If we have a simple python list, create
            # a persistent variety for the item.
            projectList = PersistentList(projectList)

        SetAttribute(chandler.project, projectList)
        
    def AddProject(self, project):
        projectList = GetAttribute(chandler.project)
        projectList.add(project)
        
    def RemoveProject(self, project):
        projectList = GetAttribute(chandler.project)
        projectList.remove(project)
        
    def GetDateCreated(self):
        return GetAttribute(chandler.dateCreated)
    
    def GetDateModified(self):
        return GetAttribute(chandler.dateModified)
    
    projectList = property(GetProjects, SetProjects)
    dateCreated = property(GetDateCreated)
    dateModified = property(GetDateModified)
        
