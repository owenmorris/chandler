#!bin/env python

# May be superfluous, the class really knows all about its state

from RdfResource import RdfResource
from RdfNamespace import rdf, rdfs

class RdfClass(RdfResource):
    def __init__(self, klass):
        RdfResource.__init__(self)

        self.name = klass.__name__
        self.url = klass.url
        self.rdfs = klass.rdfs

    def __init__(self, name, url):
        RdfResource.__init__(self)

        self.name = name
        self.url = url
        self.rdfs = PersistentDict()

    def addProperty(self, property, restriction):
        self.rdfs[property] = restriction

    def printTriples(self):
        """Scaffolding, just to give a taste"""
        print (self.url, rdf.type, rdfs.Class)

        for key in self.rdfs.keys():
            print (key, rdfs.domain, self.name)
