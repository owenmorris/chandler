__parcel__ = "osaf.examples.amazon"

import osaf.framework.blocks.Block as Block
import AmazonKinds
import application.Globals as Globals
import osaf.framework.blocks.detail.Detail as Detail

class AmazonController(Block.Block):
    def onNewAmazonCollectionEvent(self, event):
        print "Creating a new amazon collection"
        AmazonKinds.CreateCollection(self.itsView, Globals.views[0])
        
    def onNewAmazonWishListEvent(self, event):
        print "Creating a new amazon wish list"
        AmazonKinds.CreateWishListCollection(self.itsView, Globals.views[0])

class ImageBlock(Detail.HTMLDetailArea):
    def getHTMLText(self, item):
        if item == item.itsView:
            return
        if item is not None:
            
            # make the html
            HTMLText = '<html><body>\n\n'
            HTMLText = HTMLText + '<img src = "' + str(item.imageURL) + '">\n\n</html></body>'

            return HTMLText