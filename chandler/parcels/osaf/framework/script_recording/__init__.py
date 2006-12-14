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


import os, sys, wx, types
from application import schema
from osaf.framework.blocks import Block, BlockEvent
from osaf.framework.blocks.MenusAndToolbars import MenuItem
from i18n import ChandlerMessageFactory as _

_wxEventClasses = set([wx.CommandEvent,
                       wx.MouseEvent,
                       wx.KeyEvent])

_wxEventClasseInfo = {}

_wxEventTypeMapping = {
    wx.EVT_MENU.evtType[0]: "wx.EVT_MENU",
    wx.EVT_KEY_DOWN.evtType[0]: "wx.EVT_KEY_DOWN",
    wx.EVT_LEFT_DOWN.evtType[0]: "wx.EVT_LEFT_DOWN",
    wx.EVT_RIGHT_DOWN.evtType[0]: "wx.EVT_RIGHT_DOWN",
    wx.EVT_LEFT_DCLICK.evtType[0]: "wx.EVT_LEFT_DCLICK",
    wx.EVT_RIGHT_DCLICK.evtType[0]: "wx.EVT_RIGHT_DCLICK",
    wx.EVT_SCROLLWIN_LINEUP.evtType[0]: "wx.EVT_SCROLLWIN_LINEUP",
    wx.EVT_SCROLLWIN_LINEDOWN.evtType[0]: "wx.EVT_SCROLLWIN_LINEDOWN",
    wx.EVT_SCROLLWIN_PAGEUP.evtType[0]: "wx.EVT_SCROLLWIN_PAGEUP",
    wx.EVT_SCROLLWIN_PAGEDOWN.evtType[0]: "wx.EVT_SCROLLWIN_PAGEDOWN",
    wx.EVT_SCROLLWIN_THUMBTRACK.evtType[0]: "wx.EVT_SCROLLWIN_THUMBTRACK",
    wx.EVT_SCROLLWIN_THUMBRELEASE.evtType[0]: "wx.EVT_SCROLLWIN_THUMBRELEASE",

    wx.EVT_ACTIVATE.evtType[0]: "wx.EVT_ACTIVATE",
    wx.EVT_SET_FOCUS.evtType[0]: "wx.EVT_SET_FOCUS",
    wx.EVT_BUTTON.evtType[0]: "wx.EVT_BUTTON",
    wx.EVT_CHECKBOX.evtType[0]: "wx.EVT_CHECKBOX"
}

