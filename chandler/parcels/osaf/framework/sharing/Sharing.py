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
import wx

SHARING = "http://osafoundation.org/parcels/osaf/framework/sharing"
EVENTS = "http://osafoundation.org/parcels/osaf/framework/blocks/Events"
CONTENT = "http://osafoundation.org/parcels/osaf/contentmodel"

class Parcel(application.Parcel.Parcel):

    def _sharingUpdateCallback(self, url, collectionName, fromAddress):
        # When we receive the event, display a dialog
        print "Received invite from %s; collection '%s' at %s" % (fromAddress,
         collectionName, url)
        collection = collectionFromSharedUrl(url)
        if collection is not None:
            # @@@ For 0.4 we will silently eat re-invites
            pass
            """
            application.dialogs.Util.ok( \
             Globals.wxApplication.mainFrame, "Sharing Invitation",
             "Received an invite for an already subscribed collection:\n" \
             "%s\n%s" % (collection.displayName, url))
            """
        else:
            if application.dialogs.Util.yesNo( \
             Globals.wxApplication.mainFrame, "Sharing Invitation",
             "%s\nhas invited you to subscribe to\n'%s'\n\n" \
             "Would you like to accept the invitation?" \
             % (fromAddress, collectionName) ):
                wx.Yield() # @@@ Give the UI a chance to redraw before
                           # long operation
                subscribeToWebDavCollection(url)

    def _errorCallback(self, error):
        # When we receive this event, display the error
        application.dialogs.Util.ok( \
         Globals.wxApplication.mainFrame, error)


def subscribeToWebDavCollection(url):
    """ Given a URL, tell the webdav subsystem to fetch the collection it
        points to, then add the collection to the sidebar. """

    collection = collectionFromSharedUrl(url)

    # See if we are already subscribed to the collection
    if collection is not None:
        application.dialogs.Util.ok( \
         Globals.wxApplication.mainFrame,
         "Already subscribed to collection '%s':\n"
         "%s" % (collection.displayName, url))
        return

    # Fetch the collection
    try:
        collection = osaf.framework.webdav.Dav.DAV(url).get( )
    except Exception, e:
        application.dialogs.Util.ok(Globals.wxApplication.mainFrame,
         "WebDAV Error",
         "Couldn't get collection from:\n%s\n\nException %s: %s" % \
         (url, repr(e), str(e)))
        raise

    # Add the collection to the sidebar by...
    event = Globals.parcelManager.lookup(EVENTS,
     "NewItemCollectionItem")
    args = {'collection':collection}
    # ...creating a new view (which gets returned as args['view'])...
    event.Post(args)
    Globals.repository.commit()
    # ...and selecting that view in the sidebar
    Globals.mainView.selectView(args['view'], showInDetailView=collection)


def manualSubscribeToCollection():
    """ Display a dialog box prompting the user for a webdav url to 
        subscribe to.  """
    # @@@ Obsolete, or for dev purposes only

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

        wx.Yield() # @@@ Give the UI a chance to redraw before
                   # long operation

        try:
            osaf.framework.webdav.Dav.DAV(collection.sharedURL).get()
        except Exception, e:
            application.dialogs.Util.ok(Globals.wxApplication.mainFrame,
             "WebDAV Error",
             "Couldn't sync collection '%s'\nto %s\n\nException %s: %s" % \
             (collection.displayName, collection.sharedURL, repr(e), str(e)))
            raise

def putCollection(collection, url):
    """ Putting a collection on the webdav server for the first time. """

    wx.Yield() # @@@ Give the UI a chance to redraw before
               # long operation

    try:
        osaf.framework.webdav.Dav.DAV(url).put(collection)
    except Exception, e:
        application.dialogs.Util.ok(Globals.wxApplication.mainFrame,
         "WebDAV Error",
         "Couldn't publish collection '%s'\nto %s\n\nException %s: %s" % \
         (collection.displayName, url, repr(e), str(e)))
        collection.sharedURL = None # consider it not shared
        raise

def isShared(collection):
    # @@@ Temporary hack until there is a better way to test for isShared
    return collection.hasAttributeValue('sharedURL') and (collection.sharedURL
     is not None)

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

def isMailSetUp():

    # Find imap account, and make sure email address is valid
    imap = Globals.repository.findPath("//parcels/osaf/mail/IMAPAccountOne")
    if not imap.emailAddress:
        return False

    # Find smtp account, and make sure server field is set
    smtp = Globals.repository.findPath("//parcels/osaf/mail/SMTPAccountOne")
    if not smtp.host:
        return False

    return True

# Non-blocking methods that the mail thread can use to call methods on the
# main thread:

def announceSharingInvitation(url, collectionName, fromAddress):
    """ Call this method to announce that an inbound sharing invitation has
        arrived. This method is non-blocking. """
    sharingParcel = Globals.parcelManager.lookup(SHARING)
    Globals.wxApplication.CallItemMethodAsync( sharingParcel,
     '_sharingUpdateCallback', url, collectionName, fromAddress)

def announceError(error):
    """ Call this method to announce an error. This method is non-blocking. """
    sharingParcel = Globals.parcelManager.lookup(SHARING)
    Globals.wxApplication.CallItemMethodAsync( sharingParcel,
     '_errorCallback', error)
