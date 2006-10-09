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

"""
Simple Performance tests for Chandler repository
"""

import os, os.path, sys, unittest

from repository.util.Path import Path
from repository.tests.RepositoryTestCase import RepositoryTestCase
from repository.util.URL import URL
from osaf import pim
from feeds.channels import FeedChannel
import logging

logger = logging.getLogger(__name__)

# get feedparser
_chandlerDir = os.environ['CHANDLERHOME']
sys.path.append(os.path.join(_chandlerDir,'util'))
import feedparser

# get all the RSS files in RSS_HOME (repository/tests/data/rssfeeds)
# You can obtain the files from http://aloha.osafoundation.org/~twl/RSSdata/rssfeeds.syndic8.tar.bz2
RSS_HOME=os.path.join(_chandlerDir,'repository','tests','data','rssfeeds/')
if os.path.exists(RSS_HOME):
    _rssfiles = os.listdir(RSS_HOME)
else:
    _rssfiles = []

# make them file URL's
_defaultBlogs = [ "file://%s%s%s" %("", RSS_HOME, f) for f in _rssfiles ]

BASE_PATH = Path('//parcels/feeds')

class TestPerfWithRSS(RepositoryTestCase):
    """ Simple performance tests """

    def setUp(self):

        super(TestPerfWithRSS, self).setUp()
        view = self.rep.view

        # sys.path.insert(1, parcelDir)
        self.loadParcel("osaf.pim")

        view.commit()
        logger.debug("Going to try: ",len(_defaultBlogs)," feeds")

    def _stressTest(self, commitInsideLoop=False):
        """ grab a bunch of RSS data from disk and insert into the repository """
        view = self.rep.view

        itemCount = 0
        feedCount = 0
        feeds = self.__getFeeds()

        if feeds == []:
            logger.info("got no feeds")
            print "If you haven't installed the feed data, you can retrieve it from"
            print "http://aloha.osafoundation.org/~twl"
            print "select a tarball, download it, and unpack it in repository/tests/data"
            print "The data will be in a new directory called rssfeeds"
            print "You can now run the tests"
        else:
            logger.info('committing %d feeds', len(feeds))
            view.commit()
            logger.info('committed %d feeds', len(feeds))

        for feed in feeds:
            feed = view.findUUID(feed)
            logger.debug(feed.url)
            etag = feed.getAttributeValue('etag', default=None)
            lastModified = feed.getAttributeValue('lastModified', default=None)
            if lastModified:
                modified = lastModified.tuple()
            else:
                modified = None
            try:
                data = feedparser.parse(str(feed.url)[6:], etag, modified)
                feedCount += 1
                itemCount += feed.fillAttributes(data)
                if commitInsideLoop:
                    logger.info('%0.5d committing %s, %0.6d', feedCount, feed.url, itemCount)
                    view.commit()
            except Exception:
                logger.exception('While processing %s', feed.url)
                view.cancel()

        try:
#            profiler = hotshot.Profile('/tmp/TestPerfWithRss.stressTest.hotshot')
#            profiler.runcall(view.commit)
#            profiler.close()
            view.commit()
        except Exception:
            logger.exception("Final commit:")
            self.fail()

        logger.info('Processed %d items', itemCount)

        self.assert_(True)
        
    def __getFeeds(self):
        """Return a list of channel items"""
        view = self.rep.view
        chanKind = view.find(Path(BASE_PATH, 'FeedChannel'))

        feeds = []
        parent = view.find(BASE_PATH)

        for url in _defaultBlogs:
            urlhash = str(hash(url))
            item = view.find(Path(BASE_PATH, urlhash))
            if not item:
                item = FeedChannel(itsView = view)
                item.url = URL(url)
            feeds.append(item.itsUUID)

        return feeds

#    def testCommitAtEnd(self):
#        self._stressTest()

    def testCommitInsideLoop(self):
        self._stressTest(True)

    def _readItems(self, kind):
        for i in kind.iterItems(True):
            assert(i.itsName is not None)

#    def testReadBackRSS(self):
#        self._stressTest()
#        self.rep.close()
#        self.rep = DBRepository(os.path.join(self.testdir, '__repository__'))
#        self.rep.open()
#        RSSItem = self.rep.findPath('//parcels/feeds/FeedItem')
#        self._readItems(RSSItem.itsKind)
#        profiler = hotshot.Profile('/tmp/TestPerfWithRss.readBack.hotshot')
#        profiler.runcall(TestPerfWithRSS._readItems, self, RSSItem.itsKind)
#        profiler.close()

    def tearDown(self):
        self.rep.close()
        if os.path.exists(self.rep.dbHome):
            self.rep.delete()
        else:
            logger.warn("no repository at %s", self.rep.dbHome)
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestPerfWithRss.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
