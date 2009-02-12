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

from application.Plugins import PluginMenu, DemoMenu
from application import schema
import wx
from colorsys import hsv_to_rgb
from osaf.pim.structs import ColorType
from osaf.framework.blocks import BlockEvent, ColorEvent
from datetime import timedelta

def makeColorMenuItems (parcel, theClass, hues, prefix=""):
    """
    dynamically creates an array of type 'theClass' based on a list of colors
    """
    menuItems = []
    
    # make sure that all the events end up in the main parcel
    parcelLocation = "osaf.views.main"
    mainParcel = schema.parcel_for_module (parcelLocation, parcel.itsView)
    nameSpace = schema.ns (parcelLocation, parcel.itsView)

    for shortName, title, hue in hues:
        
        eventName = shortName + 'CollectionColor'
        colorEvent = getattr (nameSpace, eventName, None)
        if colorEvent is None:
            rgb = hsv_to_rgb(hue/360.0, 0.5, 1.0)
            rgb = [int(c*255) for c in rgb] + [255]
    
            colorEvent = ColorEvent.template(
                eventName,
                dispatchToBlockName = 'Sidebar',
                color = ColorType (*rgb),
                methodName = 'onCollectionColorEvent').install (mainParcel)

        menuItem = theClass.template(
            prefix + shortName + 'ColorItem',
            title = title, # XXX No keyboard shortcuts
            icon = shortName + "MenuIcon.png",
            menuItemKind = "Check",
            event = colorEvent)
        menuItems.append (menuItem)

    return menuItems

