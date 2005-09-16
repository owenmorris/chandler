# Import classes whose schemas are part of this parcel
# (this should include all ContentItem subclasses in this package)
#
from items import (
    ContentKind, ContentItem, ImportanceEnum, Group, Project
)
from notes import Note
from contacts import Contact, ContactName
from calendar.Calendar import CalendarEvent, CalendarEventMixin
from calendar.Calendar import Calendar, Location, RecurrencePattern
from tasks import Task, TaskMixin
from mail import EmailAddress
from collections import KindCollection, AbstractCollection, \
     DifferenceCollection, UnionCollection, IntersectionCollection, \
     FilteredCollection, ListCollection, InclusionExclusionCollection

import tasks, mail, calendar.Calendar

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
    collections.installParcel(parcel, oldVersion)

del schema  # don't leave this lying where others might accidentally import it

