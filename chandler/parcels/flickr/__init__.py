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
from osaf.pim.collections import KindCollection, FilteredCollection
from repository.util.URL import URL
from datetime import datetime
import dateutil
import wx
import logging
from i18n import OSAFMessageFactory as _
from osaf import messages
from osaf.framework.types.DocumentTypes import SizeType, RectType
from osaf.framework.blocks.Block import *
from osaf.framework.blocks.MenusAndToolbars import MenuItem
from osaf.startup import PeriodicTask
from datetime import timedelta


logger = logging.getLogger(__name__)

class FlickrPhotoMixin(PhotoMixin):
    schema.kindInfo(displayName=u"Flickr Photo Mixin",
                    displayAttribute="displayName")

    flickrID = schema.One(schema.Text, displayName=u"Flickr ID")
    imageURL = schema.One(schema.URL, displayName=u"imageURL")
    datePosted = schema.One(schema.DateTime, displayName=u"Upload Date")
    tags = schema.Sequence(displayName=u"Tag")
    owner = schema.One(schema.Text, displayName=_(u"owner"))

    # about = schema.Descriptor(redirectTo="title")
    who = schema.One(redirectTo="owner")

    schema.addClouds(sharing = schema.Cloud(owner, flickrID, imageURL, tags))

    def __init__(self, photo=None,*args,**kwargs):
        super(FlickrPhotoMixin,self).__init__(*args,**kwargs)
        if photo:
            self.populate(photo)

    def populate(self, photo):
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

#copied from Location class
class Tag(pim.ContentItem):

    schema.kindInfo(displayName=u"Flickr Tag")

    itemsWithTag = schema.Sequence(FlickrPhotoMixin, inverse=FlickrPhotoMixin.tags, displayName=u"Tag")

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

    getTag = classmethod (getTag)

def getPhotoByFlickrID(view, id):
    try:
        for x in FlickrPhotoMixin.iterItems(view, exact=True):
            if x.flickrID == id:
                return x
    except:
        return None

def getPhotoByFlickrTitle(view, title):
    photos = KindCollection('FlickrPhotoQuery', FlickrPhotoMixin)
    filteredPhotos = FilteredCollection('FilteredFlicrkPhotoQuery', photos)
    for x in filteredPhotos:
        return x

class PhotoCollection(pim.ListCollection):

    schema.kindInfo(displayName=u"Collection of Flickr Photos")

    userName = schema.One(
        schema.Text, displayName=messages.USERNAME, initialValue=u''
    )
    tag = schema.One(
        Tag, displayName=u"Tag", initialValue=None
    )

    def onAddToCollection (self, event):
        result = None
        if event.collectionType == 'Owner':
            userName = application.dialogs.Util.promptUser(
                messages.USERNAME,
                _(u"Enter a Flickr user name"))
            if userName is not None:
                self.userName = userName
        else:
            assert (event.collectionType == 'Tag')
            tagString = application.dialogs.Util.promptUser(
                _(u"Tag"),
                _(u"Enter a Flickr Tag"))
            if tagString is not None:
                self.tag = Tag.getTag(self.itsView, tagString)

        if self.userName or self.tag:
            try:
                self.getCollectionFromFlickr(self.itsView)
            except flickr.FlickrError, fe:
                wx.MessageBox (unicode(fe))
            else:
                result = self

        return result


    def getCollectionFromFlickr(self, repView):
        coll = pim.ListCollection(itsView = repView).setup()
        if self.userName:
            flickrUserName = flickr.people_findByUsername(self.userName.encode('utf8'))
            try:
                flickrPhotos = flickr.people_getPublicPhotos(flickrUserName.id,10)
            except AttributeError:
                #This is raised if the user has no photos
                flickrPhotos = []

            self.displayName = self.userName
        elif self.tag:
            flickrPhotos = flickr.photos_search(tags=self.tag,per_page=10,sort="date-posted-desc")
            self.displayName = self.tag.displayName

        userdata = self.itsView.findPath ("//userdata")
        for flickrPhoto in flickrPhotos:
            photoItem = getPhotoByFlickrID(repView, flickrPhoto.id)
            if photoItem is None:
                photoItem = FlickrPhoto(photo=flickrPhoto, itsView=repView, itsParent=userdata)
            self.add (photoItem)
        repView.commit()


