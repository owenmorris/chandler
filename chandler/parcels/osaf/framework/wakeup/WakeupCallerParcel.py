__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__    = "osaf.framework.wakeup"

import application, datetime
from application import schema

import osaf.contentmodel.ContentModel as ContentModel
import WakeupCaller

class WakeupCall(ContentModel.ContentItem):

    schema.kindInfo(displayName = "Wakeup Call")

    wakeupCallClass = schema.One(
        schema.Class,
        displayName = 'The WakeupCall Sub-Class',
        doc = 'The osaf.framework.wakeup.WakupCaller.WakeupCall sub-class full path and name',
        initialValue = WakeupCaller.WakeupCall,
    )
    callOnStartup = schema.One(
        schema.Boolean,
        displayName = 'Call on Start Time',
        initialValue = False,
    )
    repeat = schema.One(
        schema.Boolean,
        displayName = 'Repeat Wakeup Call',
        initialValue = False,
    )
    enabled = schema.One(
        schema.Boolean,
        displayName = 'Is The Wakeup Call Enabled',
        initialValue = True,
    )
    delay = schema.One(
        schema.TimeDelta,
        displayName = 'Delay Between Calls',
        initialValue = datetime.timedelta(0),
    )

