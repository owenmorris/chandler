#   Copyright (c) 2003-2008 Open Source Applications Foundation
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
import re
from osaf.framework.blocks import DragAndDrop
from datetime import datetime, timedelta
from osaf.framework.blocks.Block import BaseWidget
from osaf import messages
from BaseAttributeEditor import NotifyBlockToSaveValue
from osaf.framework.blocks import Block

class URLTrackingTextCtrl(wx.TextCtrl):
    """
    Subclass of C{wx.TextCtrl} that shows the "pointing hand" cursor when
    you mouse over text that looks like a URL, and posts a C{wx.TextUrlEvent}
    when you click on such text. Mostly, a python-level hack to work around
    the fact that the C{wx.TE_AUTO_URL} style isn't implemented on the Mac.
    
    @cvar URL_RE: Compiled regular expression that is used to match URLs
                  within a line of text.

    @cvar HAND_CURSOR: Shared cursor displayed when mousing over URLs
    @type HAND_CURSOR: C{wx.Cursor}
    """
    
    if wx.Platform in ('__WXMAC__', '__WXGTK__'):
        # @@@ [grant] This subclass is implemented for __WXGTK__,
        # because I've been seeing hard crashes in the auto-url-ified notes
        # field on Linux (Ubuntu 7.10, Gutsy).
        _currentCursor = None
        _showHand = False
        HAND_CURSOR = None
    
        def __init__(self, parent, id=-1, value=wx.EmptyString, 
                     pos=wx.DefaultPosition, size=wx.DefaultSize, 
                     style=0, validator=wx.DefaultValidator, 
                     name=wx.TextCtrlNameStr):
            # Pull out wx.TE_AUTO_URL, and disable it in the call to
            # super.
            autoUrl = bool(style & wx.TE_AUTO_URL)
            style &= ~wx.TE_AUTO_URL
            super(URLTrackingTextCtrl, self).__init__(parent, id, value,
                          pos, size, style, validator, name)
            
            # Set up the shared HAND_CURSOR class variable
            if type(self).HAND_CURSOR is None:
                type(self).HAND_CURSOR = wx.StockCursor(wx.CURSOR_HAND)

            # If we're auto-url-ifying, set up mouse tracking
            # and cursor tracking callbacks.
            if autoUrl:
                self.Bind(wx.EVT_MOUSE_EVENTS, self.mousey)
                self.Bind(wx.EVT_SET_CURSOR, self.cursory)
                # The best click behaviour is only to process on mouse
                # up, since this allows drag-selection of URL text. However,
                # on Mac, wx.TextCtrl doesn't appear to send EVT_LEFT_UP, so
                # we'll have to handle that case differently.
                if wx.Platform != '__WXMAC__':
                    self.Bind(wx.EVT_LEFT_UP, self.uppity)

        URL_RE = re.compile(r'''(\w+:                # alphanumerics up to a colon
                                [^%(badchars)s]{3,}) # at least three not-badchars, greedily
                                (?:[%(badchars)s]|$) # terminated by a badchar or EOL
                             ''' % {'badchars': r'''\]\[\)\('"><\s'''},
                             re.VERBOSE) # python-mode hates triple-quotes "
        
        def _get_url_range_at_cursor(self, event):
            """
            Returns (start, end), the range of the URL at the cursor, or
            (-1, -1) if no URL is present there.
            """
            status, col, line = self.HitTest(event.Position)
            return self._get_url_range(col, line)
            
        def _get_url_range(self, col, line):
            """
            Returns (start, end), the range of the URL at the given line and
            column of the text, or (-1, -1) if no URL is present there.

            @@@ This will almost certainly blow up for right-to-left scripts.
            
            """
            if col == line == 0:
                # Bug 12256, when the cursor is past the last line of text,
                # col, line == (0, 0), ignore this case
                return -1, -1

            current_and_later_lines = []
            for test_line in xrange(line, self.GetNumberOfLines()):
                text = self.GetLineText(test_line)
                stripped = text.rstrip()
                current_and_later_lines.append(stripped)
                if stripped != text:
                    break

            if not current_and_later_lines:
                return -1, -1 # no lines in the widget, no URLs to select

            earlier_lines = []
            for test_line in reversed(xrange(line)):
                text = self.GetLineText(test_line)
                stripped = text.rstrip()
                if stripped != text:
                    break
                earlier_lines.insert(0, stripped)
 
            this_line_text = current_and_later_lines[0]

            if col >= len(this_line_text) or this_line_text[col].isspace():
                # Past the end of the line, or on whitespace
                return -1, -1

            pre_space, space, word_left = this_line_text[:col].rpartition(" ")
            offset = len(pre_space) + len(space) # characters taken away, positive
            if not space:
                word_left = "".join(earlier_lines) + word_left
                lineStart = self.getLineStart(line - len(earlier_lines))
                # extra characters, negative
                offset = lineStart - self.getLineStart(line)
            else:
                lineStart = self.getLineStart(line) + offset

            current_and_later_text = "".join(current_and_later_lines)
            word_right, space, after_space = current_and_later_text[col:].partition(" ")

            # Heuristically ignore chars like (< >). which may appear at url ends,
            # look for "scheme:.*" url inside
            match = self.URL_RE.search(word_left + word_right)
            if match:
                start, end = match.span(1)
                if start <= col - offset <= end:
                    return lineStart + start, lineStart + end
            return -1, -1

        def getLineStart(self, line):
            if wx.Platform == '__WXMAC__':
                # @@@ [Bug in XYToPosition on Mac? Seems to be off by 1]
                return sum(self.GetLineLength(l) for l in xrange(line))
            else:
                return self.XYToPosition(0, line)

        def mousey(self, event):
            """
            C{wx.EVT_MOUSE_EVENTS} handler
            """
            newCursor = None
            
            #newCursor = self._currentCursor
            
            if event.Entering() or event.Moving():
                urlStart, urlEnd = self._get_url_range_at_cursor(event)
                if urlStart != urlEnd:
                    newCursor = self.HAND_CURSOR
                    self._showHand = True
                else:
                    newCursor = self._currentCursor
                    self._showHand = False
            elif event.Leaving():
                self._showHand = False
                newCursor = self._currentCursor
            elif wx.Platform == '__WXMAC__' and event.LeftDown():
                # On the Mac only, try to open URLs on left-down. Other
                # platforms will send wx.EVT_LEFT_UP events, which is
                # a better place to do this (as noted above).
                urlStart, urlEnd = self._get_url_range_at_cursor(event)
                if urlStart != urlEnd:
                    # Fake a up-mouse event. Handlers for wx.EVT_TEXT_URL
                    # should check for mouse up to get best behaviour on all
                    # platforms (wx.TE_AUTO_URL-enabled TextCtrls actually
                    # send this event on mouse down and mouse moved events
                    # as well) ...
                    upMouse = wx.MouseEvent(wx.wxEVT_LEFT_UP)
                    self.post_url_event(upMouse, urlStart, urlEnd)
                    return
        
            if newCursor is not None:
                wx.SetCursor(newCursor)
        
            if self._showHand:
                wx.CallAfter(wx.SetCursor, self.HAND_CURSOR)
        
            event.Skip()
    
        def cursory(self, event):
            """Handler for C{wx.EVT_SET_CURSOR} events"""
            eventCursor = event.Cursor
            self._currentCursor = eventCursor
            
            # On the Mac, the TextCtrl seems to reset the cursor
            # to the regular old arrow at the end of event processing.
            # so, we use wx.CallAfter (and don't Skip) to get around
            # this.
            if self._showHand and eventCursor != self.HAND_CURSOR:
                wx.CallAfter(wx.SetCursor, self.HAND_CURSOR)
            else:
                event.Skip()

        def uppity(self, event):
            """Handler for C{wx.EVT_LEFT_UP} events"""
            
            # If there's an empty selection, it means the user has just
            # single-clicked, rather than drag-selected. So, go ahead and
            # open any URL if possible here.
            selection = self.GetSelection()
            if selection[0] == selection[1]:
                col, line = self.PositionToXY(selection[0])
                urlStart, urlEnd = self._get_url_range(col, line)
                
                if urlStart != urlEnd:
                    self.post_url_event(event, urlStart, urlEnd)
                    return # Don't Skip(): we're done.
            
            event.Skip()

        def post_url_event(self, event, urlStart, urlEnd):
            """Helper to post wx.TextUrlEvent to whoever might be a-listening"""
            urlEvent = wx.TextUrlEvent(self.GetId(), event, urlStart,
                                       urlEnd)
            urlEvent.SetClientData(self)
            self.GetEventHandler().ProcessEvent(urlEvent)


class DragAndDropTextCtrl(BaseWidget,
                          DragAndDrop.DraggableWidget,
                          DragAndDrop.DropReceiveWidget,
                          DragAndDrop.TextClipboardHandler,
                          URLTrackingTextCtrl):
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
