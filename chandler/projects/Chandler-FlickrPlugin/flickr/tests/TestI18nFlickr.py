# -*- coding: utf-8 -*-
#   Copyright (c) 2004-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


""" Unit test for flickr i18n I/O """

import os, unittest
from osaf.pim.tests import TestDomainModel
from flickr import PhotoCollection, Tag, dialogs, flickr


class TestI18nFlickr(TestDomainModel.DomainModelTestCase):

    def setUp(self):
        super(TestI18nFlickr, self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'parcels', 'flickr')

        super(TestI18nFlickr, self)._openRepository(self)
        self.loadParcel("flickr")

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

        p = PhotoCollection(itsView = self.view)

        if username is not None:
            p.username = username
        elif tag is not None:
            p.tag = Tag.getTag(self.view, tag)
        else:
            self.fail("A username or tag must be passed to _testI18n()")

        try:
            col = p.fillCollectionFromFlickr(self.view)
        except flickr.FlickrError, e:
            if "api key" not in e.args[0].lower():
                raise
        else:
            self.assertTrue(self.hasKey(col, key))

    def hasKey(self, col, key):
        if col is None:
            return False

        for item in col:
            if item.displayName == key:
                return True
        return False


if __name__ == "__main__":
   unittest.main()
