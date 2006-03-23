__version__ = "$Revision: $"
__date__ = "$Date:  $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.dialogs.Util
from application import schema
import flickr
from osaf import pim
from photos import PhotoMixin
import osaf.framework.blocks.detail.Detail as Detail
from osaf.pim.collections import KindCollection
from repository.util.URL import URL
from datetime import datetime
import dateutil
import wx
import logging
from i18n import OSAFMessageFactory as _
from osaf import messages
from osaf.pim.structs import SizeType, RectType
from osaf.framework.blocks.Block import *
from osaf.framework.blocks.MenusAndToolbars import MenuItem
from osaf.startup import PeriodicTask
from datetime import timedelta


logger = logging.getLogger(__name__)

class FlickrPhotoMixin(PhotoMixin):
    """
    A mixin that adds flickr attributes to a Note item
    """
    schema.kindInfo(displayName=u"Flickr Photo Mixin")

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
    schema.kindInfo(displayName = u"Flickr Photo")

class Tag(pim.ContentItem):
    """
    Tag are items with bidirectional references to all the FlickrPhoto's with that
    tag. This makes it easy to find all photos with a given tag or all tags belonging
    to a photo. Currently, there isn't any code that takes advantage of Tags.
    """
    schema.kindInfo(displayName=u"Flickr Tag")

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
    schema.kindInfo(displayName=u"Collection of Flickr Photos")

    userName = schema.One (schema.Text, initialValue=u'')
    tag = schema.One (Tag, initialValue=None)
    fillInBackground = schema.One (schema.Boolean, defaultValue=False)

    def onAddToCollection (self, event):
        """
        An initialization routine that gets called when the collection
        is added to the sidebar. It's used to ask the user what Owner
        or Tag to use for the collection.
        """
        result = None
        if event.collectionType == 'Owner':
            userName = application.dialogs.Util.promptUser(
                messages.USERNAME,
                _(u"Enter a Flickr user name"))
            if userName is not None:
                self.userName = userName
                self.displayName = userName
        else:
            assert (event.collectionType == 'Tag')
            tagString = application.dialogs.Util.promptUser(
                _(u"Tag"),
                _(u"Enter a Flickr Tag"))
            if tagString is not None:
                self.tag = Tag.getTag(self.itsView, tagString)
                self.displayName = self.tag.displayName

        if self.userName or self.tag:
            try:
                self.fillCollectionFromFlickr(self.itsView)
            except flickr.FlickrError, fe:
                wx.MessageBox (unicode(fe))
            else:
                self.fillInBackground = True
                result = self

        return result


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
        self.view.refresh()

        # Go through all the PhotoCollections and update those that
        # have fillInBackground set. fillCollectionFromFlickr commits
        for myPhotoCollection in PhotoCollection.iterItems(self.view):
            if myPhotoCollection.fillInBackground:
                myPhotoCollection.fillCollectionFromFlickr(self.view)

        return True

class CollectionTypeEnumType(schema.Enumeration):
    """
    An enumeration used to specify two different kinds of NewFlickrCollectionEvent
    types.
    """
    values = "Tag", "Owner"

class NewFlickrCollectionEvent(ModifyCollectionEvent):
    """
    An event used to add a new FlickrCollection to the sidebar.
    """
    collectionType = schema.One (CollectionTypeEnumType, initialValue = 'Tag')

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

    # A template flickrPhotoCollection that is copied and added to the sidebar by
    # the NewFlickrCollectionEvent
    photoCollectionTemplate = PhotoCollection.update(
        parcel, 'photoCollectionTemplate',
        displayName = messages.UNTITLED)

    # A NewFlickrCollectionEvent that adds a "Owner" collection to the sidebar
    newFlickrCollectionByOwnerEvent = NewFlickrCollectionEvent.update(
        parcel, 'newFlickrCollectionByOwnerEvent',
        blockName = 'newFlickrCollectionByOwnerEvent',
        methodName='onModifyCollectionEvent',
        copyItems = True,
        disambiguateDisplayName = True,
        dispatchToBlockName = 'MainView',
        selectInBlockNamed = 'Sidebar',
        items=[photoCollectionTemplate],
        dispatchEnum = 'SendToBlockByName',
        commitAfterDispatch = True,
        collectionType = 'Owner')

    # A NewFlickrCollectionEvent that adds a "Tag" collection to the sidebar
    newFlickrCollectionByTagEvent = NewFlickrCollectionEvent.update(
        parcel, 'newFlickrCollectionByTagEvent',
        blockName = 'newFlickrCollectionByTagEvent',
        methodName='onModifyCollectionEvent',
        copyItems = True,
        disambiguateDisplayName = True,
        dispatchToBlockName = 'MainView',
        selectInBlockNamed = 'Sidebar',
        items=[photoCollectionTemplate],
        dispatchEnum = 'SendToBlockByName',
        commitAfterDispatch = True,
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
        event = newFlickrCollectionByOwnerEvent,
        eventsForNamedLookup = [newFlickrCollectionByOwnerEvent],
        parentBlock = collectionMenu)
 
    MenuItem.update(
        parcel, 'NewFlickrCollectionByTag',
        blockName = 'NewFlickrCollectionByTagIMenutem',
        title = _(u'New Flickr Collection by Tag'),
        event = newFlickrCollectionByTagEvent,
        eventsForNamedLookup = [newFlickrCollectionByTagEvent],
        parentBlock = collectionMenu)


    # The periodic task that adds new photos to the collection in the background
    PeriodicTask.update(
        parcel, 'FlickrUpdateTask',
        invoke = 'flickr.UpdateTask',
        run_at_startup = True,
        interval = timedelta(minutes=2))


    # The detail view used to display a flickrPhoto
    blocks = schema.ns('osaf.framework.blocks', parcel)
    detail = schema.ns('osaf.framework.blocks.detail', parcel)

    detail.makeSubtree(parcel, FlickrPhoto, [
        detail.DetailSynchronizedLabeledTextAttributeBlock.update(
            parcel, "AuthorArea",
            position = 0.6,
            viewAttribute=u"owner",
            stretchFactor = 0,
            childrenBlocks = [
                detail.StaticRedirectAttributeLabel.update(
                    parcel, "AuthorLabel",
                    title = u"author",
                    characterStyle = blocks.LabelStyle,
                    stretchFactor = 0.0,
                    textAlignmentEnum = "Right",
                    minimumSize = SizeType(70, 24),
                    border = RectType(0.0, 0.0, 0.0, 5.0),
                ),
                detail.StaticRedirectAttribute.update(
                    parcel  , "AuthorAttribute",
                    title = u"author",
                    characterStyle = blocks.LabelStyle,
                    stretchFactor = 0.0,
                    textAlignmentEnum = "Left",
                ),
            ])])


