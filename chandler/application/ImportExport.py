__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"

import xml.sax.handler
from wxPython.wx import *

# FIXME: the model classes below require the '_' macro to be defined;
# I'm pretty sure it's not right to do this here, though
import gettext
gettext.install('Chandler', './locale')


from persistence import Persistent
from application.repository.Thing import Thing
from application.repository.Repository import Repository

# FIXME: these might go away when we have a generic approach (see below)
from application.repository.ContactMethod import ContactMethod
from application.repository.ContactName import ContactName
from application.repository.Contact import Contact
from application.repository.Event import Event

class ImportExport:
    """
    This class allows writing the contents of the local repository
    to an xml file, and also loading the xml file back into
    the current repository.  It relays on the objects knowing
    who to encode and decode themselves, using a standard
    representation implemented in the Item class or item-specific
    overrides.
    
    FIXME: for now it uses a single, fixed file.  We'll fix
    that after we get the basic functionality implemented.
    """

    # export the repository to an xml file
    def Export(self, filepath='SavedItems'):
        outputStr = '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
        outputStr = '<ChandlerItems>\n'
        
        repository = Repository()
        for item in repository.thingList:
            if item.IsTopLevel():
               outputStr += item.DumpThing(None)
               
        outputStr += '</ChandlerItems>\n'
        
        # write the result to the file specified by the path
        outputFile = open(filepath, 'w')
        outputFile.write(outputStr)
        outputFile.close()

    # implement import by parsing the xml file.  The sax handler
    # does all the real work of making objects
    def Import(self, filepath='SavedItems'):
        parser = xml.sax.make_parser()
        handler = ImportSaxHandler()
                
        parser.setContentHandler(handler)
        parser.parse(filepath)
         
class ImportSaxHandler(xml.sax.handler.ContentHandler):
    """
        xml sax handler to parse the xml file
    """
    def __init__(self):
        self.itemStack = []
        
    def startElement(self, name, attributes):		                
        if name == 'attribute':
            key = attributes['name']
            value = attributes['value']
                             
            thingAttribute, currentThing = self.itemStack[-1]
            if isinstance(currentThing, type([])):
                currentThing.append(value)
            else:
                currentThing.SetAttribute(key, value)
        elif name == 'List':
            key = attributes['name']
            list = []
            self.itemStack.append((key, list))
        # otherwise, it must be a thing of type 'name' or the top element, which we ignore
        elif name != 'ChandlerItems':
            # toplevel objects don't have a name attribute, so test for it
            if attributes.has_key('name'):  
                key = attributes['name']
            else:
                key = None
                
            # create a thing with the given class and add it to the stack
            newThing = self.CreateThing(name)
            self.itemStack.append((key, newThing))
            
    # when we reach the end of a list or thing, add it to the previous element on the stack
    # or, if it's the top element on the stack, add it to the repository
    def endElement(self, name):
        repository = Repository()
        if name == 'ChandlerItems':
            # we reached the end of the enclosing element, so commit our changes
            repository.Commit()
        elif name != 'attribute':
            attribute, currentThing = self.itemStack[-1]
            if len(self.itemStack) > 1:
                owningattribute, owningThing = self.itemStack[-2]
                if isinstance(owningThing, type([])):
                    owningThing.append(currentThing)
                else:
                    owningThing.SetAttribute(attribute, currentThing)
                # pop the stack
                self.itemStack = self.itemStack[0: -1]
            # it's a top level object, so add it to the repository
            else:
                repository = Repository()
                repository.AddThing(currentThing)
                self.itemStack = []
              
    # here's a routine to manufacture a thing of a given class.
   
    # FIXME: this routine needs to be completely rewritten to use ThingFactories,
    # or some other generic approach that can handle generic things.
    # For now, it only works with a few hardwired types needed for the .1 release
   
    def CreateThing(self, thingName):
        if thingName == 'Contact':
            newThing = Contact('Person')
        elif thingName == 'Event':
            newThing = Event()
        elif thingName == 'ContactName':
            owningAttribute, owningThing = self.itemStack[-1]
            newThing = ContactName(owningThing)
        elif thingName == 'ContactMethod':
            newThing = ContactMethod('phone', None)
           
        return newThing
   
           
    
 
        
        
