__author__ = "Heikki Toivonen"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF"

# TODO: Would be nice if hitting enter in the edit box submitted.
# ??

from application.Application import app
from application.ViewerParcel import *
from SOAPpy import WSDL

class StockQuoteModel(ViewerParcel): 
    def __init__(self): 
        ViewerParcel.__init__(self)
                
class wxStockQuoteViewer(wxViewerParcel): 
    def OnInit(self):
        self.quoteLabel = XRCCTRL(self, "QuoteLabel")
        self.stockSymbol = XRCCTRL(self, "StockSymbol")
        EVT_MENU(self, XRCID('GetQuoteMenuItem'), self.OnGetQuote)
        EVT_BUTTON(self, XRCID('GetQuoteButton'), self.OnGetQuote)

    def OnGetQuote(self, event):
        if not hasattr (self, "proxy"):
            self.proxy = WSDL.Proxy('http://services.xmethods.net/soap/urn:xmethods-delayed-quotes.wsdl')
        stockSymbol = self.stockSymbol.GetValue()
        self.quoteLabel.Clear() # Allows user to notice something happened
        self.quoteLabel.SetLabel('$' + str(self.proxy.getQuote(stockSymbol)))


    
