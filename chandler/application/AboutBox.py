#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


import wx, wx.html, os, sys
import i18n
import Utility
import Globals
from i18n import ChandlerMessageFactory as _

class AboutBox(wx.Dialog):
    """
      This class implements an HTML informational screen presented to the user. 
    Common use is for 'About' pages.
    The page must be dismissed by clicking on its close button.
    """
    def __init__(self, parent=None, title=None, pageLocation="", html=None, isModal=True):
        """
          Sets up the about box.
        """
        style = wx.DEFAULT_DIALOG_STYLE
        size =  wx.DefaultSize
        pos = wx.DefaultPosition

        if title is None:
            title = _(u"About Chandler")

        if html is None:
            html = _getDefaultHTML()

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
        # webbrowser.open() is known to be unreliable on Linux so using wx instead
        wx.LaunchDefaultBrowser(link.GetHref(), wx.BROWSER_NEW_WINDOW)

def _getDefaultHTML():
    from version import version

    replaceValues = {

    # These images are loaded by wx from Python localization
    # Eggs. The image: prefix signals to wx invoke
    # The I18nManager.getImage method to locate the 
    # localized image.
    "pix":  "image:pixel.gif",
    "ab":   "image:about.png",
    "ver":  _(u"Version %(versionNumber)s for %(platform)s") % {"versionNumber": version, "platform":Utility.getPlatformName()},
    "abt":  _(u"About Chandler"),
    "ch":   (u"Chandler\u2122 Preview"),
    "osa":  (u"Open Source Applications Foundation"),
    #L10N: The Chandler licensing information is displayed in an HTML page.
    #      The <br> tag represents a line break and should be preserved.
    "lic": _(u"Chandler is licensed under the<br>Apache Licence, Version 2.0."),
    "loc":  _(u"Visit %(chandlerWebURL)s for more information.") % \
           {"chandlerWebURL": "<a href=\"http://chandlerproject.org\">Chandler Project</a>"},
    #This is a bummer the % in the width attribute was causing the
    #Python string parser to barf. It thought this was a replacable value :(
    "wid": "100%"

    }

    html = u"""<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>%(abt)s</title>
</head>
<body bgcolor="#FFFFFF">

<center>
<table width="%(wid)s" border="0" cellpadding="0" cellspacing="0">
<tr><td><img src="%(pix)s" width="1" height="15"></td></tr>
<tr><td><center><img src="%(ab)s" width="64" height="64"></center></td></tr>
<tr><td><img src="%(pix)s" width="1" height="20"></td></tr>
<tr><td><center><font face="verdana, arial, helvetica, sans-serif" size="+1" color="black"><strong>%(ch)s</strong></font></center></td></tr>
<tr><td><center><font face="helvetica, arial, sans-serif" size="-1" color="black">%(ver)s</font></center></td></tr>
<tr><td><img src="%(pix)s" width="1" height="10"></td></tr>
<tr><td><center><font face="helvetica, arial, sans-serif" size="-1" color="black"> %(lic)s </font></center></td></tr>
<tr><td><center><font face="helvetica, arial, sans-serif" size="-1" color="black"> %(loc)s </font></center></td></tr>
<tr><td><img src="%(pix)s" width="1" height="10"></td></tr>
<tr><td><center><font face="helvetica, arial, sans-serif" size="-1" color="black">
%(osa)s</font></center></td></tr>
</table>
</center>

</body>
</html>""" % replaceValues

    return html

def _getRelImagePath(imgName):
    f = i18n.getImage(imgName)

    if f is None:
        return ""

    n = f.name

    if isinstance(n, unicode):
        n = n.encode(sys.getfilesystemencoding())

    #We want a relative directory so
    #remove CHANDLERHOME from path
    p = n.split(Globals.chandlerDirectory)[1]

    #We still want a relative path so strip of the leading
    #directory path separator
    if p[0] == os.path.sep:
        p = p[1:]

    return unicode(p, sys.getfilesystemencoding())
