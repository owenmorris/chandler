#!bin/env python

"""Information Item
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from application.persist import Persist

from Observable import Observable
from RdfObject import RdfObject
from RdfRestriction import RdfRestriction

from RdfNamespace import dc
from RdfNamespace import chandler
# from RdfNamespace import ical

from mx.DateTime import *

# ugly hack! I can't find the type for DateTime
_datetimetype = type(now())

class InformationItem(RdfObject, Observable):
    """Information Item"""

    # Define the schema for InformationItem
    # -------------------------------------------------------------

    uri = chandler.InformationItem

    rdfs = Persist.Dict()
    
    rdfs[dc.identifier] = RdfRestriction(str, 1)
    rdfs[dc.subject] = RdfRestriction(str, 1) # dcq.SubjectSchema
    rdfs[dc.relation] = RdfRestriction(RdfObject) #InformationItem
    rdfs[chandler.linkedWith] = RdfRestriction(RdfObject) #InformationItem
    rdfs[chandler.annotatedBy] = RdfRestriction(RdfObject) #InformationItem
    rdfs[dc.title] = RdfRestriction(str, 1)
    rdfs[dc.creator] = RdfRestriction(RdfObject) #EntityItem
    rdfs[dc.date] = RdfRestriction(_datetimetype) 
    rdfs[chandler.dateCreated] = RdfRestriction(_datetimetype, 1)
    rdfs[chandler.dateModified] = RdfRestriction(_datetimetype, 1)
    rdfs[dc.description] = RdfRestriction(str, 1)
    rdfs[chandler.project] = RdfRestriction(str)
    rdfs[dc.contributor] = RdfRestriction(RdfObject) #EntityItem
    rdfs[dc.type] = RdfRestriction(str) # some enumeration?
    rdfs[dc.source] = RdfRestriction(str)
    rdfs[dc.publisher] = RdfRestriction(RdfObject) #EntityItem
    rdfs[dc.coverage] = RdfRestriction(str)
    rdfs[dc.language] = RdfRestriction(str) # some I18N type?
    rdfs[chandler.topic] = RdfRestriction(str) # dcq.SubjectSchema
    rdfs[chandler.importance] = RdfRestriction(int, 1) # some enumeration?

    def __init__(self):
        RdfObject.__init__(self)
        Observable.__init__(self)
        self.uri = str(now()) #need to generate a unique uri

    def getDateCreated(self):
        return self.getRdfAttribute(chandler.dateCreated,
                                    InformationItem.rdfs)

    def getDateModified(self):
        return self.getRdfAttribute(chandler.dateModified,
                                    InformationItem.rdfs)

    def getProjects(self):
        return self.getRdfAttribute(chandler.project,
                                    InformationItem.rdfs)

    def setProjects(self, stringlist):
        self.setRdfAttribute(chandler.project, stringlist,
                             InformationItem.rdfs)

    def getTitle(self):
        return self.getRdfAttribute(dc.title,
                                    InformationItem.rdfs)

    def setTitle(self, title):
        self.setRdfAttribute(dc.title, title,
                             InformationItem.rdfs)

    def getDescription(self):
        return self.getRdfAttribute(dc.description,
                                    InformationItem.rdfs)

    def setDescription(self, desc):
        self.setRdfAttribute(dc.description, desc,
                             InformationItem.rdfs)

    def getCreator(self):
        return self.getRdfAttribute(dc.creator,
                                    InformationItem.rdfs)

    def setCreator(self, entity):
        self.setRdfAttribute(dc.creator, entity,
                             InformationItem.rdfs)

    def getTopics(self):
        return self.getRdfAttribute(chandler.topic,
                                    InformationItem.rdfs)

    def setTopics(self, topics):
        self.setRdfAttribute(chandler.topic, topics,
                             InformationItem.rdfs)

    def getLinks(self):
        return self.getRdfAttribute(chandler.linkedWith,
                                    InformationItem.rdfs)

    def setLinks(self, linkList):
        self.setRdfAttribute(chandler.linkedWith, linkList,
                             InformationItem.rdfs)

    def getAnnotations(self):
        return self.getRdfAttribute(chandler.annotatedBy,
                                    InformationItem.rdfs)

    def setAnnotations(self, annotationList):
        self.setRdfAttribute(chandler.annotatedBy, annotationList,
                             InformationItem.rdfs)

    # Define attributes of InformationItem python objects
    # ------------------------------------------------------

    # mxDateTime
    dateCreated = property(getDateCreated)

    # mxDateTime
    dateModified = property(getDateModified)

    # list of strings (could be list of projects!)
    projects = property(getProjects, setProjects)

    # string
    title = property(getTitle, setTitle)

    # EntityItem
    creator = property(getCreator, setCreator)

    # string
    description = property(getDescription, setDescription)

    # list of strings
    topics = property(getTopics, setTopics)

    # list of InformationItems
    links = property(getLinks, setLinks)

    # list of InformationItems
    annotations = property(getAnnotations, setAnnotations)

# More open issues:
#    * are links and annotations separate lists?
#    * more or less type checking?
#    * are asserts the right way to do type checking? (assert is not the
#      right mechanism if you are testing user input, for example)
#    * mx.mxDateTime => xmlSchema date? dcq:DateScheme?

# Load the InformationItem meta information
# rdfClass = RdfClass(InformationItem)
# LocalRepository.register(rdfClass)
