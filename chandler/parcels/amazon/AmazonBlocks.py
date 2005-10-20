__parcel__ = "amazon"

import osaf.framework.blocks.Block as Block
import AmazonKinds
import application.Globals as Globals
import osaf.framework.blocks.detail.Detail as Detail

#XXX[i18n] this module sits outsite of OSAF and should have its own translation domain
from i18n import OSAFMessageFactory as _

class AmazonController(Block.Block):
    def onNewAmazonCollectionEvent(self, event):
        return AmazonKinds.SearchByKeyword(self.itsView, Globals.views[0])

    def onNewAmazonWishListEvent(self, event):
        return AmazonKinds.SearchWishListByEmail(self.itsView, Globals.views[0])

class AmazonDetailBlock(Detail.HTMLDetailArea):
    ROW_FONT = "<font face='arial, verdana, helvetica' color='black' size='%s'>%s</font>"
    STAR_URL = "http://g-images.amazon.com/images/G/01/x-locale/common/customer-reviews/stars-%s-%s.gif"

    def getHTMLText(self, item):
        if item is None or item == item.itsView:
            return None

        HTMLText = u'<html><head><body>\n'
        HTMLText += "<b>" + self.applyFont(item.ProductName, 3) + "</b><p>\n"
        HTMLText += "<table cellspacing=2 cellpadding=2 border=0>\n"
        HTMLText += "<tr><td width='30%' valign='top' align='center'><a href='" + str(item.ProductURL) + "'><img src='" + str(item.ImageURL) + "' border=1><br>" + self.applyFont(_(u"More Product Details"), 1) + "</a></td>\n"
        HTMLText += "<td valign='top' align='left'><table width='100%' border=0 cellspacing=2 cellpadding=2>"

        HTMLText += self.makeRow(item, 'Author')
        HTMLText += self.makeRow(item, 'NewPrice')
        HTMLText += self.makeRow(item, 'UsedPrice')
        HTMLText += self.makeRow(item, 'Availability')
        HTMLText += self.makeRow(item, 'ReleaseDate')
        HTMLText += self.makeRating(item)
        HTMLText += self.makeRow(item, 'Manufacturer')
        HTMLText += self.makeRow(item, 'Media')
        HTMLText += "</table>"

        if item.ProductDescription != "":
            HTMLText += "<tr><td colspan=2><br><hr>" + item.ProductDescription + "</td></tr>"

        HTMLText += "</td></tr>\n"
        HTMLText += "</table></body></html>"

        return HTMLText

    def makeRow(self, item, field):
        val = getattr(item, field, '')
        if val == '':
            return ''

        displayName = item.itsKind.getAttribute(field).displayName

        return u"<tr><td align='right' valign='top' width='40%'>" + self.applyFont("<b>" + displayName + ":</b>") + \
               "</td><td align='left' valign='top'>" + self.applyFont(val) + "</td></tr>"

    def makeRating(self, item):
        if item.AverageCustomerRating == '':
            return ''

        displayName = item.itsKind.getAttribute("AverageCustomerRating").displayName
        txt = u"<tr><td align='right' valign='top' width='40%'>" + self.applyFont("<b>" + displayName + ":</b>") + "</td>"

        txt += "<td align='left' valign='top'><img src='" + self.getRatingURL(item.AverageCustomerRating) + "'>"
        txt += self.getNumReviews(item.NumberOfReviews)

        txt += "</td></tr>"
        return txt

    def getNumReviews(self, reviews):
        if reviews == '':
            return ''

        txt = "&nbsp;("

        if int(reviews) == 1:
             txt += _(u"1 customer review")
        else:
            txt += _(u"%(numberOf)s customer reviews") % {'numberOf': reviews}

        txt += ")"

        return self.applyFont(txt)


    def getRatingURL(self, rating):
        val = rating.split(".")
        numOne = val[0]
        numTwo = 0

        if len(val) > 1 and int(val[1]) >= 5:
            numTwo = 5

        return self.STAR_URL % (numOne, numTwo)

    def applyFont(self, val, size=2):
        return self.ROW_FONT % (size, val)

 
