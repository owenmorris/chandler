#   Copyright (c) 2003-2006 Open Source Applications Foundation
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
from i18n import MessageFactory

_ = MessageFactory("Chandler-EVDBPlugin")

# Fields in the Date: drop-down. Values can be handed off
# the evdb module to run queries (with the exception of "This month".
_DATES = ["All", "Future", "Past", "Today", "Last Week", "This Week", "Next week", "This month"]

# Localized names for the above.
_DATE_NAMES = [
    _(u"All"),
    _(u"Future"),
    _(u"Past"),
    _(u"Today"),
    _(u"Last Week"),
    _(u"This Week"),
    _(u"Next Week"),
    _(u"This Month")
]


def GetSearchDictFromDialog():
    """
    Gets user input from the EVDB dialog, returning C{None}
    if the user presses "Cancel". Otherwise, the returned
    C{dict} has keys 'location',  'keywords' and 'dates',
    and
    
    
    """
    win = KeywordDialog(wx.GetApp().mainFrame, -1)
    win.CenterOnScreen()
    val = win.ShowModal()
    
    result = None

    if val == wx.ID_OK:
       # Get the new keywords
       result = win.getSearchDict()

    win.Destroy()

    return result


class KeywordDialog(wx.Dialog):
    def __init__(self, parent, ID):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, _(u"EVDB Event Search"), wx.DefaultPosition,
                   wx.DefaultSize, wx.DEFAULT_DIALOG_STYLE)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Location (text control)....
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _(u"Location:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.locationText = wx.TextCtrl(self, -1, u"", wx.DefaultPosition, [350,-1])
        box.Add(self.locationText, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
                
        # Dates (Choice)....
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _(u"Dates:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.datesChoice = wx.Choice(self, -1, choices=_DATE_NAMES)
        box.Add(self.datesChoice, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.datesChoice.SetSelection(0)
        
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        # Keywords:
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _(u"Keywords:"))
        box.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        self.keywordText = wx.TextCtrl(self, -1, u"", wx.DefaultPosition, [350,-1])
        box.Add(self.keywordText, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        sizer.Add(self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL), 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def getSearchDict(self):
        result = {}
        
        keywords = unicode(self.keywordText.GetValue())
        if keywords:
            result['keywords'] = keywords
        
        location = unicode(self.locationText.GetValue())
        if location:
            result['location'] = location
            
        dates = _DATES[self.datesChoice.GetSelection()]
        if dates != "All":
            # evdb doesn't actually support a "This month"
            # query; we have to translate it into the
            # actual month name.
            if dates == "This month":
                from time import strftime, gmtime
                dates = strftime("%B", gmtime())
            result['dates'] = dates
            
        return result

