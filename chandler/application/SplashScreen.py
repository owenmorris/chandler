__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import webbrowser
import wx
import wx.html


class SplashScreen(wx.Dialog):
    """
      This class implements an HTML informational screen presented to the user. 
    Common uses are for splash screens or 'About' pages.
    The page can be dismissed either by clicking on it or by a timer.
    """
    def __init__(self, parent, title="", pageLocation="",
                 isModal=False, useTimer=True, timerLength=10000):
        """
          Sets up the splash screen and starts its timer.
        """
        if isModal:
            style= wx.FRAME_FLOAT_ON_PARENT|wx.DEFAULT_FRAME_STYLE
        else:
            style = wx.DEFAULT_FRAME_STYLE
        super (SplashScreen, self).__init__ (parent, -1, title, style=style)
        defaultWindowWidth = 700
        maxWindowHeight = 600
        self.isModal = isModal
        panel = HTMLPanel(self, pageLocation, size=(defaultWindowWidth, -1))
        internalRep = panel.GetInternalRepresentation()
        width = internalRep.GetWidth()
        height = internalRep.GetHeight()
        if height > maxWindowHeight:
            height = maxWindowHeight
        panel.SetSize((width, height))
        self.SetClientSize(panel.GetSize())
        
        self.CentreOnScreen()
        
        if useTimer:
            self.timer = SplashTimer(self)
            self.timer.Start(timerLength)
        else:
            self.timer = None
            
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
    def OnCloseWindow(self, event):
        """
          Stops the timer from running and closes the window.
        """
        if self.timer != None:
            self.timer.Stop()
        if self.IsModal():
            self.EndModal(True)
        else:
            self.Destroy()
        
class HTMLPanel(wx.html.HtmlWindow):
    """
      Displays the html message.
    """
    def __init__(self, parent, pageLocation, size):
        """
          Sets up the wx.html.HtmlWindow and loads the proper page to be displayed.
        """
        super (HTMLPanel, self).__init__ (parent,
                                          size=size,
                                          style=wx.HW_SCROLLBAR_AUTO)
        self.parent = parent
        self.LoadPage(pageLocation)
        
    def OnCellClicked(self, cell, x, y, event):
        """
          Called whenever the splash screen is clicked.  If a link was
        clicked, then that link will be opened.  Otherwise, we close the
        splash screen.
        """
        self.linked = false
        wx.html.HtmlWindow.base_OnCellClicked(self, cell, x, y, event)
        if not self.linked:
            self.parent.Close()
        
    def OnLinkClicked(self, link):
        """
          Called whenever a link on the splash screen is clicked.  Opens that
        url in the user's default web browser.
        """
        self.linked = true
        webbrowser.open(link.GetHref())
    
class SplashTimer(wx.Timer):
    """
      A timer that keeps track of how long the splash screen has been 
    displayed.
    """
    def __init__(self, window):
        """
          Sets up the timer.
        """
        super (SplashTimer, self).__init__ ()
        self.window = window
        
    def Notify(self):
        """
          When the timer has expired, we notify the splash screen that it is
        time to close.
        """
        self.window.Close()
        
        
