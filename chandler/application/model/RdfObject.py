#!bin/env python

"""Base classes for RDF objects in Chandler
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from persistence.dict import PersistentDict

from RdfResource import RdfResource

class RdfObject(RdfResource):
    """Base class for any RDF model object in Chandler"""

    # Define the schema by creating a dictionary (rdfs) on the class.
    # The keys to the dictionary are the property URLs, the values are
    # the types of the expected as values of the properties.
    #
    # By defining InformationItem (the python class), we're defining a
    # 'rdfs:Class' in the chandler namespace. With the properties dictionary,
    # we are associating properties in various namespaces with the
    # InformationItem class, or adding to the 'rdfs:domain' of these
    # properties. The value/types of the properties dictionary define
    # the 'range' of the properties, in the context of this class.
    #
    # A note about cardinality: many of these properties should be
    # able to have multiple entries. In this case, we would expect
    # a list of objects of the listed type in the dictionary of the
    # instance. We are not currently specifying cardinality here in
    # the schema definition.
    #
    # Properties are referenced using the RdfNamespace python object.
    # It currently generates the url for the property in the form of a
    # string. We may want to change it to generate a URL object, or a
    # RdfProperty object.
    #
    # Alternatively, we could define the schema in a data file. Bootstrap
    # code could read the file and generate the schema in memory,
    # associating the InformationItem python class with the class defined
    # in the data file. We could use any one of a number of standard
    # notations: RDF/XML, N3, N-Triple, etc.
    #
    # Open issues:
    #   * Do we want to define a default value?
    #   * Do we need to specify cardinality?
    #   * Should the schema definition remain in the python code?
    #   * Where do we define properties?

    # @@@ not used
    # rdfs = PersistentDict()

    def __init__(self):
        RdfResource.__init__(self)

        # stores the rdf property/values for the object
        # each entry in the dictionary represents a triple
        # (self, key, value)
        self.rdf = PersistentDict()
        self.rdfClass = None

    def getRdfAttribute(self, url, rdfs):
        restriction = rdfs[url]
        
        if restriction.isRequired:
            value = self.rdf[url]
        else:
            value = self.rdf.get(url, restriction.default)

        assert(restriction.isValid(value))
        return value

    def setRdfAttribute(self, url, value, rdfs):
        restriction = rdfs[url]
        assert(restriction.isValid(value))
        self.rdf[url] = value

    def printTriples(self):
        """Scaffolding, just to give a taste"""
        for key in self.rdf.keys():
            print (self.url, key, self.rdf[key]) 