#
# Wakeup caller
#

class UpdateTask:
    def __init__(self, item):
        self.view = item.itsView.repository.createView("Flickr")

    def run(self):
        logger.info("receiveWakeupCall()")

        # We need the view for most repository operations
        self.view.refresh()

        # We need the Kind object for PhotoCollection
        for myPhotoCollection in PhotoCollection.iterItems(self.view):
            myPhotoCollection.getCollectionFromFlickr(self.view)

        # We want to commit the changes to the repository
        self.view.commit()
        return True

class CollectionTypeEnumType(schema.Enumeration):
      values = "Tag", "Owner"

class NewFlickrCollectionEvent(ModifyCollectionEvent):
    collectionType = schema.One (CollectionTypeEnumType, initialValue = 'Tag')

def installParcel(parcel, oldVersion=None):

    PhotoCollectionTemplate = PhotoCollection.update(
        parcel, 'PhotoCollectionTemplate',
        displayName = messages.UNTITLED).setup()

    NewFlickrCollectionByOwnerEvent = NewFlickrCollectionEvent.update(
        parcel, 'NewFlickrCollectionByOwnerEvent',
        methodName='onModifyCollectionEvent',
        copyItems = True,
        disambiguateDisplayName = True,
        dispatchToBlockName = 'MainView',
        selectInBlockNamed = 'Sidebar',
        items=[PhotoCollectionTemplate],
        dispatchEnum = 'SendToBlockByName',
        commitAfterDispatch = True,
        collectionType = 'Owner')

    NewFlickrCollectionByTagEvent = NewFlickrCollectionEvent.update(
        parcel, 'NewFlickrCollectionByOwnerEvent',
        methodName='onModifyCollectionEvent',
        copyItems = True,
        disambiguateDisplayName = True,
        dispatchToBlockName = 'MainView',
        selectInBlockNamed = 'Sidebar',
        items=[PhotoCollectionTemplate],
        dispatchEnum = 'SendToBlockByName',
        commitAfterDispatch = True,
        collectionType = 'Tag')

    collectionMenu = schema.ns('osaf.views.main', parcel).CollectionMenu

    MenuItem.update(parcel, 'FlickrParcelSeparator',
                    blockName = 'FlickrParcelSeparator',
                    menuItemKind = 'Separator',
                    parentBlock = collectionMenu)

    MenuItem.update(parcel, 'NewFlickrCollectionByOwner',
                    blockName = 'NewFlickrCollectionByOwnerMenuItem',
                    title = _(u'New Flickr Collection by Owner'),
                    event = NewFlickrCollectionByOwnerEvent,
                    eventsForNamedLookup = [NewFlickrCollectionByOwnerEvent],
                    parentBlock = collectionMenu)
 
    MenuItem.update(parcel, 'NewFlickrCollectionByTag',
                    blockName = 'NewFlickrCollectionByTagIMenutem',
                    title = _(u'New Flickr Collection by Tag'),
                    event = NewFlickrCollectionByTagEvent,
                    eventsForNamedLookup = [NewFlickrCollectionByTagEvent],
                    parentBlock = collectionMenu)


    PeriodicTask.update(parcel, 'FlickrUpdateTask',
                        invoke = 'flickr.UpdateTask',
                        run_at_startup = True,
                        interval = timedelta(minutes=2))


    blocks = schema.ns('osaf.framework.blocks', parcel)
    detail = schema.ns('osaf.framework.blocks.detail', parcel)

    detail.DetailTrunkSubtree.update(parcel, "flickr_detail_view",
        key = FlickrPhoto.getKind(parcel.itsView),
        rootBlocks = [
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
                ]
            )
        ]
    )


