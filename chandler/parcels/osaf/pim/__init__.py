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


# Import classes whose schemas are part of this parcel
# (this should include all ContentItem subclasses in this package)
#
from items import (
    ContentKind, ContentItem, ImportanceEnum, Group, Principal, 
    Project, Modification
)
from reminders import (
    isDead
)
from triage import (
    Triageable, TriageEnum, getTriageStatusName, getNextTriageStatus
)
from collections import (
    KindCollection, ContentCollection, DifferenceCollection, UnionCollection,
    IntersectionCollection, FilteredCollection, ListCollection, SmartCollection, 
    AppCollection, IndexedSelectionCollection, AllIndexDefinitions,
    IndexDefinition, AttributeIndexDefinition, MethodIndexDefinition,
    NumericIndexDefinition
)

from stamping import Stamp, has_stamp
from notes import Note
from contacts import Contact, ContactName
from calendar.Calendar import (
    CalendarEvent, EventStamp, Occurrence, LONG_TIME, zero_delta,
    EventComparator, Location, RecurrencePattern, RelativeReminder,
    TriageStatusReminder,
)
from calendar.TimeZone import installParcel as tzInstallParcel
from calendar.DateTimeUtil import (ampmNames, durationFormat, mediumDateFormat, 
     monthNames, sampleDate, sampleTime, shortDateFormat, shortTimeFormat, 
     weekdayNames, weekdayName)
from reminders import PendingReminderEntry, Reminder, Remindable
from tasks import Task, TaskStamp
from mail import EmailAddress, EmailComparator, MailStamp, MailPreferences, IMAPAccount, SMTPAccount
from osaf.framework import password
from application.Parcel import Reference
from repository.item.Item import Item
from PyICU import ICUtzinfo
from osaf import messages, startup
import tasks, mail, calendar.Calendar
from i18n import ChandlerMessageFactory as _


# Stamped Kinds

from application import schema

class MasterEventWatcher(schema.Item):
    """
    A C{MasterEventWatcher} is responsible for observing changes to
    master events, and then propagating notifications to the masters'
    modifications.

    See <http://lists.osafoundation.org/pipermail/chandler-dev/2007-January/007537.html>
    """

    targetCollection = schema.One(ContentCollection)

    def install(self):
        """
        Watch our targetCollection for changes. This is typically called
        in the UI thread only (via a startup item).
        """
        self.itsView.watchCollectionQueue(self, self.targetCollection,
                                         'onMasterEventChange')

    def onMasterEventChange(self, op, collection, name, other):
        mods = self.itsView.findValue(other, EventStamp.modifications.name, [])
        # Propagate via
        self.itsView.dispatchChanges(iter(mods))


class NonOccurrenceFilter(Item):

    def isNonOccurrence(self, view, uuid):
        occurrences, modificationFor, occurrenceFor = view.findValues(uuid,
                           (EventStamp.occurrences.name, ()),
                           (EventStamp.modificationFor.name, None),
                           (EventStamp.occurrenceFor.name, None))

        if occurrences:
            return True # a master
        elif not modificationFor and occurrenceFor:
            return False # a plain occurrence, not a modification
        else:
            return True # non-recurring, or a modification

    def isNotPureOccurrence(self, view, uuid):
        occurrenceFor, modificationFor = \
            view.findValues(uuid, (EventStamp.occurrenceFor.name, None),
                                  (EventStamp.modificationFor.name, None))
        return not occurrenceFor or modificationFor


class LongEventFilter(Item):

    def isLongEvent(self, view, uuid):
        return view.findValue(uuid, EventStamp.duration.name,
                              zero_delta) > LONG_TIME

_FILTER_ATTRIBUTES = [
    (EventStamp.anyTime.name, False),
    (EventStamp.allDay.name, False),
    (EventStamp.startTime.name, None)
]

