#!bin/env python

"""Basic tests for the InformationItem class
"""

__author__ = "Katie Capps Parlante"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "OSAF"

import unittest, sys

# hack to be able to run with hardhat, figure out something better
sys.path.append('c:\osaf\osaf\chandler\Chandler')

from application.model.InformationItem import InformationItem
from application.model.RdfRestriction import RdfRestriction

class TestEmptyProperties(unittest.TestCase):
    """Set of tests that look at empty properties on an InformationItem"""
    
    def setUp(self):
        self.item = InformationItem()

    def tearDown(self):
        pass
    
    def testEmptyDateCreated(self):
        """Look at empty dateCreated property"""
        self.assertEqual(self.item.dateCreated, None)
        self.assertEqual(self.item.getDateCreated(), None)

    def testEmptyDateModified(self):
        """Look at empty dateModified property"""
        self.assertEqual(self.item.dateModified, None)
        self.assertEqual(self.item.getDateModified(), None)

    def testEmptyProjects(self):
        """Look at empty projects property (list)"""
        self.assertEqual(self.item.projects, None)
        self.assertEqual(self.item.getProjects(), None)

    def testEmptyTitle(self):
        """Look at empty title property"""
        self.assertEqual(self.item.title, None)
        self.assertEqual(self.item.getTitle(), None)

    def testEmptyDescription(self):
        """Look at empty description property"""
        self.assertEqual(self.item.description, None)
        self.assertEqual(self.item.getDescription(), None)

    def testEmptyCreator(self):
        """Look at empty creator property"""
        self.assertEqual(self.item.creator, None)
        self.assertEqual(self.item.getCreator(), None)

    def testEmptyTopics(self):
        """Look at empty topics property (list)"""
        self.assertEqual(self.item.topics, None)
        self.assertEqual(self.item.getTopics(), None)

    def testEmptyLinks(self):
        """Look at empty links property (list)"""
        self.assertEqual(self.item.links, None)
        self.assertEqual(self.item.getLinks(), None)

    def testEmptyAnnotations(self):
        """ Look at empty annotations property (list)"""
        self.assertEqual(self.item.annotations, None)
        self.assertEqual(self.item.getAnnotations(), None)

class TestSetProperties(unittest.TestCase):
    """Set of tests that set properties on an InformationItem.
    (Each test looks to see that each property was set correctly.)"""
    
    def setUp(self):
        self.item = InformationItem()

    def tearDown(self):
        pass

    def testSetTitle(self):
        """Set the title property, look to make sure it was set."""
        testTitle = 'Test Title For InformationItem'
        self.item.title = testTitle
        self.assertEqual(self.item.title, testTitle)
        self.assertEqual(self.item.getTitle(), testTitle)

    def testSetDescription(self):
        """Set the description property, look to make sure it was set."""
        testDesc = 'Test Description for InformationItem'
        self.item.description = testDesc
        self.assertEqual(self.item.description, testDesc)
        self.assertEqual(self.item.getDescription(), testDesc)

    def testSetTopics(self):
        """Set the topics property (list), look to make sure it was set."""
        topicList = ['foo', 'bar']
        self.item.topics = topicList
        self.assertEqual(self.item.topics, topicList)
        self.assertEqual(self.item.getTopics(), topicList)

class TestSetRdf(unittest.TestCase):
    """Set of tests to check that one can set the rdf directly."""
    
    def setUp(self):
        self.item = InformationItem()

    def tearDown(self):
        pass

class TestRdfOnTheFly(unittest.TestCase):
    """Test to check that the InformationItem behaves like any RdfObject,
    able to add rdf on the fly."""
    
    def testAddRdf(self):
        """Test adding random rdf property at runtime"""

        # set up the test
        item = InformationItem()
        propertyUri = 'sample_uri'
        propertyValue = 'foo'

        # add the rdf property to the rdf dictionary
        item.rdf[propertyUri] = propertyValue

        # look to see that the property was set on the dictionary
        self.assertEqual(item.rdf[propertyUri], propertyValue)

    def testAddRdfs(self):
        """Test adding random rdf property to schema at runtime"""

        # set up the test
        item = InformationItem()
        propertyUri = 'sample_uri'
        propertyValue = 'foo'
        propertyRestriction = RdfRestriction(str, 1)

        # add the schema property restriction to the class rdfs dictionary
        InformationItem.rdfs[propertyUri] = propertyRestriction

        # add the property to the instance
        item.setRdfAttribute(propertyUri, propertyValue, InformationItem.rdfs)

        # look up the property on the instance and check its value
        self.assertEqual(item.getRdfAttribute(propertyUri,
                                              InformationItem.rdfs),
                         propertyValue)

if __name__ == "__main__":
    unittest.main()
    
