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


from osaf.framework.blocks import *
from osaf.framework.blocks.calendar import *
from osaf.views.main.Main import *
from osaf.views.main.SideBar import *
from osaf.views.main.Toolbar import *
from osaf.pim.structs import SizeType, RectType
from osaf import pim
from osaf import messages
from i18n import ChandlerMessageFactory as _
import osaf.pim.calendar
from application import schema
from chandlerdb.item.Item import MissingClass
import wx.grid
import wx

def makeMainView(parcel):    
    repositoryView = parcel.itsView

    globalBlocks = schema.ns("osaf.framework.blocks", repositoryView)
    main = schema.ns("osaf.views.main", repositoryView)
    app_ns = schema.ns("osaf.app", repositoryView)
    pim_ns = schema.ns("osaf.pim", repositoryView)

    # these reference each other... ugh!
    RTimer = ReminderTimer.template('ReminderTimer').install(parcel)
    main.ReminderTime.destinationBlockReference = RTimer
    
    # Default size for Chandler's main window
    # Note: (1024,720) is arguably better with the current design of the toolbar but
    # this has the bad side effect of starting Chandler "full screen" on some laptops with small 
    # screens which is against Apple GUI Guidelines as reported in bug 6503. 
    # So we're moving to a smaller default size. See bug 4718 for complete discussion.
    defaultChandlerSize = SizeType (970, 685)
    
    SidebarBranchPointDelegateInstance = SidebarBranchPointDelegate.update(
        parcel, 'SidebarBranchPointDelegateInstance',
        calendarTemplatePath = 'osaf.views.main.CalendarSummaryViewTemplate',
        dashboardTemplatePath = 'osaf.views.main.DashboardSummaryViewTemplate',
        searchResultsTemplatePath = 'osaf.views.main.SearchResultsViewTemplate')
    
    IconButton = SSSidebarIconButton.update(
        parcel, 'IconButton',
        buttonName = 'Icon',
        buttonOffsets = [0,21,19])
    
    SharingButton = SSSidebarSharingButton.update(
        parcel, 'SharingIcon',
        buttonName = 'SharingIcon',
        buttonOffsets = [-17,-1,16])

    sidebarSelectionCollection = pim.IndexedSelectionCollection.update(
        parcel, 'sidebarSelectionCollection',
        source = app_ns.sidebarCollection)

    initialSelectedCollection = pim_ns.allCollection
        

    Sidebar = SidebarBlock.template(
        'Sidebar',
        characterStyle = globalBlocks.SidebarRowStyle,
        columns = [Column.update(parcel, 'SidebarColName',
                                 heading = u'',
                                 scaleColumn = wx.grid.Grid.GRID_COLUMN_SCALABLE,
                                 attributeName = u'displayName')],

        scaleWidthsToFit = True,
        rowHeight = 19,
        border = RectType(0, 0, 4, 0),
        editRectOffsets = [22, -17, 0],
        buttons = [IconButton, SharingButton],
        contents = sidebarSelectionCollection,
        elementDelegate = 'osaf.views.main.SideBar.SidebarElementDelegate',
        hideColumnHeadings = True,
        defaultEditableAttribute = u'displayName',
        filterClass = MissingClass,
        disallowOverlaysForFilterClasses = [MissingClass,
                                          osaf.pim.mail.MailStamp,
                                          osaf.pim.tasks.TaskStamp],
        contextMenu = "SidebarContextMenu",
        ).install(parcel)
    Sidebar.contents.selectItem(initialSelectedCollection)
    
    miniCal = MiniCalendar.template(
        'MiniCalendar',
        contents = pim_ns.allCollection,
        calendarContainer = None,
        stretchFactor = 0.0).install(parcel)

    # customize for Linux, where toolbar items are extra-wide
    if wx.Platform != '__WXGTK__':
        quickEntryWidth = 440
    else:
        quickEntryWidth = 350

    appBarBlocks = [
        ToolBarItem.template('ApplicationBarAllButton',
            event = main.ApplicationBarAll,
            bitmap = 'ApplicationBarAll.png',
            title = _(u"All"),
            selected = True,
            toolBarItemKind = 'Radio',
            helpString = _(u'View all items')),
        ToolBarItem.template('ApplicationBarTaskButton',
            event = main.ApplicationBarTask,
            bitmap = 'ApplicationBarTask.png',
            title = _(u'Starred'),
            toolBarItemKind = 'Radio',
            helpString = _(u'View starred')),
        ToolBarItem.template('ApplicationBarEventButton',
            event = main.ApplicationBarEvent,
            bitmap = 'ApplicationBarEvent.png',
            title = _(u'Calendar'),
            toolBarItemKind = 'Radio',
            helpString = _(u'View events')),
        ToolBarItem.template('ApplicationBarSyncButton',
            event = main.SyncAll,
            bitmap = 'ApplicationBarSync.png',
            title = _(u'Sync'),
            helpString = _(u'Sync all shared collections and download new messages')),
        ToolBarItem.template('ApplicationBarQuickEntry',
            event = main.QuickEntry,
            text = u"", # text value displayed in the control
            toolBarItemKind = 'QuickEntry',
            size = SizeType (quickEntryWidth,-1),
            helpString = _(u"Create new note.")),
        ToolBarItem.template('TriageButton',
            event = main.Triage,
            title = _(u"Clean up"),
            bitmap = 'ApplicationBarTriage.png',
            helpString = _(u'Sort items by triage status')),
        SendToolBarItem.template('ApplicationBarSendButton',
            event = main.SendShareItem,
            bitmap = 'ApplicationBarSend.png',
            title = messages.SEND,
            viewAttribute='modifiedFlags',
            helpString = _(u'Send selected message')),
    ]

    ApplicationBar = ToolBar.template(
        'ApplicationBar',
        stretchFactor = 0.0,
        toolSize = SizeType(32, 32),
        buttonsLabeled = True,
        separatorWidth = 20,
        childBlocks = appBarBlocks
    ) # ToolBar ApplicationBar

    MainViewInstance = MainView.template(
        'MainView',
        size = defaultChandlerSize,
        orientationEnum='Vertical',
        eventBoundary = True,
        bufferedDraw = True,
        # This does not require localization
        displayName = u'Chandler\'s MainView',
        eventsForNamedLookup=[
            main.RequestSelectSidebarItem,
            main.SendMail,
            main.SelectedDateChanged,
            main.DayMode,
            main.ApplicationBarEvent,
            main.ApplicationBarTask,
            main.ApplicationBarAll,
            main.DisplayMailMessage,
            ],
        childBlocks = [
            main.MenuBar,
            main.SidebarContextMenu,
            main.ItemContextMenu,
            main.DragAndDropTextCtrlContextMenu,
            StatusBar.template('StatusBar'),
            ReminderTimer.template('ReminderTimer',
                                   event = main.ReminderTime,
                                   contents=pim_ns.allReminders),
            ApplicationBar,
            SplitterWindow.template('SidebarSplitterWindow',
                border = RectType(4, 0, 0, 0),
                splitPercentage = 0.15234375,
                orientationEnum = 'Vertical',
                splitController = miniCal,
                childBlocks = [
                    SplitterWindow.template('SidebarContainer',
                        stretchFactor = 0.0,
                        border = RectType(0, 0, 0, 4.0),
                        splitPercentage = 0.42,
                        splitController = miniCal,
                        childBlocks = [
                            Sidebar,
                            BoxContainer.template('PreviewAndMiniCalendar',
                                orientationEnum = 'Vertical',
                                childBlocks = [
                                    PreviewArea.template('PreviewArea',
                                        contents = pim_ns.allCollection,
                                        calendarContainer = None,
                                        timeCharacterStyle = \
                                            CharacterStyle.update(parcel, 
                                                                  'PreviewTimeStyle', 
                                                                  fontSize = 10,
                                                                  fontStyle = 'bold'),
                                        eventCharacterStyle = \
                                            CharacterStyle.update(parcel, 
                                                                  'PreviewEventStyle', 
                                                                  fontSize = 11),
                                        linkCharacterStyle = \
                                            CharacterStyle.update(parcel, 
                                                                  'PreviewLinkStyle', 
                                                                  fontSize = 11,
                                                                  fontStyle = 'underline'),
                                        stretchFactor = 0.0,
                                        miniCalendar = miniCal),
                                    miniCal
                                    ]) # BoxContainer PreviewAndMiniCalendar
                            ]), # SplitterWindow SidebarContainer
                    BranchPointBlock.template('SidebarBranchPointBlock',
                        delegate = SidebarBranchPointDelegateInstance,
                        detailItem = initialSelectedCollection,
                        selectedItem = initialSelectedCollection,
                        detailItemCollection = initialSelectedCollection,
                        setFocus = True),
                    ]) # SplitterWindow SidebarSplitterWindow      
            ]).install(parcel) # MainViewInstance MainView

    MainBranchPointDelegate = BranchPointDelegate.update(parcel, 
        'MainBranchPointDelegate')

    MainBranchPointBlock = BranchPointBlock.template(
        'MainBranchPointBlock',
        detailItem = MainViewInstance,
        selectedItem = MainViewInstance,
        childBlocks = [MainViewInstance],
        delegate = MainBranchPointDelegate).install(parcel)

    FrameWindow.update(
        parcel, 'MainViewRoot',
        blockName = 'MainViewRoot',
        windowTitle = u"Chandler",
        size = defaultChandlerSize,
        eventBoundary=True,
        views = {'MainView' : MainViewInstance},
        theActiveView = MainViewInstance,
        childBlocks = [MainBranchPointBlock])

    # Add certstore UI
    schema.synchronize(repositoryView, "osaf.framework.certstore.blocks")

    return MainViewInstance

