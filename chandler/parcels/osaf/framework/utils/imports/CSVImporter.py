"""Base class for objects that import CSV files into the repository."""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import Importer
import csv

class CSVImporter(Importer.Importer):
    """Base class for objects that import CSV files into the repository.
    
    @var dialect: The CSV dialect to be used when parsing files.
    @type dialect: string
    @var hasHeader: Whether or not the file's first line should be interpreted
                    as a header, not as data.
    @type hasHeader: boolean
    @var keyList: The keys each column in the file should be associated with.
    @type keyList: list of strings
    
    """
    def __init__(self, hasHeader=True, dialect=None, keyList=None, dest=None):
        Importer.Importer.__init__(self, dest)
        self.setDialect(dialect)
        self.setHasHeader(hasHeader)
        self.setColumnKeys(keyList)
    
    def setDialect(self, dialect=None):
        """Set the dialect for reading CSV files.  Default to excel."""
        if dialect is not None:
            self.dialect=dialect
        else:
            self.dialect='excel'
    
    def setHasHeader(self, bool=True):
        """Set whether the CSV file is expected to have a header."""
        self.hasHeader=bool
        
    def setColumnKeys(self, keyList=None):
        """Set the names that CSV columns should be mapped to."""
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
                self.setColumnKeys(csv.reader(header).next())
                reader = csv.DictReader(file, self.keyList,dialect=self.dialect)
            else:
                reader = csv.DictReader(file, self.keyList,dialect=self.dialect)
            for row in reader:
                self.lineNumber=self.lineNumber + 1
                yield self.createObjectFromDict(row)
        except csv.Error, e:
            raise Importer.FormatError,\
                  ("Couldn't parse CSV file: %s" % str(e), self.lineNumber)
                                    
    def createObjectFromDict(self, importRowDict):
        """Create an object in the repository."""
        pass
