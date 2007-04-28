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
from osaf import sharing
from i18n import ChandlerMessageFactory as _

class ConflictDialog(wx.Dialog):
    def __init__(self, conflicts):
        self.conflicts = conflicts
        wx.Dialog.__init__(self, None, -1, _(u'Pending Changes'),
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.RESIZE_BOX)
        conflictCount = len(conflicts)
        if conflictCount == 1:
            headingText = _(u"There is one pending change")
        else:
            headingText = _(u"There are %d pending changes") % conflictCount
        heading = wx.StaticText(self, -1, headingText)
        # Iterate over the items so as to be able to prepend the index.
        # Otherwise we could use:
        #   listBox = wx.ListBox(self, -1,
        #       choices=["%s: %s (%s)" % (x.field, x.value, x.peer)
        #           for x in conflicts])
        i=1
        itemList=[]
        for c in conflicts:
            fmt = "%d. %s: %s"
            if c.peer:
                if isinstance(c.peer, sharing.Share):
                    fmt += " (changed on server)"
                else:
                    fmt += " (changed by %s)" % c.peer
            itemList.append(fmt % (i, c.field.title(), c.value))
            i = i+1
        listBox = wx.ListBox(self, -1, choices=itemList)
        changesText = wx.StaticText(self, -1,
            _(u"Changes will be applied in the order listed above.\nItem cannot be Updated or Synced until changes are applied or discarded"))
        applyButton = wx.Button(self, wx.ID_OK, _(u"Apply Changes"))
        discardButton = wx.Button(self, -1, _(u"Discard Changes"))
        laterButton = wx.Button(self, wx.ID_CANCEL, _(u"Decide Later"))

        heading.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        changesText.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        applyButton.SetDefault()
        applyButton.Bind(wx.EVT_BUTTON, self.onApplyUpdates)
        discardButton.Bind(wx.EVT_BUTTON, self.onDiscardUpdates)
        laterButton.Bind(wx.EVT_BUTTON, self.onLater)

        # layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add((20, 10), 0)
        mainSizer.Add(heading, 0, wx.ALL, 5)
        mainSizer.Add(listBox, 4, wx.EXPAND|wx.ALL, 5)
        mainSizer.Add((20, 10), 0)
        changesSizer = wx.BoxSizer(wx.HORIZONTAL)
        changesSizer.Add((20, 10), 0)
        changesSizer.Add(changesText, 0, wx.EXPAND|wx.ALL, 1)
        mainSizer.Add(changesSizer, 0)
        mainSizer.Add((20, 10), 0)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add((20, 20), 0)
        buttonSizer.Add(applyButton)
        buttonSizer.Add((20, 20), 0)
        buttonSizer.Add(discardButton)
        buttonSizer.Add((20, 20), 0)
        buttonSizer.Add(laterButton)
        buttonSizer.Add((20, 20), 0)
        mainSizer.Add(buttonSizer, 0, wx.BOTTOM|wx.RIGHT, 3)
        mainSizer.Add((20, 10), 0)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        mainSizer.SetSizeHints(self)

    def onApplyUpdates(self, event):
        for c in self.conflicts:
            c.apply()
        self.Close()

    def onDiscardUpdates(self, event):
        for c in self.conflicts:
            c.discard()
        self.Close()

    def onLater(self, event):
        self.Close()
