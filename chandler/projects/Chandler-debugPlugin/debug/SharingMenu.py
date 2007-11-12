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


import wx, logging

from application import schema, dialogs
from i18n import MessageFactory

from osaf import sharing, dumpreload
from osaf.activity import Activity
from osaf.framework.blocks.Block import Block
from osaf.framework.blocks import BlockEvent, MenuItem, Menu
from repository.item.Item import Item

_ = MessageFactory("Chandler-debugPlugin")
logger = logging.getLogger(__name__)


class SharingMenuHandler(Block):

    def setStatusMessage(self, msg):
        Block.findBlockByName('StatusBar').setStatusMessage(msg)

    def getSidebarSelectedCollection(self, private=False):
        """
        Return the sidebar's selected item collection.
        Will not return private collections (whose "private" attribute
        is True) unless you pass private=True.
        """
        sidebar = Block.findBlockByName("Sidebar")
        item = sidebar.contents.getFirstSelectedItem()
        if (getattr(item, 'private', None) is not None and
            private == False and
            item.private):
            return None

        return item

    def on_debug_BackgroundSyncAllEvent(self, event):

        # Specifically *not* doing a commit here.  This is to simulate
        # a scheduled background sync.  Only manually.
        sharing.scheduleNow(self.itsView)

    def on_debug_BackgroundSyncGetOnlyEvent(self, event):

        rv = self.itsView
        collection = self.getSidebarSelectedCollection()
        if collection is not None:
            # Ensure changes in attribute editors are saved
            wx.GetApp().mainFrame.SetFocus()

            rv.commit()
            sharing.scheduleNow(rv, collection=collection, modeOverride='get')

    def on_debug_ToggleReadOnlyModeEvent(self, event):
        sharing.setReadOnlyMode(not sharing.isReadOnlyMode())

    def on_debug_ToggleReadOnlyModeEventUpdateUI(self, event):
        event.arguments['Check'] = sharing.isReadOnlyMode()

    def on_debug_InMemoryPublishEvent(self, event):
        collection = self.getSidebarSelectedCollection()
        sharing.publish(collection, None)

    def on_debug_ConvertExportFileEvent(self, event):

        wildcard = "%s|*.chex|%s|*.dump|%s (*.*)|*.*" %(_(u"Export files"),
                                                        _(u"Dump files"),
                                                        _(u"All files"))
        dlg = wx.FileDialog(wx.GetApp().mainFrame,
                            _(u"Convert from export file"), "", "", wildcard,
                            wx.OPEN)

        fromPath = None
        if dlg.ShowModal() == wx.ID_OK:
            fromPath = dlg.GetPath()
        dlg.Destroy()

        if fromPath:
            wildcard = "%s|*.rec|%s (*.*)|*.*" %(_(u"Record files"),
                                                 _(u"All files"))
            dlg = wx.FileDialog(wx.GetApp().mainFrame,
                                _(u"Convert to record file"), "", "",
                                wildcard, wx.SAVE|wx.OVERWRITE_PROMPT)
            toPath = None
            if dlg.ShowModal() == wx.ID_OK:
                toPath = dlg.GetPath()
            dlg.Destroy()

            if toPath:
                activity = Activity(_(u"Convert %s") %(fromPath))
                dialogs.Progress.Show(activity)
                activity.started()

                try:
                    dumpreload.convertToTextFile(fromPath, toPath,
                                                 activity=activity)
                    activity.completed()
                except Exception, e:
                    logger.exception("Failed to convert file")
                    activity.failed(exception=e)
                    raise
                self.setStatusMessage(_(u'File converted.'))


def makeSharingMenu(parcel, sharingMenu):

    handler = SharingMenuHandler.update(parcel, None,
                                        blockName='_debug_SharingMenuHandler')

    backgroundSyncAllEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_BackgroundSyncAll',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)
    backgroundSyncGetOnlyEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_BackgroundSyncGetOnly',
                          dispatchEnum='SendToBlockByReference',
                          destinationBlockReference=handler)
    toggleReadOnlyModeEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ToggleReadOnlyMode',
                          dispatchEnum='SendToBlockByReference',
                          commitAfterDispath=True,
                          destinationBlockReference=handler)
    inMemoryPublishEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_InMemoryPublish',
                          dispatchEnum='SendToBlockByReference',
                          commitAfterDispath=True,
                          destinationBlockReference=handler)
    convertExportFileEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_ConvertExportFile',
                          dispatchEnum='SendToBlockByReference',
                          commitAfterDispath=True,
                          destinationBlockReference=handler)

    # handled in PimBlocks
    createConflictEvent = \
        BlockEvent.update(parcel, None,
                          blockName='_debug_CreateConflict',
                          dispatchEnum='FocusBubbleUp',
                          commitAfterDispath=True)

    MenuItem.update(parcel, None,
                    blockName='_debug_BackgroundSyncAll',
                    title=_(u'Start a &background sync now'),
                    helpString=_(u'Initiates a single background sync'),
                    event=backgroundSyncAllEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_BackgroundSyncGetOnly',
                    title=_(u'Start a &GET-only background sync of current collection'),
                    helpString=_(u'Initiates a single background sync without writing to server'),
                    event=backgroundSyncGetOnlyEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_ToggleReadOnlyMode',
                    title=_(u'Read-onl&y sharing mode'),
                    helpString=_(u'Forces all sharing to be done in read-only mode'),
                    menuItemKind='Check',
                    event=toggleReadOnlyModeEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName="_debug_InMemoryPublish",
                    title=_(u"&Publish In-memory"),
                    helpString=_(u'Publish a collection in-memory'),
                    event=inMemoryPublishEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_CreateConflict',
                    title=_(u"Crea&te Conflict"),
                    helpString=_(u'Create an artificial conflict for the selected items'),
                    event=createConflictEvent,
                    parentBlock=sharingMenu)
    MenuItem.update(parcel, None,
                    blockName='_debug_ConvertExportFile',
                    title=_(u"Convert e&xport file"),
                    helpString=_(u'Convert an export file to a more readable text file'),
                    event=convertExportFileEvent,
                    parentBlock=sharingMenu)
