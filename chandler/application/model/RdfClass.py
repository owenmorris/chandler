#!bin/env python

# May be superfluous, the class really knows all about its state

from RdfResource import RdfResource
from RdfNamespace import rdf, rdfs

class RdfClass(RdfResource):
    def __init__(self, klass):
        RdfResource.__init__(self)

        self.klass = klass

    def printTriples(self):
        """Scaffolding, just to give a taste"""
        print (self.klass.uri, rdf.type, rdfs.Class)

        for key in self.klass.rdfs.keys():
            print (key, rdfs.domain, self.klass.__name__)
