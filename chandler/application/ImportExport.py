__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF License"

from persistence import Persistent
from application.repository.Thing import Thing
from application.repository.Repository import Repository

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
        
    def Import(self, filepath='SavedItems'):
        wxMessageBox(_("Import from File isn't implemented yet"))
    
        # open the specified file and read it in
        
        # parse the file, generating the items into the repository
        
        pass
        
        
        
        
