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
Conflict Dialog

This implements the spec as set out in http://chandlerproject.org/Journal/NoDataLossProposal
specifically, the image:
    http://chandlerproject.org/pub/Journal/NoDataLossProposal/No_data_loss_pop-up_Three.png
The blue background colours are still unimplemented.

The user is presented with a list of action choices, one for each conflict reported. When the
outcome of a conflict is decided (Apply/Discard), the buttons for that conflict are disabled,
reflecting the lack of any undo.

Notes:
Due to the restrictions of the text fields, the dialog is fixed-size. Attempts were made to
make the dialog resizable, but text fields are not yet well-suited to automatically shrinking
and growing on the fly inside a sizer inside a ScrolledPanel.

Dev Notes:
Alternate implementations using VScrolledWindow and wx.stc.StyledTextCtrl were attempted before
deciding to use the classes below.
"""
import wx
from wx.lib.scrolledpanel import ScrolledPanel
import wx.lib.expando
from osaf import sharing
from i18n import ChandlerMessageFactory as _
from osaf.framework.blocks import DragAndDrop

class CopyableStyleTextCtrl(wx.lib.expando.ExpandoTextCtrl, DragAndDrop.TextClipboardHandler):
    def __init__(self, parent, text, isOdd):
        super(CopyableStyleTextCtrl, self).__init__(parent, -1)

        # the actual changes are block, but the "info" text at the beginning is grey
        textColour = wx.SystemSettings_GetColour(wx.SYS_COLOUR_GRAYTEXT)
        style = wx.TextAttr(textColour)
        self.SetDefaultStyle(style)
        self.WriteText(text)

    def Hilight(self, emStart, emEnd):
        # Hilight all occurences of emStart..emEnd in the text and remove the emStart/emEnd tags
        text = self.GetValue()
        textLen = len(text)

        # make it standard text colour
        hilightStyle = wx.TextAttr(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT))

        hilightStart = text.find(emStart)
        while hilightStart >= 0:
            hilightEnd = text.find(emEnd, hilightStart)
            self.SetStyle(hilightStart, hilightEnd, hilightStyle)
            hilightStart = text.find(emStart, hilightEnd)

        # clear out the tag strings
        hilightStart = text.rfind(emStart)
        while hilightStart >= 0:
            hilightEnd = text.find(emEnd, hilightStart)
            self.Replace(hilightEnd, hilightEnd+len(emEnd), '')
            self.Replace(hilightStart, hilightStart+len(emStart), '')
            text = self.GetValue()
            hilightStart = text.rfind(emStart)

    def AdjustToSize(self):
        """
        Set the minimum height, which shows all the text without a scrollbar.
        """
        self._adjustCtrl()



class ConflictButton(wx.Button):
    """
    Buttons in the scrolling area of the conflict dialog.
    Each button needs to know which conflict it's associated with, and when
    it is clicked, it has to call back to the parent window so that both it
    and its counterpart are disabled -- i.e. clicking either "Accept" or "Discard"
    will disable both buttons.
    The method "onPress(self, event)" must be implemented in subclasses
    """
    def __init__(self, window, id, text, conflict, callback, userData):
        self.conflict = conflict
        self.callback = callback
        self.userData = userData
        super(ConflictButton, self).__init__(window, id, text)
        self.Bind(wx.EVT_BUTTON, self.onPress, self)

class ConflictAcceptButton (ConflictButton):
    def onPress(self, event):
        self.conflict.apply()
        self.callback(self.userData)

class ConflictDiscardButton (ConflictButton):
    def onPress(self, event):
        self.conflict.discard()
        self.callback(self.userData)

class ConflictVScrolledArea(ScrolledPanel):
    """
    The vertical scrolling area in which all the conflicts are listed.
    wx.VScrolledWindow handles the scrolling, via OnGetLineHeight().
    """
    columnCount = 3
    def __init__(self, frame, conflicts, callback):
        self.conflicts = conflicts
        self.acceptButtons = list()
        self.discardButtons = list()
        self.textControls = list()
        self.callback = callback

        # keep a list of buttons for disabling when clicked on
        self.sizer = wx.FlexGridSizer(rows=len(conflicts), cols=self.columnCount, hgap=8, vgap=5) 

        self.sizer.AddGrowableCol(0, proportion=1)
        super(ConflictVScrolledArea, self).__init__(frame)

        # markers used to hilight text in each conflict string. These values
        # should never appear in a conflict, since they would be stripped out
        # earlier by the EIM code.
        emStart = u"\002"
        emEnd = u"\003"
 
        i = 0
        
        # add the conflicts
        for c in conflicts:
            # if there is no peer, the change was done on the server
            if c.peer is not None:
                if isinstance(c.peer, sharing.Share):
                    editor = _(u"Subscriber")
                else:
                    editor = c.peer
            else:
                editor = _("An unknown party")

            if c.pendingRemoval:
                # local modification to an item that was removed on the server
                fmt = _(u"%(index)3d. %(em)s%(person)s%(/em)s removed this item from the %(em)scollection%(/em)s")
            elif c.change.exclusions:
                # stamp changed on an item where stamp was removed on the server
                if "sharing.model.MailMessageRecord" in c.value:
                    fmt = _(u"%(index)3d. %(em)s%(person)s%(/em)s removed %(em)saddresses%(/em)s from this item")
                elif "sharing.model.EventRecord" in c.value:
                    fmt = _(u"%(index)3d. %(em)s%(person)s%(/em)s removed this item from the %(em)sCalendar%(/em)s")
                elif "sharing.model.TaskRecord" in c.value:
                    fmt = _(u"%(index)3d. %(em)s%(person)s%(/em)s removed this item from the %(em)sTask List%(/em)s")
                else:
                    # unknown stamp type
                    fmt = _(u"%(index)3d. %(em)s%(person)s%(/em)s removed %(em)s%(fieldName)s%(/em)s from this item")
            elif c.field.title() == 'Rrule' and c.value == 'None':
                # Recurrence changed on an item where recurrence was removed on the server
                fmt = _(u"%(index)3d. %(em)s%(person)s%(/em)s changed %(em)sOccurs%(/em)s to %(em)sOnce%(/em)s")
            else:
                # general case: attribute changed both locally and on the server
                fmt = _(u"%(index)3d. %(em)s%(person)s%(/em)s changed the %(em)s%(fieldName)s%(/em)s to %(em)s%(value)s%(/em)s")

            # build the text string
            text = fmt % {
                'index': i+1,
                'person': editor,
                'fieldName': "" if c.field is None else c.field.title(),
                'value': c.value,
                'em': emStart,
                '/em': emEnd
            }

            textCtrl = CopyableStyleTextCtrl(self, text, i%2)

            # make it read-only and add it to the sizer
            textCtrl.SetEditable(False)
            self.sizer.Add(textCtrl, 1, wx.EXPAND)
            # hilight the text
            textCtrl.Hilight(emStart, emEnd)

            # add the buttons to apply/discard. Both buttons are disabled when either is
            # clicked, so we keep a reference to them in the two lists self.acceptButtons
            # and self.discardButtons, which are used in the DisableButtons() method
            acceptButton = ConflictAcceptButton(self, wx.ID_APPLY, "Apply", c, self.DisableButtons, i)
            self.acceptButtons.append(acceptButton)
            self.sizer.Add(acceptButton)

            discardButton = ConflictDiscardButton(self, -1, "Discard", c, self.DisableButtons, i)
            self.discardButtons.append(discardButton)
            self.sizer.Add(discardButton)

            i = i+1

        self.SetSizer(self.sizer)
        wx.CallAfter(self.PostCreateFixup)
        self.SetupScrolling(scroll_x=False, scroll_y=True, rate_x=20, rate_y=20)


    def PostCreateFixup(self):
        """
        call the AdjustToSize method of all the text widgets
        """
        for c in self.GetChildren():
            if isinstance(c, CopyableStyleTextCtrl):
                c.AdjustToSize()

        # readjust the scrolling
        wx.CallAfter(self.SetupScrolling, scroll_x=False, scroll_y=True, rate_x=20, rate_y=20)


    def DisableButtons(self, i):
        """
        either the "apply" or "discard" button has been pressed, so disable
        both buttons (they are not undo-able
        """
        self.acceptButtons[i].Disable()
        self.discardButtons[i].Disable()
        self.callback()

    def onLayoutNeeded(self, event):
        print "in onLayoutNeeded"
        self.SetupScrolling(scroll_x=False, scroll_y=True, rate_x=20, rate_y=20)

class ConflictDialog(wx.Dialog):
    def __init__(self, conflicts):
        wx.Dialog.__init__(self, None, -1, _(u'Pending Changes'), size=(800, 600),
            style=wx.DEFAULT_DIALOG_STYLE)
        # Make the dialog constant width so that the expano text works correctly; it cannot
        # trivially handle its width being changed on the fly.
        self.SetMinSize(wx.Size(900, 250))
        self.SetMaxSize(wx.Size(900, 600))

        # sizer for laying out all the controls vertically -- will be put inside a horizontal sizer later
        vsizer = wx.BoxSizer(wx.VERTICAL)

        # space between title bar and "pending changes" text
        vsizer.Add((0, 20), 0, flag=wx.EXPAND)

        # header "pending changes" text
        warn = _(u"Applying and discarding changes cannot be undone.")
        conflictCount = len(conflicts)
        if conflictCount == 1:
            headingText = _(u"There is 1 pending change. %(warning)s") % { 'warning': warn }
        else:
            headingText = _(u"There are %(count)d pending changes. %(warning)s") \
            % { 'count': conflictCount, 'warning': warn }

        headingText = wx.StaticText(self, -1, headingText)
        vsizer.Add(headingText, 0, flag=wx.EXPAND)

        # more space
        vsizer.Add((0, 20), 0, flag=wx.EXPAND)

        # the large, scrolling conflicts area in the middle of the dialog
        self.scroll = ConflictVScrolledArea(self, conflicts, self.changeToDone)
        vsizer.Add(self.scroll, 1, flag=wx.EXPAND)

        # space
        vsizer.Add((0, 20), 0, flag=wx.EXPAND)

        # footer text
        footerText = wx.StaticText(self, -1, _(u"All pending changed must be resolved before you can send Updates. Edits you make on attributes with\npending changes will not be synced to the server"))
        vsizer.Add(footerText)

        # "Decide later"/"Done" button, which is fflush right, so use a horizontal box sizer
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add((20, 0), 1, flag=wx.EXPAND)
        self.doneButton = wx.Button(self, wx.ID_OK, _(u"Decide later"))
        buttonSizer.Add(self.doneButton)
        vsizer.Add(buttonSizer, 0, flag=wx.EXPAND)

        # space at the bottom of the window
        vsizer.Add((0, 20), 0, flag=wx.EXPAND)

        # add some left and right space by putting the vsizer inside a horizontal sizer with spacing
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add((12, 0), 0, flag=wx.EXPAND)
        hsizer.Add(vsizer, 1, flag=wx.EXPAND)
        hsizer.Add((12, 0), 0, flag=wx.EXPAND)

        self.SetSizer(hsizer)

    def changeToDone(self):
        self.doneButton.SetLabel(_(u"Done"))
        self.doneButton.SetToolTipString(_(u"""Any unresolved items will remain undecided. You can revisit this dialog to resolve them later."""))


# do the test below by opening a PyShell in Chandler and executing:
# execfile("application/dialogs/ConflictDialog.py", { "__name__" :"__main__" })

if __name__ == "__main__":
    # pseudoConflicts
    class pChange(object):
        def __init__(self):
            self.exclusions = None
    
    class pConflict(object):
        def __init__(self, field, value, peer):
            self.state = 'conflicted'
            self.peer = peer
            self.field = field
            self.value = value
            self.change = pChange()

        def apply(self):
            self.state = 'applied'
            self.display()

        def discard(self):
            self.state = 'discarded'
            self.display()

        def display(self):
            print """ [%s] %s changed %s to:
%s""" % (self.state, self.peer, self.field, self.value)

    # a nice, long list of conflicts to see how the vertical scrolling is working
    conflicts = (
        pConflict("title", "This is the way the world ends", 'rae@tnir.org'),
        pConflict("body", """This is a very long body to see how the conflict dialog can deal with long bits of text.
Ideally, it would wrap very long lines, so I will make this line very long so as to test any wrod-wrapping problems and annoyances. It isn't quite long enough yet, so I will continue to type to the very, very end of the line.
Short last line.""", 'rae@osafoundation.org'),
        pConflict("location", "Toledo, Ohio", None),
        pConflict("Start time", "2007-06-07 0253", None),
        pConflict("End time", "2007-06-07 0500", None),
        pConflict("Occurs", "weekly", None),
        pConflict("Note", "Agimas tibi gratius", None),
        pConflict("misc", "Thursday June 7 2007", None),
        pConflict("photo1", "231.jpg", "foo1@tnir.org"),
        pConflict("photo2", "232.jpg", "foo2@tnir.org"),
        pConflict("photo3", "233.jpg", "foo3@tnir.org"),
        pConflict("photo4", "234.jpg", "foo4@tnir.org"),
        pConflict("photo5", "235.jpg", "foo5@tnir.org"),
        pConflict("photo6", "236.jpg", "foo6@tnir.org"),
        pConflict("photo7", "237.jpg", "foo7@tnir.org"),
        pConflict("photo8", "238.jpg", "foo8@tnir.org"),
        pConflict("body", """This is a very long body to see how the conflict dialog can deal with long bits of text.
Ideally, it would wrap very long lines, so I will make this line very long so as to test any wrod-wrapping problems and annoyances. It isn't quite long enough yet, so I will continue to type to the very, very end of the line.
Short last line.
This is a very long body to see how the conflict dialog can deal with long bits of text. Ideally, it would wrap very long lines, so I will make this line very long so as to test any wrod-wrapping problems and annoyances. It isn't quite long enough yet, so I will continue to type to the very, very end of the line. Blah blah blah. This is a very long body to see how the conflict dialog can deal with long bits of text. Ideally, it would wrap very long lines, so I will make this line very long so as to test any wrod-wrapping problems and annoyances. It isn't quite long enough yet, so I will continue to type to the very, very end of the line. Blah blah blah. This is a very long body to see how the conflict dialog can deal with long bits of text. Ideally, it would wrap very long lines, so I will make this line very long so as to test any wrod-wrapping problems and annoyances. It isn't quite long enough yet, so I will continue to type to the very, very end of the line. Blah blah blah.
This is a very long body to see how the conflict dialog can deal with long bits of text. Ideally, it would wrap very long lines, so I will make this line very long so as to test any wrod-wrapping problems and annoyances. It isn't quite long enough yet, so I will continue to type to the very, very end of the line. Blah blah blah.
This is a very long body to see how the conflict dialog can deal with long bits of text. Ideally, it would wrap very long lines, so I will make this line very long so as to test any wrod-wrapping problems and annoyances. It isn't quite long enough yet, so I will continue to type to the very, very end of the line. Blah blah blah.

hah!

This is a very long body to see how the conflict dialog can deal with long bits of text. Ideally, it would wrap very long lines, so I will make this line very long so as to test any wrod-wrapping problems and annoyances. It isn't quite long enough yet, so I will continue to type to the very, very end of the line. Blah blah blah. """, 'rae@osafoundation.org'),
        pConflict("photo9", "239.jpg", "foo8@tnir.org"),
    )
    dialog = ConflictDialog(conflicts)
    dialog.CenterOnScreen()
##     def show_tool():
##         import wx.lib.inspection
##         wx.lib.inspection.InspectionTool().Show()
##     wx.CallAfter(show_tool)
    dialog.ShowModal()
    dialog.Destroy()
