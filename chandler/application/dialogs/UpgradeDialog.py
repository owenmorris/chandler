#   Copyright (c) 2007 Open Source Applications Foundation
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


"""
Dialog box that conditionally runs at startup.
Provides the user with the option of starting Chandler with reload options
"""

# borrowed almost verbatim from StartupOptionsDialog - any mistakes are mine (bear)

import os, sys, wx, glob
from application.Utility import locateProfileDir


# We can't use the regular localization mechanism because the repository isn't
# open yet, but we might someday have a better way of doing this, so I'm leaving
# the hook in place.
_ = lambda msg: msg

class UpgradeDialog(wx.Dialog):
    @classmethod
    def run(cls, exception=None):
        dialog = UpgradeDialog(exception)

        profileBase = os.path.dirname(os.path.dirname(locateProfileDir()))
        dirlist     = glob.glob(os.path.join(profileBase, '0.7*'))

        if len(dirlist) > 0:
            dialog.exitReload.SetValue(True)
        else:
            dialog.normalStartup.SetValue(True)

        dialog.ShowModal()
        dialog.Destroy()

    def __init__(self, exception=None):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        style = wx.CAPTION
        pre.Create(None, -1, _(u"Reload options for Chandler"), 
                   wx.DefaultPosition, wx.DefaultSize, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Construct the controls and lay them out; their member names match 
        # the options they set in Globals.options below.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((0, 3)) 

        self.normalStartup = wx.RadioButton(self, -1, _(u"Continue with normal startup"))
        sizer.Add(self.normalStartup, flag=wx.ALL, border=5)
        self.normalStartup.Bind(wx.EVT_LEFT_DCLICK, self.onButton)

        self.exitReload = wx.RadioButton(self, -1, _(u"Exit Chandler and create a dump of your previous vesion"))
        sizer.Add(self.exitReload, flag=wx.ALL, border=5)
        self.exitReload.Bind(wx.EVT_LEFT_DCLICK, self.onButton)

        box = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.OK, _(u"OK"))
        okButton.Bind(wx.EVT_BUTTON, self.onButton)
        box.Add(okButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        sizer.Add(box, 1, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.CenterOnScreen()

    def onButton(self, event):
        if self.exitReload.GetValue():
            sys.exit(0)

        self.EndModal(wx.OK)

