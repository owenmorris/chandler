import unittest, os
import feeds
from osaf import pim
from util import testcase
from zanshin.util import blockUntil

class TestFeedImporting(testcase.SingleRepositoryTestCase):

    def runTest(self):
        self.setUp()
        self.testNonASCII()

    def testNonASCII(self):

        view = self.view

        dir = os.path.dirname(os.path.abspath(__file__))
        url = os.path.join(dir, 'japanese.rdf')

        # Use network since file:// isn't working
        url = 'http://wp.osafoundation.org/rss2'
        channel = feeds.newChannelFromURL(view, url)
        view.commit() # Make the channel available to feedsView

        print "Calling channel.update"
        blockUntil(channel.update)
        print "Back from channel.update"
        print channel

        """
        self.assertEqual(channel.displayName, u'\u8fd1\u85e4\u6df3\u4e5f\u306e\u65b0\u30cd\u30c3\u30c8\u30b3\u30df\u30e5\u30cb\u30c6\u30a3\u8ad6')

        self.assertEqual(14, len(channel))

        self.assertEqual(iter(channel).next().displayName, u'\u30b3\u30e2\u30f3\u30bb\u30f3\u30b9\u306e\u78ba\u8a8d')
        """

if __name__ == "__main__":
    # Disabling this test for the moment
    # unittest.main()
    pass
