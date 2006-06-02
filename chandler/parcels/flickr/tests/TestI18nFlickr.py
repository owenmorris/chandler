# -*- coding: utf-8 -*-
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

""" Unit test for flickr i18n I/O """

import unittest
from osaf.pim.tests import TestDomainModel
import flickr
import os



class TestI18nFlickr(TestDomainModel.DomainModelTestCase):

    def setUp(self):
        super(TestI18nFlickr, self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'parcels', 'flickr')

        super(TestI18nFlickr, self)._openRepository(self)
        self.loadParcel("flickr")
        self.view = self.rep.view


    def testI18nOwner(self):
        #Ensure that "trünk"is the displayName for
        #a photo for username "osaftestüser"
        #This tests both that the flickr module correctly converts
        #username "osaftestüser" to bytes on the outbound request to
        #the flickr server and that the module correctly converts
        #the photo title "trünk" from bytes to unicode on the inbound
        #response from the server
        #return self._testI18n(username=u"osaftestüser", key=u"trünk")
        pass

    def testI18nTag(self):
        #Ensure that "trünk"is the displayName for
        #a photo for tag "?~B??~C??~C??~B??~C??~A~J?~W?~C~E?| ? "
        #This tests both that the flickr module correctly converts
        #tag "?~B??~C??~C??~B??~C??~A~J?~W?~C~E?| ? " to bytes on the outbound request to
        #the flickr server and that the module correctly converts
        #the photo title "trünk" from bytes to unicode on the inbound
        #response from the server

        #XXX This is a place holder search on tags to test that the application
        #logic is correct. The actual test is commented out because
        #the tag is awaiting promotion to public flickr by
        #the flickr staff.
        #
        #Once that takes place the search on tag  "?~B??~C??~C??~B??~C??~A~J?~W?~C~E?| ? "
        #will be uncommented
        #return self._testI18n(tag=u"hawaii", key=u"Green Sand Beach")
        #return self._testI18n(tag=u"オンライン�得情報 ", key=u"trünk")
        pass

    def _testI18n(self, key=None, username=None, tag=None):
        if not self.isOnline():
            return

        self.assertNotEquals(key, None)

        p = flickr.PhotoCollection(itsView = self.view)

        if username is not None:
            p.username = username
        elif tag is not None:
            p.tag = flickr.Tag.getTag(self.view, tag)
        else:
            self.fail("A username or tag must be passed to the _testI18n method")

        col = p.fillCollectionFromFlickr(self.view)
        self.assertTrue(self.hasKey(col, key))


    def hasKey(self, col, key):
        if col is None:
            return False

        for item in col:
            if item.getItemDisplayName() == key:
                return True
        return False


if __name__ == "__main__":
   unittest.main()
