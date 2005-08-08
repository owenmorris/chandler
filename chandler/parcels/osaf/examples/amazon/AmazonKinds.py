__parcel__ = "osaf.examples.amazon"

import amazon
import application
from osaf.pim import ContentItem, ItemCollection
import wx
from application import schema

amazon.setLicense('0X5N4AEK0PTPMZK1NNG2')

def CreateCollection(repView, cpiaView):
    keywords = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
        "New Amazon Collection",
        "Enter your Amazon search keywords:",
        "Theodore Leung")
    newAmazonCollection = AmazonCollection(view=repView, keywords=keywords)
    return cpiaView.postEventByName('AddToSidebarWithoutCopying', {'items' : [newAmazonCollection]})
    
def CreateWishListCollection(repView, cpiaView):
    emailAddr = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
        "New Amazon Wish List",
        "What is the Amazon email address of the wish list?",
        "")
    newAmazonCollection = AmazonCollection(view=repView, email=emailAddr)
    return cpiaView.postEventByName('AddToSidebarWithoutCopying', {'items' : [newAmazonCollection]})

def NewCollectionFromKeywords(view, keywords, update = True):
    collection = AmazonCollection(keywords=keywords,view=view)
    if update:
        print "updating new amazon collection"
    return collection

class AmazonCollection(ItemCollection):

    schema.kindInfo(displayName = "Amazon Collection Kind")

    keywords = schema.One(schema.String, displayName = 'Keywords')

    myKindID = None
    myKindPath = "//parcels/osaf/examples/amazon/schema/AmazonCollection"
    
    def __init__(self,keywords=None,email=None, name=None, parent=None, kind=None, view=None):
        super(AmazonCollection, self).__init__(name, parent, kind, view)
        if keywords:
            bags = amazon.searchByKeyword(keywords)
            self.displayName = 'Amzn: ' + keywords
        elif email:
            results = amazon.searchWishListByEmail(email)
            customerName = results[0]
            bags = results[1]
            self.displayName = 'Amzn: ' + customerName
        else:
            bags = {}
        for aBag in bags:
            self.add(AmazonItem(aBag, view=view))
            
            
class AmazonItem(ContentItem):

    schema.kindInfo(displayName = "Amazon Item")

    amazonCollection = schema.One(
        AmazonCollection, displayName = 'Amazon Collection',
    )
    ProductName = schema.One(schema.String, displayName = 'Product Name')
    Author = schema.One(schema.String, displayName = 'Author(s)')
    ReleaseDate = schema.One(schema.String, displayName = 'Release Date')
    imageURL = schema.One(schema.String, displayName = 'image path')
    about = schema.One(redirectTo = 'ProductName')
    who = schema.One(redirectTo = 'Author')
    date = schema.One(redirectTo = 'ReleaseDate')

    myKindID = None
    myKindPath = "//parcels/osaf/examples/amazon/schema/AmazonItem"
    
    def __init__(self,bag, name=None, parent=None, kind=None, view=None):
        super(AmazonItem, self).__init__(name, parent, kind, view)
        if bag:
            self.ProductName = bag.ProductName
            self.imageURL = bag.ImageUrlLarge
            self.ReleaseDate = getattr(bag, 'ReleaseDate','')
            if hasattr(bag,'Authors'):
                if type(bag.Authors.Author) == type([]):
                    self.Author = ', '.join(bag.Authors.Author)
                else:
                    self.Author = bag.Authors.Author
            elif hasattr(bag,'Directors'):
                if type(bag.Directors.Director) == type([]):
                    self.Author = ', '.join(bag.Directors.Director)
                else:
                    self.Author = bag.Directors.Director
            elif hasattr(bag,'Artists'):
                if type(bag.Artists.Artist) == type([]):
                    self.Author = ', '.join(bag.Artists.Artist)
                else:
                    self.Author = bag.Artists.Artist
            else:
                self.Author = ''
            self.displayName = self.ProductName