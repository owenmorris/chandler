# Import classes whose schemas are part of this parcel
# (this should include all ContentItem subclasses in this package)
#
from items import (
    ContentKind, ContentItem, ImportanceEnum, Group, Project, Tag, TriageEnum,
    UserNotification
)
from notes import Note
from contacts import Contact, ContactName
from calendar.Calendar import CalendarEvent, CalendarEventMixin
from calendar.Calendar import Calendar, Location, RecurrencePattern
from calendar.Reminders import Reminder, RemindableMixin
from tasks import Task, TaskMixin
from mail import EmailAddress
from application.Parcel import Reference
from collections import KindCollection, AbstractCollection, \
     DifferenceCollection, UnionCollection, IntersectionCollection, \
     FilteredCollection, ListCollection, InclusionExclusionCollection, \
     IndexedSelectionCollection, CollectionColors
from structs import ColorType

import tasks, mail, calendar.Calendar
from i18n import OSAFMessageFactory as _


# Collection colors
# in the form 'Color', _('LocalizableColorString'), 360-degree based hue
import colorsys
collectionHues = [('Blue', _(u'Blue'), 210),
                  ('Green', (u'Green'), 120),
                  ('Rose', _(u'Rose'), 0),
                  ('Salmon', _(u'Salmon'), 30),
                  ('Purple', _(u'Purple'), 270),
                  ('Violet', _(u'Violet'), 240),
                  ('Fuschia', _(u'Fuschia'), 330)]

# Stamped Kinds

from application import schema

class MailedTask(tasks.TaskMixin,mail.MailMessage):
    schema.kindInfo(
        displayName = u"Mailed Task",
        description = "A Task stamped as a Mail, or vica versa",
    )

class MailedEvent(calendar.Calendar.CalendarEventMixin,mail.MailMessage):
    schema.kindInfo(
        displayName = u"Mailed Event",
        description = "An Event stamped as a Mail, or vica versa",
    )

class EventTask(
    tasks.TaskMixin,
    tasks.TaskEventExtraMixin,
    calendar.Calendar.CalendarEvent
):
    schema.kindInfo(
        displayName = u"Event Task",
        description = "A Task stamped as an Event, or vica versa",
    )

class MailedEventTask(
    tasks.TaskMixin,
    tasks.TaskEventExtraMixin,
    calendar.Calendar.CalendarEventMixin,
    mail.MailMessage
):
    schema.kindInfo(
        displayName = u"Mailed Event Task",
        description = "A Task stamped as an Event stamped as Mail, in any sequence",
    )

