
""" Class used for Items of Kind Task
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.contentmodel.tasks"

import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.contacts.Contacts as Contacts

from datetime import datetime, timedelta


class TaskMixin(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/tasks/TaskMixin"

    """
      Task Mixin is the bag of Task-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    def __init__ (self, name=None, parent=None, kind=None, view=None):
        super (TaskMixin, self).__init__(name, parent, kind, view)

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
            if not isinstance(whoFrom, Contacts.Contact):
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
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/tasks/TaskEventExtraMixin"

    """
      Task Event Extra Mixin is the bag of attributes that
    appears when you have an Item that is both a Task and a
    CalendarEvent.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    def __init__ (self, name=None, parent=None, kind=None, view=None):
        super (TaskEventExtraMixin, self).__init__(name, parent, kind, view)

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
    myKindID = None
    myKindPath = "//parcels/osaf/contentmodel/tasks/Task"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(Task, self).__init__(name, parent, kind, view)
