#!bin/env python

"""Classes test Chandler model objects
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest

from EventItem import EventItem
from TaskItem import TaskItem
from PersonItem import PersonItem
from PlaceItem import PlaceItem

from sample_data import ItemDict

class BasicEventTest(unittest.TestCase):
    def testEmptyFields(self):
        event = EventItem()
        self.assertEqual(event.headline, None)
        self.assertEqual(event.startTime, None)
        self.assertEqual(event.endTime, None)
        self.assertEqual(event.duration, None)
        
class BasicTaskTest(unittest.TestCase):
    def testEmptyFields(self):
        task = TaskItem()
        self.assertEqual(task.title, None)
        self.assertEqual(task.calendarDate, None)
        self.assertEqual(task.dateDueBy, None)
        
class BasicPersonTest(unittest.TestCase):
    def testEmptyFields(self):
        person = PersonItem()
        self.assertEqual(person.firstName, None)
        self.assertEqual(person.lastName, None)
        self.assertEqual(person.abbreviation, None)
        self.assertEqual(person.phone, None)
        
class BasicPlaceTest(unittest.TestCase):
    def testEmptyFields(self):
        place = PlaceItem()
        self.assertEqual(place.address, None)
        self.assertEqual(place.locationDescription, None)
        self.assertEqual(place.name, None)
        self.assertEqual(place.abbreviation, None)
        
class EventObserver:
    def __init__(self, headline):
        self.headline = headline
        
    def notify(self, event):
        self.headline = event.headline
        
class EventObserverTest(unittest.TestCase):
    def testNotification(self):
        observer_1 = EventObserver("headline_1")
        observer_2 = EventObserver("headline_2")
        
        self.assertNotEqual(observer_1.headline, observer_2.headline)
        
        event = EventItem()
        event.registerObserver(observer_1)
        event.registerObserver(observer_2)
        event.headline = "new headline"
        event.notifyObservers()
        
        self.assertEqual(event.headline, observer_1.headline)
        self.assertEqual(event.headline, observer_2.headline)

class SampleDataTest(unittest.TestCase):
    def testDictionary(self):
        event1 = ItemDict['event1']
        event2 = ItemDict['event2']
        event3 = ItemDict['event3']
        person1 = ItemDict['person1']
        person2 = ItemDict['person2']

        self.assertEqual(event1.startTime.year, 2002)
        self.assertEqual(event1.startTime.month, 11)
        self.assertEqual(event1.startTime.day, 6)
        self.assertEqual(event1.startTime.hour, 10)
        self.assertEqual(event1.duration.hours, 4)

        self.assertEqual(event2.relation, person1)
        self.assertEqual(event2.headline, 'Dinner with Gina')
        self.assertEqual(event2.relation.fullName, 'Gina Durante')

if __name__ == "__main__":
    unittest.main()


        