def installParcel(parcel, oldVersion=None):
    view = parcel.itsView

    collectionColors = CollectionColors.update(parcel, 'collectionColors',
        colors = [],
        colorIndex = 0
    )

    for shortName, title, hue in collectionHues:
        rgb = colorsys.hsv_to_rgb(hue/360.0, 0.5, 1.0)
        ct = ColorType(rgb[0]*255, rgb[1]*255, rgb[2]*255, 255)
        collectionColors.colors.append(ct)

    collections.installParcel(parcel, oldVersion)
    Reference.update(parcel, 'currentContact')
    Reference.update(parcel, 'currentMailAccount')
    Reference.update(parcel, 'currentSMTPAccount')

    trashCollection = ListCollection.update(
        parcel, 'trashCollection',
        displayName=_(u"Trash"),
        renameable=False,
        dontDisplayAsCalendar=True,
        outOfTheBoxCollection = True)

    notes = KindCollection.update(
        parcel, 'notes',
        kind = Note.getKind(view),
        recursive = True)

    nonRecurringNotes = FilteredCollection.update(parcel, 'nonRecurringNotes',
        source=notes,
        filterExpression=u"(not item.hasLocalAttributeValue('isGenerated') or not getattr(item, 'isGenerated', False)) and not item.hasLocalAttributeValue('modificationFor')",
        filterAttributes=['isGenerated', 'modificationFor']
    )

    notMine = UnionCollection.update(parcel, 'notMine')
    # @@@MOR Hmm, I need to somehow make rep's initialValue be a MultiUnion()
    notMine._sourcesChanged()

    mine = DifferenceCollection.update(parcel, 'mine',
        sources=[nonRecurringNotes, notMine]
    )

    # the "All" collection
    allCollection = InclusionExclusionCollection.update(parcel, 'allCollection',
        displayName=_(u"My items"),
        renameable = False,
        outOfTheBoxCollection = True,

        displayNameAlternatives = {'None': _(u'My items'),
                                   'MailMessageMixin': _(u'My mail'),
                                   'CalendarEventMixin': _(u'My calendar'),
                                   'TaskMixin': _(u'My tasks')}
    ).setup(source=mine, exclusions=trashCollection, trash=None)
    # kludge to improve on bug 4144 (not a good long term fix but fine for 0.6)
    allCollection.rep.addIndex('__adhoc__', 'numeric')


    events = KindCollection.update(parcel, 'events',
        kind = CalendarEventMixin.getKind(view),
        recursive = True)
    events.rep.addIndex("effectiveStart", 'compare', compare='cmpStartTime',
                        monitor=('startTime', 'allDay', 'anyTime'))
    events.rep.addIndex('effectiveEnd', 'compare', compare='cmpEndTime',
                    monitor=('startTime', 'allDay', 'anyTime', 'duration'))
    events.rep.addIndex('icalUID', 'value', attribute='icalUID')


    # bug 4477
    eventsWithReminders = FilteredCollection.update(
        parcel, 'eventsWithReminders',
        source=events,
        filterExpression='item.reminders',
        filterAttributes=['reminders'])

    # the monitor list assumes all reminders will be relativeTo
    # effectiveStartTime, which is true in 0.6, but may not be in the future
    eventsWithReminders.rep.addIndex('reminderTime', 'compare',
                                     compare='cmpReminderTime',
                                     monitor=('startTime', 'allDay', 'anyTime'
                                              'reminders'))

    masterFilter = "item.hasTrueAttributeValue('occurrences') and "\
                   "item.hasTrueAttributeValue('rruleset')"
    masterEvents = FilteredCollection.update(parcel, 'masterEvents',
        source = events,
        filterExpression = masterFilter,
        filterAttributes = ['occurrences', 'rruleset'])

    masterEvents.rep.addIndex("recurrenceEnd", 'compare', compare='cmpRecurEnd',
                        monitor=('recurrenceEnd'))

    locations = KindCollection.update(
        parcel, 'locations',
        kind = Location.getKind(view),
        recursive = True)

    locations.rep.addIndex('locationName', 'attribute', attribute = 'displayName')

    mailCollection = KindCollection.update(
        parcel, 'mailCollection',
        kind = mail.MailMessageMixin.getKind(view),
        recursive = True)

    emailAddressCollection = \
        KindCollection.update(parcel, 'emailAddressCollection',
                              kind=mail.EmailAddress.getKind(view),
                              recursive=True)
    emailAddressCollection.rep.addIndex('emailAddress', 'compare',
                                        compare='_compareAddr', 
                                        monitor='emailAddress')
    emailAddressCollection.rep.addIndex('fullName', 'compare',
                                        compare='_compareFullName', 
                                        monitor='fullName')

    inSource = FilteredCollection.update(
        parcel, 'inSource',
        source=mailCollection,
        filterExpression=u'getattr(item, \'isInbound\', False)',
        filterAttributes=['isInbound'])

    # The "In" collection
    inCollection = InclusionExclusionCollection.update(parcel, 'inCollection',
        displayName=_(u"In"),
        renameable=False,
        dontDisplayAsCalendar=True,
        outOfTheBoxCollection = True,
        visible = False
    ).setup(source=inSource)

    outSource = FilteredCollection.update(parcel, 'outSource',
        source=mailCollection,
        filterExpression=u'getattr(item, \'isOutbound\', False)',
        filterAttributes=['isOutbound'])

    # The "Out" collection
    outCollection = InclusionExclusionCollection.update(parcel, 'outCollection',
        displayName=_(u"Out"),
        renameable=False,
        dontDisplayAsCalendar=True,
        outOfTheBoxCollection = True,
        visible = False
    ).setup(source=outSource)

    trashCollection.setup( ) # @@@MOR Why is this done here and not earlier?

    allEventsCollection = IntersectionCollection.update(parcel,
        'allEventsCollection',
         sources=[allCollection, events]
    )

    KindCollection.update(parcel, 'notificationCollection',
        displayName=_(u"Notifications"),
        kind=UserNotification.getKind(view),
        recursive=True)# .rep.addIndex('timestamp', 'compare',
                       #              compare='_compareTimestamp',
                       #              monitor='timestamp')

del schema  # don't leave this lying where others might accidentally import it

