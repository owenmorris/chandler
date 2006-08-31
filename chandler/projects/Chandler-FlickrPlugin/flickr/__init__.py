#   Copyright (c) 2005-2006 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import application.dialogs.Util
from application import schema
import flickr
from flickr import FlickrError, FlickrNotFoundError
from osaf import pim
from photos import PhotoMixin
import osaf.views.detail as Detail
from osaf.pim.collections import KindCollection
from repository.util.URL import URL
from datetime import datetime
import dateutil
import wx
import logging
from i18n import MessageFactory
from osaf import messages
from osaf.pim.structs import SizeType, RectType
from osaf.framework.blocks.Block import *
from osaf.framework.blocks.MenusAndToolbars import MenuItem
from osaf.startup import PeriodicTask
from datetime import timedelta
from osaf.usercollections import UserCollection

_ = MessageFactory("Chandler-FlickrPlugin")

logger = logging.getLogger(__name__)

class FlickrPhotoMixin(PhotoMixin):
    """
    A mixin that adds flickr attributes to a Note item
    """
    flickrID = schema.One (schema.Text)
    imageURL = schema.One (schema.URL)
    datePosted = schema.One (schema.DateTime)
    tags = schema.Sequence ()
    owner = schema.One (schema.Text)
    who = schema.One (redirectTo="owner")

    schema.addClouds(sharing = schema.Cloud(owner, flickrID, imageURL, tags))

    def __init__(self, photo=None,*args,**kwargs):
        super(FlickrPhotoMixin,self).__init__(*args,**kwargs)
        if photo is not None:
            self.flickrID = photo.id
            self.displayName = photo.title
            self.description = photo.description.encode('utf8')
            self.owner = photo.owner.username
            if photo.owner.realname is not None and len(photo.owner.realname.strip()) > 0:
                self.owner = photo.owner.realname
    
            self.imageURL = URL(photo.getURL(urlType="source"))
            self.datePosted = datetime.utcfromtimestamp(int(photo.dateposted))
            self.dateTaken = dateutil.parser.parse(photo.datetaken)
            try:
                if photo.tags:
                    self.tags = [Tag.getTag(self.itsView, tag.text) for tag in photo.tags]
            except Exception, e:
                logging.exception(e)

        self.importFromURL(self.imageURL)

class FlickrPhoto(FlickrPhotoMixin, pim.Note):
    pass

class Tag(pim.ContentItem):
    """
    Tag are items with bidirectional references to all the FlickrPhoto's with that
    tag. This makes it easy to find all photos with a given tag or all tags belonging
    to a photo. Currently, there isn't any code that takes advantage of Tags.
    """
    itemsWithTag = schema.Sequence(FlickrPhotoMixin, inverse=FlickrPhotoMixin.tags)

    @classmethod
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
        newTag = Tag(itsView=view)
        newTag.displayName = tagName
        return newTag

class PhotoCollection(pim.ListCollection):
    """
    A ListCollection of FlickrPhotos
    """
    userName = schema.One (schema.Text, initialValue=u'')
    tag = schema.One (Tag, initialValue=None)
    fillInBackground = schema.One (schema.Boolean, defaultValue=False)


    def fillCollectionFromFlickr(self, repView):
        """
        Fills the collection with photos from the flickr website.
        """
        if self.userName:
            flickrUserName = flickr.people_findByUsername(self.userName.encode('utf8'))
            flickrPhotos = flickr.people_getPublicPhotos(flickrUserName.id,10)
        elif self.tag:
            flickrPhotos = flickr.photos_search(tags=self.tag,per_page=10,sort="date-posted-desc")
        else:
            assert(False, "we should have either a userName or tag")

        # flickrPhotosCollection is a collection of all FlickrPhotos. It has
        # an index named flickerIDIndex which indexes all the photos by
        # their flickrID which makes it easy to quickly lookup any photo by
        # index.
        flickrPhotosCollection = schema.ns('flickr', repView).flickrPhotosCollection
        for flickrPhoto in flickrPhotos:
            """
            If we've already downloaded a photo with this id use it instead.
            """
            photoUUID = flickrPhotosCollection.findInIndex(
                'flickrIDIndex', # name of Index
                'exact',         # require an exact match
                                 # compare function
                lambda uuid: cmp(flickrPhoto.id,
                                 repView.findValue(uuid, 'flickrID')))

            if photoUUID is None:
                photoItem = FlickrPhoto(photo=flickrPhoto, itsView=repView)
            else:
                photoItem = repView[photoUUID]

            self.add (photoItem)
        repView.commit()

class UpdateTask(object):
    """
    Wakeup caller is periodically add more items to the PhotoCollections.
    """
    def __init__(self, item):
        self.view = item.itsView.repository.createView("Flickr")

    def run(self):
        logger.info("receiveWakeupCall()")

        # We need the view for most repository operations
        self.view.refresh(notify=False)

        # Go through all the PhotoCollections and update those that
        # have fillInBackground set. fillCollectionFromFlickr commits
        for myPhotoCollection in PhotoCollection.iterItems(self.view):
            if myPhotoCollection.fillInBackground:
                myPhotoCollection.fillCollectionFromFlickr(self.view)

        return True

