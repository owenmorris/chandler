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

import wx
import logging
import os, sys
from application import schema, Globals
from i18n import ChandlerMessageFactory as _
from application.dialogs.RecurrenceDialog import getProxy
import TimeZoneList
from osaf.pim.calendar import TimeZoneInfo

logger = logging.getLogger(__name__)

PUBLISH   = 0
IMPORT    = 1
EXPORT    = 2

stateData = { IMPORT : 
              {'title' : _(u"Use time zones"),
               'hide'  : [wx.ID_CANCEL],
               'text'  : _(u"You have received an event with time zone information. For optimal viewing, would you like to assign a time zone to your items as well?")
              },
              PUBLISH : 
              {'title' : _(u"Use time zones"),
               'hide'  : [],
               'text'  : _(u"Would you like to assign a time zone to your items before sharing them with others?")
              },              
              EXPORT : 
              {'title' : _(u"Use time zones"),
               'hide'  : [],
               'text'  : _(u"Would you like to assign a time zone to your items before exporting them?")
              },              
            }

# don't pop up more than one dialog, which can happen when importing events
# spawns lots of non-modal dialogs.
dialogShowing = False

def ShowTurnOnTimezonesDialog(view=None, state=IMPORT, modal=False, parent=None):
    
    if dialogShowing:
        return True
    
    # Check preferences before showing the dialog
    tzprefs = schema.ns('osaf.pim', view).TimezonePrefs
    if tzprefs.showUI or not tzprefs.showPrompt:
        return True
    
    filename = 'TurnOnTimezones.xrc'
    xrcFile = os.path.join(Globals.chandlerDirectory,
                           'application', 'dialogs', filename)
    #[i18n] The wx XRC loading method is not able to handle raw 8bit paths
    #but can handle unicode
    xrcFile = unicode(xrcFile, sys.getfilesystemencoding())
    resources = wx.xrc.XmlResource(xrcFile)
    win = TurnOnTimezonesDialog(resources=resources, view=view,
                                state=state, modal=modal, parent=parent)
    win.CenterOnScreen()
    if modal:
        return win.ShowModal()
    else:
        win.Show()
        return win

class TurnOnTimezonesDialog(wx.Dialog):

    def __init__(self, resources=None, view=None, state=IMPORT,
                 modal=True, parent=None):
        global dialogShowing
        dialogShowing = True

        self.resources = resources
        self.view      = view
        self.modal     = modal
        self.state     = state
        
        self.changedTimeZone = None

        pre = wx.PreDialog()
        self.resources.LoadOnDialog(pre, parent, None, "TurnOnTimezonesDialog")
        self.PostCreate(pre)

        self.text     = wx.xrc.XRCCTRL(self, "Text")
        self.checkbox = wx.xrc.XRCCTRL(self, "Checkbox")
        self.chooser  = wx.xrc.XRCCTRL(self, "Chooser")

        TimeZoneList.buildTZChoiceList(view, self.chooser)

        self.FillButtonPanel()        
        
        self.SetText()
        
        self.Bind(wx.EVT_BUTTON, self.OnYes, id=wx.ID_YES)
        self.Bind(wx.EVT_BUTTON, self.OnNo, id=wx.ID_NO)
        self.Bind(wx.EVT_BUTTON, self.End, id=wx.ID_CANCEL)
        self.chooser.Bind(wx.EVT_CHOICE, self.OnTZChoice)

        self.Fit()

    def FillButtonPanel(self):
        """Use StdDialogButtonSizer to get buttons in the appropriate order."""
        self.buttonSizer = sizer = wx.StdDialogButtonSizer()
        sizer.AddButton(wx.Button(self, wx.ID_YES))
        sizer.AddButton(wx.Button(self, wx.ID_NO))
        sizer.AddButton(wx.Button(self, wx.ID_CANCEL))
        sizer.Realize()
        self.checkbox.GetContainingSizer().Add(sizer, wx.EXPAND|wx.ALL, 10)
        

    def SetText(self):
        self.checkbox.SetLabel(_(u"Don't ask again"))
        self.checkbox.SetValue(True)
        
        data = stateData[self.state]
        for id in data['hide']:
            self.FindWindowById(id).Hide()
        
        self.SetTitle(data['title'])
        self.text.SetLabel(data['text'])
        self.text.Wrap(250)

    def HandleDontRepeat(self):
        if self.checkbox.GetValue():
            schema.ns('osaf.pim', self.view).TimezonePrefs.showPrompt = False

    def OnYes(self, event):
        if self.changedTimeZone is not None:
            TimeZoneInfo.get(self.view).default = self.changedTimeZone

        schema.ns('osaf.pim', self.view).TimezonePrefs.showUI = True

        
        self.view.commit()

        self.HandleDontRepeat()
        self.End(ret=True)

    def OnNo(self, event):
        self.HandleDontRepeat()
        self.End(ret=True)

    def End(self, event=None, ret=False):
        global dialogShowing
        dialogShowing = False        
        if self.modal:
            self.EndModal(ret)
        self.Destroy()
        

    def OnTZChoice(self, event):
        choiceIndex = self.chooser.GetSelection()
        if choiceIndex != -1:
            oldTZ = TimeZoneInfo.get(self.view).default
            newTZ = self.chooser.GetClientData(choiceIndex)
            if newTZ == TimeZoneList.TIMEZONE_OTHER_FLAG:
                newTZ = TimeZoneList.pickTimeZone(self.view)
                if newTZ is None:
                    newTZ = oldTZ
                TimeZoneList.buildTZChoiceList(self.view, self.chooser, newTZ)

            if newTZ != oldTZ:
                self.changedTimeZone = newTZ

