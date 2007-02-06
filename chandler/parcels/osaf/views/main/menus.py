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

import logging

def makeMainMenus(parcel):

    from application import schema
    import wx
    
    from osaf.framework.blocks import Menu, MenuItem, MenuBar, ColorEvent
    from osaf.framework.blocks.calendar import VisibleHoursEvent
    from i18n import ChandlerMessageFactory as _
    from osaf import messages, pim
    from osaf.pim.structs import ColorType
    from osaf import usercollections
    from colorsys import hsv_to_rgb
    from itertools import chain

    if '__WXMAC__' in wx.PlatformInfo:
        platform_delete = _(u'Back')
        platform_command_delete = _(u'Ctrl+Back')
    else:
        platform_delete = _(u'Del')
        platform_command_delete = _(u'Ctrl+Del')

    
    def makeColorMenuItems (parcel, cls, hues):
        """
        dynamically creates an array of type 'cls' based on a list of colors
        """
        menuItems = []
        
        # make sure that all the events end up in the main parcel
        mainParcel = schema.parcel_for_module ("osaf.views.main", repositoryView)
        for shortName, title, hue in hues:
            rgb = hsv_to_rgb(hue/360.0, 0.5, 1.0)
            rgb = [int(c*255) for c in rgb] + [255]
            color = ColorType (*rgb)

            colorEvent = ColorEvent.template(
                shortName + 'CollectionColor',
                dispatchToBlockName = 'Sidebar',
                color = color,
                methodName = 'onCollectionColorEvent').install (mainParcel)
    
            menuItem = cls.template(
                shortName + 'ColorItem',
                title = title,
                icon = shortName + "MenuIcon",
                menuItemKind = "Check",
                event = colorEvent)
            menuItems.append (menuItem)

        return menuItems

    def makeVisibleHourMenuItems(parcel):
        """
        Create the 'Visible Hours' submenu. Should look like:
        
        Automatic
        ---------
        5 hours
        6 hours

        etc..
        """
        menuItems = []
        
        # include '-1' in the list of hours
        for hour in chain([-1], xrange(5, 13), [18], [24]):

            # create the event that will fire. Note that all events on
            # the same method
            eventName = 'VisibleHour' + str(hour)
            event = \
                VisibleHoursEvent.template(eventName,
                                           methodName = 'onVisibleHoursEvent',
                                           visibleHours = hour)
            event = event.install(parcel)

            # now create the menuitem itself
            if hour == -1:
                title = _(u"&Automatic")
            else:
                # XXX The keyboard shortcut is implemented for values < 10 only
                title = _(u"%(amp)s%(hours)s hours") % {'amp': '&' if hour < 10 else '', 'hours': hour}
                
            menuItem = MenuItem.template(eventName + 'Item',
                                         title = title,
                                         menuItemKind = "Check",
                                         event = event)
            menuItems.append(menuItem)

            # add a separator after 'Automatic'
            if hour == -1:
                menuItem = MenuItem.template('VisibleHourSeparator',
                                             menuItemKind="Separator")
                menuItems.append(menuItem)

        return menuItems
                                         

    repositoryView = parcel.itsView
    main = schema.ns("osaf.views.main", repositoryView)
    globalBlocks = schema.ns("osaf.framework.blocks", repositoryView)
    calBlocks = schema.ns("osaf.framework.blocks.calendar", repositoryView)

    fileMenu =  Menu.template('FileMenu',
                title = _(u'&File'),
                childrenBlocks = [
                    MenuItem.template('ImportIcalendarItem',
                        event = main.ImportIcalendar,
                        title = _(u'&Import...'),
                        helpString = _(u'Import iCalendar file')),
                    MenuItem.template('ExportIcalendarItem',
                        event = main.ExportIcalendar,
                        title = _(u'&Export...'),
                        helpString = _(u'Export Calendar Events to an iCalendar file')),
                    MenuItem.template('PrefsAccountsItem',
                        event = main.EditAccountPreferences,
                        title = _(u'&Accounts...'),
                        helpString = messages.ACCOUNT_PREFERENCES),
                    MenuItem.template('FileSeparator0',
                        menuItemKind = 'Separator'),
                    MenuItem.template('CommitView',
                        event = globalBlocks.CommitView,
                        title = _(u'&Save Changes'),
                        accel = _(u'Ctrl+S')),
                    MenuItem.template('FileSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('PrintPreviewItem',
                        event = globalBlocks.PrintPreview,
                        title = _(u'Print Pre&view')),
                    MenuItem.template('PageSetupItem',
                        event = globalBlocks.PageSetup,
                        title = _(u'Page Set&up...'),
                        accel = _(u'Shift+Ctrl+P')),
                    MenuItem.template('PrintItem',
                        event = globalBlocks.Print,
                        title = _(u'&Print...'),
                        accel = _(u'Ctrl+P'),
                        helpString = _(u'Print the current calendar'),
                        wxId = wx.ID_PRINT),
                    MenuItem.template('FileSeparator2',
                        menuItemKind = 'Separator'),
                    MenuItem.template('BackupRepository',
                        event = globalBlocks.BackupRepository,
                        title = _(u'&Backup Repository')),
                    MenuItem.template('RestoreRepository',
                        event = globalBlocks.RestoreRepository,
                        title = _(u'&Restore Repository')),
                    MenuItem.template('FileSeparator3',
                        menuItemKind = 'Separator'),
                    Menu.template('ImportExportMenu',
                        title = _(u'Import/Export'),
                        childrenBlocks = [
                            ]), # Menu ImportExportMenu
                    ])

    if wx.Platform != '__WXMAC__':
        fileMenu.attrs['childrenBlocks'].append(MenuItem.template('FileSeparator3',
                                                         menuItemKind = 'Separator'))
        fileMenu.attrs['childrenBlocks'].append(MenuItem.template('QuitItem',
                                                        event=globalBlocks.Quit,
                                                        title = _(u'&Quit'),
                                                        accel = _(u'Ctrl+Q'),
                                                        helpString = _(u'Quit Chandler'),
                                                        wxId = wx.ID_EXIT))

    MenuBar.template('MenuBar',
        childrenBlocks = [
            fileMenu,
            Menu.template('EditMenu',
                title = _(u'&Edit'),
                childrenBlocks = [
                    MenuItem.template('UndoItem',
                        event = globalBlocks.Undo,
                        title = messages.UNDO,
                        accel = _(u'Ctrl+Z'),
                        helpString = _(u"Can't Undo"),
                        wxId = wx.ID_UNDO),
                    MenuItem.template('RedoItem',
                        event = globalBlocks.Redo,
                        title = messages.REDO,
                        accel = _(u'Ctrl+Y'),
                        helpString = _(u"Can't Redo"),
                        wxId = wx.ID_REDO),
                    MenuItem.template('EditSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('CutItem',
                        event = globalBlocks.Cut,
                        title = messages.CUT,
                        accel = _(u'Ctrl+X'),
                        wxId = wx.ID_CUT),
                    MenuItem.template('CopyItem',
                        event = globalBlocks.Copy,
                        title = messages.COPY,
                        accel = _(u'Ctrl+C'),
                        wxId = wx.ID_COPY),
                    MenuItem.template('PasteItem',
                        event = globalBlocks.Paste,
                        title = messages.PASTE,
                        accel = _(u'Ctrl+V'),
                        wxId = wx.ID_PASTE),
                    MenuItem.template('SelectAllItem',
                        event = globalBlocks.SelectAll,
                        title = messages.SELECT_ALL,
                        accel = _(u'Ctrl+A'),
                        helpString = _(u'Select all'),
                        wxId = wx.ID_SELECTALL),
                    MenuItem.template('EditSeparator2',
                        menuItemKind = 'Separator'),
                    MenuItem.template('RemoveItem',
                        event = globalBlocks.Remove,
                        title = _(u'Remove'),
                        accel = platform_delete,                        
                        helpString = _(u'Remove the current selection from the current collection'),
                        wxId = wx.ID_DELETE),                    
                    MenuItem.template('DeleteItem',
                        event = main.Delete,
                        title = _(u'Delete'),
                        accel = platform_command_delete,
                        helpString = _(u'Move the current selection to the trash')),
                    MenuItem.template('EditSeparator3',
                        menuItemKind = 'Separator'),
                    MenuItem.template('SearchItem',
                        event = main.Search,
                        title = _(u'&Find'),
                        accel = _(u'Ctrl+F'),
                        helpString = _(u'Search using the Quick Entry field')),
                    MenuItem.template('EmptyTrashItem',
                        event = main.EmptyTrash,
                        title = _(u'Empty Trash'),
                        helpString = _(u'Remove all items from the Trash collection')),
                    ]), # Menu EditMenu
            
            Menu.template('ViewMenu',
                title = _(u'&View'),
                childrenBlocks = [
                    MenuItem.template('ViewAsCalendarItem',
                        event = main.ViewAsCalendar,
                        title = _(u'View as &Calendar'),
                        menuItemKind = 'Check',
                        helpString = _(u'Display data in a Calendar view')),
                    MenuItem.template('ViewAsDashboardItem',
                        event = main.ViewAsDashboard,
                        title = _(u'View as Das&hboard'),
                        menuItemKind = 'Check',
                        helpString = _(u'Display data in a Dashboard view')),
                    MenuItem.template('ViewAsTableItem',
                        event = main.ViewAsTable,
                        title = _(u'View as Ta&ble'),
                        menuItemKind = 'Check',
                        helpString = _(u'Display data in a Table view')),
                    MenuItem.template('ViewSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('WeekViewItem',
                                      event = calBlocks.WeekView,
                                      title = _(u'&Week View'),
                                      accel = _(u'Ctrl+2'),
                                      helpString = _(u'Show the calendar in week view')),
                    MenuItem.template('DayViewItem',
                                      event = calBlocks.DayView,
                                      title = _(u'&Day View'),
                                      accel = _(u'Ctrl+1'),
                                      helpString = _(u'Show the calendar in day view')),
                    MenuItem.template('GoToNextWeek',
                                      event = calBlocks.GoToNext,
                                      title = _(u'&Next Week'),
                                      accel = _(u'Ctrl+Right'),
                                      helpString = _(u'Jump to the next week')),
                    MenuItem.template('GoToPrevWeek',
                                      event = calBlocks.GoToPrev,
                                      title = _(u'&Previous Week'),
                                      accel = _(u'Ctrl+Left'),
                                      helpString = _(u'Jump to the previous week')),
                    MenuItem.template('GoToDate',
                                      event = calBlocks.GoToDate,
                                      title = _(u'&Jump to date...'),
                                      accel = _(u'Ctrl+Shift+T'),
                                      helpString = _(u'Navigate to a specific date')),
                    MenuItem.template('GoToToday',
                                      event = calBlocks.GoToToday,
                                      title = _(u'Jump to t&oday'),
                                      accel = _(u'Ctrl+T'),
                                      helpString = _(u'Navigate to today\'s date')),
                    MenuItem.template('ViewSeparator2',
                        menuItemKind = 'Separator'),
                    Menu.template('ViewConfigureWindow',
                        title = _(u'Confi&gure window'),
                        helpString = _(u'Configure the window'),
                        childrenBlocks = [
                            Menu.template('VisibleHoursMenu',
                                          title = _(u'&Visible Hours'),
                                          childrenBlocks = \
                                          makeVisibleHourMenuItems(parcel)),
                            MenuItem.template('ViewToolBarItem',
                                              event = main.ShowHideApplicationBar,
                                              title = _(u'&Toolbar'),
                                              menuItemKind = 'Check',
                                              helpString = _(u'Show or hide the Toolbar')),
                            MenuItem.template('ViewSideBarItem',
                                              event = main.ShowHideSidebar,
                                              title = _(u'&Sidebar'),
                                              menuItemKind = 'Check',
                                              helpString = _(u'Show or hide the Sidebar')),
                            MenuItem.template('ViewMiniCalItem',
                                              title = _(u'&Mini-calendar'),
                                              menuItemKind = 'Check',
                                              helpString = _(u'Show or hide the Mini-calendar')),
                            MenuItem.template('ViewDetailItem',
                                              title = _(u'&Detail view'),
                                              menuItemKind = 'Check',
                                              helpString = _(u'Show or hide the Detail view')),
                            MenuItem.template('ViewStatusBarItem',
                                              event = main.ShowHideStatusBar,
                                              title = _(u'Status &Bar'),
                                              menuItemKind = 'Check',
                                              helpString = _(u'Show or hide the Status bar')),
                            ]),
                    MenuItem.template('ViewSeparator3',
                        menuItemKind = 'Separator'),
                    MenuItem.template('EnableSectionsItem',
                        event = main.EnableSections,
                        title = _(u'Use &Sections'),
                        menuItemKind = 'Check',
                        helpString = _(u'Hide or show section dividers')),
                    MenuItem.template('EnableTimezonesItem',
                        event = main.EnableTimezones,
                        title = _(u'Use &Timezones'),
                        menuItemKind = 'Check',
                        helpString = _(u'Hide or show timezones')),
                    ]), # Menu ViewMenu
            Menu.template('ItemMenu',
                title = _(u'&Item'),
                childrenBlocks = [
                    Menu.template('NewItemMenu',
                        title = _(u'&New'),
                        helpString = _(u'Create a new Content Item'),
                        childrenBlocks = [
                            MenuItem.template('NewItemItem',
                                event = main.NewItem,
                                title = _(u'New &item'),
                                accel = _(u'Ctrl+N'),
                                helpString = _(u'Create a new item'),
                                wxId = wx.ID_NEW),
                            MenuItem.template('NewItemSeparator1',
                                menuItemKind = 'Separator'),
                            MenuItem.template('NewNoteItem',
                                event = main.NewNote,
                                title = _(u'New &note'),
                                helpString = _(u'Create a new Note')),
                            MenuItem.template('NewMessageItem',
                                event = main.NewMailMessage,
                                title = _(u'New &message'),
                                helpString = _(u'Create a new Message')),
                            MenuItem.template('NewTaskItem',
                                event = main.NewTask,
                                title = _(u'New &task'),
                                helpString = _(u'Create a new Task')),
                            MenuItem.template('NewEventItem',
                                event = main.NewCalendar,
                                title = _(u'New &event'),
                                helpString = _(u'Create a new Event')),
                            MenuItem.template('NewItemSeparator2',
                                menuItemKind = 'Separator'),
                            MenuItem.template('NewContactItem',
                                title = _(u'New &contact'),
                                helpString = _(u'Create a new Contact')),
                            ]), # Menu NewItemMenu
                    Menu.template('AddToCollectionMenu',
                        title = _(u'&Add to'),
                        helpString = _(u'Add item to a collection'),
                        childrenBlocks = [
                            ]), # Menu Add to
                    Menu.template('MoveToCollectionMenu',
                        title = _(u'&Move to'),
                        helpString = _(u'Move item to a collection'),
                        childrenBlocks = [
                            ]), # Menu Move to
                    MenuItem.template('ItemSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('SendMessageItem',
                        event = main.SendShareItem,
                        title = messages.SEND,
                        helpString = _(u'Send the selected Mail Message')),
                    MenuItem.template('ItemSeparator2',
                        menuItemKind = 'Separator'),
                    MenuItem.template('StampMessageItem',
                        event = main.FocusStampMessage,
                        title = messages.STAMP_MAIL,
                        menuItemKind = 'Check',
                        helpString = messages.STAMP_MAIL_HELP),
                    MenuItem.template('StampTaskItem',
                        event = main.FocusStampTask,
                        title = messages.STAMP_TASK,
                        menuItemKind = 'Check',
                        helpString = messages.STAMP_TASK_HELP),
                    MenuItem.template('StampEventItem',
                        event = main.FocusStampCalendar,
                        title = messages.STAMP_CALENDAR,
                        menuItemKind = 'Check',
                        helpString = messages.STAMP_CALENDAR_HELP),
                    MenuItem.template('ItemSeparator3',
                        menuItemKind = 'Separator'),
                    MenuItem.template('NeverShareItem',
                        event = main.FocusTogglePrivate,
                        title = messages.PRIVATE,
                        menuItemKind = 'Check',
                        helpString = _(u'Mark the selected item as private, so it will not be shared')),
                    ]), # Menu ItemMenu
            Menu.template('CollectionMenu',
                title = _(u'&Collection'),
                childrenBlocks = [
                    MenuItem.template('NewCollectionItem',
                        event = main.NewCollection,
                        eventsForNamedLookup = [main.NewCollection],
                        title = _(u'&New Collection'),
                        helpString = _(u'Create a new Collection')),
                    MenuItem.template('RenameItem',
                        event = globalBlocks.Rename,
                        title = _(u'&Rename'),
                        helpString = _(u'Rename the selected collection')),
                    MenuItem.template('CollectionSeparator1',
                        menuItemKind = 'Separator'),
                    Menu.template('CollectionColorMenu',
                        title = _(u'&Collection Color'),
                        childrenBlocks = makeColorMenuItems(parcel,
                                                            MenuItem,
                                                            usercollections.collectionHues)),
                    MenuItem.template('CollectionSeparator2',
                        menuItemKind = 'Separator'),
                    
                    MenuItem.template('ToggleMineItem',
                        event = main.ToggleMine,
                        title = _(u'Toggle mine/not-mine'),
                        helpString = _(u'Toggle mine/not-mine')),
                    ]), # Menu CollectionMenu
            Menu.template('ShareMenu',
                title = _(u'&Share'),
                childrenBlocks = [
                    MenuItem.template('SyncCollectionItem',
                        event = main.SyncCollection,
                        title = _(u'Sync'),
                        helpString = _(u"Synchronize a shared collection")),
                    Menu.template('SyncMenu',
                        title = _(u'Sync &All'),
                        childrenBlocks = [
                            MenuItem.template('SyncAllItem',
                                event = main.SyncAll,
                                title = _(u"&All"),
                                helpString = _(u'Sync All')),
                            MenuItem.template('SyncIMAPItem',
                                event = main.GetNewMail,
                                title = _(u'&Mail'),
                                helpString = _(u'Sync Mail')),
                            MenuItem.template('SyncWebDAVItem',
                                event = main.SyncWebDAV,
                                title = _(u'&Shares'),
                                helpString = _(u'Sync Shares')),
                            ]), # Menu SyncMenu
                    MenuItem.template('TakeOnlineOfflineItem',
                        event = main.TakeOnlineOffline,
                        title = _(u'Online/Offline status'),
                        helpString = _(u"Toggle the collection's online status")),
                    MenuItem.template('SyncPrefsItem',
                        event = main.SyncPrefs,
                        title = _(u'Set Auto-sync inter&vals...'),
                        helpString = _(u'Change synchronization preferences')),
                    
                    MenuItem.template('ShareSeparator1',
                        menuItemKind = 'Separator'),

                    MenuItem.template('SharingSubscribeToCollectionItem',
                        event = main.SharingSubscribeToCollection,
                        title = _(u'&Subscribe...'),
                        helpString = _(u'Subscribe to a published collection')),
                    MenuItem.template('UnsubscribeSidebarCollectionItem',
                        event = main.UnsubscribeSidebarCollection,
                        title = _(u'&Unsubscribe'),
                        helpString = _(u'Unsubscribe the selected collection')),
                    MenuItem.template('ShareSidebarCollectionItem',
                        event = main.ShareSidebarCollection,
                        title = _(u'Publish'),
                        helpString = _(u'Share the selected collection')),
                    MenuItem.template('UnpublishSidebarCollectionItem',
                        event = main.UnpublishSidebarCollection,
                        title = _(u'Unpublish'),
                        helpString = _(u'Remove the collection from the sharing server')),
                    MenuItem.template('ManageSidebarCollectionItem',
                        event = main.ManageSidebarCollection,
                        title = _(u'&Manage share...'),
                        helpString = _(u'Manage the selected collection')),
                    MenuItem.template('RestoreSharesItem',
                        event = main.RestoreShares,
                        title = _(u'&Restore published shares...'),
                        helpString = _(u'Restore previously published shares')),
                    
                    MenuItem.template('ShareSeparator2',
                        menuItemKind = 'Separator'),

                    MenuItem.template('CopyCollectionURLItem',
                        event = main.CopyCollectionURL,
                        title = _(u'&Copy URL(s) to clipboard'),
                        helpString = _(u"Copy the selected collection's URL(s) to the clipboard")),
                    MenuItem.template('ShareSeparator3',
                        menuItemKind = 'Separator'),
                    
                    Menu.template('FreeBusyMenu',
                        title = _(u'&FreeBusy'),
                        childrenBlocks = [
                            MenuItem.template('SharingPublishFreeBusyItem',
                                              event = main.SharingPublishFreeBusy,
                                              title = _(u'&Publish'),
                                              helpString = _(u'Publish Free/Busy information')),
                            MenuItem.template('SharingUnpublishFreeBusyItem',
                                              event = main.SharingUnpublishFreeBusy,
                                              title = _(u'&Unpublish'),
                                              helpString = _(u'Unpublish Free/Busy information')),
                            MenuItem.template('CopyFreeBusyURLItem',
                                              event = main.CopyFreeBusyURL,
                                              title = _(u'&Copy URL to clipboard'),
                                              helpString = _(u"Copy Free/Busy URL to the clipboard")),
                        ]), # Menu FreebusyMenu
                    ]), # Menu CollectionMenu
            Menu.template('ExperimentalMenu',
                title = _(u'&Experimental'),
                childrenBlocks = [
                    ]), # Menu ExperimentalMenu
            Menu.template('TestMenu',
                title = _(u'&Test'),
                childrenBlocks = [
                    MenuItem.template('GenerateSomeDataItem',
                        event = main.GenerateContentItems,
                        title = u'&Generate Data',
                        helpString = u'generates a few items of each kind'),
                    MenuItem.template('GenerateMuchDataItem',
                        event = main.GenerateContentItems,
                        title = u'G&enerate Lots of Data',
                        helpString = u'generates many items of each kind'),
                    MenuItem.template('GenerateDataItemFromFile',
                        event = main.GenerateContentItemsFromFile,
                        title = u'Generate Items from a &file',
                        helpString = u'generates Items from a file'),
                    MenuItem.template('TestSeparator1', menuItemKind='Separator'),
                    MenuItem.template('ShowBlockViewerItem',
                        event = main.ShowBlockViewer,
                        eventsForNamedLookup = [main.ShowBlockViewer],
                        title = u'Show Block Viewer',
                        helpString = u'Opens the Block Viewer'),
                    MenuItem.template('ShowRepositoryViewerItem',
                        event = main.ShowRepositoryViewer,
                        eventsForNamedLookup = [main.ShowRepositoryViewer],
                        title = u'Show Repository Viewer',
                        helpString = u'Opens the Repository Viewer'),
                    MenuItem.template('TestSeparator2', menuItemKind='Separator'),
                    MenuItem.template('ReloadParcelsItem',
                        event = main.ReloadParcels,
                        title = u'Reload Par&cels',
                        accel = u'Ctrl+R',
                        helpString = u'Reloads any parcels that have been modified'),
                    MenuItem.template('ReloadStylesItem',
                        event = main.ReloadStyles,
                        title = u'Reload St&yles',
                        helpString = u'Reloads styles'),                    
                    MenuItem.template('TestSeparator3', menuItemKind='Separator'),
                    MenuItem.template('RunSelectedScriptItem',
                        event = main.RunSelectedScript,
                        title = u'R&un a Script',
                        accel = u'Ctrl+S',
                        helpString = u'Run the CPIA Script from the Detail View'),
                    MenuItem.template("AddScriptsSetItem",
                        event = main.AddScriptsToSidebar,
                        title = u"A&dd Scripts to Sidebar",
                        helpString = u'Add Scripts to the Sidebar'),
                    MenuItem.template('ShowPyShellItem',
                        event = main.ShowPyShell,
                        title = u'&Show Python shell...',
                        helpString = u'Brings up an interactive Python shell'),
                    MenuItem.template('ShowPyCrustItem',
                        event = main.ShowPyCrust,
                        title = u'Show Python shell with &object browser...',
                        helpString = u'Brings up an interactive Python shell and object browser'),
                    MenuItem.template('SaveSettingsItem',
                        event = main.SaveSettings,
                        title = u'Save settings...',
                        helpString = u'Saves your accounts and shares'),
                    MenuItem.template('RestoreSettingsItem',
                        event = main.RestoreSettings,
                        title = u'Restore settings...',
                        helpString = u'Restores your accounts and shares'),
                    MenuItem.template('ActivateWebserverItem',
                        event = main.ActivateWebserver,
                        title = u'Activate built-in webserver',
                        helpString = u'Activates the built-in webserver at localhost:1888'),
                    MenuItem.template('TestSeparator4', menuItemKind='Separator'),
                    Menu.template('RepositoryTestMenu',
                        title=u'&Repository',
                        helpString=u'Repository stuff',
                        childrenBlocks = [
                            MenuItem.template('CheckRepositoryItem',
                                event = main.CheckRepository,
                                title = u'C&heck Repository',
                                helpString = u'run check() on the main view'),
                            MenuItem.template('CheckAndRepairRepositoryItem',
                                event = main.CheckAndRepairRepository,
                                title = u'Check and &Repair Repository',
                                helpString = u'run check(True) on the main view'),
                            MenuItem.template('CompactRepositoryItem',
                                event = main.CompactRepository,
                                title = u'C&ompact Repository',
                                helpString = u'compact the repository'),
                            MenuItem.template('IndexRepositoryItem',
                                event = main.IndexRepository,
                                title = u'Index Repository',
                                helpString = u'tickle the indexer'),
                    ]),
                    Menu.template('ProfilingMenu',
                        title=u'&Profiling',
                        childrenBlocks = [
                            MenuItem.template('StartProfilerItem',
                                event = main.StartProfiler,
                                title = u'Start Event Profiler',
                                helpString = u'Start profiling CPIA events'),
                            MenuItem.template('StopProfilerItem',
                                event = main.StopProfiler,
                                title = u'Stop Event Profiler',
                                helpString = u'Stop CPIA Event Profiler'),
                            ]),

                    Menu.template('LoggingMenu',
                        title=u'&Logging',
                        childrenBlocks = [
                            MenuItem.template('ShowLogWindowItem',
                                event = main.ShowLogWindow,
                                title = u'&Show log window',
                                helpString = u'Displays the contents of chandler.log and twisted.log'),
                            Menu.template('LoggingLevelMenu',
                                title = u'Logging level',
                                helpString = u'Change logging level',
                                childrenBlocks = [
                                    MenuItem.template('LoggingLevelCriticalMenuItem',
                                        event = main.SetLoggingLevelCritical,
                                        title = u'Critical',
                                        menuItemKind = 'Check',
                                        helpString = u'Set logging level to Critical'),
                                    MenuItem.template('LoggingLevelErrorMenuItem',
                                        event = main.SetLoggingLevelError,
                                        title = u'Error',
                                        menuItemKind = 'Check',
                                        helpString = u'Set logging level to Error'),
                                    MenuItem.template('LoggingLevelWarningMenuItem',
                                        event = main.SetLoggingLevelWarning,
                                        title = u'Warning',
                                        menuItemKind = 'Check',
                                        helpString = u'Set logging level to Warning'),
                                    MenuItem.template('LoggingLevelInfoMenuItem',
                                        event = main.SetLoggingLevelInfo,
                                        title = u'Info',
                                        menuItemKind = 'Check',
                                        helpString = u'Set logging level to Info'),
                                    MenuItem.template('LoggingLevelDebugMenuItem',
                                        event = main.SetLoggingLevelDebug,
                                        title = u'Debug',
                                        menuItemKind = 'Check',
                                        helpString = u'Set logging level to Debug'),
                                    ]), # Menu SkinsMenu
                            ]),

                    Menu.template('I18nMenu',
                        title=u'i18n',
                        childrenBlocks = [
                            MenuItem.template('ShowI18nManagerDebugItem',
                                event = main.ShowI18nManagerDebugWindow,
                                title = u'Show I18nManager debug window',
                                helpString = u'Displays a tree of projects, locales, resources, and gettext localizations'),
                            ]),

                    Menu.template('ShareTestMenu',
                        title = u'S&haring',
                        helpString = u'Sharing-related test commands',
                        childrenBlocks = [
                            MenuItem.template('EditMyNameItem',
                                event = main.EditMyName,
                                title = u'&Edit your name',
                                helpString = u'Edit your name'),
                            MenuItem.template('BackgroundSyncAllItem',
                                event = main.BackgroundSyncAll,
                                title = u'Start a &background sync now',
                                helpString = u'Initiates a single background sync'),
                            MenuItem.template('BackgroundSyncGetOnlyItem',
                                event = main.BackgroundSyncGetOnly,
                                title = u'Start a GET-only &background sync of current collection',
                                helpString = u'Initiates a single background sync without writing to server'),
                            MenuItem.template('ToggleReadOnlyModeItem',
                                event = main.ToggleReadOnlyMode,
                                title = u'Read-only sharing mode',
                                menuItemKind = 'Check',
                                helpString = u'Forces all sharing to be done in read-only mode'),
                            MenuItem.template("AddSharingLogItem",
                                event = main.AddSharingLogToSidebar,
                                title = u"A&dd sharing activity log to Sidebar",
                                helpString = u'Add sharing activity log to the Sidebar'),
                            MenuItem.template('SharingImportDemoCalendarItem',
                                event = main.SharingImportDemoCalendar,
                                title = u'Import demo calendar',
                                helpString = u'Import a demo iCalendar file from osafoundation.org'),
                            ]), # Menu ShareMenu
                    Menu.template('SkinsMenu',
                        title = u'S&kins',
                        helpString = u'Change user-interface skin',
                        childrenBlocks = [
                            MenuItem.template('ChandlerSkinMenuItem',
                                event = main.ChooseChandlerMainView,
                                title = u'Chandler',
                                menuItemKind = 'Check',
                                helpString = u'Switch to Chandler'),
                            MenuItem.template('CPIATestMenuItem',
                                event = main.ChooseCPIATestMainView,
                                title = u'CPIA Test',
                                menuItemKind = 'Check',
                                helpString = u'Switch to CPIA test'),
                            MenuItem.template('CPIATest2MenuItem',
                                event = main.ChooseCPIATest2MainView,
                                title = u'CPIA Test 2',
                                menuItemKind = 'Check',
                                helpString = u'Switch to CPIA test 2'),
                            ]), # Menu SkinsMenu
                    Menu.template('MailTests',
                        title = u'Mail Tests',
                        childrenBlocks = [
                            MenuItem.template('MeAddressDebugItem',
                                event = main.ShowMeAddressCollectionDebugWindow,
                                title = u'Show Me Address Collection',
                                helpString = u'Displays all active and old me addresses used to determine the fromMe and toMe attributes on Content Item'),
                            MenuItem.template('MimeTestItem',
                                event = main.MimeTest,
                                title = u'Load MIME Torture Tests',
                                helpString = u'Loads real world complex / broken mime message examples provided by Anthony Baxter'),
                            MenuItem.template('i18nMailTestItem',
                                event = main.i18nMailTest,
                                title = u'Load i18n Mail Tests',
                                helpString = u'Loads mail messages containing a variety of Charsets and Languages'),
                            MenuItem.template('TakMailOnlineOfflineItem',
                                event = main.TakeMailOnlineOffline,
                                title = u'Take Mail Offline',
                                helpString = u'Toggle the mail online status'),
                            ]),

                    MenuItem.template('TestSeparator5', menuItemKind='Separator'),
                    MenuItem.template('WxTestHarnessItem',
                        event = main.WxTestHarness,
                        title = u'&Wx Test Harness',
                        helpString = u'invoke the current flavor of wx debugging'),
                    ]), # Menu TestMenu
            Menu.template('HelpMenu',
                title = _(u'&Help'),
                childrenBlocks = [
                    MenuItem.template('AboutChandlerItem',
                        event = globalBlocks.About,
                        title = _(u'&About Chandler'),
                        helpString = _(u'About Chandler...'),
                        wxId = wx.ID_ABOUT),
                     MenuItem.template('HelpMenuItem',
                        event = globalBlocks.Help,
                        title = _(u'Chandler &FAQ'),
                        helpString =
                             _(u'Open Chandler FAQ in your web browser'),
                        accel = _(u'Ctrl+?')),
                    ]) # Menu HelpMenu
            ]).install (parcel) # MenuBar MenuBar
