"""Ultra-liberal RSS feed locator

http://diveintomark.org/projects/rss_finder/

Usage:
getFeeds(uri) - returns list of RSS feeds associated with this address

Example:
>>> import rssfinder
>>> rssfinder.getFeeds('http://diveintomark.org/')
['http://diveintomark.org/xml/rss.xml']
>>> rssfinder.getFeeds('macnn.com')
['http://www.macnn.com/macnn.rdf']

Can also use from the command line.  Feeds are returned one per line:
$ python rssfinder.py diveintomark.org
http://diveintomark.org/xml/rss.xml

How it works:
0. At every step, RSS feeds are minimally verified to make sure they are
   really RSS feeds.
1. If the URI points to an RSS feed, it is simply returned; otherwise
   the page is downloaded and the real fun begins.
2. Feeds pointed to by LINK tags in the header of the page (RSS autodiscovery)
3. <A> links to feeds on the same server ending in ".rss", ".rdf", or ".xml"
4. <A> links to feeds on the same server containing "rss", "rdf", or "xml"
5. <A> links to feeds on external servers ending in ".rss", ".rdf", or ".xml"
6. <A> links to feeds on external servers containing "rss", "rdf", or "xml"
7. As a last ditch effort, we search Syndic8 for feeds matching the URI

"""

__version__ = "1.1"
__date__ = "2003/02/20"
__author__ = "Mark Pilgrim (f8dy@diveintomark.org)"
__copyright__ = "Copyright 2002, Mark Pilgrim"
__license__ = "GPL"
__credits__ = """Abe Fettig for a patch to sort Syndic8 feeds by popularity
Also Jason Diamond, Brian Lalor for bug reporting and patches"""
__history__ = """
1.1 - MAP - 2003/02/20 - added support for Robot Exclusion Standard.  Will
fetch /robots.txt once per domain and verify that URLs are allowed to be
downloaded.  Identifies itself as
  rssfinder/<version> Python-urllib/<version> +http://diveintomark.org/projects/rss_finder/
"""

_debug = 0
try:
    import timeoutsocket # http://www.timo-tasi.org/python/timeoutsocket.py
    timeoutsocket.setDefaultSocketTimeout(10)
except ImportError:
    pass
try:
    import xmlrpclib # http://www.pythonware.com/products/xmlrpc/
except ImportError:
    pass
from sgmllib import SGMLParser
import urllib, urlparse, re, sys
import robotparser

def _debuglog(message):
    if _debug: print message

class RobotFileParserFixed(robotparser.RobotFileParser):
    """patched version of RobotFileParser, integrating fixes from Python 2.3a2 and bug 690214"""
    
    def can_fetch(self, useragent, url):
        """using the parsed robots.txt decide if useragent can fetch url"""
        if self.disallow_all:
            return 0
        if self.allow_all:
            return 1
        # search for given user agent matches
        # the first match counts
        url = urllib.quote(urlparse.urlparse(urllib.unquote(url))[2]) or "/"
        for entry in self.entries:
            if entry.applies_to(useragent):
                if not entry.allowance(url):
                    return 0
        # agent not found ==> access granted
        return 1
    
class URLGatekeeper:
    """a class to track robots.txt rules across multiple servers"""
    def __init__(self):
        self.rpcache = {} # a dictionary of RobotFileParserFixed objects, by domain
        self.urlopener = urllib.FancyURLopener()
        self.urlopener.version = "rssfinder/" + __version__ + " " + self.urlopener.version + " +http://diveintomark.org/projects/rss_finder/"
        _debuglog(self.urlopener.version)
        self.urlopener.addheaders = [('User-agent', self.urlopener.version)]
        robotparser.URLopener.version = self.urlopener.version
        robotparser.URLopener.addheaders = self.urlopener.addheaders
        
    def _getrp(self, url):
        protocol, domain = urlparse.urlparse(url)[:2]
        if self.rpcache.has_key(domain):
            return self.rpcache[domain]
        baseurl = '%s://%s' % (protocol, domain)
        robotsurl = urlparse.urljoin(baseurl, 'robots.txt')
        _debuglog('fetching %s' % robotsurl)
        rp = RobotFileParserFixed(robotsurl)
        rp.read()
        self.rpcache[domain] = rp
        return rp
        
    def can_fetch(self, url):
        rp = self._getrp(url)
        allow = rp.can_fetch(self.urlopener.version, url)
        _debuglog("Gatekeeper examined %s and said %s" % (url, allow))
        return allow

    def get(self, url):
        if not self.can_fetch(url): return ''
        return self.urlopener.open(url).read()

_gatekeeper = URLGatekeeper()

class BaseParser(SGMLParser):
    def __init__(self, baseuri):
        SGMLParser.__init__(self)
        self.links = []
        self.baseuri = baseuri
        
