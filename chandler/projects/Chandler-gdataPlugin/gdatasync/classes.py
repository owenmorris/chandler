#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

import os, md5
import gdata, atom, gdata.calendar.service
from osaf import pim, sharing
from osaf.sharing import NoChange as NC, Inherit
from application import schema
from chandlerdb.util.c import UUID
from application.Utility import getUserAgent
from application.dialogs.AccountPreferences import AccountPanel
from dateutil.parser import parse as dateutilparser
from osaf.pim.calendar.TimeZone import convertToICUtzinfo
from osaf.framework.twisted import waitForDeferred
from itertools import chain
from i18n import MessageFactory
_ = MessageFactory("Chandler-gdataPlugin")



import logging
logger = logging.getLogger(__name__)


__all__ = [
    'GDataAccount',
    'GDataConduit',
    'GDataState',
    'GDataTranslator',
    'GDataAccountRecord',
    'GDataConduitRecord',
    'GDataStateRecord',
]



def getService(username, password):
    service = gdata.calendar.service.CalendarService()
    service.email = username
    service.password = password
    service.ProgrammaticLogin()
    return service


class GDataAccount(sharing.SharingAccount):
    accountProtocol = schema.One(initialValue = 'GData')
    accountType = schema.One(initialValue = 'SHARING_GDATA')


    def subscribe(self, url):
        share = sharing.Share(itsView=self.itsView)
        conduit = GDataConduit(itsParent=share, account=self, url=url,
            translator=sharing.SharingTranslator)
        share.conduit = conduit
        share.get()
        return share.contents

    def publish(self, collection, activity=None, filters=None, overwrite=False):
        # Not implemented
        raise sharing.SharingError("Publishing to Google not yet supported")

    def getCalendars(self):
        service = getService(self.username,
            waitForDeferred(self.password.decryptPassword()))
        feed = service.GetCalendarListFeed()
        for entry in feed.entry:
            yield(entry.title.text, entry.GetAlternateLink().href)



class GDataState(sharing.State):
    id = schema.One(schema.Text)
    editLink = schema.One(schema.Text)
    removed = schema.One(schema.Boolean, defaultValue=False)



class GDataConduit(sharing.RecordSetConduit, sharing.HTTPMixin):

    url = schema.One(schema.Text)

    def sync(self, modeOverride=None, activity=None, forceUpdate=None,
            debug=False):

        if self.account:
            username = self.account.username
            password = waitForDeferred(self.account.password.decryptPassword())
        else:
            username = self.username
            password = self.password

        self.gService = getService(username, password)

        return super(GDataConduit, self).sync(modeOverride=modeOverride,
            activity=activity, forceUpdate=forceUpdate, debug=debug)


    def getFilter(self):
        filter = super(GDataConduit, self).getFilter()
        filter += sharing.lookupSchemaURI('cid:triage-filter@osaf.us')
        filter += sharing.lookupSchemaURI('cid:created-on-filter@osaf.us')
        filter += sharing.lookupSchemaURI('cid:has-been-sent-filter@osaf.us')
        filter += sharing.lookupSchemaURI('cid:needs-reply-filter@osaf.us')
        filter += sharing.lookupSchemaURI('cid:read-filter@osaf.us')

        filter += sharing.lookupSchemaURI('cid:icaluid-filter@osaf.us')
        filter += sharing.lookupSchemaURI('cid:non-standard-ical-filter@osaf.us')
        filter += sharing.lookupSchemaURI('cid:event-status-filter@osaf.us')
        filter += sharing.lookupSchemaURI('cid:reminders-filter@osaf.us')
        return filter




    def getRecords(self, debug=False, activity=None):
        # Get and return records, extra
        debug = True
        doLog = logger.info if debug else logger.debug

        # 'alias' for a state will be the pseudoId

        inbound = { }
        extra = { }

        query = gdata.calendar.service.CalendarEventQuery(feed=self.url)
        query.max_results = '10000'
        feed = self.gService.CalendarQuery(query)
        # feed = self.gService.GetCalendarEventFeed(self.url)
        extra['name'] = feed.title.text
        doLog("Fetched Google calendar: %s (%d entries)" % (feed.title.text,
            len(feed.entry)))

        # gdata id --> state mapping
        states = { }
        for state in self.share.states:
            states[state.id] = state

        # alias --> entry mapping
        entries = { }
        unchanged = set()
        for entry in feed.entry:
            records = []
            id = entry.id.text
            editLink = entry.GetEditLink().href
            if id in states:
                # update to existing item
                state = states[id]
                alias = self.share.states.getAlias(state)
                if state.editLink == editLink:
                    unchanged.add(alias)
                else:
                    state.editLink = editLink
                    doLog("Received update to: %s" % entry.title.text)
            else:
                # new inbound item
                alias = UUID(md5.new(entry.id.text).digest()).str16()
                state = self.newState(alias)
                state.id = id
                state.editLink = editLink
                doLog("Received new item: %s" % entry.title.text)

            state.gdataEntry = entry # non-persisted, used by putRecords next
            state.removed = False
            entries[alias] = entry

        for id, state in states.iteritems():
            alias = self.share.states.getAlias(state)
            if alias not in entries and not state.removed:
                # indicator of remote deletion
                inbound[alias] = None
                state.removed = True
                doLog("Received deletion of: %s" % alias)

        for alias, entry in entries.iteritems():
            if alias in unchanged:
                continue

            records = []
            title = entry.title.text
            body = entry.content.text
            rec = sharing.ItemRecord(alias, title, NC, NC, NC, NC, NC)
            records.append(rec)
            rec = sharing.NoteRecord(alias, body, NC, NC, NC, NC)
            records.append(rec)

            if entry.recurrence:
                # print "Skipping (recurrence)", title, entry.recurrence
                self.removeState(alias)
                continue

            else:
                where = entry.where[0]
                location = where.value_string if where and where.value_string \
                    else None

                startTime = whenToDatetime(self.itsView,
                    entry.when[0].start_time)
                endTime = whenToDatetime(self.itsView, entry.when[0].end_time)
                duration = endTime - startTime
                startTime = sharing.toICalendarDateTime(self.itsView,
                    startTime, False, anyTime=False)
                duration = sharing.toICalendarDuration(duration, allDay=False)
                rec = sharing.EventRecord(alias, startTime, duration, location,
                    None, None, None, None, NC)
                records.append(rec)

            inbound[alias] = sharing.RecordSet(records)

        return inbound, extra, False

    def putRecords(self, toSend, extra, debug=False, activity=None):

        debug = True
        doLog = logger.info if debug else logger.debug

        for alias, rs in toSend.iteritems():
            state = self.getState(alias)
            if hasattr(state, 'gdataEntry'):
                # this is an update to an existing event
                entry = state.gdataEntry
                if rs is None:
                    # Delete from the remote calendar
                    self.gService.DeleteEvent(entry.GetEditLink().href, entry)
                else:
                    # Don't bother sending if the only change is a modifiedBy
                    for r in chain(rs.inclusions, rs.exclusions):
                        if not isinstance(r, sharing.ModifiedByRecord):
                            break
                    else:
                        doLog("Skipping modifiedBy-only update of: %s", alias)
                        continue

                    applyToEntry(self.itsView, rs, entry)
                    doLog("Sending update for: %s", alias)
                    entry = self.gService.UpdateEvent(entry.GetEditLink().href,
                        entry)
                    state.editLink = entry.GetEditLink().href
                    state.removed = False
            else:
                entry = gdata.calendar.CalendarEventEntry()
                applyToEntry(self.itsView, rs, entry)
                doLog("Sending new item for: %s", alias)
                entry = self.gService.InsertEvent(entry, self.url)
                state.id = entry.id.text
                state.editLink = entry.GetEditLink().href
                state.removed = False



    def newState(self, alias):
        state = GDataState(itsView=self.itsView, peer=self.share)
        self.share.states.append(state, alias)
        return state


    def getLocation(self, privilege=None):
        return "Google"


