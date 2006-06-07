__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import webbrowser
import wx
import wx.html

class AboutBox(wx.Dialog):
    """
      This class implements an HTML informational screen presented to the user. 
    Common use is for 'About' pages.
    The page must be dismissed by clicking on its close button.
    """
    def __init__(self, parent=None, title="", pageLocation="", html="", isModal=True):
        """
          Sets up the about box.
        """
        style = wx.DEFAULT_DIALOG_STYLE
        size =  wx.DefaultSize
        pos = wx.DefaultPosition
        
        super (AboutBox, self).__init__ (parent, -1, title, pos, size, style)
                
        defaultWindowWidth = 285
        maxWindowHeight = 600
        self.isModal = isModal
        panel = HTMLPanel(self, pageLocation, html,
                          size=(defaultWindowWidth, -1))
        internalRep = panel.GetInternalRepresentation()
        width = internalRep.GetWidth()
        height = internalRep.GetHeight()
        if height > maxWindowHeight:
            height = maxWindowHeight
        panel.SetSize((width, height))
        self.SetClientSize(panel.GetSize())
        
        self.CenterOnScreen()
                    
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        # Display the dialog
        if isModal:
            self.ShowModal()
        else:
            self.Show()

        
    def OnCloseWindow(self, event):
        """
          Closes the window.
        """
        self.Destroy()
        
class HTMLPanel(wx.html.HtmlWindow):
    """
      Displays the html message.
    """
    def __init__(self, parent, pageLocation, html, size):
        """
          Sets up the wx.html.HtmlWindow and loads the proper page to be displayed.
        """
        super (HTMLPanel, self).__init__ (parent,
                                          size=size,
                                          style=wx.html.HW_SCROLLBAR_NEVER)
        self.parent = parent
        if pageLocation:
            self.LoadPage(pageLocation)
        else:
            self.SetPage(html)
        
    def OnCellClicked(self, cell, x, y, event):
        """
          Called whenever the about box is clicked.
        """
        wx.html.HtmlWindow.base_OnCellClicked(self, cell, x, y, event)
                
    def OnLinkClicked(self, link):
        """
          Called whenever a link on the about box is clicked.  Opens that
        url in the user's default web browser.
        """
        webbrowser.open(link.GetHref())
