"""Base class for Chandler Importer objects."""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals

class Importer:
    """Base class for Chandler Importer objects.
    
    @ivar lineNumber: Current line number in the source file.
    @ivar _destination: The parent object for objected that are imported.
    
    """
    def __init__(self, destination=None):
        self.setDestination(destination)
        self.lineNumber=0
    
    def setDestination(self, spec=None):
        """Set where in the repository items should be imported to.
        
        @param spec: The parent for items created when importing.
                     C{//userdata/contentitems} is the default.
        @type spec: a Path, UUID, or string that can be coerced into a Path or
                    UUID.
                    
        """
        if spec is None:
            self._destination=Globals.repository.find("//userdata/contentitems")
        else:
            self._destination=Globals.repository.find(spec)
            
    def getDestination(self):
        """Return the parent for imported items."""
        return self._destination
    
    def setSourcePath(self, path):
        """Set the filesystem path pointing to the file to be imported."""
        self._source=path
        
    def getSourcePath(self):
        """Get the filesystem path for the file that should be imported."""
        return self._source
            
    def processObjects(self, sourceFile):
        """Abstract method to process the source file.
        
        @param sourceFile: File to import objects from.
        @type sourceFile: an open file handle
        @return: The objects created.
        @rtype: an iterator
        @raise FormatError: For a malformed source file
        @raise CreationError: If the item can't be created in the repository
        
        Concrete implementations should read sourceFile, raising a
        C{FormatError} if the file isn't formatted as expected.
        Implementations that expect text files as input should increment
        lineNumber every time they read a line of text so that a more useful
        C{FormatError} can be thrown.
        
        Once enough lines have been read to define an object, the method 
        should create a Chandler object whose parent is C{_destination}
        (retrieved via L{getDestination}).  If an object can't be created for
        any reason, the method should catch any exceptions and throw a new
        C{CreationError}.
        
        If the file ends in the middle of reading in an object, a C{FormatError}
        should be thrown.
        
        """
        pass
    
    def massageObject(self, object):
        """Massage recently created object.
        
        @param object: Recently created object.
        
        Called by processFile after object creation.  Subclasses may override
        this method to make minor changes to imported objects.
        
        """
        pass

    def processFile(self):
        """Create objects in sourceFile, return the number of objects created.
        
        Throws FormatError, CreationError, and IOError.
        
        """
        self.lineNumber=0
        f=file(self.getSourcePath())
        objects=0
        for object in self.processObjects(f):
            self.massageObject(object)
            objects=objects + 1
        try:
            Globals.repository.commit()
        except:
            raise CreationError, "Error commiting to repository"
        f.close()
        return objects

class DataError(Exception):
    """Base class for exceptions when acquiring and processing external data."""
    pass

class FormatError(DataError):
    """Exception raised for errors in the source."""
    def __init__(self, message="", line=None):
        self.message = message
        self.line = line
    def __str__(self):
        if self.line is not None:
            return "At line %d: %s" % (line, message)
        else:
            return message

class CreationError(DataError):
    """Exception raised for errors creating objects in the repository."""
    def __init__(self, message="", line=None):
        self.message = message
        self.line = line
    def __str__(self):
        if self.line is not None:
            return "At line %d: %s" % (self.line, self.message)
        else:
            return self.message
