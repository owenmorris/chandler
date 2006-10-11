#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


import unittest, os, time
from feeds.channels import FeedChannel, FeedItem
from osaf import pim
from repository.util.URL import URL
from util import testcase, indexes
from zanshin.util import blockUntil
from application import Utility, schema
from twisted.internet import reactor

class TestFeedIndexing(testcase.SingleRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.ImportFeed()

    def ImportFeed(self):

        view = self.view

        dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir, "osaf.blog.rss")

        data = file(path).read()

        channel = FeedChannel(itsView=view)
        count = channel.parse(data)

        self.assertEqual(channel.displayName, "OSAF News")
        self.assertEqual(5, len(channel))

        # Test successful lookup
        url = URL("http://www.osafoundation.org/archives/000966.html")
        item = indexes.valueLookup(channel, "link", "link", url)
        self.assertEqual(item.displayName, "OSAF Welcomes Priscilla Chung")

        # Test unsuccessful lookup
        nonExistent = URL("http://www.osafoundation.org/nonexistent/")
        item = indexes.valueLookup(channel, "link", "link", nonExistent)
        self.assertEqual(item, None)

        # Although the channels module doesn"t allow duplicate links, let"s
        # test the lookup mechanism"s ability to return dupes.  We"ll add a
        # duplicate, then pass the "multiple=True" arg to indexLookup.

        url = URL("http://www.osafoundation.org/archives/000964.html")
        item = FeedItem(itsView=view, link=url)
        channel.add(item)

        items = indexes.valueLookup(channel, "link", "link", url, multiple=True)
        self.assertEqual(len(items), 2)

if __name__ == "__main__":
    unittest.main()
