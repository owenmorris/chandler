""" KindOfThing, the superclass for all classes in the repository.

    A KindOfThing stores meta-information for a class of things.
    In particular, a KindOfThing keeps a list of attribute
    templates, information about attributes that instances
    are likely to have.
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from persistence import Persistent
from persistence.dict import PersistentDict
from persistence.list import PersistentList

from application.repository.Thing import Thing
from application.repository.AttributeTemplate import AttributeTemplate
from application.repository.Namespace import chandler
from application.repository.Repository import Repository

# @@@ Temporarily placed here
class ThingFactory:
    """ A factory class to create instances of 'Thing', based on a dictionary.
        Subclasses of this factory class need to override 'CreateThing' to
        use the constructor of the appropriate class.
    """
    def CreateThing(self, dict):
        return Thing(dict)

    def GetThing(self, url, dict):
        repository = Repository()
        thing = repository.FindThing(self.url)
        if (thing is None):
            thing = self.CreateThing(dict)
            repository.AddThing(thing)
        return thing

class AkoThingFactory:
    def __init__(self, url, templateDict):
        self.url = url
        self.templateDict = templateDict
    
    def GetAko(self):
        repository = Repository()
        akoItem = repository.FindThing(self.url)
        if (akoItem is None):
            akoItem = KindOfThing(self.url, self.templateDict)
            repository.AddThing(akoItem)

            templateList = akoItem.GetAllAttributeTemplates()
            for template in templateList:
                repository.AddThing(template)
            
        return akoItem      

class KindOfThing(Thing):
    def __init__(self, url, templateList):
        Thing.__init__(self)
        self.SetURL(url)
        self.CreateAttributeTemplates(templateList)
        
    def CreateAttributeTemplates(self, attributeTemplateList):
        self[chandler.template] = PersistentList()
        for templateDict in attributeTemplateList:
            self.CreateAttributeTemplate(templateDict)
        
    def GetAttributeTemplate(self, url):
        templateList = self[chandler.template]
        for template in templateList:
            if (template.GetURL() == url):
                return template
        return None
    
    def CreateAttributeTemplate(self, dict):
        templateList = self[chandler.template]
        template = AttributeTemplate(dict)
        templateList.append(template)
    
    def RemoveAttributeTemplate(self, url):
        templateList = self[chandler.template]
        template = self.GetAttributeTemplate(url)
        if template:
            templateList.remove(template)
    
    def GetAllAttributeTemplates(self):
        templateList = self[chandler.template]
        return templateList
    
    # don't dump metaobjects like KindOfThing
    def ShouldDump(self):
        return 0
     