class CollectionTypeEnumType(schema.Enumeration):
    """
    An enumeration used to specify two different kinds of AddFlickrCollectionEvent
    types.
    """
    values = "Tag", "Owner"

class AddFlickrCollectionEvent(AddToSidebarEvent):
    """
    An event used to add a new FlickrCollection to the sidebar.
    """
    collectionType = schema.One (CollectionTypeEnumType, initialValue = 'Tag')
    
    def onNewItem (self):
        """
        Called to create a new collection that gets added to the sidebar.
        """
        photoCollection = None
        if self.collectionType == 'Owner':
            userName = application.dialogs.Util.promptUser(
                messages.USERNAME,
                _(u"Enter a Flickr user name"))
            if userName is not None:
                photoCollection = PhotoCollection (itsView = self.itsView)
                photoCollection.userName = userName
                photoCollection.displayName = userName
        else:
            assert (self.collectionType == 'Tag')
            tagString = application.dialogs.Util.promptUser(
                _(u"Tag"),
                _(u"Enter a Flickr Tag"))
            if tagString is not None:
                photoCollection = PhotoCollection (itsView = self.itsView)
                photoCollection.tag = Tag.getTag(self.itsView, tagString)
                photoCollection.displayName = photoCollection.tag.displayName

        if photoCollection is not None:
            # Setting perferredKind to None will cause it to be displayed in the All View
            UserCollection (photoCollection).preferredKind = None
            try:
                photoCollection.fillCollectionFromFlickr(self.itsView)
            except flickr.FlickrError, flickrException:
                wx.MessageBox (unicode(flickrException))
                photoCollection.delete()
                photoCollection = None
            else:
                photoCollection.fillInBackground = True

        return photoCollection

def installParcel(parcel, oldVersion=None):
    """
    Creates Items that live in the initial repository. Run at repository buildtime.
    """
    # A KindCollection of all FlickPhoto kinds. The flickrIDIndex is used to lookup
    # photos by flickrID quickly.
    flickrPhotosCollection = KindCollection.update(
        parcel, 'flickrPhotosCollection',
        kind = FlickrPhotoMixin.getKind(parcel.itsView),
        recursive = True)

    flickrPhotosCollection.addIndex ('flickrIDIndex', 'attribute', attribute='flickrID', compare="__cmp__")

    # A NewFlickrCollectionEvent that adds a "Owner" collection to the sidebar
    addFlickrCollectionByOwnerEvent = AddFlickrCollectionEvent.update(
        parcel, 'addFlickrCollectionByOwnerEvent',
        blockName = 'addFlickrCollectionByOwnerEvent',
        collectionType = 'Owner')

    # A NewFlickrCollectionEvent that adds a "Tag" collection to the sidebar
    addFlickrCollectionByTagEvent = AddFlickrCollectionEvent.update(
        parcel, 'addFlickrCollectionByTagEvent',
        blockName = 'addFlickrCollectionByTagEvent',
        collectionType = 'Tag')

    # Add menu items to Chandler
    collectionMenu = schema.ns('osaf.views.main', parcel).CollectionMenu

    MenuItem.update(
        parcel, 'FlickrParcelSeparator',
        blockName = 'FlickrParcelSeparator',
        menuItemKind = 'Separator',
        parentBlock = collectionMenu)

    MenuItem.update(
        parcel, 'NewFlickrCollectionByOwner',
        blockName = 'NewFlickrCollectionByOwnerMenuItem',
        title = _(u'New Flickr Collection by Owner'),
        event = addFlickrCollectionByOwnerEvent,
        eventsForNamedLookup = [addFlickrCollectionByOwnerEvent],
        parentBlock = collectionMenu)
 
    MenuItem.update(
        parcel, 'NewFlickrCollectionByTag',
        blockName = 'NewFlickrCollectionByTagIMenutem',
        title = _(u'New Flickr Collection by Tag'),
        event = addFlickrCollectionByTagEvent,
        eventsForNamedLookup = [addFlickrCollectionByTagEvent],
        parentBlock = collectionMenu)


    # The periodic task that adds new photos to the collection in the background
    PeriodicTask.update(
        parcel, 'FlickrUpdateTask',
        invoke = 'flickr.UpdateTask',
        run_at_startup = True,
        interval = timedelta(minutes=2))


    # The detail view used to display a flickrPhoto
    blocks = schema.ns('osaf.framework.blocks', parcel)
    detail = schema.ns('osaf.views.detail', parcel)

    detail.makeSubtree(parcel, FlickrPhoto, [
        detail.makeArea(parcel, 'AuthorArea',
                        position=0.6,
                        childrenBlocks=[
                            detail.makeLabel(parcel, _(u'author'), borderTop=4),
                            detail.makeSpacer(parcel, width=6),
                            detail.makeEditor(parcel, 'AuthorAttribute',
                                              viewAttribute=u'owner',
                                              presentationStyle={'format': 'static'}
                                          ),
                        ]).install(parcel)
    ])
