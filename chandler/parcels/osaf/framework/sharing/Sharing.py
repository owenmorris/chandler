__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import application.Parcel
import osaf.framework.webdav.Dav
import osaf.mail.message
from repository.util.UUID import UUID
import application.dialogs.PublishCollection
from repository.item.Query import KindQuery

SHARING = "http://osafoundation.org/parcels/osaf/framework/sharing"
EVENTS = "http://osafoundation.org/parcels/osaf/framework/blocks/Events"
CONTENT = "http://osafoundation.org/parcels/osaf/contentmodel"

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
        url = notification.data['share'].strip()
        collectionName = notification.data['name'].strip()
        fromAddress = notification.data['from'].strip()
        print "Received invite from %s; collection '%s' at %s" % (fromAddress,
         collectionName, url)
        collection = collectionFromSharedUrl(url)
        if collection is not None:
            application.dialogs.Util.showAlert( \
             Globals.wxApplication.mainFrame,
             "Received an invite for an already subscribed collection:\n"
             "%s\n%s" % (collection.displayName, url))
        else:
            if application.dialogs.Util.promptYesNo( \
             Globals.wxApplication.mainFrame, "Sharing Invitation",
             "%s\nhas invited you to subscribe to '%s'\nWould you like to accept the invitation?" % (fromAddress, collectionName) ):
                subscribeToWebDavCollection(url)

    def _errorCallback(self, notification):
        # When we receive this event, display the error
        error = notification.data['error']
        application.dialogs.Util.showAlert( \
         Globals.wxApplication.mainFrame, error)


def subscribeToWebDavCollection(url):
    """ Given a URL, tell the webdav subsystem to fetch the collection it
        points to, then add the collection to the sidebar. """

    collection = collectionFromSharedUrl(url)
    if collection is not None:
        application.dialogs.Util.showAlert( \
         Globals.wxApplication.mainFrame,
         "Already subscribed to collection '%s':\n"
         "%s" % (collection.displayName, url))
        return

    collection = osaf.framework.webdav.Dav.DAV(url).get( )

    # @@@ Hmm, this should always have a displayName
    if not collection.hasAttributeValue("displayName"):
        collection.displayName = "Imported"

    event = Globals.parcelManager.lookup(EVENTS,
     "NewItemCollectionItem")
    event.Post({'collection':collection})
    Globals.repository.commit()

def manualSubscribeToCollection():
    """ Display a dialog box prompting the user for a webdav url to 
        subscribe to.  """

    url = application.dialogs.Util.promptUser( \
     Globals.wxApplication.mainFrame, "Subscribe to Collection...",
     "Collection URL:", "http://code-bear.com/dav/test_item_collection")
    if url is not None:
        subscribeToWebDavCollection(url)

def manualPublishCollection(collection):
    application.dialogs.PublishCollection.ShowPublishCollectionsDialog( \
     Globals.wxApplication.mainFrame, collection)

def syncCollection(collection):
    if isShared(collection):
        print "Synchronizing", collection.sharedURL
        osaf.framework.webdav.Dav.DAV(collection.sharedURL).get()

def isShared(collection):
    return collection.hasAttributeValue('sharedURL') and collection.sharedURL

def collectionFromSharedUrl(url):
    kind = Globals.parcelManager.lookup(CONTENT, "ItemCollection")
    for item in KindQuery().run([kind]):
        if isShared(item):
            if str(item.sharedURL) == (url):
                return item
    return None

def getWebDavPath():
    acct = Globals.parcelManager.lookup(SHARING, 'WebDAVAccount')
    if acct.host:
        return "http://%s/%s" % (acct.host, acct.path)
    else:
        return None

def getWebDavAccount():
    return Globals.parcelManager.lookup(SHARING, 'WebDAVAccount')

# Non-blocking methods that the mail thread can call to post events to the
# main thread:

def announceSharingInvitation(url, collectionName, fromAddress):
    """ Call this method to announce that an inbound sharing invitation has
        arrived. This method is non-blocking. """

    def _announceSharingInvitation(url, collectionName, fromAddress):
        event = Globals.parcelManager.lookup(SHARING, 'sharingUpdateEvent')
        event.Post( { 'share' : url, 'name' : collectionName,
         'from' : fromAddress } )

    Globals.wxApplication.PostAsyncEvent(_announceSharingInvitation, url,
     collectionName, fromAddress)

def announceError(error):
    """ Call this method to announce an error. This method is non-blocking. """

    def _announceError(error):
        event = Globals.parcelManager.lookup(SHARING, 'errorEvent')
        event.Post( { 'error' : error } )

    Globals.wxApplication.PostAsyncEvent(_announceError, error)

