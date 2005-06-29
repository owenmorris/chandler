__version__ = "$Revision: $"
__date__ = "$Date:  $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.dialogs.Util
import application.Globals as Globals
from application import schema
import flickr
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.detail.Detail as Detail
import osaf.framework.wakeup.WakeupCaller as WakeupCaller
import repository.query.Query as Query
from repository.item.Query import KindQuery
from repository.util.URL import URL
import wx


class Photo(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/examples/flickr/Photo"

    schema.kindInfo(displayName="Flickr Photo")

    flickrId = schema.One(schema.String, displayName="Flickr ID")
    imageURL = schema.One(schema.URL, displayName="imageURL")
    dateUploaded = schema.One(schema.DateTime, displayName="Upload Date")
    dateCreated = schema.One(schema.DateTime, displayName="Image Capture Date")
    tags = schema.Sequence(displayName="Tag")
    title = schema.One(schema.String, displayName="Title")
    owner = schema.One(schema.String, displayName="Owner")

    about = schema.Role(redirectTo="title")
    who = schema.Role(redirectTo="owner")
    date = schema.Role(redirectTo="dateCreated")
    displayName = schema.Role(redirectTo="title")

    def __init__(self, photo=None,*args,**kwargs):
        super(Photo,self).__init__(*args,**kwargs)
        if photo:
            self.populate(photo)

    def populate(self, photo):
        self.flickrID = photo.id.encode('ascii', 'replace')
        self.title = photo.title.encode('ascii', 'replace')
        self.description = photo.description.encode('ascii', 'replace')
        self.owner = photo.owner.realname.encode('ascii', 'replace')
        self.imageURL = URL(photo.getURL(urlType="source"))
        self.dateUploaded = photo.dateuploaded
        self.dateCreated = photo.datecreated
        try:
            self.tags = [Tag.getTag(self.itsView, tag) for tag in photo.tags]
        except:
            print "tags failed"
    
#copied from Location class
class Tag(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/examples/flickr/Tag"

    schema.kindInfo(displayName="Flickr Tag")

    itemsWithTag = schema.Sequence(Photo, inverse=Photo.tags, displayName="Tag")
    def __init__(self, name=None, parent=None, kind=None, view=None):
        super (Tag, self).__init__(name, parent, kind, view)

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
        k = view.findPath(Tag.myKindPath)
        its = KindQuery(recursive=False).run([k])
        locQuery = [ i for i in its if i.displayName == tagName ]

##         locQuery = view.findPath('//Queries/calendarLocationQuery')
##         if locQuery is None:
##             queryString = u'for i in "//parcels/osaf/contentmodel/calendar/Location" \
##                       where i.displayName == $0'
##             p = view.findPath('//Queries')
##             k = view.findPath('//Schema/Core/Query')
##             locQuery = Query.Query ('calendarLocationQuery', p, k, queryString)
##         locQuery.args["$0"] = ( tagName, )

        # return the first match found, if any
        for firstSpot in locQuery:
            return firstSpot

        # make a new Tag
        newTag = Tag(view=view)
        newTag.displayName = tagName
        return newTag

    getTag = classmethod (getTag)
    
def getPhotoByFlickrID(view, id):
    k = view.findPath(Photo.myKindPath)
    its = KindQuery(recursive=False).run([k])
    photoQuery = [ i for i in its if i.flickrID == id ]    
##    photoQuery = view.findPath('//Queries/photoQuery')
##    if photoQuery is None:
##        queryString = u'for i in "//parcels/osaf/examples/flickr/Photo" \
##                                 where i.flickrID == $0'
##        p = view.findPath('//Queries')
##        k = view.findPath('//Schema/Core/Query')
##        photoQuery = Query.Query ('photoQuery', p, k, queryString)
##    photoQuery.args["$0"] = ( id, )
    for x in photoQuery:
        return x
    return None

def getPhotoByFlickrTitle(view, title):
    photoQuery = view.findPath('//Queries/photoTitleQuery')
    if photoQuery is None:
        queryString = u'for i in "//parcels/osaf/examples/flickr/Photo" \
                                 where i.title == $0'
        p = view.findPath('//Queries')
        k = view.findPath('//Schema/Core/Query')
        photoQuery = Query.Query ('photoTitleQuery', p, k, queryString)
    photoQuery.args["$0"] = ( title, )
    for x in photoQuery:
        return x
    return None

class PhotoCollection(ContentModel.ContentItem):
    myKindID = None
    myKindPath = "//parcels/osaf/examples/flickr/PhotoCollection"

    schema.kindInfo(displayName="Collection of Flickr Photos")

    photos = schema.Sequence(Photo, displayName="Photos")
    username = schema.One(schema.String, displayName="Username")
    tag = schema.One(Tag, otherName="itemsWithTag", displayName="Tag")

    def __init__(self,*args,**kwargs):
        super(PhotoCollection,self).__init__(*args,**kwargs)
        self.username = ''
        self.tag = None

        
    def getCollectionFromFlickr(self,repView):
        coll = ItemCollection.ItemCollection(view = repView)
        print "self.username =",self.username
        print "self.tag =", self.tag
        if self.username:
            flickrUsername = flickr.people_findByUsername(self.username)
            flickrPhotos = flickr.people_getPublicPhotos(flickrUsername.id,10)
            coll.displayName = self.username
        elif self.tag:
            flickrPhotos = flickr.photos_search(tags=self.tag,per_page=10)
            coll.displayName = self.tag.displayName
            
        self.sidebarCollection = coll
        print "collection created"
        for i in flickrPhotos:
            photoItem = getPhotoByFlickrID(repView, i.id)
            if photoItem is None:
                photoItem = Photo(photo=i,view=repView,parent=coll)
            coll.add(photoItem)
        repView.commit()

    def update(self,repView):
        print "in PhotoCollection.update()"
#        self.getCollectionFromFlickr(repView)

#
# Block related code
#

class FlickrCollectionController(Block.Block):
    def onNewFlickrCollectionByOwnerEvent(self, event):
        CreateCollectionFromUsername(self.itsView, Globals.views[0])

    def onNewFlickrCollectionByTagEvent(self, event):
        CreateCollectionFromTag(self.itsView, Globals.views[0])

def CreateCollectionFromUsername(repView, cpiaView):
    myPhotoCollection = PhotoCollection(view = repView)
    myPhotoCollection.username = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
                                                   "Username",
                                                   "Enter a Flickr Username",
                                                   "")
    myPhotoCollection.getCollectionFromFlickr(repView)    
    
    # Add the channel to the sidebar
    cpiaView.postEventByName('AddToSidebarWithoutCopying', 
                             {'items': [myPhotoCollection.sidebarCollection]})

def CreateCollectionFromTag(repView, cpiaView):
    myPhotoCollection = PhotoCollection(view = repView)
    tagstring = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
                                                   "Tag",
                                                   "Enter a Flickr Tag",
                                                   "")
    myPhotoCollection.tag = Tag.getTag(repView, tagstring)
    myPhotoCollection.getCollectionFromFlickr(repView)    
    
    # Add the channel to the sidebar
    cpiaView.postEventByName('AddToSidebarWithoutCopying', 
                             {'items': [myPhotoCollection.sidebarCollection]})


class PhotoBlock(Detail.HTMLDetailArea):
    def getHTMLText(self, item):
        if item == item.itsView:
            return
        if item is not None:
            
            # make the html
            HTMLText = '<html><body>\n\n'
            HTMLText = HTMLText + '<img src = "' + str(item.imageURL) + '">\n\n</html></body>'

            return HTMLText

#
# Wakeup caller
#

class WakeupCall(WakeupCaller.WakeupCall):

    def receiveWakeupCall(self, wakeupCallItem):
        print "in receiveWakeupCall()"

        # We need the view for most repository operations
        view = wakeupCallItem.itsView
        view.refresh()

        # We need the Kind object for PhotoCollection
        photoCollectionKind = Photo.PhotoCollection.getKind(view)
            
        for myPhotoCollection in KindQuery().run([photoCollectionKind]):
            myPhotoCollection.update(view)

        # We want to commit the changes to the repository
        view.commit()


    
