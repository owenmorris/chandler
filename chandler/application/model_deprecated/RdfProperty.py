#!bin/env python

from RdfResource import RdfResource
from RdfNamespace import rdf

class RdfProperty(RdfResource):
    def __init__(self, url):
        RdfResource.__init__(self)
        self.url = url

    def printTriples(self):
        """Scaffolding, just to give a taste of what the class can do"""
        print (url, rdf.type, rdf.property)


        

