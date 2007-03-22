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


import wx, webbrowser

from flickr import setLicense
from application import Utility, Globals
from i18n import MessageFactory

LICENSE_URL="http://www.flickr.com/services/api/misc.api_keys.html"
PLUGIN_NAME="Chandler-FlickrPlugin"
_m_ = MessageFactory(PLUGIN_NAME)


class LicenseTask(object):
    
    def __init__(self, item):
        pass
        
    def run(self):
        prefs = Utility.loadPrefs(Globals.options).get(PLUGIN_NAME)
        if prefs is not None:
            license = prefs.get('license')
            if license:
                setLicense(license)
        return True


class LicenseDialog(wx.Dialog):

    def __init__(self, parent, ID):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, _m_(u"Enter Flickr Web Services API Key"),
                   wx.DefaultPosition, wx.DefaultSize, wx.DEFAULT_DIALOG_STYLE)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridSizer(2, 2)

        # License (text control)....
        label = wx.StaticText(self, -1, _m_(u"API Key:"))
        grid.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.licenseText = wx.TextCtrl(self, -1, u"",
                                       wx.DefaultPosition, [150, -1])
        grid.Add(self.licenseText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
                
        sizer.Add(grid, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # Register (button)....
        button = wx.Button(self, -1, "Register")
        self.Bind(wx.EVT_BUTTON, self.onRegister, button)
        
        buttonSizer = wx.StdDialogButtonSizer()
        buttonSizer.AddButton(wx.Button(self, wx.ID_OK))
        buttonSizer.AddButton(wx.Button(self, wx.ID_CANCEL))
        buttonSizer.Realize()
        buttonSizer.Insert(0, button)

        sizer.Add(buttonSizer, 0,
                  wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def onRegister(self, evt):

        webbrowser.open(LICENSE_URL)

    def getParameters(self):

        return { 
            'license': self.licenseText.GetValue(),
        }


def promptLicense():

    dialog = LicenseDialog(wx.GetApp().mainFrame, -1)
    dialog.CenterOnScreen()

    if dialog.ShowModal() == wx.ID_OK:
        params = dialog.getParameters()
    else:
        params = None

    dialog.Destroy()

    if params is not None:
        license = params['license']
        if license:
            prefs = Utility.loadPrefs(Globals.options)
            pluginPrefs = prefs.setdefault(PLUGIN_NAME, {})
            pluginPrefs['license'] = license
            prefs.write()
            setLicense(license)
            return True

    return False
