__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import osaf.contentmodel.ContentModel as ContentModel

class WakeupCall(ContentModel.ChandlerItem):
    myKindID = None
    myKindPath = "//parcels/osaf/framework/wakeup/WakeupCall"

    def __init__(self, name=None, parent=None, kind=None, view=None):
        super(WakeupCall, self).__init__(name, parent, kind, view)