class Controller (Block.Block):
    """
    Class to handle recording events
    """
    logging = schema.One(schema.Boolean, initialValue=False)

    def onToggleRecordingEvent (self, event):
        theApp = wx.GetApp()

        if self.FilterEvent not in theApp.filterEventCallables:
            self.script = "import wx" + os.linesep
            self.script += "from " + __name__ + ".script_lib import ProcessEvent" + os.linesep + os.linesep
            self.script += "def run():" + os.linesep
            theApp.filterEventCallables.add (self.FilterEvent)
            theApp.SetCallFilterEvent()
        else:
            theApp.filterEventCallables.remove (self.FilterEvent)
            theApp.SetCallFilterEvent (False)

            dialog = wx.FileDialog (None,
                                    message = "Save script as ...",
                                    defaultDir = os.getcwd(), 
                                    defaultFile = "",
                                    wildcard = "*.py",
                                    style=wx.SAVE)
            dialog.SetFilterIndex (2)
    
            if dialog.ShowModal () == wx.ID_OK:
                #Change the working directory so the next time you save a script
                # you will be where you saved the last one.
                path = dialog.GetPath()
                os.chdir (os.path.dirname (path))
                
                #Save the script
                theFile = file (path, 'wb')
                theFile.write (self.script)
                theFile.close()
                
                # dealocate memory used for script
                self.script = ""
            dialog.Destroy()

    def onToggleRecordingEventUpdateUI (self, event):
        if self.FilterEvent in wx.GetApp().filterEventCallables:
            event.arguments['Text'] = _(u'Stop Recording')
        else:
            event.arguments['Text'] = _(u'Record Script')

    def onPlayScriptEvent (self, event):
        dialog = wx.FileDialog (None,
                                message = "Choose script",
                                defaultDir = os.getcwd(), 
                                defaultFile = "",
                                wildcard = "*.py",
                                style = wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            paths = dialog.GetPaths()
            for path in paths:
                (path, extension) = os.path.splitext (path)

                # Temporarily modify sys.path so we can load the script's module
                sys.path.insert (0, os.path.dirname(path))
                try:
                    module = __import__ (os.path.basename (path))
                finally:
                    sys.path.pop(0)

                runFunction = module.__dict__.get ("run")
                runFunction()

        dialog.Destroy()

    def FilterEvent (self, event):
        def widgetToName (widget):
            """
            Given a widget, returns the blockName if the widget is associated
            with a block, otherwise it returns the ID of the window. We can
            use this information when playing back commands to find the
            correct window.
            """
            block = getattr (widget, "blockItem", None)
            if block is None:
                if widget is wx.GetApp().mainFrame:
                    # special case for the MainFramee window
                    name = "MainFrame"
                else:
                    # Translate events in wx.Grid's GridWindow to wx.Grid
                    widgetParent = widget.GetParent()
                    if isinstance (widgetParent, wx.grid.Grid):
                        name = widgetParent.blockItem.blockName
                    else:
                        # We don't recognize the window, so use it's Id
                        name = widget.GetId()
            else:
                # We have an associated block, so use it's name
                name = block.blockName
            return name
    
        def quoteIfString (value):
            if type (value) is str:
                return '"' + value + '"'
            else:
                return value
    
        def getClassInfo (theClass):
            classInfo =  _wxEventClasseInfo.get (theClass, None)
            if classInfo is None:
                
                # Introspect the name of the class
                className = str (theClass)
                start = className.find ("e.") + 1
                className = 'wx' + className [start:className.find("'",start)]
                classInfo = {"className":className}
                
                # Introspect the class's attribute and their default values
                newInstance = theClass()
                attributes = []
                classDict = theClass.__dict__
                for (key, value) in classDict.iteritems():
                    if (key.startswith ("m_") and type (value) is property):
                        defaultValue = getattr (newInstance, key)
                        attributes.append ((key, defaultValue))
                classInfo ["attributes"] = attributes
    
                _wxEventClasseInfo [theClass] = classInfo
            return classInfo
    
        if event.__class__ in _wxEventClasses:
            eventType =  _wxEventTypeMapping.get (event.GetEventType(), None)
            if eventType is not None:
                sentToWidget = event.GetEventObject()
    
                # Ignore mouse downs in toolbars
                if not (event.GetEventType() == wx.EVT_LEFT_DOWN.evtType[0] and
                        isinstance (sentToWidget, wx.ToolBar)):

                    # Find the name of the block that the event was sent to
                    sentToName = widgetToName (sentToWidget)
                    
                    if type (sentToName) is str:
                        # Save dictionary of properties of the event
                        values = []
                        associatedBlock = Block.Block.idToBlock.get (event.GetId(), None)
                        if associatedBlock is not None:
                            associatedBlock = associatedBlock.blockName
                            values.append ('"associatedBlock":"' + associatedBlock + '"')

                        # Don't record the stop recording event
                        if associatedBlock != "RecordingMenuItem":
                            values.append ('"eventType":' + eventType)
                            values.append ('"sentTo":' + quoteIfString (sentToName))
                            properties = "{" + ", ".join (values) + "}"

                            values = []
                            classInfo = getClassInfo (event.__class__)
                            for (attribute, defaultValue) in classInfo["attributes"]:
                                value = getattr (event, attribute)
                                if value != defaultValue:
                                    values.append ('"%s":%s' % (attribute, quoteIfString (value)))
                            attributes = "{" + ", ".join (values) + "}"
                            self.script += ("    ProcessEvent (%s, %s, %s)%s" % (classInfo ["className"],
                                                                                 properties ,
                                                                                 attributes,
                                                                                 os.linesep))
                        # Comment in for testing
                        #else:
                            #print "unnamed block with id", sentToName, sentToWidget

def installParcel(parcel, old_version=None):
    main = schema.ns('osaf.views.main', parcel.itsView)

    controller = Controller.update(
        parcel, 'RecordingController',
        blockName = 'RecordingController')

    MenuItem.update(parcel, 'RecordingScriptSeparator',
                    blockName = 'RecordingScriptSeparator',
                    menuItemKind = 'Separator',
                    parentBlock = main.TestMenu)

    # Add menu and event to record scripts
    ToggleRecording = BlockEvent.update(
        parcel, 'ToggleRecording',
        blockName = 'ToggleRecording',
        dispatchEnum = 'SendToBlockByReference',
        destinationBlockReference = controller)

    MenuItem.update(
        parcel, 'RecordingMenuItem',
        blockName = 'RecordingMenuItem',
        title = _(u'Record Script'),
        helpString = _(u'Record commands in Chandler'),
        event = ToggleRecording,
        eventsForNamedLookup = [ToggleRecording],
        parentBlock = main.TestMenu)

    # Add menu and event to play a recording
    PlayScript = BlockEvent.update(
        parcel, 'PlayScript',
        blockName = 'PlayScript',
        dispatchEnum = 'SendToBlockByReference',
        destinationBlockReference = controller)

    MenuItem.update(
        parcel, 'PlayScriptMenuItem',
        blockName = 'PlayScriptMenuItem',
        title = _(u'Play Script'),
        helpString = _(u'Playback a script you recorded'),
        event = PlayScript,
        eventsForNamedLookup = [PlayScript],
        parentBlock = main.TestMenu)
