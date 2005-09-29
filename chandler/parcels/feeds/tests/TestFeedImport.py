import unittest, os
import feeds
from osaf import pim
from util import testcase

class TestFeedImporting(testcase.NRVTestCase):

    def testModifiable(self):

        view = self.view

        dir = os.path.dirname(os.path.abspath(__file__))
        url = os.path.join(dir, 'japanese.rdf')

        channel = feeds.NewChannelFromURL(view, url)

        self.assertEqual(channel.displayName, u'\u8fd1\u85e4\u6df3\u4e5f\u306e\u65b0\u30cd\u30c3\u30c8\u30b3\u30df\u30e5\u30cb\u30c6\u30a3\u8ad6')

        self.assertEqual(14, len(channel))

        self.assertEqual(iter(channel).next().displayName, u'\u30b3\u30e2\u30f3\u30bb\u30f3\u30b9\u306e\u78ba\u8a8d')

if __name__ == "__main__":
    unittest.main()