def makeMainMenus(parcel):

    from osaf.framework.blocks import Menu, MenuItem, IntervalEvent
    from osaf.framework.blocks.calendar import VisibleHoursEvent, WeekStartEvent
    from i18n import ChandlerMessageFactory as _
    from osaf import messages
    from osaf import usercollections
    from itertools import chain

    if wx.Platform == '__WXMAC__':
        # L10N: Keyboard shortcut to remove an
        # Item from a collection on OS X
        platform_remove = _(u'Back')
        # L10N: Keyboard shortcut to delete (move Item
        #       to Trash) on OS X.
        platform_delete = _(u'Ctrl+Back')
    else:
        # L10N: Keyboard shortcut to remove an
        # Item from a collection on Windows and Linux
        platform_remove = _(u'Del')
        # L10N: Keyboard shortcut to delete (move Item
        #       to Trash) on Windows and Linux.
        platform_delete = _(u'Ctrl+Del')

    
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

        hoursText = {
            # L10N: The number of visible hours to display in the Calendar week view
            5: _(u"&5 hours"),
            # L10N: The number of visible hours to display in the Calendar week view
            6: _(u"&6 hours"),
            # L10N: The number of visible hours to display in the Calendar week view
            7: _(u"&7 hours"),
            # L10N: The number of visible hours to display in the Calendar week view
            8: _(u"&8 hours"),
            # L10N: The number of visible hours to display in the Calendar week view
            9: _(u"&9 hours"),
            # L10N: The number of visible hours to display in the Calendar week view
            10: _(u"&10 hours"),
            # L10N: The number of visible hours to display in the Calendar week view
            11: _(u"11 &hours"),
            # L10N: The number of visible hours to display in the Calendar week view
            12: _(u"12 h&ours"),
            # L10N: The number of visible hours to display in the Calendar week view
            18: _(u"18 ho&urs"),
            # L10N: The number of visible hours to display in the Calendar week view
            24: _(u"&24 hours")
        }

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
                title = _(u"&Default")
            else:
                title = hoursText[hour]

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

    def iterWeekStartItems(parcel):
        import PyICU

        def addMnemonic(title, used):
            for index, character in enumerate(title):
                if (character.isalpha() and
                    not character.lower() in usedMnemonics):
                    usedMnemonics.add(character.lower())
                    return u"%s&%s" % (title[:index], title[index:])
            return title

        usedMnemonics = set()
        for dayNum, dayName in enumerate(
                                PyICU.DateFormatSymbols().getWeekdays()):
            if dayName:
                title = addMnemonic(dayName, usedMnemonics)
                event = WeekStartEvent.update(
                            parcel,
                            u"WeekStartEvent_%d" % (dayNum,),
                            methodName="onWeekStartEvent",
                            icuDay=dayNum)
                yield MenuItem.template(u"WeekStartItem_%d" % (dayNum,),
                                        title=title, menuItemKind="Check",
                                        event=event)

    repositoryView = parcel.itsView
    main = schema.ns("osaf.views.main", repositoryView)
    globalBlocks = schema.ns("osaf.framework.blocks", repositoryView)
    calBlocks = schema.ns("osaf.framework.blocks.calendar", repositoryView)

    fileMenu =  Menu.template('FileMenu',
                title = _(u'&File'),
                childBlocks = [
                    Menu.template('ImportMenu',
                        title=_(u'&Import'),
                        childBlocks=[
                            MenuItem.template('ImportICalendarItem',
                                event = main.ImportICalendar,
                                title = _(u'&Tasks and Events from .ics File...'),
                                helpString = _(u'Import Tasks and Events from iCalendar (.ics) file')),
                            MenuItem.template('ReloadFromFileItem',
                                event = main.ReloadFromFile,
                                title = _(u'&Reload Chandler Data from .chex File...'),
                                helpString = _(u'Reload your data to move to a new version of Chandler')),
                        ]),
                    Menu.template('ExportMenu',
                        title=_(u'&Export'),
                        childBlocks=[
                            MenuItem.template('ExportICalendarItem',
                                event = main.ExportICalendar,
                                title = _(u'Notes and &Events to .ics File...'),
                                helpString = _(u'Export Notes and Events to iCalendar (.ics) file')),
                            MenuItem.template('DumpToFileItem',
                                event = main.DumpToFile,
                                title = _(u'&Chandler Data to .chex File...'),
                                helpString = _(u'Export your data to move to a new version of Chandler')),
                        ]),
                    MenuItem.template('FileSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('PrefsAccountsItem',
                        event = main.EditAccountPreferences,
                        title = _(u'&Accounts...'),
                        helpString = messages.ACCOUNT_PREFERENCES),
                    MenuItem.template('ProtectPasswordsItem',
                        event = main.ProtectPasswords,
                        title = _(u'Protect Pass&words...'),
                        helpString = _(u'Protect your account passwords with a master password')),
                    MenuItem.template('ProxyConfigItem',
                        event = main.ConfigureProxies,
                        title = _(u'&Configure HTTP Proxy...'),
                        helpString = _(u'Configure HTTP Proxy')),
                    MenuItem.template('FileSeparator2',
                        menuItemKind = 'Separator'),
                    Menu.template('SyncMenu',
                        title = _(u'S&ync'),
                        childBlocks = [
                            MenuItem.template('SyncCollectionItem',
                                event = main.SyncCollection,
                                title = _(u'S&ync'),
                                helpString = _(u"Sync selected collection")),
                            MenuItem.template('SyncAllItem',
                                event = main.SyncAll,
                                title = _(u"&All"),
                                helpString = _(u'Sync mail and all shared collections')),
                            MenuItem.template('SyncIMAPItem',
                                event = main.GetNewMail,
                                title = _(u'&Mail'),
                                helpString = _(u'Sync mail')),
                            MenuItem.template('SyncWebDAVItem',
                                event = main.SyncWebDAV,
                                title = _(u'&Shares'),
                                helpString = _(u'Sync all shared collections')),
                            MenuItem.template('SyncSeparator',
                                menuItemKind = 'Separator'),
                            MenuItem.template('SyncManagerItem',
                                event = main.SyncManager,
                                title = _(u'Sy&nc Mana&ger...'),
                                helpString = _(u'Open the Sync Manager dialog')),
                            MenuItem.template('SyncPrefsItem',
                                event = main.SyncPrefs,
                                title = _(u'Set Au&to-sync...'),
                                helpString = _(u'Set auto-sync intervals')),
                            ]), # Menu SyncMenu
                    Menu.template('OfflineMenu',
                        title = _(u'Suspend Syncin&g'),
                        childBlocks = [
                            MenuItem.template('TakeOnlineOfflineItem',
                                event = main.TakeOnlineOffline,
                                title = _(u'Sus&pend Syncing'),
                                menuItemKind = 'Check',
                                helpString = _(u"Take mail and shared collections offline or online")),
                            MenuItem.template('AllOfflineItem',
                                event = main.TakeAllOnlineOffline,
                                menuItemKind = 'Check',
                                title = _(u'&All'),
                                helpString = _(u'Take mail and shared collections offline or online')),
                            MenuItem.template('TakeMailOnlineOfflineItem',
                                event = main.TakeMailOnlineOffline,
                                menuItemKind = 'Check',
                                title = _(u'&Mail'),
                                helpString = _(u'Take mail offline or online')),
                            MenuItem.template('SharesOfflineItem',
                                event = main.TakeSharesOnlineOffline,
                                menuItemKind = 'Check',
                                title = _(u'&Shares'),
                                helpString = _(u'Take shared collections offline or online')),
                            ]), # Menu OfflineMenu              
                    MenuItem.template('FileSeparator3',
                        menuItemKind = 'Separator'),
                    MenuItem.template('EnableTimezonesItem',
                        event = main.EnableTimezones,
                        title = _(u'Use Time &Zones'),
                        menuItemKind = 'Check',
                        helpString = _(u'Turn on time zone support')),
                    MenuItem.template('LocalePickerItem',
                        event = main.LocalePicker,
                        title = _(u'Swi&tch Language...'),
                        helpString = _(u'Select the language for Chandler')),
                    MenuItem.template('FileSeparator4',
                        menuItemKind = 'Separator'),
                    MenuItem.template('PrintPreviewItem',
                        event = globalBlocks.PrintPreview,
                        title = _(u'Print Pre&view...'),
                        wxId = wx.ID_PREVIEW),
                    MenuItem.template('PageSetupItem',
                        event = globalBlocks.PageSetup,
                        title = _(u'Page Set&up...'),
                        # L10N: Keyboard shortcut to launch Printing
                        #       Page Setup.
                        accel = _(u'Shift+Ctrl+P')),
                    MenuItem.template('PrintItem',
                        event = globalBlocks.Print,
                        title = _(u'&Print...'),
                        # L10N: Keyboard shortcut for Printing.
                        accel = _(u'Ctrl+P'),
                        helpString = _(u'Print the selected collection'),
                        wxId = wx.ID_PRINT),
                    MenuItem.template('FileSeparator5',
                        menuItemKind = 'Separator'),
                    MenuItem.template('CommitView',
                        event = globalBlocks.CommitView,
                        title = _(u'&Save Changes'),
                        # L10N: Keyboard shortcut to save changes.
                        accel = _(u'Ctrl+S'),
                        wxId = wx.ID_SAVE),
                    ])

    fileChildren = fileMenu.attrs['childBlocks']
    if wx.Platform == '__WXMAC__':
        fileChildren[3:3] = (
            MenuItem.template('CloseItem',
                event = globalBlocks.Close,
                title = _(u'C&lose Window'),
                # L10N: Keyboard shortcut for "Close Window" on Mac
                accel = _(u'Ctrl+W'),
                wxId = wx.ID_CLOSE,
            ),
            MenuItem.template('FileSeparator99',
                menuItemKind = 'Separator'
            ),
        )

    else:
        fileChildren.append(MenuItem.template('QuitItem',
                                event=globalBlocks.Quit,
                                title = _(u'&Quit'),
                                # L10N: Keyboard shortcut to quit Chandler.
                                accel = _(u'Ctrl+Q'),
                                helpString = _(u'Quit Chandler'),
                                wxId = wx.ID_EXIT))

    helpChildren = [
        MenuItem.template('AboutChandlerItem',
            event = BlockEvent.update(parcel, 'About'),
            title = _(u'&About Chandler'),
            helpString = _(u'About Chandler...'),
            wxId = wx.ID_ABOUT),
         MenuItem.template('GettingStartedMenuItem',
            event = BlockEvent.update(parcel, 'GettingStarted'),
            title = _(u'Chandler Get &Started Guide'),
            helpString =
                 _(u'Open the Chandler Get Started Guide in your web browser')),
         MenuItem.template('HelpMenuItem',
            event = globalBlocks.Help,
            title = _(u'Chandler &FAQ'),
            helpString =
                 _(u'Open the Chandler FAQ in your web browser'),
            # L10N: Keyboard shortcut to open the Chandler FAQ in
            #       a web browser.
            accel = _(u'Ctrl+?')),
         MenuItem.template('AskForHelpMenuItem',
            event = BlockEvent.update(parcel, 'AskForHelp'),
            title = _(u'Ask for &Help'),
            helpString = _(u'Ask for help from the Chandler Users List')),
         MenuItem.template('SubscribeUserMenuItem',
            event = BlockEvent.update(parcel, 'SubscribeUser'),
            title = _(u'S&ubscribe to Chandler Users List'),
            helpString =
                 _(u'Subscribe to the Chandler Users mailing list to ask questions and give feedback')),
         MenuItem.template('FileBugMenuItem',
            event = BlockEvent.update(parcel, 'FileBug'),
            title = _(u'Report a &Bug'),
            helpString =
                 _(u'Open instructions on how to file a bug in your web browser')),
         MenuItem.template('ShowTipMenuItem',
            event = BlockEvent.update(parcel, 'ShowTip'),
            title = _(u'Show &Tips...'),
            helpString =
                 _(u'Learn more about how you can use Chandler!')),
        ]

    updateMenu = Menu.template('UpdateMenu',
        title=_(u"Chec&k for Updates"),
        childBlocks=[
            MenuItem.template(
                'CheckForUpdatesNowItem',
                title=_(u"&Now"),
                event=IntervalEvent.update(
                    parcel,
                    'CheckForUpdatesNowEvent',
                    interval=timedelta(0),
                    dispatchToBlockName='MainView',
                    methodName="onUpdateCheckEvent",
                )
            ),
            MenuItem.template(
                'UpdatesSeparator',
                menuItemKind="Separator"
            ),
            MenuItem.template(
                'CheckForUpdatesDailyItem',
                title=_(u"Every &Day"),
                menuItemKind = 'Check',
                event=IntervalEvent.update(
                    parcel,
                    'CheckForUpdatesDailyEvent',
                    interval=timedelta(days=1),
                    dispatchToBlockName='MainView',
                    methodName="onUpdateCheckEvent",
                )
            ),
            MenuItem.template(
                'CheckForUpdatesWeeklyItem',
                title=_(u"Every &Week"),
                menuItemKind = 'Check',
                event=IntervalEvent.update(
                    parcel,
                    'CheckForUpdatesWeeklyEvent',
                    interval=timedelta(days=7),
                    dispatchToBlockName='MainView',
                    methodName="onUpdateCheckEvent",
                )
            ),
            MenuItem.template(
                'CheckForUpdatesManuallyItem',
                title=_(u"Don't Check &Automatically"),
                menuItemKind = 'Check',
                event=IntervalEvent.update(
                    parcel,
                    'CheckForUpdatesManuallyEvent',
                    interval=timedelta(days=-1),
                    dispatchToBlockName='MainView',
                    methodName="onUpdateCheckEvent",
                )
            ),
        ]
    )
        
    if wx.Platform == '__WXMAC__':
        fileChildren.insert(2, updateMenu)
    else:
        helpChildren.insert(1, updateMenu)

    menubar = Menu.template('MenuBar',
        setAsMenuBarOnFrame = True,
        childBlocks = [
            fileMenu,
            Menu.template('EditMenu',
                title = _(u'&Edit'),
                childBlocks = [
                    MenuItem.template('UndoItem',
                        event = globalBlocks.Undo,
                        title = messages.UNDO,
                        # L10N: Keyboard shortcut to undo the last operation.
                        accel = _(u'Ctrl+Z'),
                        helpString = _(u"Can't Undo"),
                        wxId = wx.ID_UNDO),
                    MenuItem.template('RedoItem',
                        event = globalBlocks.Redo,
                        title = messages.REDO,
                        # L10N: Keyboard shortcut to redo the last operation.
                        accel = _(u'Ctrl+Y'),
                        helpString = _(u"Can't Redo"),
                        wxId = wx.ID_REDO),
                    MenuItem.template('EditSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('CutItem',
                        event = globalBlocks.Cut,
                        title = messages.CUT,
                        # L10N: Keyboard shortcut for cut.
                        accel = _(u'Ctrl+X'),
                        wxId = wx.ID_CUT),
                    MenuItem.template('CopyItem',
                        event = globalBlocks.Copy,
                        title = messages.COPY,
                        # L10N: Keyboard shortcut for copy.
                        accel = _(u'Ctrl+C'),
                        wxId = wx.ID_COPY),
                    MenuItem.template('PasteItem',
                        event = globalBlocks.Paste,
                        title = messages.PASTE,
                        # L10N: Keyboard shortcut for paste.
                        accel = _(u'Ctrl+V'),
                        wxId = wx.ID_PASTE),
                    MenuItem.template('SelectAllItem',
                        event = globalBlocks.SelectAll,
                        title = messages.SELECT_ALL,
                        # L10N: Keyboard shortcut for select all.
                        accel = _(u'Ctrl+A'),
                        helpString = _(u'Select All'),
                        wxId = wx.ID_SELECTALL),
                    MenuItem.template('EditSeparator2',
                        menuItemKind = 'Separator'),
                    MenuItem.template('SearchItem',
                        event = main.Search,
                        title = _(u'&Find'),
                        # L10N: Keyboard shortcut for find / search.
                        accel = _(u'Ctrl+F'),
                        helpString = _(u'Search'),
                        wxId = wx.ID_FIND),
                    MenuItem.template('SwitchToQuickEntryItem',
                        event = main.SwitchToQuickEntry,
                        title = _(u'Go to Quic&k Entry Field'),
                        # L10N: Keyboard shortcut to put focus on
                        #      the Quick Entry Field.
                        accel = _(u'Ctrl+K'),
                        helpString = _(u'Go to the Quick Entry Field'))
                    ]), # Menu EditMenu
            Menu.template('ViewMenu',
                title = _(u'&View'),
                childBlocks = [
                    MenuItem.template('ApplicationBarAllMenu',
                        event = main.ApplicationBarAll,
                        title = _(u'&All'),
                        menuItemKind = 'Check',
                        helpString = _(u'View all items')),
                    MenuItem.template('ApplicationBarTaskMenu',
                        event = main.ApplicationBarTask,
                        title = _(u'&Starred'),
                        menuItemKind = 'Check',
                        helpString = _(u'View starred items')),
                    MenuItem.template('ApplicationBarEventMenu',
                        event = main.ApplicationBarEvent,
                        title = _(u'Ca&lendar'),
                        menuItemKind = 'Check',
                        helpString = _(u'View events')),
                    MenuItem.template('ViewSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('TriageMenu',
                        event = main.Triage,
                        title = _(u'&Clean up'),
                        accel = _(u'F5'),
                        helpString = _(u'Sort items into correct Triage sections')),
                    MenuItem.template('ViewSeparator1.5',
                        menuItemKind = 'Separator'),
                    MenuItem.template('ViewAsCalendarIteminWeekView',
                        event = main.ViewAsWeekCalendar,
                        title = _(u'&Week View'),
                        menuItemKind = 'Check',
                        helpString = _(u'Go to the Calendar Week View')),
                    MenuItem.template('ViewAsCalendarIteminDayView',
                        event = main.ViewAsDayCalendar,
                        title = _(u'&Day View'),
                        menuItemKind = 'Check',
                        helpString = _(u'Go to Calendar Day View')),
                    MenuItem.template('ViewAsMultiWeekItem',
                        event = main.ViewAsMultiWeek,
                        title = _(u'&Multi Week View'),
                        menuItemKind = 'Check',
                        helpString = _(u'View as MultiWeek View')),
                    MenuItem.template('ViewSeparator1.6',
                        menuItemKind = 'Separator'),
                    MenuItem.template('GoToNextWeek',
                        event = calBlocks.GoToNext,
                        title = _(u'&Next Week'),
                        accel = _(u'Alt+Right'),
                        helpString = _(u'Jump to next week')),
                    MenuItem.template('GoToPrevWeek',
                        event = calBlocks.GoToPrev,
                        title = _(u'&Previous Week'),
                        accel = _(u'Alt+Left'),
                        helpString = _(u'Jump to previous week')),
                    MenuItem.template('GoToDate',
                        event = calBlocks.GoToDate,
                        title = _(u'&Go to Date...'),
                        # L10N: Keyboard shortcut to go to a specific date
                        #      on the Calendar.
                        accel = _(u'Ctrl+G'),
                        helpString = _(u'Go to a specific date on the Calendar')),
                    MenuItem.template('GoToToday',
                        event = calBlocks.GoToToday,
                        title = _(u'Go to T&oday'),
                        # L10N: Keyboard shortcut to go to today's date
                        #      on the Calendar.
                        accel = _(u'Ctrl+T'),
                        helpString = _(u'Navigate to today\'s date')),
                    MenuItem.template('ViewSeparator2',
                                      menuItemKind = 'Separator'),
                    MenuItem.template('SeparateItemWindowItem',
                        event=globalBlocks.InspectSelection,
                        title=_(u"Separate &Item Window"),
                        accel=_(u'Ctrl+I'),
                        helpString=_(u"View Item in its Own Window")),
                    MenuItem.template('ViewSeparator3',
                                       menuItemKind='Separator'),
                    Menu.template('VisibleHoursMenu',
                                  title = _(u'&Visible Hours'),
                                  childBlocks = \
                                  makeVisibleHourMenuItems(parcel)),
                    Menu.template('WeekStartMenu',
                                  title=_(u'&First Day of Week'),
                                  childBlocks=list(iterWeekStartItems(parcel))),
                    ]), # Menu ViewMenu
            Menu.template('ItemMenu',
                title = _(u'&Item'),
                childBlocks = [
                    Menu.template('NewItemMenu',
                        title = _(u'&New'),
                        helpString = _(u'Create a new item'),
                        childBlocks = [
                            MenuItem.template('NewItemItem',
                                event = main.NewItem,
                                # L10N: One of the possible titles for the  Item -> New -> New Item menu.
                                # This title changes based on the area selected in the Toolbar.
                                # The keyboard mnemonic should be the same for each alternative title.
                                title = _(u'Ne&w Item'),
                                # L10N: Keyboard shortcut to create a new Item.
                                #       The shortcut will either create a Note,
                                #       Task, Event, or Message depending on
                                #       what filter button is selected in the
                                #       Toolbar. The filter buttons are All,
                                #       Mail, Task, Calendar.
                                accel = _(u'Ctrl+N'),
                                helpString = _(u'Create a new item'),
                                wxId = wx.ID_NEW),
                            MenuItem.template('NewItemSeparator1',
                                menuItemKind = 'Separator'),
                            MenuItem.template('NewNoteItem',
                                event = main.NewNote,
                                title = _(u'New &Note'),
                                # L10N: Keyboard shortcut to create a new Note.
                                accel = _(u'Ctrl+Shift+N'),
                                helpString = _(u'Create a new Note')),
                            MenuItem.template('NewStarredNoteItem',
                                event = main.NewStarredNote,
                                title = _(u'New &Starred Note'),
                                # L10N: Keyboard shortcut to create a new Starred Note (a.k.a Task).
                                accel = _(u'Ctrl+Shift+S'),
                                helpString = _(u'Create a new Starred Note')),
                            MenuItem.template('NewMessageItem',
                                event = main.NewMailMessage,
                                title = _(u'New &Message'),
                                # L10N: Keyboard shortcut to create a new Message.
                                accel = _(u'Ctrl+Shift+M'),
                                helpString = _(u'Create a new Message')),
                            MenuItem.template('NewEventItem',
                                event = main.NewCalendar,
                                title = _(u'New &Event'),
                                # L10N: Keyboard shortcut to create a new Event.
                                accel = _(u'Ctrl+Shift+E'),
                                helpString = _(u'Create a new Event')),
                            ]), # Menu NewItemMenu
                    MenuItem.template('RemoveItem',
                        event = globalBlocks.Remove,
                        title = _(u'Remo&ve'),
                        accel = platform_remove,                        
                        helpString = _(u'Remove the selected item from the selected collection'),
                        wxId = wx.ID_REMOVE),
                    MenuItem.template('DeleteItem',
                        event = globalBlocks.Delete,
                        title = _(u'&Delete'),
                        accel = platform_delete,
                        helpString = _(u'Move the selected item to the Trash'),
                        wxId = wx.ID_DELETE),
                    MenuItem.template('ItemSeparator0',
                        menuItemKind = 'Separator'),
                    MenuItem.template('MarkAsReadItem',
                        event = main.MarkAsRead,
                        title = _(u"Mark As &Read"),
                        toggleTitle = _(u"Mark As Un&read"),
                        helpString = _(u"Mark all selected items as 'Read' or 'Unread'")),
                    MenuItem.template('ItemSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('StampMessageItem',
                        event = main.FocusStampMessage,
                        title = _(u"&Address Item"),
                        toggleTitle = _(u"Remove &Addresses"),
                        helpString = messages.STAMP_MAIL_HELP),
                    MenuItem.template('StampTaskItem',
                        event = main.FocusStampTask,
                        title = _(u"S&tar Item"),
                        toggleTitle = _(u"Remove S&tar"),
                        helpString = messages.STAMP_TASK_HELP),
                    MenuItem.template('StampEventItem',
                        event = main.FocusStampCalendar,
                        title = _(u"Add to Ca&lendar"),
                        toggleTitle = _(u"Remove from Ca&lendar"),
                        helpString = messages.STAMP_CALENDAR_HELP),
                    MenuItem.template('ItemSeparator2',
                        menuItemKind = 'Separator'),
                    MenuItem.template('SendMessageItem',
                        event = main.SendShareItem,
                        title = _(u'&Send'),
                        helpString = _(u'Send the selected message')),
                    MenuItem.template('ReplyMessageItem',
                        event = main.ReplyMessage,
                        title = _(u'Re&ply'),
                        # L10N: Keyboard shortcut to Reply to a message.
                        accel = _(u'Ctrl+R'),
                        helpString = _(u'Reply to the selected message')),
                    MenuItem.template('ReplyAllMessageItem',
                        event = main.ReplyAllMessage,
                        title = _(u'Repl&y All'),
                        # L10N: Keyboard shortcut to Reply-All to a message.
                        accel = _(u'Ctrl+Shift+R'),
                        helpString = _(u'Reply to all recipients of the selected message')),
                    MenuItem.template('ForwardMessageItem',
                        event = main.ForwardMessage,
                        title = _(u'For&ward'),
                        # L10N: Keyboard shortcut to Forward a message.
                        accel = _(u'Ctrl+Shift+F'),
                        helpString = _(u'Forward the selected message')),
                    # Hidden per bug 8999/9000
                    #MenuItem.template('ItemSeparator3',
                        #menuItemKind = 'Separator'),
                    #MenuItem.template('NeverShareItem',
                        #event = main.FocusTogglePrivate,
                        #title = _(u"Never S&hare"),
                        #menuItemKind = 'Check',
                        #helpString = _(u'Mark the selected item as private so it will never be shared')),
                    ]), # Menu ItemMenu
            Menu.template('CollectionMenu',
                title = _(u'&Collection'),
                childBlocks = [
                    MenuItem.template('NewCollectionItem',
                        event = main.NewCollection,
                        eventsForNamedLookup = [main.NewCollection],
                        title = _(u'&New'),
                        helpString = _(u'Create a new collection')),
                    MenuItem.template('CollectionSeparator1',
                        menuItemKind = 'Separator'),
                    MenuItem.template('CollectionRenameItem',
                        event = main.RenameCollection,
                        title = _(u'&Rename'),
                        helpString = _(u'Rename the selected collection')),
                    # Bug #8744: Suppress 'duplicate' from collection menu
                    #MenuItem.template('CollectionDuplicateItem',
                    #    event = main.DuplicateSidebarSelection,
                    #    title = _(u'Du&plicate'),
                    #    helpString = _(u'Duplicate the selected collection')),
                    MenuItem.template('CollectionDeleteItem',
                        event = main.DeleteCollection,
                        title = _(u'&Delete'),
                        helpString = _(u'Move the selected collection to the Trash')),
                    MenuItem.template('CollectionEmptyTrashItem',
                        event = main.EmptyTrash,
                        title = _(u'&Empty Trash'),
                        helpString = _(u'Delete all items from the Trash')),
                    MenuItem.template('CollectionSeparator2',
                        menuItemKind = 'Separator'),
                    Menu.template('CollectionColorMenu',
                        title = _(u'&Calendar Color'),
                        childBlocks = makeColorMenuItems(parcel,
                                                            MenuItem,
                                                            usercollections.collectionHues)),
                    MenuItem.template('CollectionSeparator3',
                        menuItemKind = 'Separator'),
                    MenuItem.template('CollectionToggleMineItem',
                        event = main.ToggleMine,
                        title = _(u'&Keep out of Dashboard'),
                        menuItemKind = 'Check',
                        helpString = _(u'Include or exclude the selected collection from the Dashboard')),
                    ]), # Menu CollectionMenu
            Menu.template('ShareMenu',
                title = _(u'&Share'),
                childBlocks = [
                    MenuItem.template('SubscribeToCollectionItem',
                        event = main.SubscribeToCollection,
                        title = _(u'&Subscribe...'),
                        helpString = _(u'Subscribe to a shared collection')),
                    MenuItem.template('UnsubscribeCollectionItem',
                        event = main.UnsubscribeCollection,
                        title = _(u'&Unsubscribe'),
                        helpString = _(u'Stop sharing the selected collection')),
                    MenuItem.template('PublishCollectionItem',
                        event = main.PublishCollection,
                        title = _(u'&Publish...'),
                        helpString = _(u'Publish the selected collection')),
                    MenuItem.template('UnpublishCollectionItem',
                        event = main.UnpublishCollection,
                        title = _(u'U&npublish'),
                        helpString = _(u'Remove the selected shared collection from the server')),
                    MenuItem.template('ManageSidebarCollectionItem',
                        event = main.ManageSidebarCollection,
                        title = _(u'&Manage...'),
                        helpString = _(u'Manage the selected shared collection')),
                    MenuItem.template('ShareSeparator2',
                        menuItemKind = 'Separator'),
                    MenuItem.template('CollectionInviteItem',
                        event = main.CollectionInvite,
                        title = _(u'&Invite...'),
                        helpString = _(u"Open the invitation URLs dialog")),
                    ]), # Menu ShareMenu
            Menu.template('ToolsMenu',
                title = _(u'&Debug'),
                childBlocks = [
                    Menu.template('LoggingMenu',
                        title=_(u'&Logging'),
                        childBlocks = [
                            MenuItem.template('ShowLogWindowItem',
                                event = main.ShowLogWindow,
                                title = _(u'Log &Window...'),
                                helpString = _(u'Displays the contents of chandler.log')),
                            Menu.template('LoggingLevelMenu',
                                title = _(u'Logging L&evel'),
                                helpString = _(u'Change logging level'),
                                childBlocks = [
                                    MenuItem.template('LoggingLevelCriticalMenuItem',
                                        event = main.SetLoggingLevelCritical,
                                        title = _(u'&Critical'),
                                        menuItemKind = 'Check',
                                        helpString = _(u'Set logging level to Critical')),
                                    MenuItem.template('LoggingLevelErrorMenuItem',
                                        event = main.SetLoggingLevelError,
                                        title = _(u'&Error'),
                                        menuItemKind = 'Check',
                                        helpString = _(u'Set logging level to Error')),
                                    MenuItem.template('LoggingLevelWarningMenuItem',
                                        event = main.SetLoggingLevelWarning,
                                        title = _(u'&Warning'),
                                        menuItemKind = 'Check',
                                        helpString = _(u'Set logging level to Warning')),
                                    MenuItem.template('LoggingLevelInfoMenuItem',
                                        event = main.SetLoggingLevelInfo,
                                        title = _(u'&Info'),
                                        menuItemKind = 'Check',
                                        helpString = _(u'Set logging level to Info')),
                                    MenuItem.template('LoggingLevelDebugMenuItem',
                                        event = main.SetLoggingLevelDebug,
                                        title = _(u'&Debug'),
                                        menuItemKind = 'Check',
                                        helpString = _(u'Set logging level to Debug')),
                                    ]), # Menu LoggingLevelMenu
                            ]), # Menu LoggingMenu
                    Menu.template('RepositoryTestMenu',
                        title=_(u'&Repository'),
                        helpString=_(u'Repository tools'),
                        childBlocks = [
                            MenuItem.template('CheckRepositoryItem',
                                event = main.CheckRepository,
                                title = _(u'&Check'),
                                helpString = _(u'Run check() on the main view')),
                            MenuItem.template('CheckAndRepairRepositoryItem',
                                event = main.CheckAndRepairRepository,
                                title = _(u'C&heck and Repair'),
                                helpString = _(u'Run check(True) on the main view')),
                            MenuItem.template('CompactRepositoryItem',
                                event = main.CompactRepository,
                                title = _(u'C&ompact'),
                                helpString = _(u'Purge the repository of obsolete data')),
                            MenuItem.template('IndexRepositoryItem',
                                event = main.IndexRepository,
                                title = _(u'&Index'),
                                # L10N: Lucene indexes the Repository
                                helpString = _(u'Tickle the indexer')),
                            MenuItem.template('ToolsRepositorySeparator1',
                                menuItemKind = 'Separator'),
                            MenuItem.template('BackupRepository',
                                event = globalBlocks.BackupRepository,
                                title = _(u'&Back up...')),
                            MenuItem.template('RestoreRepository',
                                event = globalBlocks.RestoreRepository,
                                title = _(u'&Restore...')),
                            MenuItem.template('ToolsRepositorySeparator2',
                                menuItemKind = 'Separator'),
                            MenuItem.template('NewRepositoryItem',
                                event = main.CreateRepository,
                                title = _(u'&New...')),
                            MenuItem.template('SwitchRepositoryItem',
                                event = main.SwitchRepository,
                                title = _(u'&Switch...')),
                        ]), # Menu RepositoryTestMenu
                    Menu.template('ShareTestMenu',
                        title = _(u'S&haring'),
                        helpString = _(u'Sharing-related test commands'),
                        childBlocks = [
                            MenuItem.template('ShowActivityViewerItem',
                                event = main.ShowActivityViewer,
                                title = _(u'Activity &Viewer...'),
                                helpString = _(u'Opens the Activity Viewer')),
                            MenuItem.template("AddSharingLogItem",
                                event = main.AddSharingLogToSidebar,
                                title = _(u"&Add Sharing Activity Log to Sidebar"),
                                helpString = _(u'Add Sharing Activity Log to the Sidebar')),
                            MenuItem.template("ResetShareItem",
                                event = main.ResetShare,
                                title = _(u"R&eset State of Shared Collection"),
                                helpString = _(u"Discards metadata about shared items")),
                            MenuItem.template("RecordSetDebuggingItem",
                                event = main.RecordSetDebugging,
                                title = _(u"Set S&haring Logging Level to Debug"),
                                helpString = _(u'Enable RecordSet Debugging')),
                            MenuItem.template("UnsubscribePublishedCollectionItem",
                                event = main.UnsubscribePublishedCollection,
                                title = _(u"&Unsubscribe from Published Shares"),
                                helpString = _(u"Stop syncing to a collection you published without removing it from the server")),
                            ]), # Menu ShareMenu
                    MenuItem.template('ToolsSeparator1',
                                      menuItemKind = 'Separator'),
                    MenuItem.template(
                        'CheckForTestUpdates',
                        title=_(u"Check for Test &Updates"),
                        event=IntervalEvent.update(
                            parcel,
                            'CheckForTestUpdatesEvent',
                            interval=timedelta(0),
                            dispatchToBlockName='MainView',
                            methodName="onTestUpdateCheckEvent",
                        )
                    ),
                    Menu.template(
                        'AutoRestore',
                        title=_(u"&Automatically Reload from Backup"),
                        childBlocks = [
                            MenuItem.template('ResetAutoUpdateItem',
                                              event = main.ResetAutoUpdate,
                                              title = _(u'&Next Reload: Never'),
                                              helpString = _(u'Click to reload from backup next time Chandler starts')),
                            MenuItem.template('EnableAutoUpdateItem',
                                              event = main.EnableAutoUpdate,
                                              title = _(u'&Enabled'),
                                              helpString = _(u'Automatically reload from backup every week'),
                                              menuItemKind = 'Check',)
                        ],
                    ),
                    DemoMenu.template('ExperimentalMenu',
                        title = _(u'&Plugins'),
                        childBlocks = [
                            MenuItem.template("BrowsePluginsMenuItem",
                                              event = main.BrowsePlugins,
                                              title = _(u"&Download"),
                                              helpString = _(u'Browse for new plugins')),
                            MenuItem.template('InstallPluginsMenuItem',
                                              event = main.InstallPlugins,
                                              title = _(u"I&nstall..."),
                                              helpString = _(u'Install plugins')),
                            PluginMenu.template('PluginsMenu',
                                                title=_(u'&Active'),
                                                helpString=_(u'Activate or Deactivate Plugins'),
                                                event = main.Plugin,
                                                childBlocks = []),
                        ]), # Menu ExperimentalMenu
                ]),
            Menu.template('HelpMenu',
                title = _(u'&Help'),
                childBlocks = helpChildren) # Menu HelpMenu
            ]).install (parcel) # Menu MenuBar

    Menu.template('SidebarContextMenu',
        title = _(u'Sidebar'),
        childBlocks = [
            MenuItem.template('SidebarNewCollectionItem',
                event = main.NewCollection,
                title = _(u'&New Collection'),
                helpString = _(u'Create a new collection')),
            MenuItem.template('SidebarSeparator1',
                menuItemKind = 'Separator'),
            MenuItem.template('SidebarRenameItem',
                event = main.RenameCollection,
                title = _(u'&Rename'),
                helpString = _(u'Rename the selected collection')),
            # Bug #8744: Suppress 'duplicate' from collection menu
            #MenuItem.template('SidebarDuplicateItem',
            #    event = main.DuplicateSidebarSelection,
            #    title = _(u'Du&plicate'),
            #    helpString = _(u'Duplicate the selected collection')),
            MenuItem.template('SidebarDeleteItem',
                event = main.DeleteCollection,
                title = _(u'&Delete'),
                helpString = _(u'Move the selected collection to the Trash')),
            MenuItem.template('SidebarEmptyTrashItem',
                event = main.EmptyTrash,
                title = _(u'&Empty Trash'),
                helpString = _(u'Delete all items from the Trash')),
            MenuItem.template('SidebarSeparator2',
                menuItemKind = 'Separator'),
            Menu.template('SidebarCollectionColorMenu',
                title = _(u'&Collection Color'),
                childBlocks = makeColorMenuItems(parcel,
                                                    MenuItem,
                                                    usercollections.collectionHues,
                                                    "Sidebar")),
            MenuItem.template('SidebarSeparator3',
                menuItemKind = 'Separator'),
            MenuItem.template('SidebarToggleMineItem',
                event = main.ToggleMine,
                title = _(u'&Keep out of Dashboard'),
                menuItemKind = 'Check',
                helpString = _(u'Include or Exclude the selected collection from the Dashboard')),
            MenuItem.template('SidebarSeparator4',
                menuItemKind = 'Separator'),
            MenuItem.template('SidebarSyncCollectionItem',
                event = main.SyncCollection,
                title = _(u'S&ync'),
                helpString = _(u"Sync the selected collection")),
            MenuItem.template('SidebarTakeOnlineOfflineItem',
                event = main.TakeOnlineOffline,
                menuItemKind = 'Check',
                title = _(u'Suspend Syncin&g'),
                helpString = _(u"Take the selected collection offline and online")),
            MenuItem.template('SidebarSyncIMAPItem',
                        event = main.GetNewMail,
                        title = _(u'Sync M&ail'),
                        helpString = _(u'Sync all mail accounts')),
            MenuItem.template('SidebarSyncWebDAVItem',
                        event = main.SyncWebDAV,
                        title = _(u'Sync S&hares'),
                        helpString = _(u'Sync all shared collections')),
            MenuItem.template('SidebarSeparator5',
                menuItemKind = 'Separator'),
            MenuItem.template('SidebarSubscribeToCollectionItem',
                event = main.SubscribeToCollection,
                title = _(u'&Subscribe...'),
                helpString = _(u'Subscribe to a shared collection')),
            MenuItem.template('SidebarUnsubscribeCollectionItem',
                event = main.UnsubscribeCollection,
                title = _(u'&Unsubscribe'),
                helpString = _(u'Stop sharing the selected collection')),
            MenuItem.template('SidebarPublishCollectionItem',
                event = main.PublishCollection,
                title = _(u'&Publish...'),
                helpString = _(u'Publish the selected collection')),
            MenuItem.template('SidebarUnpublishCollectionItem',
                event = main.UnpublishCollection,
                title = _(u'Unpu&blish'),
                helpString = _(u'Remove the selected shared collection from the server')),
            MenuItem.template('SidebarManageSidebarCollectionItem',
                event = main.ManageSidebarCollection,
                title = _(u'&Manage...'),
                helpString = _(u'Manage the selected shared collection')),
            MenuItem.template('SidebarCollectionInviteItem',
                event = main.CollectionInvite,
                title = _(u'&Invite...'),
                helpString = _(u"Open the invitation URLs dialog")),
            ]).install(parcel)

    Menu.template('ItemContextMenu',
        title = _(u'Item'),
        childBlocks = [
            Menu.template('ItemContextNewItemMenu',
                title = _(u'&New'),
                helpString = _(u'Create a new item'),
                childBlocks = [
                    MenuItem.template('ItemContextNewNoteItem',
                        event = main.NewNote,
                        title = _(u'&Note'),
                        # L10N: Keyboard shortcut to create a new Note.
                        accel = _(u'Ctrl+Shift+N'),
                        helpString = _(u'Create a new note')),
                    MenuItem.template('ItemContextNewStarredNoteItem',
                        event = main.NewStarredNote,
                        title = _(u'New &Starred Note'),
                        # L10N: Keyboard shortcut to create a new Starred Note (a.k.a Task).
                        accel = _(u'Ctrl+Shift+S'),
                        helpString = _(u'Create a new Starred Note')),
                    MenuItem.template('ItemContextNewMessageItem',
                        event = main.NewMailMessage,
                        title = _(u'&Message'),
                        # L10N: Keyboard shortcut to create a new Message.
                        accel = _(u'Ctrl+Shift+M'),
                        helpString = _(u'Create a new message')),
                    MenuItem.template('ItemContextNewEventItem',
                        event = main.NewCalendar,
                        title = _(u'&Event'),
                        # L10N: Keyboard shortcut to create a new Event.
                        accel = _(u'Ctrl+Shift+E'),
                        helpString = _(u'Create a new event')),
                    ]),
            MenuItem.template('ItemContextCutItem',
                event = main.CutInActiveView,
                title = messages.CUT),
            MenuItem.template('ItemContextCopyItem',
                event = main.CopyInActiveView,
                title = messages.COPY),
            MenuItem.template('ItemContextDuplicateItem',
                event = main.DuplicateInActiveView,
                title = _(u'D&uplicate'),
                helpString = _(u'Duplicate the selected item')),
            MenuItem.template('ItemContextPasteItem',
                event = main.PasteInActiveView,
                title = messages.PASTE),
            MenuItem.template('ItemContextRemoveItem',
                event = main.RemoveInActiveView,
                title = _(u'Remo&ve'),
                accel = platform_remove,
                helpString = _(u'Remove the selected items from the selected collection')),                    
            MenuItem.template('ItemContextDeleteItem',
                event = main.DeleteInActiveView,
                title = _(u'&Delete'),
                accel = platform_delete,                        
                helpString = _(u'Move the selected item to the Trash')),
            MenuItem.template('ItemContextSeparator0',
                menuItemKind = 'Separator'),
            MenuItem.template('ItemContextMarkAsReadItem',
                event = main.MarkAsRead,
                title = _(u"&Mark As Read"),
                toggleTitle = _(u"&Mark As Unread"),
                helpString = _(u"Mark all selected items as 'Read' or 'Unread'")),
            MenuItem.template('ItemContextSeparator1',
                menuItemKind = 'Separator'),
            MenuItem.template('ItemContextStampMessageItem',
                event = main.FocusStampMessage,
                title = _(u"Addr&ess Item"),
                toggleTitle = _(u"Remove Addr&esses"),
                helpString = messages.STAMP_MAIL_HELP),
            MenuItem.template('ItemContextStampTaskItem',
                event = main.FocusStampTask,
                title = _(u"Sta&r Item"),
                toggleTitle = _(u"Remove Sta&r"),
                helpString = messages.STAMP_TASK_HELP),
            MenuItem.template('ItemContextStampEventItem',
                event = main.FocusStampCalendar,
                title = _(u"Add to Ca&lendar"),
                toggleTitle = _(u"Remove from Ca&lendar"),
                helpString = messages.STAMP_CALENDAR_HELP),
            MenuItem.template('ItemContextSeparator2',
                menuItemKind = 'Separator'),
            MenuItem.template('ItemContextSendMessageItem',
                event = main.SendShareItem,
                title = _(u'&Send'),
                helpString = _(u'Send the selected message')),
            MenuItem.template('ItemContextReplyMessageItem',
                event = main.ReplyMessage,
                title = _(u'Repl&y'),
                helpString = _(u'Reply to the selected message')),
            MenuItem.template('ItemContextReplyAllMessageItem',
                event = main.ReplyAllMessage,
                title = _(u'Reply &All'),
                helpString = _(u'Reply to all recipients of the selected message')),
            MenuItem.template('ItemContextForwardMessageItem',
                event = main.ForwardMessage,
                title = _(u'For&ward'),
                helpString = _(u'Forward the selected message')),
            # Hidden per bug 8999/9000
            #MenuItem.template('ItemContextSeparator3',
                #menuItemKind = 'Separator'),
            #MenuItem.template('ItemContextNeverShareItem',
                #event = main.FocusTogglePrivate,
                #title = _(u"Never S&hare"),
                #menuItemKind = 'Check',
                #helpString = _(u'Mark the selected item as private so it will never be shared')),
            MenuItem.template('ItemContextSeparator3',
                              menuItemKind='Separator'),
            MenuItem.template('ContextSeparateItemWindowItem',
                event=globalBlocks.InspectSelection,
                title=_(u"Separate &Item Window"),
                helpString=_(u"View Item in its Own Window")),
            ]).install(parcel)

    Menu.template('DragAndDropTextCtrlContextMenu',
        title = _(u'TextMenu'),
        childBlocks = [
            MenuItem.template('TextContextUndoItem',
                event = globalBlocks.Undo,
                title = messages.UNDO,
                wxId = wx.ID_UNDO),
            MenuItem.template('TextContextRedoItem',
                event = globalBlocks.Redo,
                title = messages.REDO,
                wxId = wx.ID_REDO),
            MenuItem.template('TextContextSeparator1',
                menuItemKind = 'Separator'),
            MenuItem.template('TextContextCutItem',
                event = globalBlocks.Cut,
                title = messages.CUT,
                wxId = wx.ID_CUT),
            MenuItem.template('TextContextCopyItem',
                event = globalBlocks.Copy,
                title = messages.COPY,
                wxId = wx.ID_COPY),
            MenuItem.template('TextContextPasteItem',
                event = globalBlocks.Paste,
                title = messages.PASTE,
                wxId = wx.ID_PASTE),
            MenuItem.template('TextContextClearItem',
                event = globalBlocks.Clear,
                title = messages.CLEAR,
                wxId = wx.ID_CLEAR),
            MenuItem.template('TextContextSeparator2',
                menuItemKind = 'Separator'),
            MenuItem.template('TextContextSelectAllItem',
                event = globalBlocks.SelectAll,
                title = messages.SELECT_ALL,
                wxId = wx.ID_SELECTALL),
            ]).install(parcel)

    return menubar
