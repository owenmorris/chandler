"""Namespaces: Useful namespaces in an easy to access form

Scaffolding, to allow a clean notation for accessing names of
KindOfThing's or Attributes.

Inspired by TRAMP (http://www.aaronsw.com/2002/tramp)
"""

__revision__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

class Namespace(object):
    """A class that allows the client to express URLs easily in python

    Example: dc.title => 'http://purl.org/dc/elements/1.1/title'
    """

    def __init__(self, prefix):
        self.prefix = prefix

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError
        return self.prefix + name

    def __getitem__(self, name):
        return self.prefix + name

        
# Rdf and schema namespaces
rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
daml = Namespace('http://www.daml.org/2001/03/daml+oil#')

# Onotolgy namespaces
dc = Namespace('http://purl.org/dc/elements/1.1/')
foaf = Namespace('http://xmlns.com/foaf/0.1/')
chandler = Namespace('http://www.osafoundation.org/2003/')
