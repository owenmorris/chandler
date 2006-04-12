__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from channels import (newChannelFromURL, FeedChannel, FeedItem,
    FeedUpdateTaskClass, updateFeeds,
    FETCH_UPDATED, FETCH_NOCHANGE, FETCH_FAILED)

from application import schema
from osaf import pim
import datetime

def installParcel(parcel, oldName=None):
    from osaf import startup

    startup.PeriodicTask.update(parcel, "FeedUpdateTask",
        invoke="feeds.FeedUpdateTaskClass",
        run_at_startup=True,
        interval=datetime.timedelta(minutes=30)
    )

    # load our blocks parcel, too
    schema.synchronize(parcel.itsView, "feeds.blocks")
