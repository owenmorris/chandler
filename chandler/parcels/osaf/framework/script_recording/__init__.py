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


import os, sys, wx, types, traceback, sys
from application import schema
from osaf.framework.blocks import Block, BlockEvent, Table
from osaf.framework.blocks.MenusAndToolbars import Menu, MenuItem, ToolBarItem
from i18n import ChandlerMessageFactory as _
from application.Application import idToString
from osaf.views.detail import DetailSynchronizedAttributeEditorBlock
from osaf.framework.script_recording.Scripts import ScriptsMenu, runScript
from tools.cats.framework import run_recorded
from i18n import ChandlerMessageFactory as _

wxEventClasseInfo = {wx.CommandEvent: {"attributes": ()},
                     wx.grid.GridEvent: {"attributes": ("Col",
                                                        "Position",
                                                        "Row")},
                     wx.MouseEvent: {"attributes": ("m_altDown",
                                                    "m_controlDown",
                                                    "m_leftDown",
                                                    "m_middleDown",
                                                    "m_rightDown",
                                                    "m_metaDown",
                                                    "m_shiftDown",
                                                    "m_x",
                                                    "m_y",
                                                    "m_wheelRotation",
                                                    "m_wheelDelta",
                                                    "m_linesPerAction")},
                     wx.KeyEvent: {"attributes": ("m_rawCode",
                                                  "m_altDown",
                                                  "m_controlDown",
                                                  "m_keyCode",
                                                  "m_metaDown",
                                                  "m_shiftDown",
                                                  "m_x",
                                                  "m_y",
                                                  "UnicodeKey")} }

wxEventTypes = ("wx.EVT_MENU",
                "wx.EVT_KEY_DOWN",
                "wx.EVT_LEFT_DOWN",
                "wx.EVT_LEFT_UP",
                "wx.EVT_RIGHT_DOWN",
                "wx.EVT_LEFT_DCLICK",
                "wx.EVT_RIGHT_DCLICK",
                "wx.EVT_CHAR",
                "wx.EVT_CHOICE",
                "wx.grid.EVT_GRID_LABEL_LEFT_CLICK",
                "wx.EVT_SCROLLWIN_LINEUP",
                "wx.EVT_SCROLLWIN_LINEDOWN",
                "wx.EVT_SCROLLWIN_PAGEUP",
                "wx.EVT_SCROLLWIN_PAGEDOWN",
                "wx.EVT_SCROLLWIN_THUMBTRACK",
                "wx.EVT_SCROLLWIN_THUMBRELEASE",

                "wx.EVT_ACTIVATE",
                "wx.EVT_SET_FOCUS",
                "wx.EVT_BUTTON",
                "wx.EVT_CHECKBOX")

ignoreBlocks = set (("RecordingMenuItem",
                     "ScriptVerificationMenuItem"))

wxEventTypeReverseMapping = {}

def getClassName (theClass):
    # Introspect the name of the class
    module = theClass.__module__
    if module == "wx._core":
        module = "wx"
    return module + '.' + theClass.__name__

for (theClass, values) in wxEventClasseInfo.iteritems():
    values ["className"] = getClassName (theClass)
    
    defaultValues = []

    try:
        newInstance = theClass()
    except TypeError:
        # wx.grid.GridEvent events can't be constructed without extra arguments
        # and don't have setters to correspond to their getters.
        newInstance = None

    for attribute in values ["attributes"]:
        defaultValues.append (getattr (newInstance, attribute, 0))
            
    values ["defaultValues"] = defaultValues    

for eventTypeName in wxEventTypes:
    dot = eventTypeName.rfind ('.')
    moduleName = eventTypeName [0:dot]
    eventName = eventTypeName [dot+1:]
    
    # Unfortunately, __import__ returns the top level module
    module = __import__ (moduleName)    
    components = moduleName.split('.')
    for component in components[1:]:
        module = getattr(module, component)

    eventType = getattr (module, eventName)
    wxEventTypeReverseMapping [eventType.evtType[0]] = eventTypeName

