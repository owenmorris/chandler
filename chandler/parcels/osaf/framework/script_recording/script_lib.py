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

def ProcessEvent (theClass, properties , attributes):
    def NameToWidget (name):
        """
        Given a name, returns the corresponding widget.
        """
        if type (name) is str:
            if name == "MainFrame":
                sentTo = application.mainFrame
            else:
                sentTo = Block.findBlockByName (name)
                if sentTo is not None:
                    sentTo = sentTo.widget
                    if isinstance (sentTo, wx.grid.Grid):
                        sentTo = sentTo.GetGridWindow()
        else:
            sentTo = wx.Window.FindWindowById (name)
        return sentTo

    application = wx.GetApp()
    event = theClass()
    
    for (attribute, value) in attributes.iteritems():
        setattr (event, attribute, value)
    
    sentToWidget = NameToWidget (properties ["sentTo"])
    
    assert isinstance (sentToWidget, wx.Window)
    event.SetEventObject (sentToWidget)
    eventType = properties["eventType"]
    event.SetEventType (eventType.evtType[0])

    # Use the associated window if present to set the Id of the event
    associatedBlock = properties.get ("associatedBlock", None)
    if associatedBlock is not None:
        event.SetId (Block.findBlockByName (associatedBlock).widget.GetId())

    if (eventType is wx.EVT_CHECKBOX):
        event.SetInt (1)

    if not sentToWidget.ProcessEvent (event):
        # Special case key downs
        if (eventType is wx.EVT_KEY_DOWN):
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

    application.propagateAsynchronousNotifications()
    application.Yield()
