__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from application import Globals
from osaf.framework.blocks.ContainerBlocks import BoxContainer
from repository.parcel.Parcel import Parcel
from SOAPpy import WSDL

class StockQuoteViewParcel(Parcel):

    def __init__(self, name, parent, kind):
        Parcel.__init__(self, name, parent, kind)

    def startupParcel(self):
        # Make sure our view is in the sidebar
        Parcel.startupParcel(self)
        rep = self.getRepository()
        urlRoot = rep.findPath("//parcels/osaf/views/main/URLRoot")
        sqNode = rep.findPath("//parcels/osaf/examples/stockquote/views/StockQuoteViewNode")
        if urlRoot and sqNode:
            urlRoot.children.append(sqNode)

class StockQuoteView(BoxContainer):

    def OnGetQuoteEvent(self, notification):
        if not hasattr (self, "proxy"):
            self.proxy = WSDL.Proxy('http://services.xmethods.net/soap/urn:xmethods-delayed-quotes.wsdl')
        symbolText = Globals.repository.findPath('//parcels/osaf/examples/stockquote/views/StockQuoteView/SymbolText')
        symbol = symbolText.widget.GetValue()
        valueLabel = Globals.repository.findPath('//parcels/osaf/examples/stockquote/views/StockQuoteView/ValueLabel')
        valueLabel.widget.SetLabel('')#Allow user to notice change
        valueLabel.widget.SetLabel('$' + str(self.proxy.getQuote( symbol )))

