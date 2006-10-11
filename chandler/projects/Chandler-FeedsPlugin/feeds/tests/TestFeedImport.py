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
from feeds.channels import FeedChannel, FETCH_FAILED, FETCH_NOCHANGE, FETCH_UPDATED
from osaf import pim
from util import testcase, indexes
from zanshin.util import blockUntil
from application import Utility, schema
from twisted.internet import reactor

class TestFeedImporting(testcase.SingleRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.RemoteFeed()
        self.NonASCII()

    def RemoteFeed(self):

        Utility.initTwisted()

        view = self.view

        url = u"http://wp.osafoundation.org/rss2"
        url = str(url)
        view.refresh(notify=False)
        channel = FeedChannel(itsView=view)
        channel.displayName = url
        channel.url = channel.getAttributeAspect("url", "type").makeValue(url)
        view.commit() # Make the channel available to feedsView
        status = blockUntil(channel.refresh)
        view.refresh()

        # Only bother checking if the fetch was successful.  If there is a
        # timeout or other network problem, that shouldn"t fail the test.
        if status == FETCH_UPDATED:
            self.assertEqual(channel.displayName,
                "Open Source Applications Foundation Blog")

    def NonASCII(self):

        view = self.view

        dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(dir, "japanese.rdf")

        data = file(path).read()

        channel = FeedChannel(itsView=view)
        count = channel.parse(data)

        self.assertEqual(channel.displayName, u"\u8fd1\u85e4\u6df3\u4e5f\u306e\u65b0\u30cd\u30c3\u30c8\u30b3\u30df\u30e5\u30cb\u30c6\u30a3\u8ad6")

        self.assertEqual(14, len(channel))
        url = "http://blog.japan.cnet.com/kondo/archives/002364.html"
        item = indexes.valueLookup(channel, "link", "link", url)
        self.assertEqual(item.displayName, u"\u30b3\u30e2\u30f3\u30bb\u30f3\u30b9\u306e\u78ba\u8a8d")

if __name__ == "__main__":
    unittest.main()
