#!bin/env python

""" Loads sample data -- until db is worked out
"""

# ------------------------------------------------
# Temporary data for initial running purposes:
# would normally be found in db or rdf

from mx.DateTime import *
from PersonItem import PersonItem
from EventItem import EventItem

_rdfItems = ((PersonItem, {'firstName':'Gina',
                           'lastName':'Durante',
                           'identifier':'person1'}),
             
             (PersonItem, {'firstName':'Nick',
                           'lastName':'Parlante',
                           'abbreviation':'NP',
                           'identifier':'person2'}),
             
             (PersonItem, {'firstName':'Al',
                           'lastName':'Cho',
                           'identifier':'person3'}),
             
             (PersonItem, {'firstName':'Morgen',
                           'lastName':'Sagen',
                           'identifier':'person4'}),
             
             (EventItem, {'headline':'OSAF meeting',
                          'startTime':(2002, 11, 6, 10, 0),
                          'endTime':(2002, 11, 6, 14, 0),
                          'identifier':'event1',
                          'relation':'person3'}),
             
             (EventItem, {'headline':'Dinner with Gina',
                          'startTime':(2002, 11, 7, 18, 0),
                          'endTime':(2002, 11, 7, 21, 0),
                          'identifier':'event2',
                          'relation':'person1'}),
             
             (EventItem, {'headline':'Call Dad',
                          'startTime':(2002, 11, 8, 15, 0),
                          'endTime':(2002, 11, 8, 15, 30),
                          'identifier':'event3'}),
             
             (EventItem, {'headline':'Work on Chandler',
                          'startTime':(2002, 11, 4, 8, 30),
                          'endTime':(2002, 11, 4, 11, 30),
                          'identifier':'event4'}))

ItemDict = {}
for itemData in _rdfItems:
    cls = itemData[0]
    item = cls()
    properties = itemData[1]
    id = properties['identifier']
    for key in properties.keys():
        if key == 'relation':
            setattr(item, key, ItemDict[properties[key]])
        elif key == 'startTime' or key == 'endTime':
            year, month, day, min, sec = properties[key]
            setattr(item, key, DateTime(year, month, day, min, sec))
        else:
            setattr(item, key, properties[key])

    ItemDict[id] = item





