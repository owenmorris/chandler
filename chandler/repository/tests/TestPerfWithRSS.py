"""
Simple Performance tests for Chandler repository
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

from bsddb.db import DBNoSuchFileError
from repository.persistence.XMLRepository import XMLRepository
from repository.schema.DomainSchemaLoader import DomainSchemaLoader
import repository.parcel.LoadParcels as LoadParcels
import application.Globals as Globals

import sys

_chandlerDir = os.environ['CHANDLERDIR']
sys.path.append(os.path.join(_chandlerDir,'parcels','OSAF','examples','zaobao'))
import feedparser
import posix


RSS_HOME = _chandlerDir + '/repository/tests/data/rssfeeds/'

_rssfiles = posix.listdir(RSS_HOME)

_defaultBlogs = [ "file://"+RSS_HOME+f for f in _rssfiles ]
print "Going to try: ",len(_defaultBlogs)," blogs"

BASE_PATH = '//parcels/OSAF/examples/zaobao'

class TestPerfWithRSS(unittest.TestCase):
    """ Simple performance tests """

    def setUp(self):
        self.rootdir = _chandlerDir
        self.rep = XMLRepository('RSSPerfUnitTest-Repository')
        Globals.repository = self.rep # to keep indexer happy
        self.rep.create()
        schemaPack = os.path.join(self.rootdir, 'repository', 'packs', 'schema.pack')
        self.rep.loadPack(schemaPack)

        parcelDir = os.path.join(self.rootdir,'parcels')
        sys.path.insert(1, parcelDir)
        LoadParcels.LoadParcels(parcelDir, self.rep)
        
        self.rep.commit()

    def test(self):
        repository = self.rep

        feeds = self.__getFeeds()
        for feed in feeds:
            etag = feed.getAttributeValue('etag', default=None)
            lastModified = feed.getAttributeValue('lastModified', default=None)
            if lastModified:
                modified = lastModified.tuple()
            else:
                modified = None
            try:
                data = feedparser.parse(feed.url, etag, modified)
                feed.Update(data)
            except Exception, e:
                print feed.url,":",e

        repository.commit()
#        for f in feeds:
#            print f
#            for a in f.iterAttributes():
#                print a
#            for i in f.iterChildren():
#                print i.title
        
    def __getFeeds(self):
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

    def tearDown(self):
        self.rep.close()
        self.rep.delete()

if __name__ == "__main__":
#    import hotshot
#    profiler = hotshot.Profile('/tmp/TestItems.hotshot')
#    profiler.run('unittest.main()')
#    profiler.close()
    unittest.main()