def whenToDatetime(rv, when):
    return convertToICUtzinfo(rv, dateutilparser(when))


NONCHANGES = (NC, Inherit)

def applyToEntry(rv, diff, entry):
    for r in diff.inclusions:
        if isinstance(r, sharing.ItemRecord):
            if r.title not in NONCHANGES:
                if entry.title is None:
                    entry.title = atom.Title(text=r.title)
                else:
                    entry.title.text = r.title
        elif isinstance(r, sharing.NoteRecord):
            if r.body not in NONCHANGES:
                if entry.content is None:
                    entry.content = atom.Content(text=r.body)
                else:
                    entry.content.text = r.body
        elif isinstance(r, sharing.EventRecord):
            if r.location not in NONCHANGES:
                entry.where = [gdata.calendar.Where(value_string=r.location)]

            if r.dtstart not in NONCHANGES:
                if len(entry.when) == 0:
                    entry.when.append(gdata.calendar.When())

                if r.duration is NC:
                    # start time changed, but duration didn't.  However we
                    # don't know the duration from the EIM record, so go back
                    # to the the event entry and compute duration
                    startTime = whenToDatetime(rv, entry.when[0].start_time)
                    endTime = whenToDatetime(rv, entry.when[0].end_time)
                    duration = endTime - startTime
                else:
                    duration = sharing.fromICalendarDuration(r.duration)

                startTime, allDay, anyTime = sharing.fromICalendarDateTime(
                    rv, r.dtstart)
                entry.when[0].start_time = startTime.isoformat()
                endTime = startTime + duration
                entry.when[0].end_time = endTime.isoformat()





text1024 = sharing.TextType(size=1024)

class GDataAccountRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/gdatasync/account/0"
    uuid = sharing.key(sharing.ItemRecord.uuid)


class GDataConduitRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/gdatasync/conduit/0"
    uuid = sharing.key(sharing.ItemRecord.uuid)
    url = sharing.field(text1024)


class GDataStateRecord(sharing.Record):
    URI = "http://osafoundation.org/eim/gdatasync/state/0"
    uuid = sharing.key(sharing.ItemRecord.uuid)
    id = sharing.field(text1024)
    editLink = sharing.field(text1024)
    removed = sharing.field(sharing.IntType)


class GDataTranslator(sharing.Translator):
    URI = "cid:gdata-translator@osaf.us"
    version = 1
    description = u"Translator for Google Data syncing"

    @GDataAccountRecord.importer
    def import_account(self, record):
        self.withItemForUUID(record.uuid, GDataAccount)

    @sharing.exporter(GDataAccount)
    def export_account(self, account):
        yield GDataAccountRecord(account)


    @GDataConduitRecord.importer
    def import_conduit(self, record):
        self.withItemForUUID(record.uuid, GDataConduit, url=record.url)

    @sharing.exporter(GDataConduit)
    def export_conduit(self, conduit):
        yield GDataConduitRecord(conduit, conduit.url)


    @GDataStateRecord.importer
    def import_state(self, record):
        self.withItemForUUID(record.uuid, GDataState, id=record.id,
            editLink=record.editLink, removed=bool(record.removed))

    @sharing.exporter(GDataState)
    def export_state(self, state):
        yield GDataStateRecord(state, state.id, state.editLink,
            1 if state.removed else 0)

