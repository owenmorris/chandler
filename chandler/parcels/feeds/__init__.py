__revision__  = "$Revision:6542 $"
__date__      = "$Date:2005-08-13 16:44:24 -0700 (Sat, 13 Aug 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from channels import (NewChannelFromURL, FeedChannel, FeedItem,
    FeedUpdateTaskClass)
from application import schema
import datetime


def installParcel(parcel, oldName=None):

    startup = schema.ns("osaf.startup", parcel)
    
    startup.PeriodicTask.update(parcel, "FeedUpdateTask",
        invoke="feeds.FeedUpdateTaskClass",
        run_at_startup=True,
        interval=datetime.timedelta(minutes=30)
    )

    # load our blocks parcel, too
    schema.synchronize(parcel.itsView, "feeds.blocks")

