#!bin/env python

"""Base classes for RDF resources in Chandler
"""

from application.persist import Persist

class RdfResource(object, Persist.Persistent):
    def __init__(self):
        pass

    
