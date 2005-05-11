"""
Simple Performance tests for Chandler repository
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, sys, unittest

from bsddb.db import DBNoSuchFileError
from repository.util.Path import Path
from repository.item.Query import KindQuery
from repository.tests.RepositoryTestCase import RepositoryTestCase
from osaf.examples.zaobao.RSSData import RSSChannel

# get Zaobao's feedparser
_chandlerDir = os.environ['CHANDLERHOME']
sys.path.append(os.path.join(_chandlerDir,'parcels','osaf','examples','zaobao'))
import feedparser

# get all the RSS files in RSS_HOME (repository/tests/data/rssfeeds)
# You can obtain the files from http://aloha.osafoundation.org/~twl/RSSdata/rssfeeds.syndic8.tar.bz2
RSS_HOME=os.path.join(_chandlerDir,'repository','tests','data','rssfeeds/')
if os.path.exists(RSS_HOME):
    _rssfiles = os.listdir(RSS_HOME)
else:
    _rssfiles = []

# make them file URL's
_defaultBlogs = [ "%s%s%s" %("", RSS_HOME, f) for f in _rssfiles ]

BASE_PATH = Path('//parcels/osaf/examples/zaobao/schema')

class TestPerfWithRSS(RepositoryTestCase):
    """ Simple performance tests """

    def setUp(self):

        super(TestPerfWithRSS, self).setUp()

        # sys.path.insert(1, parcelDir)
        self.loadParcel("http://osafoundation.org/parcels/osaf/examples/zaobao")

        self.rep.commit()
        self.rep.logger.debug("Going to try: ",len(_defaultBlogs)," feeds")

    def _stressTest(self, commitInsideLoop=False):
        """ grab a bunch of RSS data from disk and insert into the repository """
        repository = self.rep

        itemCount = 0
        feedCount = 0
        feeds = self.__getFeeds()

        if feeds == []:
            self.rep.logger.info("got no feeds")
            print "If you haven't installed the feed data, you can retreive it from"
            print "http://aloha.osafoundation.org/~twl"
            print "select a tarball, download it, and unpack it in repository/tests/data"
            print "The data will be in a new directory called rssfeeds"
            print "You can now run the tests"
        else:
            self.rep.logger.info('committing %d feeds', len(feeds))
            self.rep.commit()
            self.rep.logger.info('committed %d feeds', len(feeds))

        for feed in feeds:
            feed = self.rep.findUUID(feed)
            self.rep.logger.debug(feed.url)
            etag = feed.getAttributeValue('etag', default=None)
            lastModified = feed.getAttributeValue('lastModified', default=None)
            if lastModified:
                modified = lastModified.tuple()
            else:
                modified = None
            try:
                data = feedparser.parse(feed.url, etag, modified)
                itemCount += len(data['items'])
                feedCount += 1
                feed.Update(data)
                if commitInsideLoop:
                    self.rep.logger.info('%0.5d committing %s, %0.6d',
                                         feedCount, feed.url, itemCount)
                    repository.commit()
            except Exception:
                self.rep.logger.exception('While processing %s', feed.url)
                self.rep.cancel()

        try:
#            profiler = hotshot.Profile('/tmp/TestPerfWithRss.stressTest.hotshot')
#            profiler.runcall(repository.commit)
#            profiler.close()
            repository.commit()
        except Exception:
            self.rep.logger.exception("Final commit:")
            self.fail()

        self.rep.logger.info('Processed %d items', itemCount)

        self.assert_(True)
        
    def __getFeeds(self):
        """Return a list of channel items"""
        repository = self.rep
        chanKind = repository.find(Path(BASE_PATH, 'RSSChannel'))

        feeds = []
        parent = repository.find(BASE_PATH)

        for url in _defaultBlogs:
            urlhash = str(hash(url))
            item = repository.find(Path(BASE_PATH, urlhash))
            if not item:
                item = RSSChannel(view = repository.view)
                item.url = url
            feeds.append(item.itsUUID)

        return feeds

#    def testCommitAtEnd(self):
#        self._stressTest()

    def testCommitInsideLoop(self):
        self._stressTest(True)

    def _readItems(self, kind):
        items = KindQuery().run([kind]) 
        for i in items:
            assert(i.itsName is not None)

#    def testReadBackRSS(self):
#        self._stressTest()
#        self.rep.close()
#        self.rep = DBRepository(os.path.join(self.testdir, '__repository__'))
#        self.rep.open()
#        RSSItem = self.rep.findPath('//parcels/osaf/examples/zaobao/RSSItem')
#        self._readItems(RSSItem.itsKind)
#        profiler = hotshot.Profile('/tmp/TestPerfWithRss.readBack.hotshot')
#        profiler.runcall(TestPerfWithRSS._readItems, self, RSSItem.itsKind)
#        profiler.close()

    def tearDown(self):
        self.rep.close()
        if os.path.exists(self.rep.dbHome):
            self.rep.delete()
        else:
            self.rep.logger.warn("no repository at %s", self.rep.dbHome)
        

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestPerfWithRss.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
