#!bin/env python

"""Rdf Namespaces: Useful namespaces in an easy to access form

Scaffolding, to allow the RdfObject subclasses to use a clean notation
when referring to RDF properties.

Inspired by TRAMP (http://www.aaronsw.com/2002/tramp)
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

class RdfNamespace(object):
    """A class that allows the client to express URIs easily in python

    Example: dc.title => 'http://purl.org/dc/elements/1.1/title'
    """

    def __init__(self, prefix):
        self.prefix = prefix

    def __getattr__(self, name):
        return self.prefix + name

    def __getitem__(self, name):
        return self.prefix + name

        
# Rdf and schema namespaces
rdf = RdfNamespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
rdfs = RdfNamespace('http://www.w3.org/2000/01/rdf-schema#')
daml = RdfNamespace('http://www.daml.org/2001/03/daml+oil#')

# Onotolgy namespaces
dc = RdfNamespace('http://purl.org/dc/elements/1.1/')
foaf = RdfNamespace('http://xmlns.com/foaf/0.1/')
chandler = RdfNamespace('http://www.osafoundation.org/2002/')

