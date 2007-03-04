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
from application.Application import idToString

wxEventClasses = set([wx.CommandEvent,
                      wx.MouseEvent,
                      wx.KeyEvent])

wxEventTypes = ["EVT_MENU",
                "EVT_KEY_DOWN",
                "EVT_LEFT_DOWN",
                "EVT_LEFT_UP",
                "EVT_RIGHT_DOWN",
                "EVT_LEFT_DCLICK",
                "EVT_RIGHT_DCLICK",
                "EVT_CHAR",
                "EVT_CHOICE",
                "EVT_SCROLLWIN_LINEUP",
                "EVT_SCROLLWIN_LINEDOWN",
                "EVT_SCROLLWIN_PAGEUP",
                "EVT_SCROLLWIN_PAGEDOWN",
                "EVT_SCROLLWIN_THUMBTRACK",
                "EVT_SCROLLWIN_THUMBRELEASE",

                "EVT_ACTIVATE",
                "EVT_SET_FOCUS",
                "EVT_BUTTON",
                "EVT_CHECKBOX"]

ignoreBlocks = set (["RecordingMenuItem",
                     "IncludeTeststMenuItem"])

wxEventClasseInfo = {}
wxEventTypeReverseMapping = {}

class Controller (Block.Block):
    """
    Class to handle recording events
    """
    includeTests = schema.One(schema.Boolean, initialValue=True)

    def onToggleRecordingEvent (self, event):
        theApp = wx.GetApp()

        if self.FilterEvent not in theApp.filterEventCallables:
            self.script = "import wx, osaf" + os.linesep
            self.script += "from " + __name__ + ".script_lib import ProcessEvent, VerifyOn" + os.linesep + os.linesep
            self.script += "def run():" + os.linesep
            self.verifyOn = None
            self.lastFocus = None

            theApp.filterEventCallables.add (self.FilterEvent)
            theApp.SetCallFilterEvent()
        else:
            theApp.filterEventCallables.remove (self.FilterEvent)
            theApp.SetCallFilterEvent (False)

            dialog = wx.FileDialog (None,
                                    message = _(u"Save script as ..."),
                                    defaultFile = u"",
                                    wildcard = u"*.py",
                                    style = wx.SAVE|wx.CHANGE_DIR)
    
            if dialog.ShowModal () == wx.ID_OK:
                #Change the working directory so the next time you save a script
                # you will be where you saved the last one.
                path = dialog.GetPath()
                
                #Save the script
                (root, ext) = os.path.splitext (path)
                if len (ext) == 0:
                    path += ".py"
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

    def onIncludeTestsEvent (self, event):
        self.includeTests = not self.includeTests
        if self.includeTests:
            self.lastFocus = None

    def onIncludeTestsEventUpdateUI (self, event):
        event.arguments['Check'] = self.includeTests

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
                    if widget == wx.Window_FindFocus():
                        name = "__FocusWindow__"
                    else:
                        id = widget.GetId()
                        name = idToString.get (id, None)
                        if name is None:
                            # negative ids vary from run to run. So you need to change the
                            # creation of this widget to register it's id using Application's
                            # newIdForString
                            assert id > 0
                            name = id                            
            else:
                # We have an associated block, so use it's name
                name = block.blockName
            return name
    
        def valueToString (value):
            theType = type (value)
            if theType is str:
                return '"' + value + '"'
            elif theType is unicode:
                return 'u"' + value + '"'
            elif theType is bool or theType is int:
                return str(value)
            else:
                return value

        def getClassName (theObject):
            # Introspect the name of the class
            theClass = theObject.__class__
            module = theClass.__module__
            if module == "wx._core":
                module = "wx"
            return module + '.' + theClass.__name__

        def getClassInfo (theObject):
            theClass = theObject.__class__
            classInfo =  wxEventClasseInfo.get (theClass, None)
            if classInfo is None:
                
                classInfo = {"className": getClassName (theObject)}
                
                # Introspect the class's attribute and their default values
                newInstance = theClass()
                attributes = []
                classDict = theClass.__dict__
                for (key, value) in classDict.iteritems():
                    if (key.startswith ("m_") and type (value) is property):
                        defaultValue = getattr (newInstance, key)
                        attributes.append ((key, defaultValue))
                classInfo ["attributes"] = attributes
    
                wxEventClasseInfo [theClass] = classInfo
            return classInfo
    
        def getEventType (event):
            if len (wxEventTypeReverseMapping) == 0:
                for eventTypeName in wxEventTypes:
                    eventType = wx.__dict__[eventTypeName]
                    wxEventTypeReverseMapping [eventType.evtType[0]] = "wx." + eventTypeName
            return wxEventTypeReverseMapping.get (event.GetEventType(), None)
    
        if event.__class__ in wxEventClasses:
            eventType =  getEventType (event)
            if eventType is not None:
                sentToWidget = event.GetEventObject()

                # Ignore mouse downs in toolbars
                if not (eventType == 'wx.EVT_LEFT_DOWN' and
                        isinstance (sentToWidget, wx.ToolBar)):

                    # Find the name of the block that the event was sent to
                    # Translate events in wx.Grid's GridWindow to wx.Grid
                    widgetParent = sentToWidget.GetParent()
                    parentBlockItem = getattr (widgetParent, "blockItem", None)
                    if isinstance (widgetParent, wx.grid.Grid) and parentBlockItem is not None:
                        sentToName = parentBlockItem.blockName
                    else:
                        sentToName = widgetToName (sentToWidget)
                    
                    if type (sentToName) is str:
                        # Save dictionary of properties of the event
                        values = []
                        associatedBlock = Block.Block.idToBlock.get (event.GetId(), None)
                        if associatedBlock is not None:
                            associatedBlock = associatedBlock.blockName
                            values.append ('"associatedBlock":"' + associatedBlock + '"')

                        # Don't record the stop recording event
                        if associatedBlock not in ignoreBlocks:
                            values.append ('"eventType":' + eventType)
                            values.append ('"sentTo":' + valueToString (sentToName))

                            # Track selection of choice controls so we can set them on playback
                            if eventType == "wx.EVT_CHOICE":
                                values.append ('"selectedItem":' + valueToString (sentToWidget.GetSelection()))

                            # Use mouse up events in text controls to set selection during playback
                            if eventType == 'wx.EVT_LEFT_UP':
                                if not isinstance (sentToWidget, wx.TextCtrl):
                                    return
                                (start, end) = sentToWidget.GetSelection()
                                print start, end
                                values.append ('"selectionRange": (' +
                                               valueToString (start) + "," +
                                               valueToString (end) + ')')

                            if self.includeTests:
                                focusWindow = wx.Window_FindFocus()
                                if self.lastFocus != focusWindow:
                                    
                                    # Keep track of the focus window changes
                                    self.lastFocus = focusWindow
                                    
                                    # The newFocusWindow is either a blockName or a tupe of class, id
                                    newFocusWindow = widgetToName (focusWindow)
                                    if newFocusWindow == "__FocusWindow__" or type (newFocusWindow) is int:
                                        newFocusWindow = '(' + getClassName (focusWindow) + ',' + str(focusWindow.GetId()) + ')'
                                    else:
                                        newFocusWindow = valueToString (newFocusWindow)
                                    values.append ('"newFocusWindow":' + newFocusWindow)

                                #  Record the state of the last widget so we can check that the state is the same
                                # afer the event is played back
                                #  Don't record the last state for EVT_CHAR events. They happen before the previous
                                # key down event is processed. This causes problems with verification when key down
                                # events are processed before EVT_CHAR events during playback.
                                if eventType != 'wx.EVT_CHAR':
                                    lastSentToWidget = getattr (self, "lastSentToWidget", None)
                                    if lastSentToWidget is not None:
                                        method = getattr (lastSentToWidget, "GetValue", None)
                                        if method is not None:
                                            values.append ('"lastWidgetValue":' + valueToString (method()))
                                        
                            properties = "{" + ", ".join (values) + "}"

                            values = []
                            classInfo = getClassInfo (event)
                            for (attribute, defaultValue) in classInfo["attributes"]:
                                value = getattr (event, attribute)
                                if value != defaultValue:
                                    values.append ('"%s":%s' % (attribute, valueToString (value)))
                            attributes = "{" + ", ".join (values) + "}"
                            if self.verifyOn is not self.includeTests:
                                self.script += "    VerifyOn ("
                                if not self.includeTests:
                                    self.script += "False"
                                self.script += ")" + os.linesep
                                self.verifyOn = self.includeTests

                            self.script += ("    ProcessEvent (%s, %s, %s)%s" % (classInfo ["className"],
                                                                                 properties ,
                                                                                 attributes,
                                                                                 os.linesep))
                            self.lastSentToWidget = sentToWidget
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

    # Add menu and event to include testing in script
    IncludeTests = BlockEvent.update(
        parcel, 'IncludeTests',
        blockName = 'IncludeTests',
        dispatchEnum = 'SendToBlockByReference',
        destinationBlockReference = controller)

    MenuItem.update(
        parcel, 'IncludeTestsMenuItem',
        menuItemKind = 'Check',
        blockName = 'IncludeTeststMenuItem',
        title = _(u'Include Tests in Script'),
        helpString = _(u"Includes code in the script to verify that the UI's data matches the state when the script was recorded"),
        event = IncludeTests,
        eventsForNamedLookup = [IncludeTests],
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
