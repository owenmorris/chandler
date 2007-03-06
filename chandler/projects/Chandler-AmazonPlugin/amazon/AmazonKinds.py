#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

__parcel__ = "amazon"

import amazon, sgmllib, wx, string

from osaf.pim import ContentItem, ListCollection
from repository.util.URL import URL
from application import schema, dialogs, Utility, Globals
from i18n import MessageFactory
import AmazonDialog

_ = MessageFactory("Chandler-AmazonPlugin")


def _isEmpty(text):
    return not text or not text.strip()

def _showError(errText):
    theApp = wx.GetApp()
    if theApp is not None:
        application.dialogs.Util.ok(wx.GetApp().mainFrame,
                                    _(u"Amazon Error"), errText)

def SearchByKeyword(repView, keywords=None, countryCode=None, category=None):
    """
    Performs an amazon search by keyword and creates an AmazonCollection
    containing AmazonItem's for each product found that matches the search
    criteria (only retrieves the first 10 products). If an AmazonCollection
    already exists for the search criteria the method creates AmazonItem's
    for new products and adds them to the existing collection.

    The method can be used programatically or via user input. If no keywords,
    countryCode, and category variables are passed in, an Amazon Search By
    Keyword dialog is displayed for the user to choose the keywords,
    countryCode, and category.

    The method contacts the Amazon site specified by the countryCode and
    retrieves the products that match the search criteria.

    @type repView: A Repository.view
    @param repView: The repository view in which to create the AmazonItems'
                    and AmazonCollection

    @type keywords: unicode
    @param keywords: The keywords to search on. If the value is None a
                     dialog is displayed for the user to enter the information.

    @type countryCode: unicode
    @param countryCode: The countryCode of the amazon site to contact.
                        If the value is None a dialog is displayed for
                        the user to enter the information.

    @type category: unicode
    @param category: The category to search in. If the value is None a
                     dialog is displayed for the user to enter the information.

    @rtype: AmazonCollection or None
    @return: An AmazonCollection containing AmazonItem's for each product or
             None if no products found or an error occurs.
    """

    if keywords is None or countryCode is None or category is None:
        keywords, countryCode, category = AmazonDialog.promptKeywords()

    if _isEmpty(keywords):
        """
        The user did not enter any text to search on or hit the cancel button
        """
        return None

    while True:
        try:
            bags = amazon.searchByKeyword(keywords, locale=countryCode,
                                          product_line=category)
            return _AddToCollection(repView, keywords, countryCode, bags) 
        except amazon.NoLicenseKey:
            if AmazonDialog.promptLicense():
                continue
            return None
        except (amazon.AmazonError, AttributeError), e:
            dt = {'keywords': keywords}
            _showError(_(u"No Amazon products were found for keywords '%(keywords)s'") % dt)
            return None


def SearchWishListByEmail(repView, emailAddr=None, countryCode=None):
    """
    Retrieves an amazon wishlist by email address and creates an
    AmazonCollection containing AmazonItem's for each product in
    the wishlist (only retrieves first 10 products found). If an
    AmazonCollection already exists for the search criteria the
    method creates AmazonItem's for new products and adds them to
    the existing collection.

    The method can be used programatically or via user input. If no
    emailAddr and countryCode variables are passed in, an Amazon
    WishList By Email dialog is displayed for the user to input the
    emailAddr and countryCode.

    The method contacts the Amazon site specified by the countryCode
    and retrieves the products for the wishlist.

    @type repView: A Repository.view
    @param repView: The repository view in which to create the AmazonItems'
                    and AmazonCollection

    @type emailAddr: unicode
    @param emailAddr: The email address for the user wishlist

    @type countryCode: unicode
    @param countryCode: The countryCode of the amazon site to contact.
                        If the value is None a dialog is displayed for
                        the user to enter the information.

    @rtype: AmazonCollection or None
    @return: An AmazonCollection containing AmazonItem's for each product or
             None if no products found or an error occurs.
    """

    if emailAddr is None or countryCode is None:
        emailAddr, countryCode = AmazonDialog.promptEmail()

    if _isEmpty(emailAddr):
        return None

    while True:
        try:
            customerName, bags = \
                amazon.searchWishListByEmail(emailAddr, locale=countryCode)
            return _AddToCollection(repView, customerName, countryCode, bags) 
        except amazon.NoLicenseKey:
            if AmazonDialog.promptLicense():
                continue
            return None
        except (amazon.AmazonError, AttributeError), e:
            dt = {'emailAddress': emailAddr}
            _showError(_(u"No Amazon Wishlist was found for email address '%(emailAddress)s'") % dt)
            return None


