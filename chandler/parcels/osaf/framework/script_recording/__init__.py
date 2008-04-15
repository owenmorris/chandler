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


import os, sys, wx, types, traceback, sys, run_recorded
from application import schema
from osaf.framework.blocks import Block, BlockEvent, Table
from osaf.framework.blocks.MenusAndToolbars import Menu, MenuItem, ToolBarItem
from i18n import ChandlerMessageFactory as _
from osaf.views.detail import DetailSynchronizedAttributeEditorBlock
from Scripts import ScriptsMenu, runScript
from wx.lib.buttons import GenButton
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
                                                  "UnicodeKey")},
                     wx.ClipboardTextEvent: {"attributes": ()},
                     wx.FocusEvent: {"attributes": ()},
                     wx._core.PyCommandEvent: {"attributes": ()}}

wxEventTypes = ("wx.EVT_MENU",
                "wx.EVT_KEY_DOWN",
                "wx.EVT_KEY_UP",
                "wx.EVT_LEFT_DOWN",
                "wx.EVT_LEFT_UP",
                "wx.EVT_RIGHT_DOWN",
                "wx.EVT_LEFT_DCLICK",
                "wx.EVT_RIGHT_DCLICK",
                "wx.EVT_CHAR",
                "wx.EVT_TEXT_ENTER",
                "wx.EVT_CHOICE",
                "wx.EVT_SCROLLWIN_LINEUP",
                "wx.EVT_SCROLLWIN_LINEDOWN",
                "wx.EVT_SCROLLWIN_PAGEUP",
                "wx.EVT_SCROLLWIN_PAGEDOWN",
                "wx.EVT_SCROLLWIN_THUMBTRACK",
                "wx.EVT_SCROLLWIN_THUMBRELEASE",
                "wx.EVT_ACTIVATE",
                "wx.EVT_SET_FOCUS",
                "wx.EVT_BUTTON",
                "wx.EVT_CHECKBOX",
                "wx.EVT_LISTBOX",
                "wx.EVT_RADIOBUTTON")

checkFocusEventTypes = ("wx.EVT_LEFT_DOWN",
                        "wx.EVT_RIGHT_DOWN",
                        "wx.EVT_LEFT_DCLICK",
                        "wx.EVT_CHAR",
                        "wx.EVT_TEXT_ENTER",
                        "wx.EVT_CHOICE",
                        "wx.EVT_BUTTON",
                        "wx.EVT_CHECKBOX")

# These event types work differently on the different platform so validation isn't relable.
ignoreValueCheckEventTypes = ("wx.EVT_SET_FOCUS",
                              "wx.EVT_TEXT_ENTER",
                              "wx.EVT_KEY_UP",
                              "wx.EVT_LEFT_UP")

# Scripts run at different times, and on machines in different time zones, so these widgets
#values vary from run to run.
ignoreValueCheckForWidgets = set (("EditCalendarStartDate",
                                   "EditCalendarEndDate",
                                   "EditCalendarStartTime",
                                   "EditCalendarEndTime",
                                   "EditTimeZone"))

ignoreEventsToAssociatedBlocks = set (("RecordingMenuItem",
                                       "ScriptVerificationMenuItem"))

