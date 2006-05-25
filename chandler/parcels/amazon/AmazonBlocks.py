__parcel__ = "amazon"

import osaf.framework.blocks.Block as Block
import AmazonKinds
import osaf.framework.blocks.detail.Detail as Detail

#XXX[i18n] this module sits outsite of OSAF and should have its own translation domain
from i18n import OSAFMessageFactory as _

class AmazonController(Block.Block):
    def onNewAmazonCollectionEvent(self, event):
        """
        Called when a NewAmazonCollection Search by Keyword Event is triggered.

        @type event: BlockEvent
        @param event: The BlockEvent triggered on NewAmazonCollection command

        @rtype: AmazonCollection or None
        @return: AmazonCollection for the search keyword or None if search results == 0
        """
        return AmazonKinds.SearchByKeyword(self.itsView)

    def onNewAmazonWishListEvent(self, event):
        """
        Called when a NewAmazonCollection Email Wishlist Event is triggered.

        @type event: BlockEvent
        @param event: The BlockEvent triggered on NewAmzonWishListEvent command

        @rtype: AmazonCollection or None
        @return: AmazonCollection for the wishlist or None if search results == 0
        """
        return AmazonKinds.SearchWishListByEmail(self.itsView)

class AmazonDetailBlock(Detail.HTMLDetailArea):
    """
    HTMLDetailArea block which renders an AmazonItem as an HTML page including the Product picture
    and customer rating.
    """

    ROW_FONT = "<font face='arial, verdana, helvetica' color='black' size='%s'>%s</font>"
    STAR_URL = "http://g-images.amazon.com/images/G/01/x-locale/common/customer-reviews/stars-%s-%s.gif"

    def getHTMLText(self, item):
        """
        Generates the HTML layout of an AmazonItem.

        @type item: AmazonItem
        @param item: The AmazonItem to use for the HTMLDetailArea

        @rtype: unicode
        @return: The HTML layout for the AmazonItem
        """
        if item is None or item == item.itsView:
            return None

        HTMLText = u'<html><head><body>\n'
        HTMLText += "<b>" + self._applyFont(item.ProductName, 3) + "</b><p>\n"
        HTMLText += "<table cellspacing=2 cellpadding=2 border=0>\n"
        HTMLText += "<tr><td width='30%' valign='top' align='center'><a href='" + str(item.ProductURL) + "'><img src='" + str(item.ImageURL) + "' border=1><br>" + self._applyFont(_(u"More Product Details"), 1) + "</a></td>\n"
        HTMLText += "<td valign='top' align='left'><table width='100%' border=0 cellspacing=2 cellpadding=2>"

        HTMLText += self._makeRow(item, 'Author')
        HTMLText += self._makeRow(item, 'NewPrice')
        HTMLText += self._makeRow(item, 'UsedPrice')
        HTMLText += self._makeRow(item, 'Availability')
        HTMLText += self._makeRow(item, 'ReleaseDate')
        HTMLText += self._makeRating(item)
        HTMLText += self._makeRow(item, 'Manufacturer')
        HTMLText += self._makeRow(item, 'Media')
        HTMLText += "</table>"

        if item.ProductDescription != "":
            HTMLText += "<tr><td colspan=2><br><hr>" + item.ProductDescription + "</td></tr>"

        HTMLText += "</td></tr>\n"
        HTMLText += "</table></body></html>"

        return HTMLText

    def _makeRow(self, item, field):
        val = getattr(item, field, '')
        if val == '':
            return ''

        displayName = item.itsKind.getAttribute(field).displayName

        return u"<tr><td align='right' valign='top' width='40%'>" + self._applyFont("<b>" + displayName + ":</b>") + \
               "</td><td align='left' valign='top'>" + self._applyFont(val) + "</td></tr>"

    def _makeRating(self, item):
        if item.AverageCustomerRating == '':
            return ''

        displayName = item.itsKind.getAttribute("AverageCustomerRating").displayName
        txt = u"<tr><td align='right' valign='top' width='40%'>" + self._applyFont("<b>" + displayName + ":</b>") + "</td>"

        txt += "<td align='left' valign='top'><img src='" + self._getRatingURL(item.AverageCustomerRating) + "'>"
        txt += self._getNumReviews(item.NumberOfReviews)

        txt += "</td></tr>"
        return txt

    def _getNumReviews(self, reviews):
        if reviews == '':
            return ''

        txt = "&nbsp;("

        if int(reviews) == 1:
             txt += _(u"1 customer review")
        else:
            txt += _(u"%(numberOf)s customer reviews") % {'numberOf': reviews}

        txt += ")"

        return self._applyFont(txt)


    def _getRatingURL(self, rating):
        val = rating.split(".")
        numOne = val[0]
        numTwo = 0

        if len(val) > 1 and int(val[1]) >= 5:
            numTwo = 5

        return self.STAR_URL % (numOne, numTwo)

    def _applyFont(self, val, size=2):
        return self.ROW_FONT % (size, val)

 