class Controller (Block.Block):
    """
    Class to handle recording events
    """
    verifyScripts = schema.One(schema.Boolean, initialValue=True)
    
    def onToggleRecordingEvent (self, event):
        theApp = wx.GetApp()

        if self.FilterEvent not in theApp.filterEventCallables:
            self.script = "import wx, osaf" + os.linesep
            self.script += "from " + __name__ + ".script_lib import ProcessEvent, InitializeScript" + os.linesep + os.linesep
            self.script += "def run():" + os.linesep
            self.script += "    InitializeScript ()" + os.linesep

            if hasattr (self, "lastFocus"):
                del self.lastFocus

            theApp.filterEventCallables.add (self.FilterEvent)
            theApp.SetCallFilterEvent()
        else:
            theApp.filterEventCallables.remove (self.FilterEvent)
            theApp.SetCallFilterEvent (False)

            dialog = wx.FileDialog (None,
                                    message = _(u"Save script as ..."),
                                    defaultDir = run_recorded.recorded_scripts_dir, 
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
            event.arguments['Text'] = _(u'Stop &recording...')
        else:
            event.arguments['Text'] = _(u'&Record script')

    def onScriptVerificationEvent (self, event):
        #Change boolean in scripts folder to determine script completion notification message
        self.verifyScripts  = not self.verifyScripts

    def onScriptVerificationEventUpdateUI (self, event):
        event.arguments['Check'] = self.verifyScripts and __debug__
        event.arguments['Enable'] = __debug__

    def onBrowseScriptEvent (self, event):
        dialog = wx.FileDialog (None,
                                message = "Choose script",
                                defaultDir = run_recorded.recorded_scripts_dir, 
                                defaultFile = "",
                                wildcard = "*.py",
                                style = wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            paths = dialog.GetPaths()
            for path in paths:
                (path, extension) = os.path.splitext (path)
                
                #split the filename out of the path
                (path, filename) = os.path.split(path)

                #run the recorded script
                runScript (filename)
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
                return "'" + value.encode('string_escape') + "'"
            elif theType is unicode:
                return "u'" + value.encode('unicode_escape') + "'"
            elif theType is bool or theType is int:
                return str(value)
            else:
                return value

        if event.__class__ in wxEventClasseInfo:
            eventType = wxEventTypeReverseMapping.get (event.GetEventType(), None)
            if eventType is not None:
                sentToWidget = event.GetEventObject()

                # Ignore events on widgets that are being deleted
                if not getattr (sentToWidget, "widgetIsBeingDeleted", False):
                    # Find the name of the block that the event was sent to
                    # Translate events in wx.Grid's GridWindow to wx.Grid
                    widgetParent = sentToWidget.GetParent()
                    parentBlockItem = getattr (widgetParent, "blockItem", None)

                    if (parentBlockItem is not None and
                        (isinstance (parentBlockItem, Table) or
                         isinstance (parentBlockItem, DetailSynchronizedAttributeEditorBlock) or
                         isinstance (parentBlockItem, ToolBarItem))):
                        sentToName = parentBlockItem.blockName
                    else:
                        sentToName = widgetToName (sentToWidget)
                    
                    if type (sentToName) is str:
                        # Save dictionary of properties of the event
                        values = []
                        associatedBlock = Block.Block.idToBlock.get (event.GetId(), None)
                        if associatedBlock is not None:
                            associatedBlock = associatedBlock.blockName
                            values.append ("'associatedBlock':'" + associatedBlock + "'")

                        # Don't record the stop recording event
                        if associatedBlock not in ignoreBlocks:
                            values.append ("'eventType':" + eventType)
                            values.append ("'sentTo':" + valueToString (sentToName))

                            # Track selection of choice controls so we can set them on playback
                            if eventType == "wx.EVT_CHOICE":
                                values.append ("'selectedItem':" + valueToString (sentToWidget.GetSelection()))

                            # Use mouse up events in text controls to set selection during playback
                            if (eventType == 'wx.EVT_LEFT_UP' and isinstance (sentToWidget, wx.TextCtrl)):
                                (start, end) = sentToWidget.GetSelection()
                                values.append ("'selectionRange': (" +
                                               valueToString (start) + "," +
                                               valueToString (end) + ')')

                            focusWindow = wx.Window_FindFocus()
                            
                            if wx.Platform != "__WXMAC__":
                                # On platforms other than mac the focus window is a wx.TextCtrl
                                # whose parent is the wx.SearchCtrl
                                parentWidget = focusWindow.GetParent()
                                if isinstance (parentWidget, wx.SearchCtrl):
                                    focusWindow = parentWidget

                            if not hasattr (self, "lastFocus"):
                                self.lastFocus = focusWindow
                            if self.lastFocus != focusWindow:
                                
                                # Keep track of the focus window changes
                                self.lastFocus = focusWindow
                                
                                # The newFocusWindow is either a blockName or a tupe of class, id
                                newFocusWindow = widgetToName (focusWindow)
                                if newFocusWindow == "__FocusWindow__" or type (newFocusWindow) is int:
                                    values.append ("'newFocusWindow':" + str(focusWindow.GetId()))
                                else:
                                    values.append ("'newFocusWindow':" + valueToString (newFocusWindow))
                                values.append ("'newFocusWindowClass':" + getClassName (focusWindow.__class__))

                            #  Record the state of the last widget so we can check that the state is the same
                            # afer the event is played back
                            lastSentToWidget = getattr (self, "lastSentToWidget", None)
                            if lastSentToWidget is not None and not isinstance (lastSentToWidget, wx._core._wxPyDeadObject):
                                method = getattr (lastSentToWidget, "GetValue", None)
                                if method is not None:
                                    values.append ("'lastWidgetValue':" + valueToString (method()))
                                
                            # Keep track of the last widget so we can record the change in Value and
                            # verify it during playbeck.
                            self.lastSentToWidget = sentToWidget
 
                            properties = "{" + ", ".join (values) + "}"

                            values = []
                            classInfo = wxEventClasseInfo [event.__class__]
                            for (attribute, defaultValue) in zip (classInfo["attributes"], classInfo["defaultValues"]):
                                value = getattr (event, attribute)
                                if value != defaultValue:
                                    values.append ("'%s':%s" % (attribute, valueToString (value)))
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

    #Define the block events for use with the menu items to be created.

    # Add menu and event to record scripts
    ToggleRecording = BlockEvent.update(
        parcel, 'ToggleRecording',
        blockName = 'ToggleRecording',
        dispatchEnum = 'SendToBlockByReference',
        destinationBlockReference = controller)

    # Add menu and event to include testing in script
    ScriptVerification = BlockEvent.update(
        parcel, 'ScriptVerification',
        blockName = 'ScriptVerification',
        dispatchEnum = 'SendToBlockByReference',
        destinationBlockReference = controller)
    
    # Create a block event that will be used for the dynamic play script menu system
    PlayableSripts = BlockEvent.template('PlayableSripts',
                    dispatchToBlockName = 'ScriptMenu',
                    commitAfterDispatch = True).install(parcel)    
    
    # Add event to play a recording
    #create the block event that will handle the event raised by open script menu item
    BrowseScript = BlockEvent.update(
        parcel, 'BrowseScript',
        blockName = 'BrowseScript',
        dispatchEnum = 'SendToBlockByReference',
        destinationBlockReference = controller)
    
    Menu.template(
        'ScriptingMenuItem',
        title = _(u'Scriptin&g'),
        childBlocks = [
            MenuItem.template(
                'RecordingMenuItem',
                title = _(u'&Record script'), # see onToggleRecordingEventUpdateUI
                helpString = _(u'Record commands in Chandler'),
                event = ToggleRecording),
            MenuItem.template(
                'ScriptVerificationMenuItem',
                title = _(u'&Verify script'),
                helpString = _(u"When scripts run, verification ensure that the UI's data matches the state when the script was recorded"),
                menuItemKind = 'Check',
                event = ScriptVerification),
            
            # Create the block for the dynamic menu
            # Add a dynamic menu to display the playable scripts
            ScriptsMenu.template(
                'ScriptMenu',
                title = _(u'Run &Script'),
                event = PlayableSripts,
                childBlocks = [
                    # Add a menu item that allows user to browse for a specific playable script
                    MenuItem.template(
                        'PlayScriptMenuItem',
                        title = _(u'&Browse...'),
                        helpString = _(u'Open a script you recorded to play'),
                        event = BrowseScript)
                ])
            ],
        parentBlock = main.ToolsMenu).install(parcel)
