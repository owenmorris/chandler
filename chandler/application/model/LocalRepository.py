#!bin/env python

# Scaffolding, provide a singleton LocalRepository to store the RDF objects
# Use the borg pattern (from python cookbook 5.22) 

from application.persist import Persist

from RdfObject import RdfObject
from RdfClass import RdfClass
from RdfProperty import RdfProperty

class LocalRepository:

    _shared_state = {}
    
    _storage = Persist.Storage("_RepositoryTest_")
    
    _shared_state['classList'] =_storage.persist('local_classes',
                                                 Persist.List())
    
    _shared_state['propertyList'] = _storage.persist('local_properties',
                                                     Persist.List())
    
    _shared_state['objectList'] = _storage.persist('local_objects',
                                                   Persist.List())
    
    _storage.commit()
    
    def __init__(self):
        self.__dict__ = self._shared_state

    def addClass(self, klass):
        """ """
        assert(isinstance(klass, RdfClass))
        self.classList.append(klass)
        self._storage.commit()

    def addProperty(self, prop):
        """ """
        assert(isinstance(prop, RdfProperty))
        self.propertyList.append(prop)
        self._storage.commit()

    def addObject(self, obj):
        """ """
        assert(isinstance(obj, RdfObject))
        self.objectList.append(obj)
        self._storage.commit()

    def commit(self):
        self._storage.commit()


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
