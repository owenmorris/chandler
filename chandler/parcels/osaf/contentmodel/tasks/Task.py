
""" Class used for Items of Kind Task
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.item.Item as Item
import mx.DateTime as DateTime
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.Notes as Notes
import application.Globals as Globals


class TaskParcel(application.Parcel.Parcel):
    def startupParcel(self):
        super(TaskParcel, self).startupParcel()
        self._setUUIDs()

    def onItemLoad(self):
        super(TaskParcel, self).onItemLoad()
        self._setUUIDs()

    def _setUUIDs(self):
        taskKind = self['Task']
        TaskParcel.taskKindID = taskKind.itsUUID
        TaskParcel.taskMixinKindID = self['TaskMixin'].itsUUID
        TaskParcel.taskEventExtraMixinKindID = self['TaskEventExtraMixin'].itsUUID

    def getTaskKind(cls):
        assert cls.taskKindID, "Task parcel not yet loaded"
        return Globals.repository[cls.taskKindID]

    getTaskKind = classmethod(getTaskKind)

    def getTaskMixinKind(cls):
        assert cls.taskMixinKindID, "Task parcel not yet loaded"
        return Globals.repository[cls.taskMixinKindID]
    
    getTaskMixinKind = classmethod(getTaskMixinKind)

    def getTaskEventExtraMixinKind(cls):
        assert cls.taskEventExtraMixinKindID, "Task parcel not yet loaded"
        return Globals.repository[cls.taskEventExtraMixinKindID]
    
    getTaskEventExtraMixinKind = classmethod(getTaskEventExtraMixinKind)

    taskKindID = None
    taskMixinKindID = None
    taskEventExtraMixinKindID = None

class TaskMixin(Item.Item):
    """
      Task Mixin is the bag of Task-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    def __init__ (self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = TaskParcel.getTaskMixinKind()
        super (TaskMixin, self).__init__(name, parent, kind)

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
        self.dueDate = DateTime.now() + DateTime.DateTimeDelta(0,1)

        # default the title to any super class "about" definition
        try:
            self.about = self.getAnyAbout ()
        except AttributeError:
            pass

        # default the requestor to any super class "whoFrom" definition
        try:
            self.requestor = self.getAnyWhoFrom ()
        except AttributeError:
            pass

        # default the requestee to any super class "who" definition
        try:
            # shallow copy the list
            self.requestee = self.getAnyWho ()
        except AttributeError:
            pass

    def getAnyDate (self):
        """
        Get any non-empty definition for the "date" attribute.
        """
        try:
            return self.dueDate
        except AttributeError:
            pass
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

class TaskEventExtraMixin(Item.Item):
    """
      Task Event Extra Mixin is the bag of attributes that
    appears when you have an Item that is both a Task and a
    CalendarEvent.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    def __init__ (self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = TaskParcel.getTaskEventExtraMixinKind()
        super (TaskEventExtraMixin, self).__init__(name, parent, kind)

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
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = Globals.repository.findPath("//parcels/osaf/contentmodel/tasks/Task")
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        super(Task, self).__init__(name, parent, kind)

