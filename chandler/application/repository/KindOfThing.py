""" KindOfThing, the superclass for all classes in the repository.

    A KindOfThing stores meta-information for a class of things.
    In particular, a KindOfThing keeps a list of attribute
    templates, information about attributes that instances
    are likely to have.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence import Persistent
from persistence.dict import PersistentDict
from persistence.list import PersistentList

from application.repository import Thing

class KindOfThing(Thing):
    def __init__(self, uri, templateList):
        Thing.__init__(self)
        self.SetUri(uri)
        self.CreateAttributeTemplate(templateList)
        
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
        templateList.add(template)
    
    def RemoveAttributeTemplate(self, uri):
        templateList = self[chandler.template]
        template = GetAttributeTemplate(uri)
        if template:
            templateList.remove(template)
    
    def GetAllAttributeTemplates(self):
        templateList = self[chandler.template]
        return templateList