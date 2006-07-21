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


""" Class used for Items of Kind Task
"""

__all__ = ['TaskStatusEnum', 'TaskMixin', 'Task', 'TaskEventExtraMixin']

import items, notes
from contacts import Contact

from datetime import datetime, timedelta
from application import schema

from PyICU import ICUtzinfo


class TaskStatusEnum(schema.Enumeration):
    values = "todo", "blocked", "done", "deferred"


class TaskMixin(items.ContentItem):
    """
    This is the set of Task-specific attributes.

    Task Mixin is the bag of Task-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    
    schema.kindInfo(
        description = 
            "This Kind is 'mixed in' to others kinds to create Kinds that "
            "can be instantiated"
    )

    reminderTime = schema.One(
        schema.DateTimeTZ,
        displayName = u'ReminderTime',
        doc = 'This may not be general enough',
    )
    requestor = schema.One(
        Contact,
        displayName = u'Requestor',
        description =
            "Issues:\n"
            '   Type could be Contact, EmailAddress or String\n'
            '   Think about using the icalendar terminology\n',
        inverse = Contact.requestedTasks,
    )
    requestee = schema.Sequence(
        items.ContentItem,
        displayName = u'Requestee',
        description =
            "Issues:\n"
            '   Type could be Contact, EmailAddress or String\n'
            '   Think about using the icalendar terminology\n',
        otherName = 'taskRequests',
    )

    taskStatus = schema.One(
        TaskStatusEnum,
        displayName = u'Task Status',
    )
    dueDate = schema.One(schema.DateTimeTZ)
    whoFrom = schema.One(redirectTo = 'requestor')
    about = schema.One(redirectTo = 'displayName')

    schema.addClouds(
        copying = schema.Cloud(
            requestor, requestee
        )
    )
    
    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(TaskMixin, self).InitOutgoingAttributes ()
        except AttributeError:
            pass

        TaskMixin._initMixin (self) # call our init, not the method of a subclass

    def _initMixin (self):
        """
          Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """
        # default status is To Do
        self.taskStatus = 'todo'

        # default due date is 1 hour hence
        self.dueDate = datetime.now(ICUtzinfo.default) + timedelta(hours=1)

        # default the title to any super class "about" definition
        try:
            self.about = self.getAnyAbout ()
        except AttributeError:
            pass

        # TBD - default the requestee to any super class "who" definition
        # requestee attribute is currently not implemented.

class TaskEventExtraMixin(items.ContentItem):
    """
      Task Event Extra Mixin is the bag of attributes that
    appears when you have an Item that is both a Task and a
    CalendarEvent.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """

    schema.kindInfo(
        description =
            "The attributes specific to an item that is both a task and an "
            "event.  This is additional 'due by' information. "
    )

    dueByDate = schema.One(
        schema.DateTimeTZ,
        displayName = u'Due by Date',
        doc = 'The date when a Task Event is due.',
    )
    dueByRecurrence = schema.Sequence(
        'osaf.pim.calendar.Calendar.RecurrencePattern',
        displayName = u'Due by Recurrence',
        doc = 'Recurrence information for a Task Event.',
    )
    dueByTickler = schema.One(
        schema.DateTimeTZ,
        displayName = u'Due by Tickler',
        doc = 'The reminder information for a Task Event.',
    )

    def InitOutgoingAttributes (self):
        """ Init any attributes on ourself that are appropriate for
        a new outgoing item.
        """
        try:
            super(TaskEventExtraMixin, self).InitOutgoingAttributes ()
        except AttributeError:
            pass
        TaskEventExtraMixin._initMixin (self) # call our init, not the method of a subclass

    def _initMixin (self):
        """
          Init only the attributes specific to this mixin.
        Called when stamping adds these attributes, and from __init__ above.
        """
        # default the dueByDate to the task's dueDate
        try:
            self.dueByDate = self.dueDate
        except AttributeError:
            pass


class Task(TaskMixin, notes.Note):
    """
    Task type
    
    Issues:
      - Do we want to support the idea of tasks having sub-tasks? If so, 
        then we need to add attributes for 'superTask' and 'subTasks'.

      - Task should maybe have a 'Timezone' attribute.
    """

