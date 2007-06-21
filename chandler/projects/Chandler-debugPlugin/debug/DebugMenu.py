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

import sys, wx, i18n

from application import schema, Globals, styles
from application.dialogs.Util import DebugWindow
from i18n import MessageFactory
from osaf.framework.blocks import \
    BlockEvent, NewBlockWindowEvent, MenuItem, Menu
from osaf.framework.blocks.Block import Block

from debug.blockviewer import makeBlockViewer
from debug.repositoryviewer import makeRepositoryViewer

_ = MessageFactory("Chandler-debugPlugin")


class DebugMenuHandler(Block):

    def setStatusMessage(self, msg):
        Block.findBlockByName('StatusBar').setStatusMessage(msg)

    def showPyShell(self, withFilling=False):
        """
        A window with a python interpreter
        """
        from wx import py
        from tools import headless

        headless.view = view = self.itsView

        def run(scriptText):
            import osaf.framework.scripting as Scripting
            Scripting.run_script(scriptText, view)

        # Import helper methods/variables from headless, and also add
        # whatever other methods we want to the mix (such as the run method,
        # above).  locals will be passed to PyCrust/Shell to make those
        # symbols available to the developer
        locals = headless.getExports(run=run,
                                     view=view,
                                     schema=schema,
                                     app_ns=schema.ns('osaf.app', view),
                                     pim_ns=schema.ns('osaf.pim', view))

        if withFilling:
            browseableObjects = {
                "globals": Globals,
                "parcelsRoot": view.getRoot('parcels'),
                "repository": view.repository,
                "wxApplication": wx.GetApp(),
            }
            self.pyFrame = py.crust.CrustFrame(rootObject=browseableObjects,
                                               rootLabel="Chandler",
                                               locals=locals)
        else:
            self.pyFrame = py.shell.ShellFrame(locals=locals)

        self.pyFrame.SetSize((700, 700))
        self.pyFrame.Show(True)

        # Install a custom displayhook to keep Python from setting the global
        # _ (underscore) to the value of the last evaluated expression.  If 
        # we don't do this, our mapping of _ to gettext can get overwritten.
        # This is useful in interactive debugging with PyShell.

        def _displayHook(obj):
            if obj is not None:
                print repr(obj)

        sys.displayhook = _displayHook

    def on_debug_ShowPyShellEvent(self, event):
        self.showPyShell(False)

    def on_debug_ShowPyCrustEvent(self, event):
        self.showPyShell(True)

    def on_debug_ShowWidgetInspectorEvent(self, event):
        from wx.lib.inspection import InspectionTool
        InspectionTool().Show()

    def on_debug_ReloadStylesEvent(self, event):
        styles.loadConfig()

    def on_debug_WxTestHarnessEvent(self, event):
        """
         This method is for testing and does not require translation strings.
        """
        mainWidget = wx.GetApp().mainFrame
        if isinstance(mainWidget, wx.Window):
            #ForceRedraw works; the other two fail to induce a window update !!!
            #mainWidget.ForceRedraw()
            #mainWidget.ClearBackground()
            #mainWidget.Refresh(True)
            #mainWidget.Layout()
            statusMsg = "invalidated main view and back buffer"
        else:
            statusMsg = "wxDang"

        self.setStatusMessage(statusMsg)

    def on_debug_ShowI18nManagerDebugWindowEvent(self, event):
        
        win = DebugWindow(_(u"I18nManager Resource Debugger"),
                          i18n._I18nManager.getDebugString())
        win.CenterOnScreen()
        win.ShowModal()
        win.Destroy()

    def on_debug_RestartAppEvent(self, event):

        app = wx.GetApp()
        app.PostAsyncEvent(app.restart)


def makeDebugMenu(parcel, toolsMenu):

    handler = DebugMenuHandler.update(parcel, None,
                                      blockName='_debug_DebugMenuHandler')

    showPyShellEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ShowPyShell',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)
    showPyCrustEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ShowPyCrust',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)

    showWidgetInspectorEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ShowWidgetInspector',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)

    reloadStylesEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ReloadStyles',
                          dispatchEnum='SendToBlockByReference',
                          commitAfterDispatch=True,
                          destinationBlockReference=handler)

    wxTestHarnessEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_WxTestHarness',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)

    showI18nManagerDebugWindowEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ShowI18nManagerDebugWindow',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)
    
    showBlockViewerEvent = \
        NewBlockWindowEvent.update(parcel, None,
                                   blockName='_debug_ShowBlockViewer',
                                   treeOfBlocks=makeBlockViewer(parcel))

    showRepositoryViewerEvent = \
        NewBlockWindowEvent.update(parcel, None,
                                   blockName='_debug_ShowRepositoryViewer',
                                   treeOfBlocks=makeRepositoryViewer(parcel))

    restartAppEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_RestartApp',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)

    debugMenu = Menu.update(parcel, None,
                            blockName='_debug_debugMenu',
                            title=_(u'&Debug'),
                            parentBlock=toolsMenu)

    MenuItem.update(parcel, None, 
                    blockName='_debug_ShowPyShellItem',
                    title=_(u'&Show Python shell...'),
                    helpString=_(u'Brings up an interactive Python shell'),
                    event=showPyShellEvent,
                    parentBlock=debugMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_ShowPyCrustItem',
                    title=_(u'Show Python shell with &object browser...'),
                    helpString=_(u'Brings up an interactive Python shell and object browser'),
                    event=showPyCrustEvent,
                    parentBlock=debugMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_ShowWidgetInspectorItem',
                    title=_(u'Show widget &inspection tool...'),
                    helpString=_(u'Displays the widget inspection tool, showing all current widgets and sizers'),
                    event=showWidgetInspectorEvent,
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_debug_separator_1',
                    menuItemKind='Separator',
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_ReloadStylesItem',
                    title=_(u'Reload St&yles'),
                    helpString=_(u'Reloads styles'),
                    event=reloadStylesEvent,
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_debug_separator_2',
                    menuItemKind='Separator',
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_WxTestHarnessItem',
                    title=_(u'&Wx Test Harness'),
                    helpString=_(u'invoke the current flavor of wx debugging'),
                    event=wxTestHarnessEvent,
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_debug_separator_3',
                    menuItemKind='Separator',
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_ShowI18nManagerDebugItem',
                    title=_(u'Show I18nManager &debug window...'),
                    helpString=_(u'Displays a tree of projects, locales, resources, and gettext localizations'),
                    event=showI18nManagerDebugWindowEvent,
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_debug_separator_4',
                    menuItemKind='Separator',
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_ShowBlockViewerItem',
                    title=_(u'Show &Block Viewer...'),
                    helpString=_(u'Opens the Block Viewer'),
                    event = showBlockViewerEvent,
                    eventsForNamedLookup = [showBlockViewerEvent],
                    parentBlock=debugMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_ShowRepositoryViewerItem',
                    title=_(u'Show &Repository Viewer...'),
                    helpString=_(u'Opens the Repository Viewer'),
                    event=showRepositoryViewerEvent,
                    eventsForNamedLookup=[showRepositoryViewerEvent],
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_debug_separator_5',
                    menuItemKind='Separator',
                    parentBlock=debugMenu)

    MenuItem.update(parcel, None,
                    blockName='_debug_RestartApp',
                    title=_(u'Restart Chandler'),
                    helpString=_(u'Restarts Chandler'),
                    event=restartAppEvent,
                    parentBlock=debugMenu)