class LinkParser(BaseParser):
    RSSTYPE = ('application/rss+xml', 'text/xml')
    def do_link(self, attrs):
        rels = [v for k,v in attrs if k=='rel']
        if not rels: return
        if rels[0].lower() <> 'alternate': return
        types = [v for k,v in attrs if k=='type']
        if not types: return
        type = types[0]
        isRSSType = 0
        for t in self.RSSTYPE:
            isRSSType = type.startswith(t)
            if isRSSType: break
        if not isRSSType: return
        hrefs = [v for k,v in attrs if k=='href']
        if not hrefs: return
        self.links.append(urlparse.urljoin(self.baseuri, hrefs[0]))

class ALinkParser(BaseParser):
    def start_a(self, attrs):
        hrefs = [v for k,v in attrs if k=='href']
        if not hrefs: return
        self.links.append(urlparse.urljoin(self.baseuri, hrefs[0]))

def makeFullURI(uri):
    if not uri.count('http://'):
        uri = 'http://%s' % uri
    return uri

def getLinks(data, baseuri):
    p = LinkParser(baseuri)
    p.feed(data)
    return p.links

def getALinks(data, baseuri):
    p = ALinkParser(baseuri)
    p.feed(data)
    return p.links

def getLocalLinks(links, baseuri):
    baseuri = baseuri.lower()
    urilen = len(baseuri)
    return [l for l in links if l.lower().startswith(baseuri)]

def isFeedLink(link):
    return link[-4:].lower() in ('.rss', '.rdf', '.xml')

def isXMLRelatedLink(link):
    link = link.lower()
    return link.count('rss') + link.count('rdf') + link.count('xml')

def isRSS(data):
    data = data.lower()
    if data.count('<html'): return 0
    return data.count('<rss') + data.count('<rdf')

def isFeed(uri):
    _debuglog('verifying that %s is a feed' % uri)
    protocol = urlparse.urlparse(uri)
    if protocol[0] not in ('http', 'https'): return 0
    data = _gatekeeper.get(uri)
    return isRSS(data)

def sortFeeds(feed1Info, feed2Info):
    return cmp(feed2Info['headlines_rank'], feed1Info['headlines_rank'])

def getFeedsFromSyndic8(uri):
    feeds = []
    try:
        server = xmlrpclib.Server('http://www.syndic8.com/xmlrpc.php')
        feedids = server.syndic8.FindFeeds(uri)
        infolist = server.syndic8.GetFeedInfo(feedids, ['headlines_rank','status','dataurl'])
        infolist.sort(sortFeeds)
        feeds = [f['dataurl'] for f in infolist if f['status']=='Syndicated']
        _debuglog('found %s feeds through Syndic8' % len(feeds))
    except:
        pass
    return feeds
    
def getFeeds(uri,progressDlg):
    fulluri = makeFullURI(uri)
    data = _gatekeeper.get(fulluri)
    # is this already a feed?
    if isRSS(data):
        return [fulluri]
    # nope, it's a page, try LINK tags first
    _debuglog('looking for LINK tags')
    feeds = getLinks(data, fulluri)
    if not progressDlg.Update(1, "starting search"): return 'cancelled'
    _debuglog('found %s feeds through LINK tags' % len(feeds))
    if not progressDlg.Update(2, "searched for LILNK tags"): return 'cancelled'
    feeds = filter(isFeed, feeds)
    if not feeds:
        # no LINK tags, look for regular <A> links that point to feeds
        _debuglog('no LINK tags, looking at A tags')
        if not progressDlg.Update(3, "searched for A tags"): return 'cancelled'
        links = getALinks(data, fulluri)
        locallinks = getLocalLinks(links, fulluri)
        # look for obvious feed links on the same server
        feeds = filter(isFeed, filter(isFeedLink, locallinks))
        if not feeds:
            # look harder for feed links on the same server
            if not progressDlg.Update(4, "looking harder for XML related links"): return 'cancelled'
            feeds = filter(isFeed, filter(isXMLRelatedLink, locallinks))
        if not feeds:
            # look for obvious feed links on another server
            if not progressDlg.Update(5, "looking at other servers"): return 'cancelled'
            feeds = filter(isFeed, filter(isFeedLink, links))
        if not feeds:
            if not progressDlg.Update(6, "looking harder at other servers"): return 'cancelled'
            # look harder for feed links on another server
            feeds = filter(isFeed, filter(isXMLRelatedLink, links))
    #if not feeds:
        #if not progressDlg.Update(7, "last resort: search Syndic8"): return 'cancelled'
        ## still no luck, search Syndic8 for feeds (requires xmlrpclib)
        #_debuglog('still no luck, searching Syndic8')
        #feeds = getFeedsFromSyndic8(uri)
    #progressDlg.Destroy()
    return feeds

if __name__ == '__main__':
    if sys.argv[1:]:
        uri = sys.argv[1]
    else:
        uri = 'http://diveintomark.org/'
    print "\n".join(getFeeds(uri))

