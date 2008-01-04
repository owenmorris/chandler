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


"""
Attribute Editors
"""
__parcel__ = "osaf.framework.attributeEditors"

import wx
from osaf.framework.blocks import DragAndDrop
from datetime import datetime, timedelta
from osaf.framework.blocks.Block import BaseWidget
from osaf import messages
from BaseAttributeEditor import NotifyBlockToSaveValue
from osaf.framework.blocks import Block

class DragAndDropTextCtrl(BaseWidget,
                          DragAndDrop.DraggableWidget,
                          DragAndDrop.DropReceiveWidget,
                          DragAndDrop.TextClipboardHandler,
                          wx.TextCtrl):
    def __init__(self, *arguments, **keywords):
        super (DragAndDropTextCtrl, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
                      
    def OnMouseEvents(self, event):
        # trigger a Drag and Drop if we're a single line and all selected
        if self.IsSingleLine() and event.LeftDown():
            selStart, selEnd = self.GetSelection()
            if selStart==0 and selEnd>1 and selEnd==self.GetLastPosition():
                # not the initial left-down event, but is it a dragging while left-down?
                if event.Dragging() and event.LeftIsDown(): 
                    # have we had the focus for a little while?
                    if hasattr(self, 'focusedSince'):
                        if datetime.now() - self.focusedSince > timedelta(seconds=.2):
                            # Try Dragging the text
                            result = self.DoDragAndDrop()
                            if result != wx.DragMove and result != wx.DragCopy:
                                # Drag not allowed - set an insertion point instead
                                hit, row, column = self.HitTest(event.GetPosition())
                                if hit != wx.TE_HT_UNKNOWN:
                                    self.SetInsertionPoint(self.XYToPosition(row, column))
                                else:
                                    self.SetInsertionPointEnd() # workaround for bug 4116
                            return # don't skip, eat the click.
        event.Skip()

    def OnSetFocus(self, event):
        self.focusedSince = datetime.now()
        event.Skip()        

    def OnKillFocus(self, event):
        # when grid creates the control, it never gets the EVT_SET_FOCUS
        if hasattr(self, 'focusedSince'):
            del self.focusedSince
        event.Skip()        
    
    def OnRightClick(self, event):
        """
        Build and display our context menu
        """
        self.SetFocus()
        
        # Use menu block so that script recording/playback works
        contextMenuBlock = Block.Block.findBlockByName ('DragAndDropTextCtrlContextMenu')
        menu = wx.MenuItem.GetSubMenu (contextMenuBlock.widget)
        
        if wx.Platform == '__WXGTK__':
            # (see note below re: GTK)
            menu.Bind(wx.EVT_MENU, self.OnMenuChoice)
            menu.Bind(wx.EVT_UPDATE_UI, self.OnMenuUpdateUI)

        # We don't display the context menus while playing back scripts because 
        # context menus block the event loop while they are up
        if not wx.GetApp().PlaybackEventPending():
            self.PopupMenu(menu)

        # event.Skip() intentionally not called: we don't want
        # the menu built into wx to appear!

    # GTK's popup handling seems totally broken (our menu does pop up,
    # but the enabling and actual execution don't happen). So, do our own.
    if wx.Platform == '__WXGTK__':
        popupHandlers = {
            # (FYI: these are method names, and so should not be localized.)
            wx.ID_UNDO: 'Undo',
            wx.ID_REDO: 'Redo',
            wx.ID_CUT: 'Cut',
            wx.ID_COPY: 'Copy',
            wx.ID_PASTE: 'Paste',
            wx.ID_CLEAR: 'Clear',
            wx.ID_SELECTALL: 'SelectAll'
            }
        def OnMenuChoice(self, event):
            handlerName = DragAndDropTextCtrl.popupHandlers.get(event.GetId(), None)
            if handlerName is None:
                event.Skip()
                return
            h = getattr(self, handlerName)
            return h()
    
        def OnMenuUpdateUI(self, event):
            evtName = DragAndDropTextCtrl.popupHandlers.get(event.GetId(), None)
            if evtName is None:
                event.Skip()
                return
            handlerName = "Can%s" % evtName
            h = getattr(self, handlerName)
            enabled = h()
            event.Enable(enabled)
        
        # wx.TextCtrl.Clear is documented to remove all the text in the
        # control; only the GTK version works this way (the others do what
        # we want, which is to remove the selection). So, here, we hack
        # Clear to just remove the selection on GTK only.
        def Clear(self):
            self.Remove(*self.GetSelection())
            NotifyBlockToSaveValue(self)

        def CanClear(self):    
            (selStart, selEnd) = self.GetSelection()
            return self.CanCut() and selStart != selEnd
    else:
        # CanClear for all other platforms.
        def CanClear(self):
            return self.CanCut()

    def Cut(self):
        result = self.GetStringSelection()
        super(DragAndDropTextCtrl, self).Cut()
        return result

    def Copy(self):
        result = self.GetStringSelection()
        super(DragAndDropTextCtrl, self).Copy()
        return result
    
    def onCopyEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanCopy()

    def onCopyEvent(self, event):
        self.Copy()

    def onCutEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanCut()

    def onCutEvent(self, event):
        self.Cut()
        NotifyBlockToSaveValue(self)

    def onPasteEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanPaste()

    def onPasteEvent(self, event):
        self.Paste()
        NotifyBlockToSaveValue(self)

    def onClearEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanClear()
    
    def onClearEvent(self, event):
        self.Clear()
        NotifyBlockToSaveValue(self)
    
    def onRedoEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanRedo()

    def onRedoEvent(self, event):
        self.Redo()
        NotifyBlockToSaveValue(self)

    def onUndoEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanUndo()
    
    def onUndoEvent(self, event):
        self.Undo()
        NotifyBlockToSaveValue(self)

    def onRemoveEventUpdateUI(self, event):
        (startSelect, endSelect) = self.GetSelection()
        event.arguments ['Enable'] = startSelect < self.GetLastPosition()

    def onDeleteEventUpdateUI(self, event):
        """
        Bug 5717, OnDelete shouldn't be active in a text ctrl on Mac.
        """
        event.arguments['Enable'] = wx.Platform == '__WXMAC__'

    def onRemoveEvent(self, event):
        # I tried the following code, but it didn't work. Perhaps it's
        # related to bug (#3978). So I rolled my own. -- DJA
        #keyEvent = wx.KeyEvent()
        #keyEvent.m_keyCode = wx.WXK_DELETE
        #self.EmulateKeyPress (keyEvent)
        (startSelect, endSelect) = self.GetSelection()
        if startSelect < self.GetLastPosition():
            if startSelect == endSelect:
                endSelect += 1
            self.Remove (startSelect, endSelect)

    onDeleteEvent = onRemoveEvent

    def onSelectAllEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.GetLastPosition() > 0

    def onSelectAllEvent(self, event):
        self.SetSelection(-1, -1)

    def ActivateInPlace(self):
        self.SelectAll()
