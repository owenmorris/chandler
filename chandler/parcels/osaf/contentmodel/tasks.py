""" Class used for Items of Kind Task
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

__all__ = ['TaskStatusEnum', 'TaskMixin', 'Task', 'TaskEventExtraMixin']

import ContentModel, Notes
from contacts import Contact

from datetime import datetime, timedelta
from application import schema


class TaskStatusEnum(schema.Enumeration):
    schema.kindInfo(displayName="Task Status")
    values = "todo", "blocked", "done", "deferred"


class TaskMixin(ContentModel.ContentItem):
    """This is the set of Task-specific attributes.

      Task Mixin is the bag of Task-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    
    schema.kindInfo(
        displayName = "Task Mixin Kind",
        description = 
            "This Kind is 'mixed in' to others kinds to create Kinds that "
            "can be instantiated"
    )

    recurrence = schema.Sequence(
        displayName = 'Recurrence Patterns',
        doc = 'This is a placeholder and probably not used for 0.5',
    )
    reminderTime = schema.One(
        schema.DateTime,
        displayName = 'ReminderTime',
        doc = 'This may not be general enough',
    )
    requestor = schema.One(
        Contact,
        displayName = 'Requestor',
        issues = [
            'Type could be Contact, EmailAddress or String',
            'Think about using the icalendar terminology'
        ],
        inverse = Contact.requestedTasks,
    )
    requestee = schema.Sequence(
        ContentModel.ContentItem,
        displayName = 'Requestee',
        issues = [
            'Type could be Contact, EmailAddress or String',
            'Think about using the icalendar terminology'
        ],
        otherName = 'taskRequests',
    )

    taskStatus = schema.One(
        TaskStatusEnum,
        displayName = 'Task Status',
    )
    dueDate = schema.One(schema.DateTime, displayName = 'Due date')
    who = schema.One(redirectTo = 'requestee')
    whoFrom = schema.One(redirectTo = 'requestor')
    about = schema.One(redirectTo = 'displayName')

    # XXX these two links should probably point to TaskMixin instead of
    #     Task, because as-is they won't support stamping.  Note that if
    #     this is corrected, the opposite ends should be set using 'inverse'
    #     instead of 'otherName'.
    dependsOn = schema.Sequence(
        'Task', displayName = 'Depends On', otherName = 'preventsProgressOn',
    )
    preventsProgressOn = schema.Sequence(
        'Task', displayName = 'Blocks', otherName = 'dependsOn',
    )

    schema.addClouds(
        copying = schema.Cloud(
            requestor, requestee, dependsOn, preventsProgressOn
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
        self.dueDate = datetime.now() + timedelta(hours=1)

        # default the title to any super class "about" definition
        try:
            self.about = self.getAnyAbout ()
        except AttributeError:
            pass

        # default the requestor to any super class "whoFrom" definition
        try:
            whoFrom = self.getAnyWhoFrom ()

            # I only want a Contact
            if not isinstance(whoFrom, Contact):
                whoFrom = self.getCurrentMeContact(self.itsView)

            self.requestor = whoFrom
        except AttributeError:
            pass

        """ @@@ Commenting out this block
        requestee can only accept Contact items.  At some point
        this code will need inspect the results of getAnyWho() and
        create Contact items for any EmailAddresses in the list

        # default the requestee to any super class "who" definition
        try:
            shallow copy the list
            self.requestee = self.getAnyWho ()

        except AttributeError:
            pass

        @@@ End block comment """

    def getAnyDate (self):
        """
        Get any non-empty definition for the "date" attribute.
        """
        
        # @@@ Don't do this for now, per bug 2654; will be revisited in 0.6.
        """
        try:
            return self.dueDate
        except AttributeError:
            pass
        """
        return super (TaskMixin, self).getAnyDate ()

    def getAnyWho (self):
        """
        Get any non-empty definition for the "who" attribute.
        """
        try:
            return self.requestee
        except AttributeError:
            pass
        return super (TaskMixin, self).getAnyWho ()

    def getAnyWhoFrom (self):
        """
        Get any non-empty definition for the "whoFrom" attribute.
        """
        try:
            return self.requestor
        except AttributeError:
            pass
        return super (TaskMixin, self).getAnyWhoFrom ()

class TaskEventExtraMixin(ContentModel.ContentItem):
    """
      Task Event Extra Mixin is the bag of attributes that
    appears when you have an Item that is both a Task and a
    CalendarEvent.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """

    schema.kindInfo(
        displayName = "Task Event Extra Mixin Kind",
        description =
            "The attributes specific to an item that is both a task and an "
            "event.  This is additional 'due by' information. "
    )

    dueByDate = schema.One(
        schema.DateTime,
        displayName = 'Due by Date',
        doc = 'The date when a Task Event is due.',
    )
    dueByRecurrence = schema.Sequence(
        'osaf.contentmodel.calendar.Calendar.RecurrencePattern',
        displayName = 'Due by Recurrence',
        doc = 'Recurrence information for a Task Event.',
    )
    dueByTickler = schema.One(
        schema.DateTime,
        displayName = 'Due by Tickler',
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

class Task(TaskMixin, Notes.Note):

    schema.kindInfo(
        displayName = "Task",
        issues = [
            "Do we want to support the idea of tasks having sub-tasks? If so, "
            "then we need to add attributes for 'superTask' and 'subTasks'.",
            
            "Task should maybe have a 'Timezone' attribute.",
        ]
    )

