#!bin/env python

# Scaffolding, provide a singleton LocalRepository to store the RDF objects
# Use the borg pattern (from python cookbook 5.22) 

from Persistence import Persistent, PersistentList
import Transaction
from ZODB import DB, FileStorage

from RdfObject import RdfObject
from RdfClass import RdfClass
from RdfProperty import RdfProperty

class LocalRepository:

    # as per the borg pattern, this will become the object's __dict__
    _shared_state = {}
    
    _storage = FileStorage.FileStorage('_RepositoryTest_')
    _db = DB.DB(_storage)
    _connection = _db.open()
    _dbroot = _connection.root()
    
    if not _dbroot.has_key('classList'):
        _dbroot['classList'] = PersistentList.PersistentList()
    _shared_state['classList'] = _dbroot['classList']
        
    if not _dbroot.has_key('propertyList'):
        _dbroot['propertyList'] = PersistentList.PersistentList()
    _shared_state['propertyList'] = _dbroot['propertyList']
        
    if not _dbroot.has_key('objectList'):
        _dbroot['objectList'] = PersistentList.PersistentList()
    _shared_state['objectList'] = _dbroot['objectList']
    
    Transaction.get_transaction().commit()
    
    def __init__(self):
        self.__dict__ = self._shared_state

    # @@@ Need to close the file at some point?
    # def __del__( self ):
    #    self._db.close( )
        
    def addClass(self, klass):
        """ """
        assert(isinstance(klass, RdfClass))
        self.classList.append(klass)
        Transaction.get_transaction().commit()

    def addProperty(self, prop):
        """ """
        assert(isinstance(prop, RdfProperty))
        self.propertyList.append(prop)
        Transaction.get_transaction().commit()

    def addObject(self, obj):
        """ """
        assert(isinstance(obj, RdfObject))
        self.objectList.append(obj)
        Transaction.get_transaction().commit()

    def commit(self):
        Transaction.get_transaction().commit()

    def printSchemaTriples(self):
        print "*************Printing Class Triples***************"
        for klass in self.classList:
            klass.printTriples()

        print "*************Printing Property Triples***************"
        for prop in self.propertyList:
            prop.printTriples()

    def printDataTriples(self):
        print "*************Printing Object Triples***************"
        for obj in self.objectList:
            obj.printTriples()
            
    def printTriples(self):
        self.printSchemaTriples()
        self.printDataTriples()
    

