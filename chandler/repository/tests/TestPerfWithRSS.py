"""
Simple Performance tests for Chandler repository
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, os.path, sys, unittest

from bsddb.db import DBNoSuchFileError
from repository.item.Query import KindQuery
from repository.persistence.XMLRepository import XMLRepository
import repository.parcel.LoadParcels as LoadParcels
import application.Globals as Globals

# get Zaobao's feedparser
_chandlerDir = os.environ['CHANDLERHOME']
sys.path.append(os.path.join(_chandlerDir,'Chandler','parcels','OSAF','examples','zaobao'))
import feedparser

# get all the RSS files in RSS_HOME (repository/tests/data/rssfeeds)
# You can obtain the files from http://aloha.osafoundation.org/~twl/rssfeeds.tar.gz
RSS_HOME=os.path.join(_chandlerDir,'Chandler','repository','tests','data','rssfeeds/')
if os.path.exists(RSS_HOME):
    _rssfiles = os.listdir(RSS_HOME)
else:
    _rssfiles = []

# make them file URL's
_defaultBlogs = [ "file://"+RSS_HOME+f for f in _rssfiles ]

BASE_PATH = '//parcels/OSAF/examples/zaobao'

class TestPerfWithRSS(unittest.TestCase):
    """ Simple performance tests """

    def setUp(self):
        self.rootdir = _chandlerDir
        self.testdir = os.path.join(self.rootdir, 'Chandler', 'repository',
                                    'tests')
        self.rep = XMLRepository(os.path.join(self.testdir, '__repository__'))
        Globals.repository = self.rep # to keep indexer happy
        self.rep.create()
        schemaPack = os.path.join(self.rootdir, 'Chandler', 'repository', 'packs', 'schema.pack')
        self.rep.loadPack(schemaPack)

        parcelDir = os.path.join(self.rootdir,'Chandler','parcels')
        sys.path.insert(1, parcelDir)
        LoadParcels.LoadParcel(os.path.join(parcelDir, 'OSAF', 'examples', 
         'zaobao'), '//parcels/OSAF/examples/zaobao', parcelDir, self.rep)
        
        self.rep.commit()
        self.rep.logger.debug("Going to try: ",len(_defaultBlogs)," feeds")

    def _stressTest(self, commitInsideLoop=False):
        """ grab a bunch of RSS data from disk and insert into the repository """
        repository = self.rep

        itemCount = 0
        feeds = self.__getFeeds()

        if feeds == []:
            self.rep.logger.info("got 0 feeds")
            print "If you haven't installed the feed data, you can retreive it from"
            print "http://aloha.osafoundation.org/~twl"
            print "select a tarball, download it, and unpack it in repository/tests/data"
            print "The data will be in a new directory called rssfeeds"
            print "You can now run the tests"
        else:
            self.rep.logger.info('got %d feeds' %(len(feeds)))

        for feed in feeds[:]:
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
                feed.Update(data)
                if commitInsideLoop:
                    repository.commit()
            except Exception, e:
                self.rep.logger.error("%s in %s" % (e,feed.url))

        try:
#            profiler = hotshot.Profile('/tmp/TestPerfWithRss.stressTest.hotshot')
#            profiler.runcall(repository.commit)
#            profiler.close()
            repository.commit()
        except Exception, e:
            print e
            self.rep.logger.error("Final commit:")
            self.fail()
        self.rep.logger.info("Processed %d items" % itemCount)
        self.assert_(True)
        
    def __getFeeds(self):
        """Return a list of channel items"""
        repository = self.rep
        chanKind = repository.find(BASE_PATH + '/RSSChannel')

        feeds = []
        parent = repository.find(BASE_PATH)

        for url in _defaultBlogs:
            urlhash = str(hash(url))
            item = repository.find(BASE_PATH + '/' + urlhash)
            if not item:
                item = chanKind.newItem(urlhash, parent)
                item.url = url
            feeds.append(item)

        return feeds

    def testCommitAtEnd(self):
        self._stressTest()

    def testCommitInsideLoop(self):
        self._stressTest(True)

    def _readItems(self, kind):
        items = KindQuery().run([kind]) 
        for i in items:
            assert(i.getItemName() is not None)

    def testReadBackRSS(self):
        self._stressTest()
        self.rep.close()
        self.rep = XMLRepository(os.path.join(self.testdir, '__repository__'))
        self.rep.open()
        RSSItem = self.rep.find('//parcels/OSAF/examples/zaobao/RSSItem')
        self._readItems(RSSItem.kind)
#        profiler = hotshot.Profile('/tmp/TestPerfWithRss.readBack.hotshot')
#        profiler.runcall(TestPerfWithRSS._readItems, self, RSSItem.kind)
#        profiler.close()

    def tearDown(self):
        self.rep.close()
        self.rep.delete()

if __name__ == "__main__":
    import hotshot
#    profiler = hotshot.Profile('/tmp/TestPerfWithRss.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
