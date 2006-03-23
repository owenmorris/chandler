#
# Very basic wrapper around the API in
#    <http://api.evdb.com/docs/events/ical>
#

from application import schema
from i18n import OSAFMessageFactory as _

import urllib, logging
from zanshin.util import blockUntil
import zanshin.webdav
import osaf.sharing as sharing

import osaf.pim

APP_KEY = 'CtssgKSFQDrFsBVC'
logger = logging.getLogger(__name__)


def GetCollectionFromSearch(repoView, searchTerms):

    # We turn searchTerms into a URI, using the
    # above API.

    # ... need the app key (identifies Chandler).
    query = 'ical?app_key=%s' % (urllib.quote_plus(APP_KEY))
    displayName = "EVDB"
    
    # ... add in keywords
    q = searchTerms.get('keywords', None)
    if q:
        query = '%s&q=%s' % (
                query,
                q.encode('UTF-8'))
        displayName = "%s %s" % (displayName, q)

    # ... location ...
    location = searchTerms.get('location', None)
    if location:
        query = '%s&location=%s' % (
                query,
                urllib.quote_plus(location).encode('UTF-8'))
        displayName = "%s %s" % (displayName, location)

    # ... and dates ...
    dates = searchTerms.get('dates', None)
    if dates:
        query = '%s&date=%s' % (
                query,
                urllib.quote_plus(dates).encode('UTF-8'))
        displayName = "%s %s" % (displayName, dates)
           
    logger.info('sending query %s', query)

    collection = osaf.pim.ListCollection(itsView=repoView, displayName=displayName)

    share = sharing.Share(itsView=repoView, contents=collection)

    # /rest/events/ics returns all matching events in ics
    # (ICalendar) format, so we just need an ICalendarFormat
    # object to parse the data.
    share.format = sharing.ICalendarFormat(itsParent=share)
    
    # Since we're doing an HTTP GET to fetch all matching
    # events, we can use a SimpleHTTPConduit here.
    share.conduit = sharing.SimpleHTTPConduit(itsParent=share,
                        shareName=query,
                        account=None,
                        host = 'api.evdb.com',
                        port = 80,
                        sharePath = '/rest/events')
    
    share.mode = "get"
    share.filterClasses = ["osaf.pim.calendar.Calendar.CalendarEventMixin"]
    
    try:
        share.get()
        
        return collection
    except sharing.TransformationError:
        return collection
    except Exception, e:
        logger.exception("Error during GET from EVDB")
        repoView.cancel()
        raise


