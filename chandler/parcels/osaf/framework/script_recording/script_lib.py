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

import wx
from osaf.framework.blocks.Block import Block
from osaf.framework.attributeEditors.AETypeOverTextCtrl import AETypeOverTextCtrl
from application import schema

# On Windows a key down and char event will also generate an enter and key up so we need to avoid
# processing those otherwise we'll get duplicate events
ignoreMSWEvents = set ((wx.EVT_TEXT_ENTER,
                        wx.EVT_KEY_UP))

def ProcessEvent (line, theClass, properties, attributes):
    
    def nameToWidget (name):
        
        id = {"__wxID_OK__": wx.ID_OK,
              "__wxID_CANCEL__": wx.ID_CANCEL,
              "__wxID_YES__": wx.ID_YES,
              "__wxID_NO__": wx.ID_NO}.get (name, None)
        if id is not None:
            widget = wx.FindWindowById (id)
            assert isinstance (widget, wx.Button), \
                   "event %d -- Expected widget with id %s to be a button. Instead it is %s" \
                   % (eventNumber, name, sentTo, str(widget))
            return widget
        elif name == "__none__":
            return None
        elif name.startswith ("__block__"):
            block = Block.findBlockByName (name [len ("__block__"):])
            return block.widget
        else:
            return wx.FindWindowByName (name)

    application = wx.GetApp()
    eventNumber = application.eventsIndex - 1
    
    if wx.Platform == "__WXMAC__":
        window = wx.Window_FindFocus()
        if isinstance (window, wx.Window):
            windowName = window.GetName()
        else:
            windowName = ""

    application.ProcessIdle()
    application.Yield (True)
    application.mainFrame.Update()

    if wx.Platform == "__WXMAC__":
        window = wx.Window_FindFocus()
        if isinstance (window, wx.Window):
            windowName = window.GetName()
        else:
            windowName = ""

    sentTo = properties ["sentTo"]
    sentToWidget = nameToWidget (sentTo)

    assert (isinstance (sentToWidget, wx.Window) or
            isinstance (sentToWidget, wx.Menu) or
            isinstance (sentToWidget, wx.MenuItem) or
            isinstance (sentToWidget, wx.ToolBarTool), \
            "event %d -- Unexpected type of widget: sentTo is %s; sendToWidget is %s" % (eventNumber, sentTo, str(sentToWidget)))
    
    if isinstance (sentToWidget, wx.ToolBarTool):
        assert sentToWidget.IsControl()
        sentToWidget = sentToWidget.GetControl()

    elif isinstance (sentToWidget, wx.MenuItem):
        assert sentToWidget.IsSubMenu()
        sentToWidget = sentToWidget.GetSubMenu()

    eventType = properties["eventType"]

    if theClass is not wx.grid.GridEvent:
        event = theClass()
        for (attribute, value) in attributes.iteritems():
            setattr (event, attribute, value)
    else:
        # Unfortunately, wx.grid.GridEvent doesn't have setters and getters. Eventually
        # I will add this to wxWidgets and remove this special case code -- DJA
        position = attributes ["Position"]
        event = wx.grid.GridEvent (-1,
                                   eventType.evtType[0],
                                   Block.findBlockByName (sentTo).widget,
                                   row = attributes ["Row"],
                                   col = attributes ["Col"],
                                   x = position [0], y = position [1])

    event.SetEventObject (sentToWidget)
    event.SetEventType (eventType.evtType[0])

    # Use the associated block if present to set the Id of the event
    associatedBlock = properties.get ("associatedBlock", None)
    if associatedBlock is not None:
        id = Block.findBlockByName (associatedBlock).widget.GetId()
    else:
        GetIdMethod = getattr (sentToWidget, "GetId", None)
        assert GetIdMethod is not None, "event %d -- Unexpected widget, doesn't have GetId: sentTo is %s; sendToWidget is %s" % (eventNumber, sentTo, str(sentToWidget))
        id = GetIdMethod()
    event.SetId (id)

    # Special case clicks on checkboxes to toggle the widget's value
    # And special case wx.Choice to set the selection. Both of these
    # are necessary before the event is processed so the GetValue
    # validation passes
    if eventType is wx.EVT_CHECKBOX:
        sentToWidget.SetValue (not sentToWidget.GetValue())

    # andSpecial case wx,Choice to set the selection
    elif eventType is wx.EVT_CHOICE or eventType is wx.EVT_LISTBOX:
        selectedItem = properties ["selectedItem"]
        event.SetInt (selectedItem)
        sentToWidget.SetSelection (selectedItem)
    
    # A bug in wxWidgets on Windows stores the wrong value for m_rawCode in wx.EVT_CHAR
    # Since the correct valus is stored in wx.EVT_KEY_DOWN and wx.EVT_KEY_DOWN
    # precedes wx.EVT_KEY_DOWN, we'll cache it for the next wx.EVT_KEY_DOWN
    # Raw key codes are only used on Windows. There they correspond to virtual
    # keycodes. For this reason we record scripts on Windows to play back on the
    # other platforms.
    if eventType is wx.EVT_KEY_DOWN:
        ProcessEvent.last_rawCode = event.m_rawCode

    # Track contents of clipboard in events with the clipboard property
    contents = properties.get ("clipboard", None)
    if contents is not None:
        # Work around for bug #
        success = wx.TheClipboard.Open()
        assert success, "event %d -- The clipboard can't be opened" % eventNumber
        success = wx.TheClipboard.SetData (wx.TextDataObject (contents))
        assert success, "event %d -- Clipboard SetData failed" % eventNumber
        
        data = wx.TextDataObject()
        success = wx.TheClipboard.GetData (data)
        assert success, "event %d -- Clipboard GetData failed. This is often caused by a bug in Parallels, try turning off Clipboard Synchronization" % eventNumber
        value = data.GetText()
        
        # Work around for bug #11699
        if wx.Platform != "__WXMAC__":
            assert value == contents, 'event %d -- Clipboard broken: set: "%s"; got: "%s"' % (eventNumber, contents, value)
        wx.TheClipboard.Close()

    # Verify script if necessary
    if schema.ns('osaf.framework.script_recording', application.UIRepositoryView).RecordingController.verifyScripts:
        lastSentToWidget = ProcessEvent.lastSentToWidget

        # Make sure the menu or button is enabled
        if eventType is wx.EVT_MENU:
            updateUIEvent = wx.UpdateUIEvent (event.GetId())
            updateUIEvent.SetEventObject (sentToWidget)
            sentToWidget.ProcessEvent (updateUIEvent)
            assert updateUIEvent.GetEnabled() is True,\
                   "event %d -- You're sending a command to a disable menu" % eventNumber
            
        # Check to makee sure we're focused to the right window
        recordedFocusWindow = properties.get ("recordedFocusWindow", None)
        if recordedFocusWindow is not None:
            recordedFocusWindowClass = properties["recordedFocusWindowClass"]
            focusWindow = wx.Window_FindFocus()
            
            # On Macintosh there is a setting under SystemPreferences>Keyboar&Mouse>KeyboardShortcuts
            # neare the bottom of the page titled "Full Keyboard Access" that defaults to
            # not letting you set the focus to certain controls, e.g. CheckBoxes. So we
            # don't verify the focus in those cases.
            #
            # On Linux events sent to toolbar cause the focus window to become None
            #
            # Also, when lastSentToWidget is None the focus window may not be accurate.

            if not ( (wx.Platform == "__WXMAC__" and issubclass (recordedFocusWindowClass, wx.CheckBox)) or
                     (wx.Platform == "__WXGTK__" and isinstance (sentToWidget, wx.ToolBar)) or
                     lastSentToWidget is None):
                if focusWindow is None:
                    focusWindowName = "None"
                else:
                    focusWindowName = focusWindow.GetName()
                assert focusWindow is nameToWidget (recordedFocusWindow),\
                       "event %d -- Focus is: %s; expecting: %s" % (eventNumber, focusWindowName, recordedFocusWindow)

        # Check to make sure last event caused expected change

        if lastSentToWidget is not None and not isinstance (lastSentToWidget, wx._core._wxPyDeadObject):
            GetValueMethod = getattr (lastSentToWidget, "GetValue", None)
        else:
            GetValueMethod = None

        if GetValueMethod is not None:
            lastWidgetValue = properties.get ("lastWidgetValue", None)
            if lastWidgetValue is not None:
                value = GetValueMethod()

                assert value == lastWidgetValue,\
                       'event %d -- widget %s value, "%s" doesn\'t match the value when the script was recorded: "%s"; application.IsActive() is %s'\
                        % (eventNumber, ProcessEvent.lastSentTo, value, lastWidgetValue, str(application.IsActive()))

        # Keep track of the last widget. Use Id because widget can be deleted

        # Return characters with wx.EVT_CHAR events cause problems with verification so we won't verify
        # this case. I think that the reason verification is a problem her is because our emulation of
        # these events is slighty from different from the way they are handled by the OS when we record the script.
        if attributes.get ("UnicodeKey", 0) == 13 and (eventType is wx.EVT_CHAR or eventType is wx.EVT_KEY_DOWN):
            ProcessEvent.lastSentToWidget = None
        else:
            ProcessEvent.lastSentToWidget = sentToWidget
            ProcessEvent.lastSentTo = sentTo

    processed = False
    if eventType is wx.EVT_SET_FOCUS:
        if wx.Window_FindFocus() is not sentToWidget:
            # Setting your focus to the window that has the focus causes the
            #  window to lose focus on Windows
            sentToWidget.SetFocus()
            # On Linux we occasionally need to Yield for the Focus to be properly set
            if wx.Window_FindFocus() is not sentToWidget:
                application.Yield (True)
                focusWindow = wx.Window.FindFocus()
                if focusWindow is not sentToWidget:
                    if isinstance (focusWindow, wx.Window):
                        focusWindowName = focusWindow.GetName()
                    else:
                        focusWindowName = ""
                    assert False, \
                           "event %d -- SetFocus failed; Focus is: %s; expecting: %s; application.IsActive() is %s" \
                           % (eventNumber, focusWindowName, sentTo, str(application.IsActive()))

    else:
        if wx.Platform != "__WXMSW__" or eventType not in ignoreMSWEvents:
            # On windows we ignore certain events that are generated as a side effect of other events
            if not sentToWidget.ProcessEvent (event):
                processed = True
                if (eventType is wx.EVT_KEY_DOWN and
                    event.m_keyCode in set ((wx.WXK_ESCAPE, wx.WXK_TAB, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER))):
                    # Special case key downs that end edits in the grid
                    gridWindow = sentToWidget.GetParent()
                    if (gridWindow is not None and
                        isinstance (gridWindow.GetParent(), wx.grid.Grid)):
                        event.SetEventObject (gridWindow)
                        gridWindow.ProcessEvent (event)
        
                elif eventType is wx.EVT_CHAR and not event.m_controlDown:
                    # Make sure the selection is valid
                    if __debug__:
                        GetSelectionMethod = getattr (sentToWidget, "GetSelection", None)
                        if GetSelectionMethod is not None:
                            (start, end) = GetSelectionMethod()
                            assert start >= 0 and end >= 0 and start <= end
        
                    # Try EmulateKeyPress
                    EmulateKeyPress = getattr(sentToWidget, 'EmulateKeyPress', None)
                    if EmulateKeyPress is not None:
                        # On Linx if we call EmulateKeyPress with a return character in a
                        # single line textCtrl it will insert a return character.
                        UnicodeKey = event.UnicodeKey
        
                        if (UnicodeKey != 13 or sentToWidget.IsMultiLine()):
                            # A bug in wxWidgets on Windows stores the wrong value for m_rawCode in wx.EVT_CHAR
                            # Since the correct valus is stored in wx.EVT_KEY_DOWN and wx.EVT_KEY_DOWN
                            # precedes wx.EVT_KEY_DOWN, we'll cache it for the next wx.EVT_KEY_DOWN
                            event.m_rawCode = ProcessEvent.last_rawCode
                            # Also on Linux we need to translate returns to line feeds.
                            if wx.Platform == "__WXGTK__" and UnicodeKey == 13:
                                event.UnicodeKey = 10
            
                            EmulateKeyPress (event)

    selectionRange = properties.get ("selectionRange", None)
    if selectionRange is not None:
        (start, end) = selectionRange
        # On windows GetValue uses "\n" for end of lines, but the widget stores
        # "\n\r" for end of lines and SetSelection uses offsets that include
        # the extra "\r" characters
        if wx.Platform == "__WXMSW__":
            value = sentToWidget.GetValue()
            start = start + value.count ('\n', 0, start)
            end = end + value.count ('\n', 0, end)

        sentToWidget.SetSelection (start, end)
        
    window = wx.Window_FindFocus()
    if isinstance (window, wx.Window):
        windowName = window.GetName()
    else:
        windowName = ""


    # On windows when we propagate notifications while editing a text control
    # it will end up calling wxSynchronizeWidget in wxTable, which will end the
    # editing of the table
    if not isinstance (sentToWidget, wx.TextCtrl):
        application.propagateAsynchronousNotifications()

    # Since scrips don't actually move the cursor and cause wxMouseCaptureLostEvents
    # to be generated we'll periodically release the capture from all the windows.
    # Alternatively, it might be better to record and playback wxMouseCaptureLostEvents.
    while True:
        capturedWindow = wx.Window.GetCapture()
        if capturedWindow is not None:
            capturedWindow.ReleaseMouse()
        else:
            break

def InitializeScript ():
    ProcessEvent.lastSentToWidget = None
