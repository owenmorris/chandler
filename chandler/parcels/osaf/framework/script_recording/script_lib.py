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
from osaf.framework.blocks.Block import Block

lastFocus = None
lastSentToWidget = None
includeTests = False

def ProcessEvent (theClass, properties , attributes):
    def NameToWidget (name):
        """
        Given a name, returns the corresponding widget.
        """
        if type (name) is str:
            if name == "MainFrame":
                sentTo = application.mainFrame
            elif name == "__FocusWindow__":
                sentTo = wx.Window_FindFocus()
            else:
                sentTo = Block.findBlockByName (name)
                if sentTo is not None:
                    sentTo = sentTo.widget
                    if isinstance (sentTo, wx.grid.Grid):
                        sentTo = sentTo.GetGridWindow()
        else:
            sentTo = wx.Window.FindWindowById (name)
        return sentTo

    global includeTests, lastFocus, lastSentToWidget

    application = wx.GetApp()
    event = theClass()
    
    for (attribute, value) in attributes.iteritems():
        setattr (event, attribute, value)
    
    sentToWidget = NameToWidget (properties ["sentTo"])
    
    assert isinstance (sentToWidget, wx.Window) or isinstance (sentToWidget, wx.Menu)
    event.SetEventObject (sentToWidget)
    eventType = properties["eventType"]
    event.SetEventType (eventType.evtType[0])

    # Use the associated window if present to set the Id of the event
    associatedBlock = properties.get ("associatedBlock", None)
    if associatedBlock is not None:
        event.SetId (Block.findBlockByName (associatedBlock).widget.GetId())

    # Special case clicks on checkboxes to toggle the widget's value
    if eventType is wx.EVT_CHECKBOX:
        sentToWidget.SetValue(not sentToWidget.GetValue())

    # Check to see if the correct window has focus
    if includeTests:
        focusWindow = wx.Window_FindFocus()
        newFocusWindow = properties.get ("newFocusWindow", None)
        
        # Check to makee sure the focus window changes as expected
        if lastFocus != focusWindow:
            assert newFocusWindow is not None, "Focus window unexpectedly changed"
            
            # And that we get the expected focus window
            if type (newFocusWindow) is str:
                assert focusWindow is NameToWidget (newFocusWindow), "An unexpected window has the focus"
            else:
                (theClass, id) = newFocusWindow
                assert isinstance (focusWindow, theClass)
                if id > 0:
                    assert focusWindow.GetId() == id, "Focus window has unexpected id"
                else:
                    assert focusWindow.GetId() < 0, "Focus window has unexpected id"

            lastFocus = focusWindow
        else:
            assert newFocusWindow is None, "Focus window should have changed"
            
        # Check to make sure last event caused expected change
        if lastSentToWidget is not None:
            method = getattr (lastSentToWidget, "GetValue", None)
            lastWidgetValue = properties.get ("lastWidgetValue", None)
            if method is not None:
                value = method()
                assert value == lastWidgetValue, "widget's value doesn't match the value when the script was recorded"
            else:
                assert lastWidgetValue is None, "last widget differes from its value when the script was recorded"

    if not sentToWidget.ProcessEvent (event):
        # Special case key downs
        if eventType is wx.EVT_KEY_DOWN:
            # Try EmulateKeyPress
            EmulateKeyPress = getattr(sentToWidget, 'EmulateKeyPress', None)
            if EmulateKeyPress is not None:
                EmulateKeyPress (event)
            else:
                # If that doesn't work try WriteText
                writeMethod = getattr(sentToWidget, 'WriteText', None)
                if writeMethod is not None:
                    writeMethod (str(chr(event.GetKeyCode())))
                else:
                    assert False, "wx.EVT_KEY_DOWN failed"
        elif eventType is wx.EVT_CHECKBOX:
            widget.SetValue(not widget.GetValue())

    lastSentToWidget = sentToWidget

    application.propagateAsynchronousNotifications()
    application.Yield()
