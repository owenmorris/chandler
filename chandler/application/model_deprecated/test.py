#!bin/env python

# Exercise the api

from LocalRepository import LocalRepository
from RdfClass import RdfClass

from InformationItem import InformationItem
from EventItem import EventItem

# Get the local repository (will get a 'borg')
lr = LocalRepository()

# Add schema data to the repository for InformationItems
classes = [RdfClass(InformationItem), RdfClass(EventItem)]
for classObject in classes:
    lr.addClass(classObject)

# Print schema triples from the repository
lr.printSchemaTriples()

# Create an information item -- rdf object
infoItem = InformationItem()
lr.addObject(infoItem)

infoItem.title = 'hello world!'
infoItem.projects = ['osaf']

# Create an event item
eventItem = EventItem()
lr.addObject(eventItem)

eventItem.headline = 'meeting with someone'
eventItem.title = 'meeting with someone'

# Print only data triples
lr.printDataTriples()

