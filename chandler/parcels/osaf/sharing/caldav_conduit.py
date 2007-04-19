#   Copyright (c) 2004-2007 Open Source Applications Foundation
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

__all__ = [
    'CalDAVConduit',
    'CalDAVRecordSetConduit',
    'CalDAVFreeBusyConduit',
    'FreeBusyAnnotation',
]

import datetime, bisect
from application import schema
from osaf import pim
import webdav_conduit
import shares
import zanshin, twisted.web.http
from xml.etree.cElementTree import XML
from PyICU import ICUtzinfo
from i18n import ChandlerMessageFactory as _
from osaf.pim.calendar.TimeZone import serializeTimeZone

import logging

logger = logging.getLogger(__name__)

# constants for cosmoExcludeFreeBusy functions
COSMO_NS = 'http://osafoundation.org/cosmo/DAV'
EXCLUDE_ID = zanshin.util.PackElement('exclude-free-busy-rollup', COSMO_NS)

class CalDAVConduit(webdav_conduit.WebDAVConduit):
    ticketFreeBusy = schema.One(schema.Text, initialValue="")

    def _createCollectionResource(self, handle, resource, childName):
        displayName = self.share.contents.displayName
        timezone = serializeTimeZone(ICUtzinfo.default)
        return handle.blockUntil(resource.createCalendar, childName,
                                 displayName, timezone)

    def _getDisplayNameForShare(self, share):
        container = self._getContainerResource()
        try:
            result = container.serverHandle.blockUntil(container.getDisplayName)
        except:
            result = ""

        return result or super(CalDAVConduit,
                               self)._getDisplayNameForShare(share)

    def _putItem(self, item):
        result = super(CalDAVConduit, self)._putItem(item)

        itemName = self._getItemPath(item)
        serverHandle = self._getServerHandle()
        container = self._getContainerResource()
        resourcePath = container.path + itemName
        resource = serverHandle.getResource(resourcePath)

        return result


    def create(self):
        """Create the collection as usual, then set cosmoExcludeFreeBusy."""
        super(CalDAVConduit, self).create()
        self.setCosmoExcludeFreeBusy(not self.inFreeBusy)


    def getCosmoExcludeFreeBusy(self):
        """
        Issue a PROPFIND for cosmo:exclude-free-busy-rollup.

        @return: Boolean
        """
        handle, resource = self._getHandleAndResource()

        def handlePropfind(response):
            if response.status != twisted.web.http.MULTI_STATUS:
                raise zanshin.http.HTTPError(
                    status=response.status, message=response.message)

            propfindElement = XML(response.body)

            for rsrc, props in resource._iterPropfindElement(propfindElement):
                for prop in props:
                    if (EXCLUDE_ID == prop.tag):
                        return prop.text == 'true'

        request = zanshin.webdav.PropfindRequest(
            zanshin.webdav.quote(resource.path), 0, [EXCLUDE_ID], None)

        def deferredPropFindCallback():
            return resource._addRequest(request).addCallback(handlePropfind)

        return handle.blockUntil(deferredPropFindCallback)

    def setCosmoExcludeFreeBusy(self, exclude):
        """Issue a PROPPATCH to set cosmo:exclude-free-busy-rollup to exclude.

        @param exclude: a Boolean, should the collection be excluded from 
                        freebusy
        @return: Boolean, success or failure
        """

        def handleProppatch(results):
            """
            Return whether the server really did change 
            cosmo:exclude-free-busy-rollup.

            """
            result = results.get(EXCLUDE_ID, None)

            status = None

            # result should be of the form 'HTTP/1.1 200 OK'
            # We want to extract the int value of the 2nd
            # field, if possible,
            if result is not None:
                try:
                    status = int(result.split()[1])
                except (TypeError, IndexError):
                    # IndexError: no spaces in result
                    # TypeError: field wasn't an int
                    pass

            if status in (twisted.web.http.CREATED, twisted.web.http.OK):
                return True
            else:
                return False

        handle, resource = self._getHandleAndResource()
        propstopatch = {EXCLUDE_ID: exclude and 'true' or 'false'}
        def deferredPropPatchCallback():
            return resource.proppatch(propstopatch).addCallback(handleProppatch)

        return handle.blockUntil(deferredPropPatchCallback)

    def _getHandleAndResource(self):
        handle = self._getServerHandle()
        location = self.getLocation()
        if not location.endswith("/"):
            location += "/"
        resource = handle.getResource(location)
        return (handle, resource)

    def createFreeBusyTicket(self):
        handle, resource = self._getHandleAndResource()

        ticket = handle.blockUntil(resource.createTicket, read=False,
                                   freebusy=True)
        logger.debug("Freebusy ticket: %s %s",
            ticket.ticketId, ticket.ownerUri)
        self.ticketFreeBusy = ticket.ticketId

        return self.ticketFreeBusy

    def getLocation(self, privilege=None):
        url = super(CalDAVConduit, self).getLocation(privilege)
        if privilege in ('freebusy', 'subscribed'):
            if self.ticketFreeBusy:
                url = url + u"?ticket=%s" % self.ticketFreeBusy
        return url

MINIMUM_FREEBUSY_UPDATE_FREQUENCY = datetime.timedelta(hours=1)
MERGE_GAP_DAYS = 3

utc = ICUtzinfo.getInstance('UTC')

