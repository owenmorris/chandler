__version__ = "$Revision: $"
__date__ = "$Date:  $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.dialogs.Util
import application.Globals as Globals
from application import schema
import flickr
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.photos.Photos as Photos
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.detail.Detail as Detail
import osaf.framework.wakeup.WakeupCaller as WakeupCaller
import repository.query.Query as Query
from repository.util.URL import URL
from datetime import datetime
import dateutil
import wx
import os, logging

logger = logging.getLogger('Flickr')
logger.setLevel(logging.INFO)


class FlickrPhoto(Photos.Photo):

    schema.kindInfo(displayName="Flickr Photo", displayAttribute="caption")

    flickrID = schema.One(schema.String, displayName="Flickr ID")
    imageURL = schema.One(schema.URL, displayName="imageURL")
    datePosted = schema.One(schema.DateTime, displayName="Upload Date")
    tags = schema.Sequence(displayName="Tag")
    # title = schema.One(schema.String, displayName="Title")
    owner = schema.One(schema.String, displayName="Owner")

    # about = schema.Role(redirectTo="title")
    who = schema.Role(redirectTo="owner")

    schema.addClouds(sharing = schema.Cloud(owner, flickrID, imageURL, tags))

    def __init__(self, photo=None,*args,**kwargs):
        super(FlickrPhoto,self).__init__(*args,**kwargs)
        if photo:
            self.populate(photo)

    def populate(self, photo):
        self.flickrID = photo.id.encode('ascii', 'replace')
        self.caption = photo.title.encode('ascii', 'replace')
        self.description = photo.description.encode('ascii', 'replace')
        self.owner = photo.owner.realname.encode('ascii', 'replace')
        self.imageURL = URL(photo.getURL(urlType="source"))
        self.datePosted = datetime.utcfromtimestamp(int(photo.dateposted))
        self.dateTaken = dateutil.parser.parse(photo.datetaken)
        try:
        if photo.tags:
            self.tags = [Tag.getTag(self.itsView, tag.text) for tag in photo.tags]
        except Exception, e:
            print "tags failed", e
        self.importFromURL(self.imageURL)
    
#copied from Location class
class Tag(ContentModel.ContentItem):

    schema.kindInfo(displayName="Flickr Tag")

    itemsWithTag = schema.Sequence(FlickrPhoto, inverse=FlickrPhoto.tags, displayName="Tag")

    def __str__ (self):
        """
          User readable string version of this Tag
        """
        if self.isStale():
            return super(Tag, self).__str__()
            # Stale items can't access their attributes
        return self.getItemDisplayName ()

    def getTag (cls, view, tagName):
        """
          Factory Method for getting a Tag.

          Lookup or create a Tag based on the supplied name string.
        If a matching Tag object is found in the repository, it
        is returned.  If there is no match, then a new item is created
        and returned.  
        @param tagName: name of the Tag
        @type tagName: C{String}
        @return: C{Tag} created or found
        """
        # make sure the tagName looks reasonable
        assert tagName, "Invalid tagName passed to getTag factory"

        # get all Tag objects whose displayName match the param
        # return the first match found, if any
        for i in Tag.iterItems(view, exact=True):
            if i.displayName == tagName:
                return i

        # make a new Tag
        newTag = Tag(view=view)
        newTag.displayName = tagName
        return newTag

    getTag = classmethod (getTag)
    
def getPhotoByFlickrID(view, id):
    try:
        for x in FlickrPhoto.iterItems(view, exact=True):
            if x.flickrID == id:
                return x
    except:
        return None

def getPhotoByFlickrTitle(view, title):
    photoQuery = view.findPath('//Queries/photoTitleQuery')
    if photoQuery is None:
        queryString = u'for i in "//parcels/osaf/examples/flickr/FlickrPhoto" \
                                 where i.title == $0'
        p = view.findPath('//Queries')
        k = view.findPath('//Schema/Core/Query')
        photoQuery = Query.Query ('photoTitleQuery', p, k, queryString)
    photoQuery.args["$0"] = ( title, )
    for x in photoQuery:
        return x
    return None

class PhotoCollection(ContentModel.ContentItem):

    schema.kindInfo(displayName="Collection of Flickr Photos")

    photos = schema.Sequence(FlickrPhoto, displayName="Flickr Photos")
    username = schema.One(
        schema.String, displayName="Username", initialValue=''
    )
    tag = schema.One(
        Tag, otherName="itemsWithTag", displayName="Tag", initialValue=None
    )
       
    def getCollectionFromFlickr(self,repView):
        coll = ItemCollection.ItemCollection(view = repView)
        if self.username:
            flickrUsername = flickr.people_findByUsername(self.username)
            flickrPhotos = flickr.people_getPublicPhotos(flickrUsername.id,10)
            coll.displayName = self.username
        elif self.tag:
            flickrPhotos = flickr.photos_search(tags=self.tag,per_page=10,sort="date-posted-asc")
            coll.displayName = self.tag.displayName
            
        self.sidebarCollection = coll

        for i in flickrPhotos:
            photoItem = getPhotoByFlickrID(repView, i.id)
            if photoItem is None:
                photoItem = FlickrPhoto(photo=i,view=repView,parent=coll)
            coll.add(photoItem)
        repView.commit()

    def update(self,repView):
        self.getCollectionFromFlickr(repView)

#
# Block related code
#

class FlickrCollectionController(Block.Block):
    def onNewFlickrCollectionByOwnerEvent(self, event):
        CreateCollectionFromUsername(self.itsView, Globals.views[0])

    def onNewFlickrCollectionByTagEvent(self, event):
        CreateCollectionFromTag(self.itsView, Globals.views[0])

def CreateCollectionFromUsername(repView, cpiaView):
    username = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
                                                   "Username",
                                                   "Enter a Flickr Username",
                                                   "")
    if username:
        myPhotoCollection = PhotoCollection(view = repView)
        myPhotoCollection.username = username
        try:
            myPhotoCollection.getCollectionFromFlickr(repView)

            # Add the channel to the sidebar
            cpiaView.postEventByName('AddToSidebarWithoutCopying',
                                     {'items': [myPhotoCollection.sidebarCollection]})
        except FlickrError, fe:
            application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                        "Flickr Error",
                                        str(fe))

def CreateCollectionFromTag(repView, cpiaView):
    tagstring = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
                                                   "Tag",
                                                   "Enter a Flickr Tag",
                                                   "")
    if tagstring:
        myPhotoCollection = PhotoCollection(view = repView)
        myPhotoCollection.tag = Tag.getTag(repView, tagstring)
        try:
            myPhotoCollection.getCollectionFromFlickr(repView)

            # Add the channel to the sidebar
            cpiaView.postEventByName('AddToSidebarWithoutCopying',
                                     {'items': [myPhotoCollection.sidebarCollection]})
        except FlickrError, fe:
            application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                        "Flickr Error",
                                        str(fe))

#
# Wakeup caller
#

class WakeupCall(WakeupCaller.WakeupCall):

    def receiveWakeupCall(self, wakeupCallItem):
        logger.info("receiveWakeupCall()")

        # We need the view for most repository operations
        view = wakeupCallItem.itsView
        view.refresh()

        # We need the Kind object for PhotoCollection
        for myPhotoCollection in PhotoCollection.iterItems(view):
            myPhotoCollection.update(view)

        # We want to commit the changes to the repository
        view.commit()
