#!bin/env python

"""Basic tests for the EventItem class
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, sys

from application.model.EventItem import EventItem

class TestEmptyProperties(unittest.TestCase):
    """Set of tests that look at empty properties on an Event Item"""
    
    def setUp(self):
        self.item = EventItem()

    def tearDown(self):
        pass
    
    def testEmptyStartTime(self):
        """Look at empty startTime property"""
        self.assertEqual(self.item.startTime, None)
        self.assertEqual(self.item.getStartTime(), None)

    def testEmptyEndTime(self):
        """Look at empty endTime property"""
        self.assertEqual(self.item.endTime, None)
        self.assertEqual(self.item.getEndTime(), None)

    def testEmptyDuration(self):
        """Look at empty duration property"""
        self.assertEqual(self.item.duration, None)
        self.assertEqual(self.item.getDuration(), None)

    def testEmptyHeadline(self):
        """Loot at empty headline property"""
        self.assertEqual(self.item.headline, None)
        self.assertEqual(self.item.getHeadline(), None)

    def testEmptyRecurrence(self):
        """Look at empty recurrence property"""
        self.assertEqual(self.item.recurrence, None)
        self.assertEqual(self.item.getRecurrence(), None)

    def testEmptyReminders(self):
        """Look at empty reminders property (list)"""
        self.assertEqual(self.item.reminders, None)
        self.assertEqual(self.item.getReminders(), None)

    def testEmptyTimeTransparency(self):
        """Look at time transparency property"""
        self.assertEqual(self.item.timeTransparency, None)
        self.assertEqual(self.item.getTimeTransparency(), None)

    def testEmptyParticipants(self):
        """Look at participants property (list)"""
        self.assertEqual(self.item.participants, None)
        self.assertEqual(self.item.getParticipants(), None)

    def testEmptyLocations(self):
        """Look at locations property (list)"""
        self.assertEqual(self.item.locations, None)
        self.assertEqual(self.item.getLocations(), None)

    def testEmptyCalendars(self):
        """Look at calendars property (list)"""
        self.assertEqual(self.item.calendars, None)
        self.assertEqual(self.item.getCalendars(), None)

class TestSetProperties(unittest.TestCase):
    """Set of tests that set properties on an EventItem.
    (Each test looks to see that each property was set correctly.)"""

    def setUp(self):
        self.item = EventItem()

    def tearDown(self):
        pass

    def testSetHeadline(self):
        """Set the headline property, look to make sure it was set."""
        testHeadline = 'Test Headline For EventItem'
        self.item.headline = testHeadline
        self.assertEqual(self.item.headline, testHeadline)
        self.assertEqual(self.item.getHeadline(), testHeadline)

class TestInformationItem(unittest.TestCase):
    """Set of tests to exercise InformationItem methods (superclass)"""

    def testEmptyProperties(self):
        """Test a few InformationItem properties to make sure they work."""
        item = EventItem()
        self.assertEqual(item.description, None)
        self.assertEqual(item.getTopics(), None)
        self.assertEqual(item.links, None)

    def testSetProperties(self):
        """Test setting a few InformationItem properties"""
        item = EventItem()

        # title
        testTitle = 'Test Title for EventItem'
        item.title = testTitle
        self.assertEqual(item.title, testTitle)
        self.assertEqual(item.getTitle(), testTitle)

        # a list
        topicList = ['foo', 'bar']
        item.topics = topicList
        self.assertEqual(item.topics, topicList)
        self.assertEqual(item.getTopics(), topicList)
        
def shellTest():
    unittest.main()

if __name__ == "__main__":
    unittest.main()