class FreeBusyAnnotation(schema.Annotation):
    schema.kindInfo(annotates=pim.ContentCollection)
    update_needed = schema.Sequence()
    recently_updated = schema.Sequence()

    def addDateNeeded(self, view, needed_date, force_update = False):
        """
        Check for recently updated dates, if it was updated more than
        MINIMUM_FREEBUSY_UPDATE_FREQUENCY in the past (or force_update is True)
        move it to update_needed.

        Next, check if that date has already been requested.  If no existing
        update is found, create a new one.

        Return True if an update is created or changed, False otherwise.

        """
        # need to think about what happens when bgsync changes get merged
        # with the UI view when shuffling FreeBusyUpdates about

        # test if the date's in recently_updated, then check in update_needed
        for update in getattr(self, 'recently_updated', []):
            if update.date == needed_date:
                if force_update or \
                   update.last_update + MINIMUM_FREEBUSY_UPDATE_FREQUENCY < \
                   datetime.datetime.now(utc):
                    update.needed_for = self.itsItem
                    return True
                else:
                    # nothing to do
                    return False

        for update in getattr(self, 'update_needed', []):
            if update.date == needed_date:
                return False

        # no existing update items for needed_date, create one
        FreeBusyUpdate(itsView = view, date = needed_date,
                       needed_for = self.itsItem)
        return True

    def dateUpdated(self, updated_date):
        update_found = False
        # this is inefficient when processing, say, 60 days have been updated,
        # with difficulty I convinced myself to avoid premature optimization
        for update in getattr(self, 'recently_updated', []):
            if update.date == updated_date:
                update.last_update = datetime.datetime.now(utc)
                if getattr(update, 'needed_for', False):
                    del update.needed_for
                update_found = True
                break
        for update in getattr(self, 'update_needed', []):
            if update.date == updated_date:
                if update_found:
                    # redundant update request created by a different view
                    update.delete()
                else:
                    del update.needed_for
                    update.updated_for = self.itsItem
                    update.last_update = datetime.datetime.now(utc)
                return

    def cleanUpdates(self):
        for update in getattr(self, 'recently_updated', []):
            if update.last_update + MINIMUM_FREEBUSY_UPDATE_FREQUENCY < \
               datetime.datetime.now(utc) and \
               getattr(update, 'needed_for', False):
                update.delete()

class FreeBusyUpdate(schema.Item):
    """
    A FreeBusyUpdate item can be a request to update a particular date, or a
    record of a recent update received.  Items are used instead of a simple
    dictionary so the background sync view can merge changes from the UI view,
    because changes to a repository Dictionary don't merge smoothly.

    """
    date = schema.One(schema.Date)
    last_update = schema.One(schema.DateTime)
    needed_for = schema.One(FreeBusyAnnotation,
                            inverse=FreeBusyAnnotation.update_needed)
    updated_for = schema.One(FreeBusyAnnotation,
                            inverse=FreeBusyAnnotation.recently_updated)


class CalDAVFreeBusyConduit(CalDAVConduit):
    """A read-only conduit, using the results of a free-busy report for get()"""

    def _getFreeBusy(self, resource, start, end):
        serverHandle = self._getServerHandle()
        response = serverHandle.blockUntil(resource.getFreebusy, start, end, depth='infinity')
        # quick hack to temporarily handle Cosmo's multistatus response
        return response.body

    def exists(self):
        # this should probably do something nicer
        return True

    def _get(self, contentView, resourceList, *args, **kwargs):

        if self.share.contents is None:
            self.share.contents = pim.SmartCollection(itsView=self.itsView)
            shares.SharedItem(self.share.contents).add()
        updates = FreeBusyAnnotation(self.share.contents)
        updates.cleanUpdates()


        oneday = datetime.timedelta(1)
        yesterday = datetime.date.today() - oneday
        for i in xrange(29):
            updates.addDateNeeded(self.itsView, yesterday + i * oneday)

        needed_dates = []
        date_ranges = [] # a list of (date, number_of_days) tuples
        for update in getattr(updates, 'update_needed', []):
            bisect.insort(needed_dates, update.date)

        if len(needed_dates) > 0:
            start_date = working_date = needed_dates[0]
            for date in needed_dates:
                if date - working_date > oneday * MERGE_GAP_DAYS:
                    days = (working_date - start_date).days
                    date_ranges.append( (start_date, days) )
                    start_date = working_date = date
                else:
                    working_date = date

            days = (working_date - start_date).days
            date_ranges.append( (start_date, days) )

        # prepare resource, add security context
        resource = self._resourceFromPath(u"")
        if getattr(self, 'ticketFreeBusy', False):
            resource.ticketId = self.ticketFreeBusy
        elif getattr(self, 'ticketReadOnly', False):
            resource.ticketId = self.ticketReadOnly

        zero_utc = datetime.time(0, tzinfo = utc)
        for period_start, days in date_ranges:
            start = datetime.datetime.combine(period_start, zero_utc)
            end = datetime.datetime.combine(period_start + (days + 1) * oneday,
                                            zero_utc)

            text = self._getFreeBusy(resource, start, end)
            self.share.format.importProcess(contentView, text, item=self.share)

            for i in xrange(days + 1):
                updates.dateUpdated(period_start + i * oneday)

        # a stats data structure appears to be required
        stats = {
            'share' : self.share.itsUUID,
            'op' : 'get',
            'added' : [],
            'modified' : [],
            'removed' : []
        }

        return stats

    def get(self):
        self._get()



class CalDAVRecordSetConduit(webdav_conduit.WebDAVRecordSetConduit):


    def _createCollectionResource(self, handle, resource, childName):
        displayName = self.share.contents.displayName
        timezone = serializeTimeZone(ICUtzinfo.default)
        return handle.blockUntil(resource.createCalendar, childName,
                                 displayName, timezone)

    def getCollectionName(self):
        container = self._getContainerResource()
        try:
            result = container.serverHandle.blockUntil(container.getDisplayName)
        except:
            result = _(u"Unknown")

        return result

    def getPath(self, uuid):
        return "%s.ics" % uuid
