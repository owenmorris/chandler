
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
        TaskParcel.taskAspectKindID = self['TaskAspect'].itsUUID

    def getTaskKind(cls):
        assert cls.taskKindID, "Task parcel not yet loaded"
        return Globals.repository[cls.taskKindID]

    getTaskKind = classmethod(getTaskKind)

    def getTaskAspectKind(cls):
        assert cls.taskAspectKindID, "Task parcel not yet loaded"
        return Globals.repository[cls.taskAspectKindID]
    
    getTaskAspectKind = classmethod(getTaskAspectKind)

    taskKindID = None
    taskAspectKindID = None

class TaskAspect(Item.Item):
    """
      Task Aspect is the bag of Task-specific attributes.
    We only instantiate these Items when we "unstamp" an
    Item, to save the attributes for later "restamping".
    """
    pass

class Task(ContentModel.ContentItem, TaskAspect):

    def __init__(self, name=None, parent=None, kind=None):
        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()
        if not kind:
            kind = Globals.repository.findPath("//parcels/osaf/contentmodel/tasks/Task")
        super(Task, self).__init__(name, parent, kind)

        self.whoAttribute = "requestor"
        self.dateAttribute = "dueDate"

