""" ZaoBao blocks
"""

__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from repository.item.Query import KindQuery
from osaf.framework.blocks.ControlBlocks import Tree, ItemDetail, ListDelegate
import osaf.examples.zaobao.RSSData as RSSData
import osaf.framework.blocks.detail.Detail as Detail

class ZaoBaoItemDetail(Detail.HTMLDetailArea):

    def getHTMLText(self, item):
        if item == item.itsView:
            return
        if item is not None:
            displayName = item.getAttributeValue('displayName', default='<Untitled>')

            # make the html
            HTMLText = '<html><body>\n\n'

            link = item.getAttributeValue('link', default=None)
            if link:
                HTMLText = HTMLText + '<a href="%s">' % (link)
            HTMLText = HTMLText + '<h5>%s</h5>' % (displayName)
            if link:
                HTMLText = HTMLText + '</a>\n'

            content = item.getAttributeValue('content', default=None)
            if content:
                content = content.getReader().read()
            else:
                content = displayName
            #desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            HTMLText = HTMLText + '<p>' + content + '</p>\n\n'
            #should find a good way to localize "more..."
            HTMLText = HTMLText + '<br><a href="' + str(item.link) + '">more...</a>'

            HTMLText = HTMLText + '</body></html>\n'

            return HTMLText


class LinkDetail(Detail.StaticRedirectAttribute):
    def staticTextLabelValue(self, item):
        theLabel = str(item.getAttributeValue(Detail.GetRedirectAttribute(item, self.whichAttribute())))
        return theLabel
