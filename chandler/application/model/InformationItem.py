#!bin/env python

"""Base classes for RDF objects in Chandler
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "Python"

from RdfModel import RdfObject, ObservableItem

class InformationItem(RdfObject, ObservableItem):
    """Base class for objects that can be viewed in tables"""
    
    def __init__(self):
        RdfObject.__init__(self)
        ObservableItem.__init__(self)
        self.identifier = None
        self.subject = None
        self.relation = None
        self.content = None
        self.dateCreated = None
        self.dateModified = None
        self.creator = None
        self.date = None
        self.description = None
        self.title = None
        self.project = None
