__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import repository.item.Item as Item
import osaf.contentmodel.ContentModel as ContentModel
import application.Globals as Globals
import chandlerdb.util.UUID as UUID

class WakeupCallerParcel(application.Parcel.Parcel):

    def startupParcel(self):
        super(WakeupCallerParcel, self).startupParcel()
        self._setUUIDs()

    def onItemLoad(self):
        super(WakeupCallerParcel, self).onItemLoad()
        self._setUUIDs()

    def _setUUIDs(self):
        WakeupCallKind = self['WakeupCall']
        WakeupCallerParcel.wakeupCallKindID = WakeupCallKind.itsUUID

    def getWakeupCallKind(cls):
        assert cls.wakeupCallKindID, "wakeup call not yet loaded"
        return Globals.repository[cls.wakeupCallKindID]

        wakeupCallKindID = None

    getWakeupCallKind = classmethod(getWakeupCallKind)

class WakeupCall(Item.Item):

    def __init__(self, name=None, parent=None, kind=None):
        if not kind:
            kind = Globals.repository.findPath("//parcels/osaf/framework/wakeup/WakeupCall")

        if not parent:
            parent = ContentModel.ContentModel.getContentItemParent()

        super(WakeupCall, self).__init__(name, parent, kind)
