#!bin/env python

"""InformationItem is the base item class in Chandler.

Subclasses include EventItem, PersonItem, DocumentItem, NoteItem, etc.
InformationItem groups together many of the dublin core attributes, as well
as other common attributes.
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

from persistence.dict import PersistentDict

from Observable import Observable
from RdfObject import RdfObject
from RdfRestriction import RdfRestriction

from RdfNamespace import dc
from RdfNamespace import chandler

from mx.DateTime import *

# ugly hack! I can't find the type for DateTime
_DateTimeType = type(now())

# forward declarations, so that the types can be used
# in InformationItem's RdfRestrictions
class InformationItem:
    pass

class EntityItem:
    pass

class InformationItem(RdfObject, Observable):
    """Information Item"""

    # The uri for the InformationItem class: might want to do this
    # differently
    uri = chandler.InformationItem

    # Define the schema for InformationItem
    # -------------------------------------------------------------
    # Note: recursive references to InformationItem (via EntityItem as
    # well) prevent using InformationItem and EntityItem types -- need
    # to fix this somehow. Perhaps we'll need to use strings instead of
    # types.

    rdfs = PersistentDict()
    
    rdfs[dc.identifier] = RdfRestriction(str, 1)
    rdfs[dc.subject] = RdfRestriction(str, 1) # dcq.SubjectSchema
    rdfs[dc.relation] = RdfRestriction(InformationItem)
    rdfs[chandler.linkedWith] = RdfRestriction(InformationItem)
    rdfs[chandler.annotatedBy] = RdfRestriction(InformationItem)
    rdfs[dc.title] = RdfRestriction(str, 1)
    rdfs[dc.creator] = RdfRestriction(EntityItem)
    rdfs[dc.date] = RdfRestriction(_DateTimeType) 
    rdfs[chandler.dateCreated] = RdfRestriction(_DateTimeType, 1)
    rdfs[chandler.dateModified] = RdfRestriction(_DateTimeType, 1)
    rdfs[dc.description] = RdfRestriction(str, 1)
    rdfs[chandler.project] = RdfRestriction(RdfObject) #ProjectItem 
    rdfs[dc.contributor] = RdfRestriction(EntityItem)
    rdfs[dc.type] = RdfRestriction(str) # some enumeration?
    rdfs[dc.source] = RdfRestriction(str)
    rdfs[dc.publisher] = RdfRestriction(EntityItem)
    rdfs[dc.coverage] = RdfRestriction(str)
    rdfs[dc.language] = RdfRestriction(str) # some I18N type?
    rdfs[chandler.topic] = RdfRestriction(str) # dcq.SubjectSchema
    rdfs[chandler.importance] = RdfRestriction(int, 1) # some enumeration?

    def __init__(self):
        RdfObject.__init__(self)
        Observable.__init__(self)
        self.uri = str(now()) #need to generate a unique uri

    # Define attributes of InformationItem python objects
    # ------------------------------------------------------

    def getDateCreated(self):
        """Returns date/time the item was created"""
        return self.getRdfAttribute(chandler.dateCreated,
                                    InformationItem.rdfs)

    # mxDateTime
    dateCreated = property(getDateCreated,
                           doc='mxDateTime: creation date/time of the item')

    def getDateModified(self):
        """Returns date/time the item was last modified"""
        return self.getRdfAttribute(chandler.dateModified,
                                    InformationItem.rdfs)

    # mxDateTime
    dateModified = property(getDateModified,
                            doc='mxDateTime: last modified date/time')

    def getProjects(self):
        """Returns a list of ProjectItems.
        This item is related to these projects.
        """
        return self.getRdfAttribute(chandler.project,
                                    InformationItem.rdfs)

    def setProjects(self, stringlist):
        """Set the list of projects this item is related to.
        Expects a Persist.List() containing ProjectItems.
        """
        self.setRdfAttribute(chandler.project, stringlist,
                             InformationItem.rdfs)

    # list of ProjectItems
    projects = property(getProjects, setProjects,
                        doc='Persistent list of related ProjectItems')

    def getTitle(self):
        """Returns the item's title, a string"""
        return self.getRdfAttribute(dc.title,
                                    InformationItem.rdfs)

    def setTitle(self, title):
        """Sets the item's title, expects a string"""
        self.setRdfAttribute(dc.title, title,
                             InformationItem.rdfs)

    # string
    title = property(getTitle, setTitle,
                     doc='string: the title of the item')

    def getDescription(self):
        """Returns a string, a description of the item"""
        return self.getRdfAttribute(dc.description,
                                    InformationItem.rdfs)

    def setDescription(self, desc):
        """Sets the description of the item, expects a string."""
        self.setRdfAttribute(dc.description, desc,
                             InformationItem.rdfs)

    # string
    description = property(getDescription, setDescription,
                           doc='string: a description of the item')

    def getCreator(self):
        """Returns an EntityItem, a person or organization."""
        return self.getRdfAttribute(dc.creator,
                                    InformationItem.rdfs)

    def setCreator(self, entity):
        """Expects an EntityItem, the creator of the item"""
        self.setRdfAttribute(dc.creator, entity,
                             InformationItem.rdfs)

    # EntityItem
    creator = property(getCreator, setCreator,
                       doc='EntityItem: dublin core creator')

    def getTopics(self):
        """Returns a list of strings, representing topics (like categories)"""
        return self.getRdfAttribute(chandler.topic,
                                    InformationItem.rdfs)

    def setTopics(self, topics):
        """Sets the list of topics the item is related to.
        Expects a Persist.List containing strings."""
        self.setRdfAttribute(chandler.topic, topics,
                             InformationItem.rdfs)

    # list of strings
    topics = property(getTopics, setTopics,
                      doc='Persistent list of strings: related topics')


    def getLinks(self):
        """Returns a list of related InformationItems"""
        return self.getRdfAttribute(chandler.linkedWith,
                                    InformationItem.rdfs)

    def setLinks(self, linkList):
        """Sets a list of InformationItems related to this item.
        Expects a Persist.List containing InformationItems"""
        self.setRdfAttribute(chandler.linkedWith, linkList,
                             InformationItem.rdfs)

    # list of InformationItems
    links = property(getLinks, setLinks,
                     doc='Persistent list of InformationItems: related items')

    def getAnnotations(self):
        """Returns a list of InformationItems that annotate this item."""
        return self.getRdfAttribute(chandler.annotatedBy,
                                    InformationItem.rdfs)

    def setAnnotations(self, annotationList):
        """Sets a list of InformationItems to annotate this item.
        Expects a Persist.List containing InformationItems."""
        self.setRdfAttribute(chandler.annotatedBy, annotationList,
                             InformationItem.rdfs)

    # list of InformationItems
    annotations = property(getAnnotations, setAnnotations,
                           doc='Persistent list of InformationItems')

# More open issues:
#    * are links and annotations separate lists?
#    * more or less type checking?
#    * are asserts the right way to do type checking? (assert is not the
#      right mechanism if you are testing user input, for example)
#    * mx.mxDateTime => xmlSchema date? dcq:DateScheme?

# Load the InformationItem meta information
# rdfClass = RdfClass(InformationItem)
# LocalRepository.register(rdfClass)
