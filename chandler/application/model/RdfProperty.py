#!bin/env python

from RdfResource import RdfResource
from RdfNamespace import rdf

class RdfProperty(RdfResource):
    def __init__(self, uri):
        RdfResource.__init__(self)
        self.uri = uri

    def printTriples(self):
        """Scaffolding, just to give a taste of what the class can do"""
        print (uri, rdf.type, rdf.property)


        

