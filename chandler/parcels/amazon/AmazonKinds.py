__parcel__ = "amazon"

import amazon
from amazon import AmazonError
import application
from osaf.pim import ContentItem, ListCollection
from repository.util.URL import URL
import wx
from application import schema
from i18n import OSAFMessageFactory as _
import logging
import string

log = logging.getLogger(__name__)


amazon.setLicense('0X5N4AEK0PTPMZK1NNG2')



def isEmpty(text):
    if text is None or len(string.strip(text)) == 0:
        return True

    return False



def showError(errText):
    application.dialogs.Util.ok(wx.GetApp().mainFrame,
                _(u"Amazon Error"), errText)


def CreateCollection(repView, cpiaView):
    keywords = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
        _(u"New Amazon Collection"),
        _(u"Enter your Amazon search keywords:"),
          u"Theodore Leung")

    if isEmpty(keywords):
        """The user did not enter any text to search on or hit the cancel button"""
        return

    try:
        results = amazon.searchByKeyword(keywords)
        newAmazonCollection = AmazonCollection(results, view=repView, keywords=keywords)
        return cpiaView.postEventByName('AddToSidebarWithoutCopying', {'items' : [newAmazonCollection]})

    except (AmazonError, AttributeError), e:
        log.exception(e)
        showError(_(u"No Amazon Wishlist was found for search keywords '%(keywords)s'") % {'keywords': keywords})

def CreateWishListCollection(repView, cpiaView):
    emailAddr = application.dialogs.Util.promptUser(wx.GetApp().mainFrame,
        _(u"New Amazon Wish List"),
        _(u"What is the Amazon email address of the wish list?"),
          u"")

    if isEmpty(emailAddr):
        return
    try:
        results = amazon.searchWishListByEmail(emailAddr)
        newAmazonCollection = AmazonCollection(results, view=repView, email=emailAddr)
        return cpiaView.postEventByName('AddToSidebarWithoutCopying', {'items' : [newAmazonCollection]})

    except (AmazonError, AttributeError), e:
        log.exception(e)
        showError(_(u"No Amazon Wishlist was found for email address '%(emailAddress)s'") \
                                                            % {'emailAddress': emailAddr})


class AmazonCollection(ListCollection):

    schema.kindInfo(displayName = u"Amazon Collection Kind")

    keywords = schema.One(schema.Text, displayName = u'Keywords')

    myKindID = None
    myKindPath = "//parcels/osaf/examples/amazon/schema/AmazonCollection"

    def __init__(self, results, keywords=None,email=None, name=None, parent=None, kind=None, view=None):
        super(AmazonCollection, self).__init__(name, parent, kind, view)
        if keywords:
            self.displayName = u'Amzn: ' + keywords
            bags = results

        elif email:
            customerName = results[0]
            bags = results[1]
            self.displayName = u'Amzn: ' + customerName
        else:
            bags = {}

        for aBag in bags:
            self.add(AmazonItem(aBag, view=view))


class AmazonItem(ContentItem):

    schema.kindInfo(displayName = u"Amazon Item")

    amazonCollection = schema.One(
        AmazonCollection, displayName = u'Amazon Collection',
    )
    ProductName = schema.One(schema.Text, displayName = _(u'Product Name'))
    Author = schema.One(schema.Text, displayName = _(u'Author(s)'))
    ReleaseDate = schema.One(schema.Text, displayName = _(u'Release Date'))
    imageURL = schema.One(schema.URL, displayName = u'image path')
    about = schema.One(redirectTo = 'ProductName')
    who = schema.One(redirectTo = 'Author')
    date = schema.One(redirectTo = 'ReleaseDate')

    myKindID = None
    myKindPath = "//parcels/osaf/examples/amazon/schema/AmazonItem"
 
    def __init__(self,bag, name=None, parent=None, kind=None, view=None):
        super(AmazonItem, self).__init__(name, parent, kind, view)
        if bag:
            self.ProductName = bag.ProductName
            self.imageURL = URL(str(bag.ImageUrlLarge))
            self.ReleaseDate = getattr(bag, 'ReleaseDate','')
            if hasattr(bag,'Authors'):
                if type(bag.Authors.Author) == type([]):
                    self.Author = u', '.join(bag.Authors.Author)
                else:
                    self.Author = bag.Authors.Author
            elif hasattr(bag,'Directors'):
                if type(bag.Directors.Director) == type([]):
                    self.Author = u', '.join(bag.Directors.Director)
                else:
                    self.Author = bag.Directors.Director
            elif hasattr(bag,'Artists'):
                if type(bag.Artists.Artist) == type([]):
                    self.Author = ', '.join(bag.Artists.Artist)
                else:
                    self.Author = bag.Artists.Artist
            else:
                self.Author = u''
            self.displayName = self.ProductName