class FloatingEventFilter(Item):

    def isFloatingEvent(self, view, uuid):
        anyTime, allDay, start = view.findValues(uuid, *_FILTER_ATTRIBUTES)
        return (anyTime or allDay or (start is not None and
                                      start.tzinfo == ICUtzinfo.floating))


UTC = ICUtzinfo.getInstance("UTC")

class UTCEventFilter(Item):

    def isUTCEvent(self, view, uuid):
        anyTime, allDay, start = view.findValues(uuid, *_FILTER_ATTRIBUTES)
        if anyTime or allDay:
            return False
        return (start is not None and start.tzinfo == UTC)

class RecurrenceAwareFilter(Item):
    attrAndDefault = ()

    @classmethod
    def makeCollection(cls, parcel, name, source):
        filter = cls(None, parcel)
        collection = FilteredCollection.update(
                        parcel, name,
                        source=source,
                        filterMethod=(filter, 'matches'),
                        filterAttributes=[cls.attrAndDefault[0]],
                    )
        return collection

    def matches(self, view, uuid):
        return view.findInheritedValues(uuid, type(self).attrAndDefault)[0]

class UnexpiredFilter(Item):
    findValuePair = (Reminder.nextPoll.name, None)

    def notExpired(self, view, uuid):
        nextPoll = view.findValue(uuid, *self.findValuePair)

        return nextPoll != Reminder.farFuture

    def compare(self, u1, u2, vals):
        view = self.itsView
        if u1 in vals:
            np1 = vals[u1]
        else:
            np1 = view.findValue(u1, self.findValuePair[0], None)
        if u2 in vals:
            np2 = vals[u2]
        else:
            np2 = view.findValue(u2, self.findValuePair[0], None)

        if np1 == np2:
            return 0
        if np1 is None:
            return -1
        if np2 is None:
            return 1
        return cmp(np1, np2)

    def compare_init(self, u, vals):
        return self.itsView.findValue(u, self.findValuePair[0], None)


class ToMeFilter(RecurrenceAwareFilter):
    attrAndDefault = mail.MailStamp.toMe.name, True

class FromMeFilter(RecurrenceAwareFilter):
    attrAndDefault = mail.MailStamp.fromMe.name, False