def _AddToCollection(repView, text, countryCode, bags):
    col, d = AmazonCollection.getCollection(repView, text, countryCode)

    counter = 0

    for aBag in bags:
        #_printBag(aBag, 0)
        #print "\n----------------------\n\n"

        #XXX This is temp for .6.
        # A dict of unique Amazon URLs is
        # returned with the collection.
        # The dict is searched and if an item with
        # the same URL exists a new item is not created.
        if not d.has_key(str(aBag.URL)):
            counter += 1
            col.add(AmazonItem(bag=aBag, itsView=repView))

    d = {'collectionName': col.displayName, 'numOf': counter}

    theApp = wx.GetApp()
    if theApp is not None:
        if counter == 0:
            msg = _(u"No new products were found for collection '%(collectionName)s'") % d
        elif counter == 1:
            msg = _(u"Added 1 product to collection '%(collectionName)s'") % d
        else:
            msg = _(u"Added %(numOf)s products to collection '%(collectionName)s'") % d
        theApp.CallItemMethodAsync("MainView", 'setStatusMessage', msg)

    repView.commit()

    return col


class AmazonCollection(ListCollection):
    keywords = schema.One(schema.Text)

    @classmethod
    def getCollection(cls, repView, text, countryCode):
        """
        Returns an AmazonCollection with a displayName combining the text
        and country code variables.

        The method checks to see if a AmazonCollection already exists
        matching the displayName combination of the text and countryCode
        variables. If one exists that collection is returned otherwise
        an AmazonCollection is created with the text / countryCode
        displayName and is returned.

        @type repView: A Repository.view
        @param repView: The repository view in which to create the AmazonItems'
                        and AmazonCollection

        @type text: unicode
        @param text: The text to use in combination with the countryCode to
                     create the AmazonCollection displayName

        @type countryCode: unicode
        @param countryCode: The countryCode to use in combination with the text
                            to create the AmazonCollection displayName

        @rtype: AmazonCollection
        @return: An existing AmazonCollection that matches the text/CountryCode
                 displayName combination or a new AmazonCollection if no
                 match is found.
       """


        displayName = AmazonCollection.makeCollectionName(text, countryCode)
        sidebarCollection = schema.ns("osaf.app", wx.GetApp().UIRepositoryView).sidebarCollection

        for collection in sidebarCollection:
            if collection.displayName.lower() == displayName.lower():
                #XXX: Create a dict of the productURL's of all items
                # of AmazonItem kind. If a url in the dict matches a 
                # new url that is downloaded it is not added to the 
                # collection

                d = {}
                for item in collection:
                    if isinstance(item, AmazonItem):
                        d[str(item.ProductURL)] = ''

                return collection, d

        collection = AmazonCollection(itsView=repView)
        collection.displayName = displayName
        sidebarCollection.add (collection)

        return collection, {}


    @classmethod
    def makeCollectionName(cls, text, countryCode):
        """
        Returns the displayName for an AmazonCollection based on the text
        and countryCode passed in.

        @type text: unicode
        @param text: The text to use in combination with the countryCode
                     to create the AmazonCollection displayName

        @type countryCode: unicode
        @param countryCode: The countryCode to use in combination with the
                            text to create the AmazonCollection displayName

        @rtype: unicode
        @return: The unicode displayName to be used for the AmazonCollection
        """

        if countryCode == 'gb':
            #The country code for the United Kingdom is 'GB' but
            #the web domain for the United Kingdom is .uk
            return u'Amzn.uk:' + text
        elif countryCode != 'us':
            return u'Amzn.' + countryCode + ': ' + text
        else:
            return u'Amzn:' + text

