
""" Class used for Items of Kind Task
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
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

    def getTaskKind(cls):
        assert cls.taskKindID, "Task parcel not yet loaded"
        return Globals.repository[cls.taskKindID]

    getTaskKind = classmethod(getTaskKind)

    def getTaskMixinKind(cls):
        assert cls.taskMixinKindID, "Task parcel not yet loaded"
        return Globals.repository[cls.taskMixinKindID]
    
    getTaskMixinKind = classmethod(getTaskMixinKind)

    taskKindID = None
    taskMixinKindID = None

class TaskMixin(Item.Item):
    """
      Task Mixin is the bag of Task-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    pass

class Task(Notes.Note, TaskMixin):
    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = Globals.repository.findPath("//parcels/osaf/contentmodel/tasks/Task")
        super(Task, self).__init__(name, parent, kind)

