__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import application.Parcel
import osaf.framework.webdav.Dav
from repository.util.UUID import UUID

SHARING = "http://osafoundation.org/parcels/osaf/framework/sharing"
EVENTS = "http://osafoundation.org/parcels/osaf/framework/blocks/Events"

class Parcel(application.Parcel.Parcel):

    def startupParcel(self):
        # Subscribe to the sharing update event
        event = Globals.parcelManager.lookup(SHARING, 'sharingUpdateEvent')
        Globals.notificationManager.Subscribe([event], UUID(),
         self._sharingUpdateCallback)
        event = Globals.parcelManager.lookup(SHARING, 'errorEvent')
        Globals.notificationManager.Subscribe([event], UUID(),
         self._errorCallback)

    def _sharingUpdateCallback(self, notification):
        # When we receive the event, display a dialog
        url = notification.data['share']
        if application.dialogs.Util.promptYesNo( \
         Globals.wxApplication.mainFrame, "Sharing Invitation",
         "Subscribe to %s?" % url):
            subscribeToWebDavCollection(url)

    def _errorCallback(self, notification):
        # When we receive this event, display the error
        error = notification.data['error']
        application.dialogs.Util.showAlert( \
         Globals.wxApplication.mainFrame, error)


def subscribeToWebDavCollection(url):
    """ Given a URL, tell the webdav subsystem to fetch the collection it
        points to, then add the collection to the sidebar. """

    collection = osaf.framework.webdav.Dav.DAV(url).get( )
    event = Globals.parcelManager.lookup(EVENTS,
     "NewItemCollectionItem")
    event.Post({'collection':collection})
    Globals.repository.commit()


def sendInvites(addresses, url):
    """ Tell the email subsystem to send a sharing invite to the given
        addresses. """
    for address in addresses:
        print address
    # validate the addresses
    # parcels.osaf.mail.sharing.<sendinvite>(address, url)

def manualSubscribeToCollection():
    """ Display a dialog box prompting the user for a webdav url to 
        subscribe to.  """

    url = application.dialogs.Util.promptUser( \
     Globals.wxApplication.mainFrame, "Subscribe to Collection...",
     "Collection URL:", "http://code-bear.com/dav/test_item_collection")
    if url is not None:
        subscribeToWebDavCollection(url)

def manualPublishCollection(collection):
    print 'Share collection "%s"' % collection.displayName
    url = application.dialogs.Util.promptUser( \
     Globals.wxApplication.mainFrame, "Publish Collection...",
     "URL to publish collection to:",
     "http://code-bear.com/dav/%s" % collection.itsUUID)
    if url is not None:
        addresses = application.dialogs.Util.promptUser( \
         Globals.wxApplication.mainFrame, "Publish Collection...",
         "Email address to send invites: (comma separated)", "")
        osaf.framework.webdav.Dav.DAV(url).put(collection)
        if addresses is not None:
            addresses = addresses.split(",")
            sendInvites(addresses, url)

def syncCollection(collection):
    if collection.hasAttributeValue('sharedURL'):
        print "Synchronizing", collection.sharedURL
        osaf.framework.webdav.Dav.DAV(collection.sharedURL).get()
    else:
        print "Collection hasn't been shared yet"



# Non-blocking methods that the mail thread can call to post events to the
# main thread:

def announceSharingUrl(url):
    """ Call this method to announce that an inbound sharing invitation has
        arrived. This method is non-blocking. """

    def _announceSharingUrl(url):
        event = Globals.parcelManager.lookup(SHARING, 'sharingUpdateEvent')
        event.Post( { 'share' : url } )

    Globals.wxApplication.PostAsyncEvent(_announceSharingUrl, url)

def announceError(error):
    """ Call this method to announce an error. This method is non-blocking. """

    def _announceError(error):
        event = Globals.parcelManager.lookup(SHARING, 'errorEvent')
        event.Post( { 'error' : error } )

    Globals.wxApplication.PostAsyncEvent(_announceError, error)