def installParcel(parcel, oldVersion=None):
    view = parcel.itsView

    # Create our one collection of indexDefinition mappings; when each gets
    # created, its __init__ will add it to this collection automagically.
    AllIndexDefinitions.update(parcel, "allIndexDefinitions")
    Reference.update(parcel, 'currentContact')

    MailPreferences.update(parcel, 'MailPrefs')
    Reference.update(parcel, 'currentMeEmailAddress')
    Reference.update(parcel, 'currentMeEmailAddresses')

    cur = Reference.update(parcel, 'currentIncomingAccount')
    cur1 = Reference.update(parcel, 'currentOutgoingAccount')


    if cur.item is None:
        cur.item = IMAPAccount(itsView=view,
            displayName = _(u'Incoming mail'),
            replyToAddress = EmailAddress(itsView=view),
            password = password.Password(itsView=view)
            )


    if cur1.item is None:
        cur1.item = SMTPAccount(itsView=view,
            displayName = _(u'Outgoing mail'),
            password = password.Password(itsView=view),
            )




    trashCollection = ListCollection.update(
        parcel, 'trashCollection',
        displayName=_(u"Trash"))

    notes = KindCollection.update(
        parcel, 'noteCollection',
        kind = Note.getKind(view),
        recursive = True)

    mine = UnionCollection.update(parcel, 'mine')

    # it would be nice to get rid of these intermediate fully-fledged
    # item collections, and replace them with lower level Set objects
    mineNotes = IntersectionCollection.update(parcel, 'mineNotes',
                                              sources=[mine, notes])

    nonOccurrenceFilter = NonOccurrenceFilter(None, parcel)

    nonRecurringNotes = FilteredCollection.update(parcel, 'nonRecurringNotes',
        source=mineNotes,
        filterMethod=(nonOccurrenceFilter, 'isNonOccurrence'),
        filterAttributes=[EventStamp.occurrenceFor.name,
                          EventStamp.modificationFor.name,
                          EventStamp.occurrences.name]
    )

    allContentItems = KindCollection.update(
        parcel, 'allContentItems',
        kind = ContentItem.getKind(view),
        recursive=True)

    contentItems = FilteredCollection.update(parcel, 'contentItems',
        source=allContentItems,
        filterMethod=(nonOccurrenceFilter, 'isNotPureOccurrence'),
        filterAttributes=[EventStamp.occurrenceFor.name,
                          EventStamp.modificationFor.name])

    allReminders = KindCollection.update(
        parcel, 'allReminders', kind=Reminder.getKind(view), recursive=True
    )

    allFutureReminders = FilteredCollection.update(
        parcel, 'allFutureReminders',
        source=allReminders,
        filterMethod=(UnexpiredFilter(None, parcel), 'notExpired'),
        filterAttributes=[UnexpiredFilter.findValuePair[0]],
    )

    allFutureReminders.addIndex('reminderPoll',
        'method', method=(UnexpiredFilter(None, parcel), 'compare'),
        monitor=[UnexpiredFilter.findValuePair[0]])

    # the "All" / "My" collection
    allCollection = SmartCollection.update(parcel, 'allCollection',
        displayName=_(u"Dashboard"),
        source=nonRecurringNotes,
        exclusions=trashCollection,
        trash=None,
    )
    # kludge to improve on bug 4144 (not a good long term fix but fine for 0.6)
    allCollection.addIndex('__adhoc__', 'numeric')

    events = EventStamp.getCollection(view)
    eventComparator = EventComparator.update(parcel, 'eventComparator')

    EventStamp.addIndex(events, 'effectiveStart', 'method',
                    method=(eventComparator, 'cmpStartTime'),
                    monitor=(EventStamp.startTime, EventStamp.allDay,
                             EventStamp.anyTime))
    EventStamp.addIndex(events, 'effectiveEnd', 'method',
                    method=(eventComparator, 'cmpEndTime'),
                    monitor=(EventStamp.startTime, EventStamp.allDay,
                             EventStamp.anyTime, EventStamp.duration))

    # floatingEvents need to be reindexed in effectiveStart and effectiveEnd
    # when the floating timezone changes
    filterAttributes = [entry[0] for entry in _FILTER_ATTRIBUTES]
    floatingEvents = FilteredCollection.update(parcel, 'floatingEvents',
        source = events,
        filterMethod=(FloatingEventFilter(None, parcel), 'isFloatingEvent'),
        filterAttributes=filterAttributes)
    floatingEvents.addIndex('__adhoc__', 'numeric')

    # UTCEvents need to be reindexed in effectiveStartNoTZ and effectiveEndNoTZ
    # when the floating timezone changes, because UTC events are treated
    # specially
    UTCEvents = FilteredCollection.update(parcel, 'UTCEvents',
        source = events,
        filterMethod= (UTCEventFilter(None, parcel), 'isUTCEvent'),
        filterAttributes=filterAttributes)
    UTCEvents.addIndex('__adhoc__', 'numeric')

    longEvents = FilteredCollection.update(parcel, 'longEvents',
        source = events,
        filterMethod= (LongEventFilter(None, parcel), 'isLongEvent'),
        filterAttributes = [EventStamp.duration.name])
    longEvents.addIndex('effectiveStart', 'subindex',
                        superindex=(events, events.__collection__,
                                    'effectiveStart'))
    longEvents.addIndex('effectiveEnd', 'subindex',
                        superindex=(events, events.__collection__,
                                    'effectiveEnd'))

    filterAttributes = (EventStamp.rruleset.name, EventStamp.occurrences.name)
    masterFilter = "view.hasTrueValues(uuid, '%s', '%s')" % filterAttributes
    nonMasterFilter = "not " + masterFilter

    masterEvents = FilteredCollection.update(parcel, 'masterEvents',
        source = events,
        filterExpression = masterFilter,
        filterAttributes = list(filterAttributes))

    nonMasterEvents = FilteredCollection.update(parcel, 'nonMasterEvents',
        source = events,
        filterExpression = nonMasterFilter,
        filterAttributes = list(filterAttributes))

    MasterEventWatcher.update(parcel, 'masterEventWatcher',
        targetCollection=masterEvents)


    EventStamp.addIndex(masterEvents, "recurrenceEnd", 'method',
                        method=(eventComparator, 'cmpRecurEnd'),
                        monitor=(EventStamp.recurrenceEnd,))

    EventStamp.addIndex(masterEvents, 'effectiveStart', 'subindex',
                          superindex=(events, events.__collection__,
                                      'effectiveStart'))

    locations = KindCollection.update(
        parcel, 'locations',
        kind = Location.getKind(view),
        recursive = True)

    locations.addIndex('locationName', 'attribute', attribute = 'displayName')

    mailCollection = mail.MailStamp.getCollection(view)

    emailAddressCollection = \
        KindCollection.update(parcel, 'emailAddressCollection',
                              kind=mail.EmailAddress.getKind(view),
                              recursive=True)
    emailComparator = EmailComparator.update(parcel, 'emailComparator')
    emailAddressCollection.addIndex('emailAddress', 'method',
                                    method=(emailComparator, 'cmpAddress'), 
                                    monitor='emailAddress')
    emailAddressCollection.addIndex('fullName', 'method',
                                    method=(emailComparator, 'cmpFullName'), 
                                    monitor='fullName')

    # Contains all current and former me addresses
    meEmailAddressCollection = ListCollection.update(
        parcel, 'meEmailAddressCollection')

    meEmailAddressCollection.addIndex('emailAddress', 'method',
                                  method=(emailComparator, 'cmpAddress'),
                                  monitor='emailAddress')


    inSource = ToMeFilter.makeCollection(parcel, 'inSource', mailCollection)
    # this index must be added to shield from the duplicate
    # source (mailCollection) that is going to be in mine
    inSource.addIndex('__adhoc__', 'numeric')

    # The "In" collection
    inCollection = SmartCollection.update(parcel, 'inCollection',
        displayName=_(u"In"),
        source=inSource,
        trash=trashCollection,
        visible=True)
    mine.addSource(inCollection)

    outSource = FromMeFilter.makeCollection(parcel, 'outSource', mailCollection)
    # this index must be added to shield from the duplicate
    # source (mailCollection) that is going to be in mine
    outSource.addIndex('__adhoc__', 'numeric')

    # The "Out" collection
    outCollection = SmartCollection.update(parcel, 'outCollection',
        displayName=_(u"Out"),
        visible=True,
        source=outSource,
        trash=trashCollection,
    )
    mine.addSource(outCollection)

    allEventsCollection = IntersectionCollection.update(parcel,
        'allEventsCollection',
         sources=[allCollection, events]
    )

    searchResults = SmartCollection.update(
        parcel, 'searchResults',
        displayName = messages.UNTITLED)

    TriageStatusReminder.update(parcel, 'triageStatusReminder')
    startup.Startup.update(parcel, "installWatchers",
        invoke=__name__ + ".installWatchers"
    )

    tzInstallParcel(parcel)

def installWatchers(startup):
    """
    Helper function that allows our TriageStatusReminder to watch for
    changes in Events (and in particular, their startTimes)
    """
    from application import schema # we del'ed it below!
    myNamespace = schema.ns(__name__, startup.itsView)
    myNamespace.triageStatusReminder.installWatcher()
    myNamespace.masterEventWatcher.install()

del schema  # don't leave this lying where others might accidentally import it

