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


# Import classes whose schemas are part of this parcel
# (this should include all ContentItem subclasses in this package)
#
from items import (
    ContentKind, ContentItem, ImportanceEnum, Group, Principal, 
    Project, Tag, TriageEnum, getTriageStatusName, getNextTriageStatus,
    Modification, UserNotification, isDead
)
from collections import (
    KindCollection, ContentCollection, DifferenceCollection, UnionCollection,
    IntersectionCollection, FilteredCollection, ListCollection, SmartCollection, 
    AppCollection, IndexedSelectionCollection, AllIndexDefinitions,
    IndexDefinition, AttributeIndexDefinition, MethodIndexDefinition,
)

from stamping import Stamp, has_stamp
from notes import Note
from contacts import Contact, ContactName
from calendar.Calendar import CalendarEvent, EventStamp, LONG_TIME, zero_delta
from calendar.Calendar import EventComparator, Location, RecurrencePattern
from calendar.TimeZone import installParcel as tzInstallParcel
from calendar.DateTimeUtil import (ampmNames, durationFormat, mediumDateFormat, 
     monthNames, sampleDate, sampleTime, shortDateFormat, shortTimeFormat, 
     weekdayNames, weekdayName)
from reminders import Reminder, Remindable
from tasks import Task, TaskStamp
from mail import EmailAddress, EmailComparator
from application.Parcel import Reference
from repository.item.Item import Item
from PyICU import ICUtzinfo

import tasks, mail, calendar.Calendar
from i18n import ChandlerMessageFactory as _


# Stamped Kinds

from application import schema

class NonOccurrenceFilter(Item):

    def isNonOccurrence(self, view, uuid):
        occurrences, modificationFor, occurrenceFor = view.findValues(uuid,
                           (EventStamp.occurrences.name, None),
                           (EventStamp.modificationFor.name, None),
                           (EventStamp.occurrenceFor.name, None))

        if occurrences is not None and len(occurrences) > 0:
            return True # a master
        elif not modificationFor and occurrenceFor:
            return False # a plain occurrence, not a modification
        else:
            return True # non-recurring, or a modification

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
        return IndexDefinition.findInheritedValues(view, uuid,
                                      type(self).attrAndDefault)[0]

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
    Reference.update(parcel, 'currentMailAccount')
    Reference.update(parcel, 'currentSMTPAccount')

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

    nonRecurringNotes = FilteredCollection.update(parcel, 'nonRecurringNotes',
        source=mineNotes,
        filterMethod=(NonOccurrenceFilter(None, parcel), 'isNonOccurrence'),
        filterAttributes=[EventStamp.occurrenceFor.name,
                          EventStamp.modificationFor.name,
                          EventStamp.occurrences.name]
    )

    itemKindCollection = KindCollection.update(
        parcel, 'contentItems',
        kind = ContentItem.getKind(view),
       recursive=True)
       
    itemsWithRemindersIncludingTrash = FilteredCollection.update(
        parcel, 'itemsWithRemindersIncludingTrash',
        source=itemKindCollection,
        filterExpression="view.hasTrueValue(uuid, '%s')" % (
                                                    Remindable.reminders.name,),
        filterAttributes=[Remindable.reminders.name])

    itemsWithReminders = AppCollection.update(
        parcel, 'itemsWithReminders',
        source=itemsWithRemindersIncludingTrash,
        exclusions=trashCollection,
        trash=None,
    )

    # the monitor list assumes all reminders will be relativeTo
    # effectiveStartTime, which is true in 0.6, but may not be in the future
    Remindable.addIndex(itemsWithReminders, 'reminderTime', 'compare',
                        compare='cmpReminderTime',
                        monitor=(EventStamp.startTime, EventStamp.allDay,
                                 EventStamp.anyTime, Remindable.reminders))


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
    EventStamp.addIndex(events, 'effectiveStartNoTZ', 'method',
                    method=(eventComparator, 'cmpStartTimeNoTZ'),
                    monitor=(EventStamp.startTime, EventStamp.allDay,
                             EventStamp.anyTime))
    EventStamp.addIndex(events, 'effectiveEndNoTZ', 'method',
                    method=(eventComparator, 'cmpEndTimeNoTZ'),
                    monitor=(EventStamp.startTime, EventStamp.allDay,
                             EventStamp.anyTime, EventStamp.duration))
    
    EventStamp.addIndex(view, 'icalUID', 'value', attribute=Note.icalUID)
    
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
    longEvents.addIndex('effectiveStartNoTZ', 'subindex',
                        superindex=(events, events.__collection__,
                                    'effectiveStartNoTZ'))
    longEvents.addIndex('effectiveEnd', 'subindex',
                        superindex=(events, events.__collection__,
                                    'effectiveEnd'))
    longEvents.addIndex('effectiveEndNoTZ', 'subindex',
                        superindex=(events, events.__collection__,
                                    'effectiveEndNoTZ'))
    
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


    EventStamp.addIndex(masterEvents, "recurrenceEnd", 'method',
                        method=(eventComparator, 'cmpRecurEnd'),
                        monitor=(EventStamp.recurrenceEnd,))

    EventStamp.addIndex(masterEvents, "recurrenceEndNoTZ", 'method',
                        method=(eventComparator, 'cmpRecurEndNoTZ'),
                        monitor=(EventStamp.recurrenceEnd))

    EventStamp.addIndex(masterEvents, 'effectiveStart', 'subindex',
                          superindex=(events, events.__collection__,
                                      'effectiveStart'))
    EventStamp.addIndex(masterEvents, 'effectiveStartNoTZ', 'subindex',
                          superindex=(events, events.__collection__,
                                      'effectiveStartNoTZ'))

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

    meAddressCollection = ListCollection.update(
        parcel, 'meAddressCollection')

    meAddressCollection.addIndex('emailAddress', 'method',
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

    KindCollection.update(parcel, 'notificationCollection',
        displayName=_(u"Notifications"),
        kind=UserNotification.getKind(view),
        recursive=True).addIndex('timestamp', 'value', attribute='timestamp')

    searchResults = ListCollection.update(
        parcel, 'searchResults',
        displayName=_(u"Search Results"))

    tzInstallParcel(parcel)


del schema  # don't leave this lying where others might accidentally import it