class AmazonItem(ContentItem):

    amazonCollection = schema.One(AmazonCollection)

    # When you add/remove/modify attributes here remember to update the
    # corresponding names displayed in the user interface in __init__.py
    ProductDescription = schema.One(schema.Text)
    Author = schema.One(schema.Text)
    Media = schema.One(schema.Text)
    ReleaseDate = schema.One(schema.Text)
    ImageURL = schema.One(schema.URL)
    ProductURL = schema.One(schema.URL)
    NewPrice = schema.One(schema.Text)
    UsedPrice = schema.One(schema.Text)
    Availability = schema.One(schema.Text)
    Manufacturer = schema.One(schema.Text)
    AverageCustomerRating = schema.One(schema.Text)
    NumberOfReviews = schema.One(schema.Text)
    
    @apply
    def productName():
        def fget(self):
            return self.displayName
        def fset(self, value):
            self.displayName = value
        return property(fget, fset)
 
    def __init__(self, *args, **kwds):

        bag = kwds.pop('bag', None)
        super(AmazonItem, self).__init__(*args, **kwds)

        if bag:
            self.ProductName = bag.ProductName
            desc = getattr(bag, 'ProductDescription', '')

            if desc != '':
                # The HTML is stripped because some descriptions
                # contain img src links to images as part of the description.
                # In theory this would be a nice feature but since the wx
                # HTML widget is slow and does not render till everything is
                # downloaded it impacts the display of the product considerably.
                desc = _stripHTML(desc)

            self.ProductDescription = desc
            self.Media = getattr(bag, 'Media', '')
            self.Manufacturer = getattr(bag, 'Manufacturer', '')
            self.NewPrice = getattr(bag, 'OurPrice', '')
            self.UsedPrice = getattr(bag, 'UsedPrice', '')
            self.Availability = getattr(bag, 'Availability', '')
            self.ImageURL = URL(bag.ImageUrlMedium.encode('ascii'))
            self.ProductURL = URL(bag.URL.encode('ascii'))
            self.ReleaseDate = getattr(bag, 'ReleaseDate','')

            if hasattr(bag, 'Authors'):
                if type(bag.Authors.Author) == type([]):
                    self.Author = u', '.join(bag.Authors.Author)
                else:
                    self.Author = bag.Authors.Author
            elif hasattr(bag, 'Directors'):
                if type(bag.Directors.Director) == type([]):
                    self.Author = u', '.join(bag.Directors.Director)
                else:
                    self.Author = bag.Directors.Director
            elif hasattr(bag, 'Artists'):
                if type(bag.Artists.Artist) == type([]):
                    self.Author = ', '.join(bag.Artists.Artist)
                else:
                    self.Author = bag.Artists.Artist
            else:
                # If no artist, author, or directory use the Manufacturer which
                # will either have a value or be '' by default
                self.Author = self.Manufacturer

            if hasattr(bag, 'Reviews'):
                self.AverageCustomerRating = getattr(bag.Reviews,
                                                     'AvgCustomerRating', '')
                self.NumberOfReviews = getattr(bag.Reviews,
                                               'TotalCustomerReviews', '')
            else:
                self.AverageCustomerRating = ''
                self.NumberOfReviews = ''

            self.displayName = self.ProductName


class DisplayNamesItem(schema.Item):
    namesDictionary = schema.Mapping(schema.Text, defaultValue={})


def _printBag(aBag, level):
    """
    This is used for debugging the incoming Amazon XML which is
    parsed by amazon.py in to c{amazon.Bags}
    """
    for at in dir(aBag):
        val = getattr(aBag, at)

        if isinstance(val, unicode):
            val = val.encode('utf8')

        print "%s%s: %s" % ('\t'*level, at, val)

        if isinstance(val, amazon.Bag):
            _printBag(val, level+1)
        elif (isinstance(val, list) and len(val) > 0 and
              isinstance(val[0], amazon.Bag)):
            for bag in val:
                _printBag(bag, level+1)


class _Cleaner(sgmllib.SGMLParser):
    entitydefs={"nbsp": " "} 

    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        self.result = []
    def do_p(self, *junk):
        self.result.append(u'<p>')
    def do_br(self, *junk):
        self.result.append(u'<br>')
    def handle_data(self, data):
        self.result.append(data)
    def cleaned_text(self):
        txt = u''
        for uniText in self.result:
            if isinstance(uniText, str):
                uniText = unicode(uniText, 'utf8', 'ignore')

            txt += uniText
        return txt


def _stripHTML(text):
    c = _Cleaner()
    try:
        c.feed(text)
    except sgmllib.SGMLParseError:
        return text
    else:
        return c.cleaned_text()
