__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
from application import Globals
from osaf.framework.blocks.ContainerBlocks import BoxContainer
from SOAPpy import WSDL

class StockQuoteViewParcel(application.Parcel.Parcel):

    def startupParcel(self):
        # Make sure our view is in the sidebar
        super(StockQuoteViewParcel, self).startupParcel()

class StockQuoteView(BoxContainer):

    def OnGetQuoteEvent(self, notification):
        if not hasattr (self, "proxy"):
            self.proxy = WSDL.Proxy('http://services.xmethods.net/soap/urn:xmethods-delayed-quotes.wsdl')
        symbolText = Globals.repository.findPath('//parcels/osaf/examples/stockquote/views/StockQuoteView/SymbolText')
        symbol = symbolText.widget.GetValue()
        valueLabel = Globals.repository.findPath('//parcels/osaf/examples/stockquote/views/StockQuoteView/ValueLabel')
        valueLabel.widget.SetLabel('')#Allow user to notice change
        valueLabel.widget.SetLabel('$' + str(self.proxy.getQuote( symbol )))

    def onEnterPressedEvent(self, notification):
        self.OnGetQuoteEvent(notification)
