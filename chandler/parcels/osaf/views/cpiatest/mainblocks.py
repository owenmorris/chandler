from osaf.framework.blocks import *
from osaf.framework.blocks.calendar import *
from osaf.views.main.Main import *
from osaf.views.main.SideBar import *
from osaf.framework.types.DocumentTypes import SizeType, RectType
from osaf import pim
from osaf import messages
from i18n import OSAFMessageFactory as _
import osaf.pim.calendar
from application import schema

def makeCPIATestMainView (parcel):
    repositoryView = parcel.itsView

    globalBlocks = schema.ns("osaf.framework.blocks", repositoryView)
    main = schema.ns("osaf.views.main", repositoryView)
    cpiatest = schema.ns("osaf.views.cpiatest", repositoryView)
    app = schema.ns("osaf.app", repositoryView)

    SidebarBranchPointDelegateInstance = SidebarBranchPointDelegate.update(
        parcel, 'SidebarBranchPointDelegateInstance',
        tableTemplatePath = '//parcels/osaf/views/main/TableSummaryViewTemplate',
        calendarTemplatePath = '//parcels/osaf/views/main/CalendarSummaryViewTemplate')
    
    IconButton = SSSidebarIconButton.update(
        parcel, 'IconButton',
        buttonName = 'Icon',
        buttonOffsets = [1,17,16])
    
    SharingButton = SSSidebarSharingButton.update(
        parcel, 'SharingIcon',
        buttonName = 'SharingIcon',
        buttonOffsets = [-17,-1,16])

    sidebarSelectionCollection = pim.IndexedSelectionCollection.update(
        parcel, 'sidebarSelectionCollection',
        source = app.sidebarCollection)

    Sidebar = SidebarBlock.template(
        'Sidebar',
        characterStyle = globalBlocks.SidebarRowStyle,
        columnReadOnly = [False],
        columnHeadings = [u''],
        border = RectType(0, 0, 4, 0),
        editRectOffsets = [17, -17, 0],
        buttons = [IconButton, SharingButton],
        contents = sidebarSelectionCollection,
        selectedItemToView = app.allCollection,
        elementDelegate = 'osaf.views.main.SideBar.SidebarElementDelegate',
        hideColumnHeadings = True,
        columnWidths = [150],
        columnData = [u'displayName'],
        filterKind = osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(repositoryView)).install(parcel)
    Sidebar.contents.selectItem (app.allCollection)

    ApplicationBar = Toolbar.template(
        'ApplicationBar',
        stretchFactor = 0.0,
        toolSize = SizeType(26, 26),
        buttonsLabeled = True,
        separatorWidth = 20,
        childrenBlocks = [
            ToolbarItem.template('ApplicationBarAllButton',
                event = main.ApplicationBarAll,
                bitmap = 'ApplicationBarAll.png',
                title = _(u"All"),
                toolbarItemKind = 'Radio',
                helpString = _(u'View all items')),
            ToolbarItem.template('ApplicationBarMailButton',
                event = main.ApplicationBarMail,
                bitmap = 'ApplicationBarMail.png',
                title = _(u'Mail'),
                toolbarItemKind = 'Radio',
                helpString = _(u'View only mail')),
            ToolbarItem.template('ApplicationBarTaskButton',
                event = main.ApplicationBarTask,
                bitmap = 'ApplicationBarTask.png',
                title = _(u'Tasks'),
                toolbarItemKind = 'Radio',
                helpString = _(u'View only tasks')),
            ToolbarItem.template('ApplicationBarButton',
                event = main.ApplicationBarEvent,
                bitmap = 'ApplicationBarEvent.png',
                title = _(u'CalendarX'),
                selected = True,
                toolbarItemKind = 'Radio',
                helpString = _(u'View only events')),
            ToolbarItem.template('ApplicationSeparator1',
                toolbarItemKind = 'Separator'),
            ToolbarItem.template('ApplicationBarSyncButton',
                event = main.SyncAll,
                bitmap = 'ApplicationBarSync.png',
                title = _(u'Sync All'),
                toolbarItemKind = 'Button',
                helpString = _(u'Get new Mail and synchronize with other Chandler users')),
            ToolbarItem.template('ApplicationBarNewButton',
                event = main.NewNote,
                bitmap = 'ApplicationBarNew.png',
                title = _(u'New'),
                toolbarItemKind = 'Button',
                helpString = _(u'Create a new Item')),
            ToolbarItem.template('ApplicationSeparator2',
                toolbarItemKind = 'Separator'),
            ToolbarItem.template('ApplicationBarSendButton',
                event = main.SendShareItem,
                bitmap = 'ApplicationBarSend.png',
                title = messages.SEND,
                toolbarItemKind = 'Button',
                helpString = _(u'Send the selected Item')),
            ]) # Toolbar ApplicationBar

    MainViewInstance = MainView.template(
        'MainView',
        size = SizeType(1024, 720),
        orientationEnum = 'Vertical',
        eventBoundary = True,
        displayName = _(u'Chandler\'s MainView'),
        eventsForNamedLookup = [
            main.RequestSelectSidebarItem,
            main.SendMail,
            main.SelectedDateChanged,
            main.ShareItem,
            main.SelectWeek,
            main.ApplicationBarEvent,
            main.ApplicationBarTask,
            main.ApplicationBarMail,
            main.ApplicationBarAll],
        childrenBlocks = [
            cpiatest.MenuBar,
            StatusBar.template('StatusBar'),
            ReminderTimer.template('ReminderTimer',
                                   event = main.ReminderTime),
            BoxContainer.template('ToolbarContainer',
                orientationEnum = 'Vertical',
                childrenBlocks = [
                    ApplicationBar,
                    BoxContainer.template('SidebarContainerContainer',
                        border = RectType(4, 0, 0, 0),
                        childrenBlocks = [
                            SplitterWindow.template('SidebarContainer',
                                stretchFactor = 0.0,
                                border = RectType(0, 0, 0, 4.0),
                                childrenBlocks = [
                                    Sidebar,
                                    BoxContainer.template('PreviewAndMiniCalendar',
                                        orientationEnum = 'Vertical',
                                        childrenBlocks = [
                                            PreviewArea.template('PreviewArea',
                                                contents = app.allEventsCollection,
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
                                                stretchFactor = 0.0),
                                            MiniCalendar.template('MiniCalendar',
                                                contents = app.allEventsCollection,
                                                calendarContainer = None,
                                                stretchFactor = 0.0),
                                            ]) # BoxContainer PreviewAndMiniCalendar
                                    ]), # SplitterWindow SidebarContainer
                            BranchPointBlock.template('SidebarBranchPointBlock',
                                delegate = SidebarBranchPointDelegateInstance,
                                detailItem = app.allCollection,
                                selectedItem = app.allCollection,
                                detailItemCollection = app.allCollection),
                            ]) # BoxContainer SidebarContainerContainer
                    ]) # BoxContainer ToolbarContainer
            ]).install (parcel) # MainViewInstance MainView

    return MainViewInstance

