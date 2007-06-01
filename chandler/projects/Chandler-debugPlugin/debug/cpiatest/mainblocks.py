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


from osaf.framework.blocks import *
from osaf.framework.blocks.calendar import *
from osaf.views.main.Main import *
from osaf.views.main.menus import makeMainMenus
from osaf.views.main.SideBar import *
from osaf.pim.structs import SizeType, RectType
from osaf import pim
from osaf import messages
from repository.item.Item import MissingClass
from i18n import ChandlerMessageFactory as _
import osaf.pim.calendar
from application import schema
import wx.grid

def makeCPIATestMainView(parcel):
    repositoryView = parcel.itsView

    globalBlocks = schema.ns("osaf.framework.blocks", repositoryView)
    main = schema.ns("osaf.views.main", repositoryView)
    app_ns = schema.ns("osaf.app", repositoryView)
    pim_ns = schema.ns("osaf.pim", repositoryView)

    menubar = makeMainMenus(parcel)

    SidebarBranchPointDelegateInstance = SidebarBranchPointDelegate.update(
        parcel, 'SidebarBranchPointDelegateInstance',
        calendarTemplatePath = 'osaf.views.main.CalendarSummaryViewTemplate',
        dashboardTemplatePath = 'osaf.views.main.DashboardSummaryViewTemplate',
        searchResultsTemplatePath = 'osaf.views.main.SearchResultsViewTemplate')
    
    IconButton = SSSidebarIconButton2.update(
        parcel, 'IconButton2',
        buttonName = 'Icon2',
        buttonOffsets = [0,25,19])
    
    SharingButton = SSSidebarSharingButton.update(
        parcel, 'SharingIcon',
        buttonName = 'SharingIcon',
        buttonOffsets = [-17,-1,16])

    sidebarSelectionCollection = pim.IndexedSelectionCollection.update(
        parcel, 'sidebarSelectionCollection',
        source = app_ns.sidebarCollection)

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
        filterClass = pim_ns.EventStamp,
        disallowOverlaysForFilterClasses = [MissingClass,
                                          osaf.pim.mail.MailStamp,
                                          osaf.pim.tasks.TaskStamp]
        ).install(parcel)
    Sidebar.contents.selectItem (pim_ns.allCollection)

    miniCal = MiniCalendar.template(
        'MiniCalendar',
        contents = pim_ns.allCollection,
        calendarContainer = None,
        stretchFactor = 0.0).install(parcel)

    ApplicationBar = ToolBar.template(
        'ApplicationBar',
        stretchFactor = 0.0,
        toolSize = SizeType(26, 26),
        buttonsLabeled = True,
        separatorWidth = 20,
        childBlocks = [
            ToolBarItem.template('ApplicationBarAllButton',
                event = main.ApplicationBarAll,
                bitmap = 'ApplicationBarAll.png',
                title = _(u"All"),
                toolBarItemKind = 'Radio',
                helpString = _(u'View all items')),
            ToolBarItem.template('ApplicationBarMailButton',
                event = main.ApplicationBarMail,
                bitmap = 'ApplicationBarMail.png',
                title = _(u'Mail'),
                toolBarItemKind = 'Radio',
                helpString = _(u'View only mail')),
            ToolBarItem.template('ApplicationBarTaskButton',
                event = main.ApplicationBarTask,
                bitmap = 'ApplicationBarTask.png',
                title = _(u'Tasks'),
                toolBarItemKind = 'Radio',
                helpString = _(u'View only tasks')),
            ToolBarItem.template('ApplicationBarEventButton',
                event = main.ApplicationBarEvent,
                bitmap = 'ApplicationBarEvent.png',
                title = _(u'Calendar'),
                selected = True,
                toolBarItemKind = 'Radio',
                helpString = _(u'View only events')),
            ToolBarItem.template('ApplicationSeparator1',
                toolBarItemKind = 'Separator'),
            ToolBarItem.template('ApplicationBarSyncButton',
                event = main.SyncAll,
                bitmap = 'ApplicationBarSync.png',
                title = _(u'Sync All'),
                helpString = _(u'Get new Mail and synchronize with other Chandler users')),
            ToolBarItem.template('ApplicationBarNewButton',
                event = main.NewItem,
                bitmap = 'ApplicationBarNew.png',
                title = _(u'New'),
                helpString = _(u'Create a new Item')),
            ToolBarItem.template('ApplicationSeparator2',
                toolBarItemKind = 'Separator'),
            ToolBarItem.template('ApplicationBarSendButton',
                event = main.SendShareItem,
                bitmap = 'ApplicationBarSend.png',
                title = messages.SEND,
                helpString = _(u'Send the selected Item')),
            ToolBarItem.template('ApplicationSeparator3',
                toolBarItemKind = 'Separator'),
            ToolBarItem.template('ApplicationBarQuickEntry',
                event = main.QuickEntry,
                text = u"/", # text value displayed in the control
                toolBarItemKind = 'QuickEntry',
                size = SizeType (200,-1),
                helpString = _(u'Quick entry field: enter search string, or command beginning with "/"')),
        ]
    ) # ToolBar ApplicationBar

    MainViewInstance = MainView.template(
        'MainView',
        size = SizeType(1024, 720),
        orientationEnum = 'Vertical',
        eventBoundary = True,
        bufferedDraw = True,
        displayName = _(u'Chandler\'s MainView'),
        eventsForNamedLookup = [
            main.RequestSelectSidebarItem,
            main.SendMail,
            main.SelectedDateChanged,
            main.DayMode,
            main.ApplicationBarEvent,
            main.ApplicationBarTask,
            main.ApplicationBarMail,
            main.ApplicationBarAll,
            ],
        childBlocks = [
            menubar,
            StatusBar.template('StatusBar'),
            ApplicationBar,
            BoxContainer.template('SidebarContainerContainer',
                border = RectType(4, 0, 0, 0),
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
                        detailItem = pim_ns.allCollection,
                        selectedItem = pim_ns.allCollection,
                        detailItemCollection = pim_ns.allCollection),
                    ]) # BoxContainer SidebarContainerContainer
            ]).install (parcel) # MainViewInstance MainView

    return MainViewInstance

