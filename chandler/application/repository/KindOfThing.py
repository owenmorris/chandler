""" KindOfThing, the superclass for all classes in the repository.

    A KindOfThing stores meta-information for a class of things.
    In particular, a KindOfThing keeps a list of attribute
    templates, information about attributes that instances
    are likely to have.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence import Persistent
from persistence.dict import PersistentDict
from persistence.list import PersistentList

from application.repository.Thing import Thing
from application.repository.AttributeTemplate import AttributeTemplate
from application.repository.Namespace import chandler
from application.repository.Repository import Repository

class AkoThingFactory:
    def __init__(self, uri, templateDict):
        self.uri = uri
        self.templateDict = templateDict
    
    def GetAko(self):
        repository = Repository()
        akoItem = repository.FindThing(self.uri)
        if (akoItem is None):
            akoItem = KindOfThing(self.uri, self.templateDict)
            repository.AddThing(akoItem)

            templateList = akoItem.GetAllAttributeTemplates()
            for template in templateList:
                repository.AddThing(template)
            
        return akoItem      

class KindOfThing(Thing):
    def __init__(self, uri, templateList):
        Thing.__init__(self)
        self.SetUri(uri)
        self.CreateAttributeTemplates(templateList)
        
    def CreateAttributeTemplates(self, attributeTemplateList):
        self[chandler.template] = PersistentList()
        for templateDict in attributeTemplateList:
            self.CreateAttributeTemplate(templateDict)
        
    def GetAttributeTemplate(self, uri):
        templateList = self[chandler.template]
        for template in templateList:
            if (template.GetUri() == uri):
                return template
        return None
    
    def CreateAttributeTemplate(self, dict):
        templateList = self[chandler.template]
        template = AttributeTemplate(dict)
        templateList.append(template)
    
    def RemoveAttributeTemplate(self, uri):
        templateList = self[chandler.template]
        template = GetAttributeTemplate(uri)
        if template:
            templateList.remove(template)
    
    def GetAllAttributeTemplates(self):
        templateList = self[chandler.template]
        return templateList