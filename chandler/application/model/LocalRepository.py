#!bin/env python

# Scaffolding, provide a singleton LocalRepository to store the RDF objects
# Use the borg pattern (from python cookbook 5.22) 

from persistence import Persistent
from persistence.list import PersistentList

# use repository access protocol:
import os

import transaction
from zodb import db, storage

from RdfObject import RdfObject
from RdfClass import RdfClass
from RdfProperty import RdfProperty

class LocalRepository:

    # as per the borg pattern, this will become the object's __dict__
    _shared_state = {}
 
    # begin { global rap initialization:    
    _use_rap = False
    _echo_rap = False
    if os.path.exists('_echo_.txt'):
        _echo_rap = True
        print "_echo_.txt exists: _echo_rap = True"
    else:
        print "file _echo_.txt is missing: _echo_rap = False"
        
    if os.path.exists('_rap_.txt'):
        _use_rap = True
        if _echo_rap: print "_rap_.txt exists: _use_rap = True"
    else:
        if _echo_rap: print "file _rap_.txt is missing: _use_rap = False"
    
    if _use_rap:
        try:
            import rap
        except:
            _use_rap = False
            print "import rap failed; maybe net/rap has not been built"
         
    if _use_rap:
        rap.RAP_ClientInit() # should later call rap.RAP_ClientShutdown()
        print "rap.RAP_ClientInit()"

    _shared_state['_use_rap'] = _use_rap
    _shared_state['_echo_rap'] = _echo_rap
    # } end
   
    _storage = storage.file.FileStorage('_RepositoryTest_')
    _db = db.DB(_storage)
    _connection = _db.open()
    _dbroot = _connection.root()
 
    # begin {
    
    if _use_rap:
        hostname = "localhost"
        repname = "fs-trace-rep"
        _storage.setRepository(hostname, repname, _echo_rap)
    # } end
    
    if not _dbroot.has_key('classList'):
        _dbroot['classList'] = PersistentList()
    _shared_state['classList'] = _dbroot['classList']
        
    if not _dbroot.has_key('propertyList'):
        _dbroot['propertyList'] = PersistentList()
    _shared_state['propertyList'] = _dbroot['propertyList']
        
    if not _dbroot.has_key('objectList'):
        _dbroot['objectList'] = PersistentList()
    _shared_state['objectList'] = _dbroot['objectList']
    
    transaction.get_transaction().commit()
    
    def __init__(self):
        self.__dict__ = self._shared_state
        # begin {
        if self._echo_rap:
            if self._use_rap:
                print "LocalRepository._use_rap => True"
            else:
                print "LocalRepository._use_rap => False"
        # } end

    # @@@ Need to close the file at some point?
    # def __del__( self ):
    #    self._db.close( )
        
    def addClass(self, klass):
        """ """
        assert(isinstance(klass, RdfClass))
        self.classList.append(klass)
        transaction.get_transaction().commit()

    def addProperty(self, prop):
        """ """
        assert(isinstance(prop, RdfProperty))
        self.propertyList.append(prop)
        transaction.get_transaction().commit()

    def addObject(self, obj):
        """ """
        assert(isinstance(obj, RdfObject))
        self.objectList.append(obj)
        transaction.get_transaction().commit()

    def deleteObject(self, obj):
        try:
            index = self.objectList.index(obj)
            del self.objectList[index]
        except:
            # FIXME: need to indicate failure somehow...
            pass
        
    def commit(self):
        transaction.get_transaction().commit()

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
    