# Add human readable comments about what the script is doing by recording these events in a comment
commentTheseEventTypes = set (("wx.EVT_CHAR",
                               "wx.EVT_MENU",
                               "wx.EVT_LEFT_DOWN",
                               "wx.EVT_RIGHT_DOWN",
                               "wx.EVT_LEFT_DCLICK",                               
                               "wx.EVT_CHOICE",
                               "wx.EVT_BUTTON",
                               "wx.EVT_CHECKBOX",
                               "wx.EVT_LISTBOX",
                               "wx.EVT_RADIOBUTTON"))

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
    
    def valueToString (self, value):
        theType = type (value)
        if theType is str:
            return "'" + value.encode('string_escape') + "'"
        elif theType is unicode:
            return "u'" + value.encode('unicode_escape').replace ("'", "\\'") + "'"
        elif theType is bool or theType is int:
            return str(value)
        else:
            return value

    def onToggleRecordingEvent (self, event):
        theApp = wx.GetApp()

        if self.FilterEvent not in theApp.filterEventCallables:
            self.commands = ""
            self.comments = ""
            self.typingSequence = None

            if hasattr (self, "lastFocus"):
                del self.lastFocus
                
            self.lineNumber = 0
            self.lastOffset = len(self.commands)
            self.lastEventWasSetFocus = False

            theApp.filterEventCallables.add (self.FilterEvent)
            theApp.SetCallFilterEvent()
        else:
            theApp.filterEventCallables.remove (self.FilterEvent)
            theApp.SetCallFilterEvent (False)

            dialog = wx.FileDialog (None,
                                    message = _(u"Save Script"),
                                    defaultDir = run_recorded.recorded_scripts_dir(), 
                                    defaultFile = u"",
                                    wildcard = u"*.py",
                                    style = wx.SAVE|wx.CHANGE_DIR)
    
            if dialog.ShowModal () == wx.ID_OK:
                # Finish the script
                if self.typingSequence is not None:
                    self.comments += "        Type %s (%d)%s" % \
                        (self.valueToString (self.typingSequence),
                         self.startTypingLineNumber,
                         os.linesep)

                # Change the working directory so the next time you save a script
                #you will be where you saved the last one.
                path = dialog.GetPath()
                
                # Save the script
                (root, ext) = os.path.splitext (path)
                if len (ext) == 0:
                    path += ".py"
                theFile = file (path, 'wb')
                self.script = "import wx, osaf, application" + os.linesep
                self.script += "def run():" + os.linesep

                if len (self.comments) > 0:
                    self.script += '    """' + os.linesep
                    self.script += self.comments
                    self.script += '    """' + os.linesep + os.linesep

                self.script += "    wx.GetApp().RunRecordedScript ([" + os.linesep

                if len (self.commands) > 0:
                    self.script += self.commands
                self.script += "    ])" + os.linesep

                theFile.write (self.script)
                theFile.close()
                # dealocate memory used for script
                del self.script
                del self.comments
                del self.commands
            dialog.Destroy()

    def onToggleRecordingEventUpdateUI (self, event):
        if self.FilterEvent in wx.GetApp().filterEventCallables:
            event.arguments['Text'] = _(u'Stop &Recording...')
        else:
            event.arguments['Text'] = _(u'&Record Script')

    def onScriptVerificationEvent (self, event):
        #Change boolean in scripts folder to determine script completion notification message
        self.verifyScripts  = not self.verifyScripts

    def onScriptVerificationEventUpdateUI (self, event):
        event.arguments['Check'] = self.verifyScripts and __debug__
        event.arguments['Enable'] = __debug__

    def onBrowseScriptEvent (self, event):
        dialog = wx.FileDialog (None,
                                message = "Choose script",
                                defaultDir = run_recorded.recorded_scripts_dir(), 
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
            Given a widget, returns a name that can be used to find the
            same widget during playback.
            """
            if isinstance (widget, wx.Button):
                name = {wx.ID_OK: "__wxID_OK__",
                        wx.ID_CANCEL: "__wxID_CANCEL__",
                        wx.ID_YES: "__wxID_YES__",
                        wx.ID_NO: "__wxID_NO__"}.get (widget.GetId(), None)
                if name is not None:
                    return name
            if isinstance (widget, wx.Window):
                return widget.GetName()
            elif widget is None:
                return "__none__"
            else:
                return "__block__" + widget.blockItem.blockName
    
        def writeComment ():
            if eventType in commentTheseEventTypes:
                if eventType == "wx.EVT_CHAR":
                    if self.typingSequence is None:
                        self.typingSequence = unicode (unichr (event.UnicodeKey))
                        self.startTypingLineNumber = self.lineNumber
                    else:
                        self.typingSequence += unichr (event.UnicodeKey)
                else:
                    if self.typingSequence is not None:
                        self.comments += "        Type %s (%d)%s" % \
                            (self.valueToString (self.typingSequence),
                             self.startTypingLineNumber,
                             os.linesep)
                        self.typingSequence = None
                    
                    if eventType == "wx.EVT_MENU":
                        widget = associatedBlock.widget
                        if isinstance (widget, wx.MenuItem):
                            # Find the menu name using wx.Widgets menu APIs that are carefully
                            #optimized for maximum pain and inefficiency. Blocks eliminate the
                            #wxWidgets non-orthoganality, but they are going away so do it the hard way.
                            menuName = widget.GetLabel()
                            menu = widget.GetMenu()
                            while True:                                            
                                widget = menu
                                menu = widget.GetParent()
                                if menu is not None:
                                    for item in menu.GetMenuItems():
                                        if item.IsSubMenu() and item.GetSubMenu() is widget:
                                            menuName = menu.GetLabelText (item.GetId()) + " > " + menuName
                                            break
                                    else:
                                        assert False, "Didn't find expected sub menu in menu item"
                                else:
                                    break
                            
                            menuBar = widget.GetMenuBar()
                            if menuBar is None:
                                menuName = "Context Menu" + " > " + menuName
                            else:
                                for index in xrange (menuBar.GetMenuCount()):
                                    if menuBar.GetMenu (index) is widget:
                                        menuName = menuBar.GetLabelTop (index) + " > " + menuName
                                        break
                                else:
                                    assert False, "Didn't find expected menu in menuBar"

                            self.comments += "        Choose menu '%s' (%d)%s" % \
                                (menuName, self.lineNumber, os.linesep)
                        elif isinstance (widget, wx.ToolBarTool):
                            toolBar = widget.GetToolBar()
                            toolIndex = toolBar.GetToolPos (widget.GetId())

                            self.comments += "        Choose toolbar button '%s' (%d)%s" % \
                                (widget.GetLabel(), self.lineNumber, os.linesep)
                
                    elif eventType == "wx.EVT_LEFT_DOWN":
                        self.comments += "        Left Mouse Down in %s (%d)%s" % (sentToName, self.lineNumber, os.linesep)
                    elif eventType == "wx.EVT_RIGHT_DOWN":
                        self.comments += "        Right Mouse Down in %s (%d)%s" % (sentToName, self.lineNumber, os.linesep)
                    elif eventType == "wx.EVT_LEFT_DCLICK":
                        self.comments += "        Left Mouse Double Click in %s (%d)%s" % (sentToName, self.lineNumber, os.linesep)

        def lookupMenuAccelerator (event):
            """
            wxWidgets has this functionality but doesn't expose it correctly
            """
            def getNextMenuItem (menu):
                for menuItem in menu.GetMenuItems():
                    if menuItem.IsSubMenu():
                        for subMenuItem in getNextMenuItem (menuItem.GetSubMenu()):
                            yield subMenuItem
                    yield menuItem

            flags = 0
            keyCode = event.m_keyCode
            if event.m_controlDown:
                flags |= wx.ACCEL_CTRL
                keyCode += 64 # convert to non control character
            if event.m_altDown:
                flags |= wx.ACCEL_ALT
            if event.m_shiftDown:
                flags |= wx.ACCEL_SHIFT
                
            if flags != 0:
                menuBar = wx.GetApp().mainFrame.GetMenuBar()
                for index in xrange (menuBar.GetMenuCount()):
                    for menuItem in getNextMenuItem (menuBar.GetMenu (index)):
                        accel = menuItem.GetAccel()
                        if (accel is not None and
                            accel.GetKeyCode() == keyCode and
                            accel.GetFlags() == flags):
                            return menuItem
            return None
    
        if event.__class__ in wxEventClasseInfo:
            eventType = wxEventTypeReverseMapping.get (event.GetEventType(), None)
            if eventType is not None:

                # Save dictionary of properties of the event
                values = []
                if eventType == "wx.EVT_CHAR":
                    # Translate command keys to menu commands
                    menuItem = lookupMenuAccelerator (event)
                    if menuItem is not None:
                        id = menuItem.GetId()
                        senttoWidget = event.GetEventObject()
                        event = wx.CommandEvent (commandType = wx.EVT_MENU.evtType[0], winid = id)
                        eventType = "wx.EVT_MENU"
                        event.SetEventObject (senttoWidget)
                        
                        # Special feature when using a command key to paste, we keep track of the
                        # clipboard so that playing back uses the clipboard that was recorded
                        if id == wx.ID_PASTE:
                            data = wx.TextDataObject()
                            if wx.TheClipboard.Open():
                                if wx.TheClipboard.GetData (data):
                                    values.append ("'clipboard':" + self.valueToString (data.GetText()))
                                wx.TheClipboard.Close()

                sentToWidget = event.GetEventObject()

                # Ignore events on widgets that are being deleted. Also ignore 
                if (not getattr (sentToWidget, "widgetIsBeingDeleted", False) and
                    # Ignore focus events on generic buttons since not all platforms can set the focus to them.
                    not (eventType == "wx.EVT_SET_FOCUS" and isinstance (sentToWidget, GenButton))):

                    # Find the name of the block that the event was sent to
                    # Translate events in wx.Grid's GridWindow to wx.Grid
                    sentToName = widgetToName (sentToWidget)
                    
                    associatedBlock = self.findBlockById(event.GetId(),
                                                         event.GetEventObject())
                    if associatedBlock is not None:
                        associatedBlockName = associatedBlock.blockName
                        values.append ("'associatedBlock':" + self.valueToString (associatedBlockName))
                    else:
                        associatedBlockName = ""

                    # Don't record the stop recording event
                    if associatedBlockName not in ignoreEventsToAssociatedBlocks:
                        values.append ("'eventType':" + eventType)
                        values.append ("'sentTo':" + self.valueToString (sentToName))

                        # Track selection of choice controls so we can set them on playback
                        if (eventType == "wx.EVT_CHOICE" or eventType == "wx.EVT_LISTBOX"):
                            values.append ("'selectedItem':" + self.valueToString (sentToWidget.GetSelection()))

                        # Use mouse up events in text controls to set selection during playback
                        if (eventType == 'wx.EVT_LEFT_UP' and isinstance (sentToWidget, wx.TextCtrl)):
                            (start, end) = sentToWidget.GetSelection()
                            # On windows GetValue uses "\n" for end of lines, but the widget stores
                            # "\n\r" for end of lines and SetSelection uses offsets that include
                            # the extra "\r" characters
                            if wx.Platform == "__WXMSW__":
                                value = sentToWidget.GetValue()
                                value = value.replace ('\n', '\n\r')
                                start = start - value.count ('\n', 0, start)
                                end = end - value.count ('\n',0, end)
                            values.append ("'selectionRange': (" +
                                           self.valueToString (start) + "," +
                                           self.valueToString (end) + ')')

                        focusWindow = wx.Window_FindFocus()
                        
                        # Record the focus for verification on playback only for certain
                        # types of events
                        if (eventType in checkFocusEventTypes):
                            if not hasattr (self, "lastFocus"):
                                self.lastFocus = focusWindow
                            if self.lastFocus != focusWindow:
                                
                                # Keep track of the focus window changes
                                self.lastFocus = focusWindow
                                
                                # Don't verify focus changes when they are GenButtons, which some platforms
                                # can't set the focus to.
                                if not isinstance (focusWindow, GenButton):
                                    values.append ("'recordedFocusWindow':" + self.valueToString (widgetToName(focusWindow)))
                                    values.append ("'recordedFocusWindowClass':" + getClassName (focusWindow.__class__))

                        #  Record the state of the last widget so we can check that the state is the same
                        # afer the event is played back. Don't record if
                        # - we don't have a valid lastSentToWidget.
                        # - we've got a command key since playing back command key events doesn't update
                        #   the widget's value.
                        # - we have a type or widget in our ignore list.
                        lastSentToWidget = getattr (self, "lastSentToWidget", None)
                        if (lastSentToWidget is not None and
                            not isinstance (lastSentToWidget, wx._core._wxPyDeadObject)):
                            method = getattr (lastSentToWidget, "GetValue", None)
                            if (method is not None and
                                not (eventType == "wx.EVT_CHAR" and event.m_controlDown) and
                                not eventType in ignoreValueCheckEventTypes and
                                not lastSentToWidget.GetName() in ignoreValueCheckForWidgets):
                                    values.append ("'lastWidgetValue':" + self.valueToString (method()))

                        # Keep track of the last widget so we can record the change in Value and
                        # verify it during playbeck.
                        self.lastSentToWidget = sentToWidget

                        properties = "{" + ", ".join (values) + "}"

                        values = []
                        classInfo = wxEventClasseInfo [event.__class__]
                        for (attribute, defaultValue) in zip (classInfo["attributes"], classInfo["defaultValues"]):
                            value = getattr (event, attribute)
                            if value != defaultValue:
                                values.append ("'%s':%s" % (attribute, self.valueToString (value)))
                        attributes = "{" + ", ".join (values) + "}"

                        # We only record the last SetFocus event in a sequence of SetFocus events
                        # to avoid sending focus to items that no longer exist.
                        thisEventIsSetFocus = eventType == "wx.EVT_SET_FOCUS"

                        if self.lastEventWasSetFocus and thisEventIsSetFocus:
                            self.commands = self.commands [:self.lastOffset]
                            self.lineNumber -= 1
                        else:
                            self.lastOffset = len(self.commands)
                        self.lastEventWasSetFocus = thisEventIsSetFocus

                        self.commands += ("        (%s, %s, %s, %s),%s" % (self.lineNumber,
                                                                           classInfo ["className"],
                                                                           properties ,
                                                                           attributes,
                                                                           os.linesep))
                        writeComment()
                        self.lineNumber += 1
                        
                    #Comment in for testing
                    #else:
                        #print "unnamed block with id", sentToName, sentToWidget
        #else:
            #print event

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
                title = _(u'&Record Script'), # see onToggleRecordingEventUpdateUI
                helpString = _(u'Record commands in Chandler'),
                event = ToggleRecording),
            MenuItem.template(
                'ScriptVerificationMenuItem',
                title = _(u'&Verify Script'),
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
