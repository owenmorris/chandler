"""Base class for Chandler Importer objects."""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import csv

class Importer:
    """Base class for Chandler Importer objects.
    
    @ivar lineNumber: Current line number in the source file.
    @ivar destination: The parent object for objects that are imported.
    @ivar source: The filesystem path for the file that should be imported
    @ivar mapping: An L{ImportMap.ImportMap} object
    
    """
    def __init__(self, destination=None):
        if destination == None:
            self.destination=Globals.repository.findPath("//userdata/contentitems")
        else:
            self.destination=Globals.repository.findPath(destination)
        self.lineNumber=0
    
    def processObjects(self, sourceFile):
        """Abstract method to process the source file.
        
        @param sourceFile: File to import objects from.
        @type sourceFile: an open file handle
        @return: The objects created.
        @rtype: an iterator
        @raise FormatError: For a malformed source file
        @raise CreationError: If the item can't be created in the repository
        
        Concrete implementations should read sourceFile, raising a
        L{FormatError} if the file isn't formatted as expected.
        Implementations that expect text files as input should increment
        lineNumber every time they read a line of text so that a more useful
        L{FormatError} can be thrown.
        
        Once enough lines have been read to define an object, the method 
        should create a Chandler object whose parent is C{destination}.  If an
        object can't be created for any reason, the method should catch any
        exceptions and throw a new L{CreationError}.
        
        If the file ends in the middle of reading in an object, a L{FormatError}
        should be thrown.
        
        """
        pass
    
    def postProcess(self, object):
        """Further process recently created object.
        
        @param object: Recently created object.
        
        Called by processFile after object creation.  Subclasses may override
        this method to make changes to imported objects and to create attributes
        not defined in the mapping.
        
        """
        pass

    def processFile(self):
        """Create objects in sourceFile.
        
        return: The number of high-level objects created, each high level object
        may have created many items as attributes.

        Raises FormatError, CreationError, and IOError.
        
        """
        self.lineNumber=0
        f=file(self.source)
        objects=0
        for object in self.processObjects(f):
            self.postProcess(object)
            objects=objects + 1
        try:
            Globals.repository.commit()
        except:
            raise CreationError, "Error commiting to repository",self.lineNumber
        f.close()
        return objects

class CSVImporter(Importer):
    """Base class for objects that import CSV files into the repository.
    
    @var dialect: The CSV dialect to be used when parsing files.
    @type dialect: string
    @var hasHeader: Whether or not the file's first line should be interpreted
                    as a header, not as data.
    @type hasHeader: boolean
    @var keyList: The keys each column in the file should be associated with.
    @type keyList: list of strings
    
    """
    def __init__(self, hasHeader=True, dialect='excel', keyList=None, dest=None):
        Importer.__init__(self, dest)
        self.dialect=dialect
        self.hasHeader=hasHeader
        self.keyList=keyList
    
    def processObjects(self, file):
        """Main iterator for importing objects from CSV.
        
        @see processObjects in L{Importer}.
        
        If C{hasHeader} is C{True}, use the first line of C{file} to determine
        the column keys. Otherwise use keyList.
        
        """
        try:
            if self.hasHeader:
                self.lineNumber=self.lineNumber + 1
                header=iter([file.readline()])
                self.keyList=(csv.reader(header).next())
                reader = csv.DictReader(file, self.keyList,dialect=self.dialect)
            else:
                reader = csv.DictReader(file, self.keyList,dialect=self.dialect)
            for row in reader:
                self.lineNumber=self.lineNumber + 1
                result=self.mapping.process(row)
                if not result:
                    raise DataError, \
                        ("Mapping error at line %s of the import file" \
                        % self.lineNumber)
                else:
                    yield result
        except csv.Error, e:
            raise FormatError,\
                  ("Couldn't parse CSV file: %s" % str(e), self.lineNumber)

class DataError(Exception):
    """Base class for exceptions when acquiring and processing external data."""
    pass

class FormatError(DataError):
    """Exception raised for errors in the source."""
    def __init__(self, message="", line=None):
        self.message = message
        self.line = line
    def __str__(self):
        if self.line != None:
            return "At line %d: %s" % (line, message)
        else:
            return message

class CreationError(DataError):
    """Exception raised for errors creating objects in the repository."""
    def __init__(self, message="", line=None):
        self.message = message
        self.line = line
    def __str__(self):
        if self.line != None:
            return "At line %d: %s" % (self.line, self.message)
        else:
            return self.message
