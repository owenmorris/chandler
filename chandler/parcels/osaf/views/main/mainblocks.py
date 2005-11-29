from osaf.framework.blocks import *
from osaf.framework.types.DocumentTypes import SizeType, ColorType, RectType
from osaf.framework.blocks.calendar import *
from osaf.views.main.Main import *
from osaf.views.main.SideBar import *

from osaf.framework import scripting

from osaf import pim

import osaf.pim.notes
import osaf.pim.calendar
import osaf.pim.mail
import osaf.pim.tasks

from application import schema
from i18n import OSAFMessageFactory as _
from osaf import messages

# in the form 'Color', _('LocalizableColorString'), 360-degree based hue
collection_hues = [('Blue', _(u'Blue'), 210),
                   ('Green', (u'Green'), 120),
                   ('Rose', _(u'Rose'), 0),
                   ('Salmon', _(u'Salmon'), 30),
                   ('Purple', _(u'Purple'), 270),
                   ('Violet', _(u'Violet'), 240),
                   ('Fuschia', _(u'Fuschia'), 330)]

def make_color_blocks(parcel, cls, hues):
    """
    dynamically creates an array of type 'cls' based on a list of colors
    """
    menuitems = []
    
    for shortname, title, hue in hues:
        rgb = wx.Image.HSVtoRGB (wx.Image_HSVValue (hue/360.0, 0.5, 1.0))
        color = ColorType (rgb.red, rgb.green, rgb.blue, 255)
        colorevent = \
            ColorEvent.template(shortname + 'CollectionColor',
                                'SendToBlockByName',
                                dispatchToBlockName='Sidebar',
                                color=color,
                                methodName='onCollectionColorEvent').install(parcel)

        menuitem = cls.template(shortname + 'ColorItem',
                                title=title,
                                icon=shortname + "MenuIcon",
                                menuItemKind="Check",
                                event=colorevent)
        menuitems.append(menuitem)
    return menuitems
                                     

    
def make_mainview(parcel):

    repositoryView = parcel.itsView
    globalBlocks = schema.ns("osaf.framework.blocks", repositoryView)
    repositoryViewer = schema.ns("osaf.views.repositoryviewer", repositoryView)
    app  = schema.ns("osaf.app", repositoryView)

    # these reference each other... ugh!
    RTimer = ReminderTimer.template('ReminderTimer').install(parcel)
    
    ReminderTimerEvent = \
        BlockEvent.template('ReminderTime',
                            'SendToBlockByReference',
                            destinationBlockReference=RTimer).install(parcel)
    
    ReminderTimer.update(parcel, 'ReminderTimer',
                         event=ReminderTimerEvent,
                         contents=app.eventsWithReminders)

    # from //parcels/osaf/views/main
    NewNoteEvent = \
        KindParameterizedEvent.template('NewNote',
            methodName='onNewEvent',
            kindParameter=osaf.pim.notes.Note.getKind(repositoryView),
            commitAfterDispatch=True,
            dispatchEnum='ActiveViewBubbleUp').install(parcel)
    # from //parcels/osaf/views/main
    RunSelectedScriptEvent = \
        BlockEvent.template('RunSelectedScript',
            dispatchEnum='FocusBubbleUp').install(parcel)
    # Event to put "Scripts" in the Sidebar
    AddScriptsToSidebarEvent = \
        BlockEvent.template('AddScriptsToSidebar',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    BackupRepositoryEvent = \
        BlockEvent.template('BackupRepository',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    UnsubscribeSidebarCollectionEvent = \
        BlockEvent.template('UnsubscribeSidebarCollection',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ShowPyCrustEvent = \
        BlockEvent.template('ShowPyCrust',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ApplicationBarMailEvent = \
        KindParameterizedEvent.template('ApplicationBarMail',
            methodName='onKindParameterizedEvent',
            kindParameter=osaf.pim.mail.MailMessageMixin.getKind(repositoryView),
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='Sidebar').install(parcel)
    # from //parcels/osaf/views/main
    ShowHideStatusBarEvent = \
        BlockEvent.template('ShowHideStatusBar',
            methodName='onShowHideEvent',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='StatusBar').install(parcel)
    # "Item" menu events
    FocusTogglePrivateEvent = \
        BlockEvent.template('FocusTogglePrivate',
            dispatchEnum='FocusBubbleUp').install(parcel)
    FocusStampMessageEvent = \
        KindParameterizedEvent.template('FocusStampMessage',
            methodName='onFocusStampEvent',
            kindParameter=osaf.pim.mail.MailMessageMixin.getKind(repositoryView),
            dispatchEnum='FocusBubbleUp').install(parcel)
    FocusStampTaskEvent = \
        KindParameterizedEvent.template('FocusStampTask',
            methodName='onFocusStampEvent',
            kindParameter=osaf.pim.tasks.TaskMixin.getKind(repositoryView),
            dispatchEnum='FocusBubbleUp').install(parcel)
    FocusStampCalendarEvent = \
        KindParameterizedEvent.template('FocusStampCalendar',
            methodName='onFocusStampEvent',
            kindParameter=osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(repositoryView),
            dispatchEnum='FocusBubbleUp').install(parcel)
    # from //parcels/osaf/views/main
    SharingSubscribeToCollectionEvent = \
        BlockEvent.template('SharingSubscribeToCollection',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    CheckRepositoryEvent = \
        BlockEvent.template('CheckRepository',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    i18nMailTestEvent = \
        BlockEvent.template('i18nMailTest',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ShowLogWindowEvent = \
        BlockEvent.template('ShowLogWindow',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ActivateWebserverEvent = \
        BlockEvent.template('ActivateWebserver',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ActivateShareMergingEvent = \
        BlockEvent.template('ActivateShareMerging',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    CommitRepositoryEvent = \
        BlockEvent.template('CommitRepository',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    GetNewMailEvent = \
        BlockEvent.template('GetNewMail',
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ManageSidebarCollectionEvent = \
        BlockEvent.template('ManageSidebarCollection',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    StopProfilerEvent = \
        BlockEvent.template('StopProfiler',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ShowPyShellEvent = \
        BlockEvent.template('ShowPyShell',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    EditAccountPreferencesEvent = \
        BlockEvent.template('EditAccountPreferences',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ShowHideSidebarEvent = \
        BlockEvent.template('ShowHideSidebar',
            methodName='onShowHideEvent',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='SidebarContainer').install(parcel)
    # from //parcels/osaf/views/main
    ReloadParcelsEvent = \
        BlockEvent.template('ReloadParcels',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ApplicationBarAllEvent = \
        KindParameterizedEvent.template('ApplicationBarAll',
            methodName='onKindParameterizedEvent',
            kindParameter=None,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='Sidebar').install(parcel)
    # from //parcels/osaf/views/main
    NewMailMessageEvent = \
        KindParameterizedEvent.template('NewMailMessage',
            methodName='onNewEvent',
            kindParameter=osaf.pim.mail.MailMessage.getKind(repositoryView),
            commitAfterDispatch=True,
            dispatchEnum='ActiveViewBubbleUp').install(parcel)
    # from //parcels/osaf/views/main
    ApplicationBarEventEvent = \
        KindParameterizedEvent.template('ApplicationBarEvent',
            methodName='onKindParameterizedEvent',
            kindParameter=osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(repositoryView),
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='Sidebar').install(parcel)
    # from //parcels/osaf/views/main
    NewCalendarEvent = \
        KindParameterizedEvent.template('NewCalendar',
            methodName='onNewEvent',
            kindParameter=osaf.pim.calendar.Calendar.CalendarEvent.getKind(repositoryView),
            commitAfterDispatch=True,
            dispatchEnum='ActiveViewBubbleUp').install(parcel)
    # from //parcels/osaf/views/main
    DeleteEvent = \
        BlockEvent.template('Delete',
            commitAfterDispatch=True,
            dispatchEnum='FocusBubbleUp').install(parcel)
    # from //parcels/osaf/views/main
    AddCPIAViewEvent = \
        ModifyCollectionEvent.template('AddCPIAView',
            methodName='onModifyCollectionEvent',
            dispatchToBlockName='MainView',
            commitAfterDispatch=True,
            items=[repositoryViewer.CPIAView],
            dispatchEnum='SendToBlockByName').install(parcel)
    # from //parcels/osaf/views/main
    ShareSidebarCollectionEvent = \
        BlockEvent.template('ShareSidebarCollection',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    StartProfilerEvent = \
        BlockEvent.template('StartProfiler',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    LoadLoggingConfigEvent = \
        BlockEvent.template('LoadLoggingConfig',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    RestoreSharesEvent = \
        BlockEvent.template('RestoreShares',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    SyncCollectionEvent = \
        BlockEvent.template('SyncCollection',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    ToggleMineEvent = \
        BlockEvent.template('ToggleMine',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='Sidebar').install(parcel)
    # from //parcels/osaf/views/main
    SharingImportDemoCalendarEvent = \
        BlockEvent.template('SharingImportDemoCalendar',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ShowHideApplicationBarEvent = \
        BlockEvent.template('ShowHideApplicationBar',
            methodName='onShowHideEvent',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='ApplicationBar').install(parcel)
    # from //parcels/osaf/views/main
    NewTaskEvent = \
        KindParameterizedEvent.template('NewTask',
            methodName='onNewEvent',
            kindParameter=osaf.pim.tasks.Task.getKind(repositoryView),
            commitAfterDispatch=True,
            dispatchEnum='ActiveViewBubbleUp').install(parcel)
    # from //parcels/osaf/views/main
    GenerateContentItemsEvent = \
        BlockEvent.template('GenerateContentItems',
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    AddRepositoryViewEvent = \
        ModifyCollectionEvent.template('AddRepositoryView',
            methodName='onModifyCollectionEvent',
            dispatchToBlockName='MainView',
            commitAfterDispatch=True,
            items=[repositoryViewer.RepositoryView],
            dispatchEnum='SendToBlockByName').install(parcel)
    # from //parcels/osaf/views/main
    ChooseChandlerMainViewEvent = \
        ChoiceEvent.template('ChooseChandlerMainView',
            dispatchEnum='SendToBlockByName',
            methodName='onChoiceEvent',
            choice='MainView',
            dispatchToBlockName='MainViewRoot').install(parcel)
    # from //parcels/osaf/views/main
    ExportIcalendarEvent = \
        BlockEvent.template('ExportIcalendar',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    SyncAllEvent = \
        BlockEvent.template('SyncAll',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ShareToolEvent = \
        BlockEvent.template('ShareTool',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    NewCollectionEvent = \
        ModifyCollectionEvent.template('NewCollection',
            methodName='onModifyCollectionEvent',
            copyItems = True,
            disambiguateDisplayName = True,
            dispatchToBlockName = 'MainView',
            selectInBlockNamed = 'Sidebar',
            editAttributeNamed = 'displayName',
            items=[app.untitledCollection],
            dispatchEnum = 'SendToBlockByName').install(parcel)
    # from //parcels/osaf/views/main
    ImportImageEvent = \
        BlockEvent.template('ImportImage',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    AddAllAdditionalViewsEvent = \
        ModifyCollectionEvent.template('AddAllAdditionalViews',
            methodName='onModifyCollectionEvent',
            dispatchToBlockName='MainView',
            commitAfterDispatch=True,
            items=[repositoryViewer.RepositoryView, repositoryViewer.CPIAView],
            dispatchEnum='SendToBlockByName').install(parcel)
    # from //parcels/osaf/views/main
    GenerateContentItemsFromFileEvent = \
        BlockEvent.template('GenerateContentItemsFromFile',
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ApplicationBarTaskEvent = \
        KindParameterizedEvent.template('ApplicationBarTask',
            methodName='onKindParameterizedEvent',
            kindParameter=osaf.pim.tasks.TaskMixin.getKind(repositoryView),
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='Sidebar').install(parcel)
    # from //parcels/osaf/views/main
    EmptyTrashEvent = \
        BlockEvent.template('EmptyTrash',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    UnpublishSidebarCollectionEvent = \
        BlockEvent.template('UnpublishSidebarCollection',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    MimeTestEvent = \
        BlockEvent.template('MimeTest',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    SyncWebDAVEvent = \
        BlockEvent.template('SyncWebDAV',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    WxTestHarnessEvent = \
        BlockEvent.template('WxTestHarness',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ImportIcalendarEvent = \
        BlockEvent.template('ImportIcalendar',
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    CopyCollectionURLEvent = \
        BlockEvent.template('CopyCollectionURL',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    TakeOnlineOfflineEvent = \
        BlockEvent.template('TakeOnlineOffline',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ChooseCPIATestMainViewEvent = \
        ChoiceEvent.template('ChooseCPIATestMainView',
            dispatchEnum='SendToBlockByName',
            methodName='onChoiceEvent',
            choice='CPIATestMainView',
            dispatchToBlockName='MainViewRoot').install(parcel)

    TestEvent = \
        BlockEvent.template('Test',
                            dispatchEnum='SendToBlockByName',
                            dispatchToBlockName='MainView').install(parcel)

    RequestSelectSidebarItemEvent = \
        BlockEvent.template('RequestSelectSidebarItem',
                            'SendToBlockByName',
                            dispatchToBlockName='Sidebar').install(parcel)
    
    SendMailEvent = \
        BlockEvent.template('SendMail',
                            'SendToBlockByName',
                            dispatchToBlockName='MainView').install(parcel)
                  
    ShareItemEvent = \
        BlockEvent.template('ShareItem',
                            'SendToBlockByName',
                            dispatchToBlockName='MainView').install(parcel)
                  
    SelectWeekEvent = \
        BlockEvent.template('SelectWeek',
                            'BroadcastEverywhere').install(parcel)
        
    SidebarTrunkDelegateInstance = \
        SidebarTrunkDelegate.update(parcel, 'SidebarTrunkDelegateInstance',
                                    tableTemplatePath='//parcels/osaf/views/main/TableSummaryViewTemplate',
                                    calendarTemplatePath='//parcels/osaf/views/main/CalendarSummaryViewTemplate')
    
    IconButton = SSSidebarIconButton.update(parcel, 'IconButton',
                                            buttonName='Icon',
                                            buttonOffsets=[1,17,16])
    
    SharingButton = SSSidebarSharingButton.update(parcel, 'SharingIcon',
                                            buttonName='SharingIcon',
                                            buttonOffsets=[-17,-1,16])

    sidebarSelectionCollection = pim.IndexedSelectionCollection.update(parcel,
                                                                       'sidebarSelectionCollection',
                                                                       source=app.sidebarCollection)

    Sidebar = SidebarBlock.template('Sidebar',
        characterStyle=globalBlocks.SidebarRowStyle,
        columnReadOnly=[False],
        columnHeadings=[u''],
        border=RectType(0, 0, 4, 0),
        editRectOffsets=[17, -17, 0],
        buttons=[IconButton, SharingButton],
        contents=sidebarSelectionCollection,
        selectedItemToView=app.allCollection,
        elementDelegate='osaf.views.main.SideBar.SidebarElementDelegate',
        hideColumnHeadings=True,
        columnWidths=[150],
        columnData=[u'displayName'],
        filterKind=osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(parcel.itsView)).install(parcel)
    Sidebar.contents.selectItem (app.allCollection)

    mainview = \
    MainView.template('MainView',
        size=SizeType(1024, 720),
        orientationEnum='Vertical',
        eventBoundary=True,
        displayName=_(u'Chandler\'s MainView'),
        eventsForNamedLookup=[
            RequestSelectSidebarItemEvent,
            SendMailEvent,
            ShareItemEvent,
            SelectWeekEvent,
            ApplicationBarEventEvent,
            ApplicationBarTaskEvent,
            ApplicationBarMailEvent,
            ApplicationBarAllEvent,
        ],
        childrenBlocks=[
            MenuBar.template('MenuBar',
                childrenBlocks=[
                    Menu.template('FileMenu',
                        title=_(u'&File'),
                        childrenBlocks=[
                            Menu.template('NewItemMenu',
                                title=_(u'New Item'),
                                helpString=_(u'Create a new Content Item'),
                                childrenBlocks=[
                                    MenuItem.template('NewNoteItem',
                                        event=NewNoteEvent,
                                        title=_(u'Note'),
                                        accel=_(u'Ctrl+N'),
                                        helpString=_(u'Create a new Note')),
                                    MenuItem.template('NewMessageItem',
                                        event=NewMailMessageEvent,
                                        title=_(u'Message'),
                                        accel=_(u'Ctrl+M'),
                                        helpString=_(u'Create a new Message')),
                                    MenuItem.template('NewTaskItem',
                                        event=NewTaskEvent,
                                        title=_(u'Task'),
                                        helpString=_(u'Create a new Task')),
                                    MenuItem.template('NewEventItem',
                                        event=NewCalendarEvent,
                                        title=_(u'Event'),
                                        helpString=_(u'Create a new Event')),
                                    MenuItem.template('NewSeparator1',
                                        menuItemKind='Separator'),
                                    MenuItem.template('NewContactItem',
                                        title=_(u'Contact'),
                                        helpString=_(u'Create a new Contact')),
                                    ]), # Menu NewItemMenu
                            MenuItem.template('FileSeparator1',
                                menuItemKind='Separator'),
                            MenuItem.template('NewCollectionItem',
                                event=NewCollectionEvent,
                                title=_(u'New Collection'),
                                helpString=_(u'Create a new Collection')),
                            MenuItem.template('FileSeparator2',
                                menuItemKind='Separator'),
                            MenuItem.template('PrintPreviewItem',
                                event=globalBlocks.PrintPreview,
                                title=_(u'Print Preview')),
                            MenuItem.template('PrintItem',
                                event=globalBlocks.Print,
                                title=_(u'Print...'),
                                accel=_(u'Ctrl+P'),
                                helpString=_(u'Print the current calendar')),
                            MenuItem.template('FileSeparator3',
                                menuItemKind='Separator'),
                            Menu.template('ImportExportMenu',
                                title=_(u'Import/Export'),
                                childrenBlocks=[
                                    MenuItem.template('ImportIcalendarItem',
                                        event=ImportIcalendarEvent,
                                        title=_(u'Import iCalendar data'),
                                        helpString=_(u'Import iCalendar file from import.ics')),
                                    MenuItem.template('ExportIcalendarItem',
                                        event=ExportIcalendarEvent,
                                        title=_(u'Export Events as iCalendar'),
                                        helpString=_(u'Export Calendar Events to export.ics')),
                                    MenuItem.template('ImportImageItem',
                                        event=ImportImageEvent,
                                        title=_(u'Import an image from disk'),
                                        helpString=_(u'Import an image from disk')),
                                    ]), # Menu ImportExportMenu
                            Menu.template('SyncMenu',
                                title=_(u'Sync'),
                                childrenBlocks=[
                                    MenuItem.template('SyncAllItem',
                                        event=SyncAllEvent,
                                        title=_(u"Sync All"),
                                        helpString=_(u'Sync All')),
                                    MenuItem.template('SyncIMAPItem',
                                        event=GetNewMailEvent,
                                        title=_(u'Mail'),
                                        helpString=_(u'Sync Mail')),
                                    MenuItem.template('SyncWebDAVItem',
                                        event=SyncWebDAVEvent,
                                        title=_(u'Shares'),
                                        helpString=_(u'Sync Shares')),
                                    ]), # Menu SyncMenu
                            MenuItem.template('PrefsAccountsItem',
                                event=EditAccountPreferencesEvent,
                                title=_(u'Accounts...'),
                                helpString=messages.ACCOUNT_PREFERENCES),
                            MenuItem.template('FileSeparator4',
                                menuItemKind='Separator'),
                            MenuItem.template('QuitItem',
                                event=globalBlocks.Quit,
                                title=_(u'Quit'),
                                accel=_(u'Ctrl+Q'),
                                helpString=_(u'Quit Chandler')),
                            ]), # Menu FileMenu
                    Menu.template('EditMenu',
                        title=_(u'&Edit'),
                        childrenBlocks=[
                            MenuItem.template('UndoItem',
                                event=globalBlocks.Undo,
                                title=messages.UNDO,
                                accel=_(u'Ctrl+Z'),
                                helpString=_(u"Can't Undo")),
                            MenuItem.template('RedoItem',
                                event=globalBlocks.Redo,
                                title=messages.REDO,
                                accel=_(u'Ctrl+Y'),
                                helpString=_(u"Can't Redo")),
                            MenuItem.template('EditSeparator1',
                                menuItemKind='Separator'),
                            MenuItem.template('CutItem',
                                event=globalBlocks.Cut,
                                title=messages.CUT,
                                accel=_(u'Ctrl+X')),
                            MenuItem.template('CopyItem',
                                event=globalBlocks.Copy,
                                title=messages.COPY,
                                accel=_(u'Ctrl+C')),
                            MenuItem.template('PasteItem',
                                event=globalBlocks.Paste,
                                title=messages.PASTE,
                                accel=_(u'Ctrl+V')),
                            MenuItem.template('ClearItem',
                                event=globalBlocks.Clear,
                                title=messages.CLEAR),
                            MenuItem.template('SelectAllItem',
                                event=globalBlocks.SelectAll,
                                title=messages.SELECT_ALL,
                                accel=_(u'Ctrl+A'),
                                helpString=_(u'Select all')),
                            MenuItem.template('EditSeparator2',
                                menuItemKind='Separator'),
                            MenuItem.template('RemoveItem',
                                event=globalBlocks.Remove,
                                title=_(u'Remove'),
                                helpString=_(u'Remove the current selection from the current collection')),
                            MenuItem.template('DeleteItem',
                                event=DeleteEvent,
                                title=_(u'Delete'),
                                accel=_(u'DELETE'),
                                helpString=_(u'Move the current selection to the trash')),
                            MenuItem.template('EmptyTrashItem',
                                event=EmptyTrashEvent,
                                title=_(u'Empty Trash'),
                                helpString=_(u'Remove all items from the Trash collection')),
                            ]), # Menu EditMenu
                    Menu.template('ViewMenu',
                        title=_(u'&View'),
                        childrenBlocks=[
                            MenuItem.template('ViewAllItem',
                                event=ApplicationBarAllEvent,
                                title=_(u'All items'),
                                menuItemKind='Radio',
                                helpString=_(u'View all kinds of items')),
                            MenuItem.template('ViewMailItem',
                                event=ApplicationBarMailEvent,
                                title=_(u'Mail'),
                                menuItemKind='Radio',
                                helpString=_(u'View only mail messages')),
                            MenuItem.template('ViewTaskItem',
                                event=ApplicationBarTaskEvent,
                                title=_(u'Tasks'),
                                menuItemKind='Radio',
                                helpString=_(u'View only tasks')),
                            MenuItem.template('ViewEventItem',
                                event=ApplicationBarEventEvent,
                                title=_(u'Calendar'),
                                menuItemKind='Radio',
                                helpString=_(u'View only calendar items')),
                            MenuItem.template('ViewSeparator1',
                                menuItemKind='Separator'),
                            MenuItem.template('ViewToolBarItem',
                                event=ShowHideApplicationBarEvent,
                                title=_(u'View Toolbar'),
                                menuItemKind='Check',
                                helpString=_(u'Show or Hide the Toolbar')),
                            MenuItem.template('ViewSideBarItem',
                                event=ShowHideSidebarEvent,
                                title=_(u'View Sidebar'),
                                menuItemKind='Check',
                                helpString=_(u'Show or hide the Sidebar')),
                            MenuItem.template('ViewStatusBarItem',
                                event=ShowHideStatusBarEvent,
                                title=_(u'View Status Bar'),
                                menuItemKind='Check',
                                helpString=_(u'Show or hide the Status bar')),
                            ]), # Menu ViewMenu
                    Menu.template('ItemMenu',
                        title=_(u'&Item'),
                        childrenBlocks=[
                            MenuItem.template('SendMessageItem',
                                event=globalBlocks.SendShareItem,
                                title=messages.SEND,
                                helpString=_(u'Send the selected Mail Message')),
                            MenuItem.template('ItemSeparator1',
                                menuItemKind='Separator'),
                            MenuItem.template('StampMessageItem',
                                event=FocusStampMessageEvent,
                                title=messages.STAMP_MAIL,
                                menuItemKind='Check',
                                helpString=messages.STAMP_MAIL_HELP),
                            MenuItem.template('StampTaskItem',
                                event=FocusStampTaskEvent,
                                title=messages.STAMP_TASK,
                                menuItemKind='Check',
                                helpString=messages.STAMP_TASK_HELP),
                            MenuItem.template('StampEventItem',
                                event=FocusStampCalendarEvent,
                                title=messages.STAMP_CALENDAR,
                                menuItemKind='Check',
                                helpString=messages.STAMP_CALENDAR_HELP),
                            MenuItem.template('ItemSeparator2',
                                menuItemKind='Separator'),
                            MenuItem.template('NeverShareItem',
                                event=FocusTogglePrivateEvent,
                                title=messages.PRIVATE,
                                menuItemKind='Check',
                                helpString=_(u'Mark the selected item as private, so it will not be shared')),
                            ]), # Menu ItemMenu
                    Menu.template('CollectionMenu',
                        title=_(u'&Collection'),
                        childrenBlocks=[
                            MenuItem.template('SharingSubscribeToCollectionItem',
                                event=SharingSubscribeToCollectionEvent,
                                title=_(u'Subscribe...'),
                                helpString=_(u'Subscribe to a published collection')),
                            MenuItem.template('ShareSidebarCollectionItem',
                                event=ShareSidebarCollectionEvent,
                                title=_(u'Share'),
                                helpString=_(u'Share the selected collection')),
                            MenuItem.template('ManageSidebarCollectionItem',
                                event=ManageSidebarCollectionEvent,
                                title=_(u'Manage share...'),
                                helpString=_(u'Manage the selected collection')),
                            MenuItem.template('UnsubscribeSidebarCollectionItem',
                                event=UnsubscribeSidebarCollectionEvent,
                                title=_(u'Unsubscribe'),
                                helpString=_(u'Unsubscribe the selected collection')),
                            MenuItem.template('UnpublishSidebarCollectionItem',
                                event=UnpublishSidebarCollectionEvent,
                                title=_(u'Unpublish'),
                                helpString=_(u'Remove the collection from the sharing server')),
                            MenuItem.template('CopyCollectionURLItem',
                                event=CopyCollectionURLEvent,
                                title=_(u'Copy URL(s) to clipboard'),
                                helpString=_(u"Copy the selected collection's URL(s) to the clipboard")),
                            MenuItem.template('TakeOnlineOfflineItem',
                                event=TakeOnlineOfflineEvent,
                                title=_(u'Online/Offline status'),
                                helpString=_(u"Toggle the collection's online status")),
                            MenuItem.template('SyncCollectionItem',
                                event=SyncCollectionEvent,
                                title=_(u'Sync collection'),
                                helpString=_(u'Synchronize a shared collection')),
                            MenuItem.template('RenameItem',
                                event=globalBlocks.Rename,
                                title=_(u'Rename'),
                                helpString=_(u'Rename the selected collection')),
                            Menu.template('CollectionColorMenu',
                                title=_(u'&Collection Color'),
                                childrenBlocks=make_color_blocks(parcel,
                                                                 MenuItem,
                                                                 collection_hues)),
                            MenuItem.template('RestoreSharesItem',
                                event=RestoreSharesEvent,
                                title=u'Restore published shares...',
                                helpString=u'Restore previously published shares'),
                            MenuItem.template('CollectionSeparator1',
                                menuItemKind='Separator'),
                            MenuItem.template('ToggleMineItem',
                                event=ToggleMineEvent,
                                title=_(u'Toggle mine/not-mine'),
                                helpString=_(u'Toggle mine/not-mine')),
                            ]), # Menu CollectionMenu
                    Menu.template('TestMenu',
                        title=_(u'&Test'),
                        childrenBlocks=[
                            MenuItem.template('GenerateSomeDataItem',
                                event=GenerateContentItemsEvent,
                                title=u'Generate Data',
                                helpString=u'generates a few items of each kind'),
                            MenuItem.template('GenerateMuchDataItem',
                                event=GenerateContentItemsEvent,
                                title=u'Generate Lots of Data',
                                helpString=u'generates many items of each kind'),
                            MenuItem.template('GenerateDataItemFromFile',
                                event=GenerateContentItemsFromFileEvent,
                                title=u'Generate Items from a file',
                                helpString=u'generates Items from a file'),
                            MenuItem.template('MimeTestItem',
                                event=MimeTestEvent,
                                title=u'MIME Torture Tests',
                                helpString=u'Loads real world complex / broken mime message examples provided by Anthony Baxter'),
                            MenuItem.template('i18nMailTestItem',
                                event=i18nMailTestEvent,
                                title=u'i18n Mail Tests',
                                helpString=u'Loads mail messages containing a variety of Charsets and Languages'),
                            MenuItem.template('StartProfilerItem',
                                event=StartProfilerEvent,
                                title=u'Start Profiler',
                                helpString=u'Start profiling events'),
                            MenuItem.template('StopProfilerItem',
                                event=StopProfilerEvent,
                                title=u'Stop Profiler',
                                helpString=u'Stop profiling events'),
                            MenuItem.template('ReloadParcelsItem',
                                event=ReloadParcelsEvent,
                                title=u'Reload Parcels',
                                accel=u'Ctrl+R',
                                helpString=u'Reloads any parcels that have been modified'),
                            MenuItem.template('CommitRepositoryItem',
                                event=CommitRepositoryEvent,
                                title=u'Commit Repository',
                                helpString=u'Performs a repository commit()'),
                            MenuItem.template('CheckRepositoryItem',
                                event=CheckRepositoryEvent,
                                title=u'Check Repository',
                                helpString=u'run check() on the current view'),
                            MenuItem.template('BackupRepositoryItem',
                                event=BackupRepositoryEvent,
                                title=u'Backup Repository',
                                helpString=u'backup the repository'),
                            MenuItem.template('RunSelectedScriptItem',
                                event=RunSelectedScriptEvent,
                                title=u'Run a Script',
                                accel=u'Ctrl+S',
                                helpString=u'Run the CPIA Script from the Detail View'),
                            MenuItem.template("AddScriptsSetItem",
                                event = AddScriptsToSidebarEvent,
                                title = u"Add Scripts to Sidebar",
                                helpString=u'Add Scripts to the Sidebar'),
                            MenuItem.template('WxTestHarnessItem',
                                event=WxTestHarnessEvent,
                                title=u'Wx Test Harness',
                                helpString=u'invoke the current flavor of wx debugging'),
                            MenuItem.template('ShowPyShellItem',
                                event=ShowPyShellEvent,
                                title=u'Show Python shell...',
                                helpString=u'Brings up an interactive Python shell'),
                            MenuItem.template('ShowPyCrustItem',
                                event=ShowPyCrustEvent,
                                title=u'Show Python shell with object browser...',
                                helpString=u'Brings up an interactive Python shell and object browser'),
                            MenuItem.template('ShowLogWindowItem',
                                event=ShowLogWindowEvent,
                                title=u'Show log window',
                                helpString=u'Displays the contents of chandler.log and twisted.log'),
                            MenuItem.template('ActivateWebserverItem',
                                event=ActivateWebserverEvent,
                                title=u'Activate built-in webserver',
                                helpString=u'Activates the built-in webserver at localhost:1888'),
                            MenuItem.template('ActivateShareMergingItem',
                                event=ActivateShareMergingEvent,
                                title=u'Activate Share Merging',
                                helpString=u'Activates merging of non-overlapping sharing changes'),
                            MenuItem.template('LoadLoggingConfigItem',
                                event=LoadLoggingConfigEvent,
                                title=u'Load logging configuration file...',
                                helpString=u'Load logging configuration file'),
                            Menu.template('ShareMenu',
                                title=u'Share',
                                helpString=u'Sharing-related test commands',
                                childrenBlocks=[
                                    MenuItem.template('SharingImportDemoCalendarItem',
                                        event=SharingImportDemoCalendarEvent,
                                        title=u'Import demo calendar',
                                        helpString=u'Import a demo iCalendar file from osafoundation.org'),
                                    MenuItem.template('ShareToolItem',
                                        event=ShareToolEvent,
                                        title=u'Share tool...',
                                        helpString=u'Display the Share Tool'),
                                    ]), # Menu ShareMenu
                            Menu.template('SkinsMenu',
                                title=u'Skins',
                                helpString=u'Change user-interface skin',
                                childrenBlocks=[
                                    MenuItem.template('ChandlerSkinMenuItem',
                                        event=ChooseChandlerMainViewEvent,
                                        title=u'Chandler',
                                        helpString=u'Switch to Chandler'),
                                    MenuItem.template('CPIATestSkinMenuItem',
                                        event=ChooseCPIATestMainViewEvent,
                                        title=u'CPIA Test',
                                        helpString=u'Switch to CPIA test'),
                                    ]), # Menu SkinsMenu
                            Menu.template('AddAdditionalViews',
                                title=u'Add Additional Views',
                                helpString=u'Add views to the sidebar',
                                childrenBlocks=[
                                    MenuItem.template('AddAllAdditionalViewsItem',
                                        event=AddAllAdditionalViewsEvent,
                                        title=u'Add All Additional Views',
                                        helpString=u'Adds all of the extra views to the sidebar'),
                                    MenuItem.template('TestSeparator1',
                                        menuItemKind='Separator'),
                                    MenuItem.template('AddRepositoryViewItem',
                                        event=AddRepositoryViewEvent,
                                        title=u'Add Repository Viewer',
                                        helpString=u'Adds the repository viewer to the sidebar'),
                                    MenuItem.template('AddCPIAViewItem',
                                        event=AddCPIAViewEvent,
                                        title=u'Add CPIA Viewer',
                                        helpString=u'Adds the CPIA viewer to the sidebar'),
                                    ]), # Menu AddAdditionalViews
                            MenuItem.template('TestTItem',
                                event=TestEvent,
                                title=u'Testing code',
                                helpString=u'Testing code')
                            ]), # Menu TestMenu
                    Menu.template('HelpMenu',
                        title=_(u'&Help'),
                        childrenBlocks=[
                            MenuItem.template('AboutChandlerItem',
                                event=globalBlocks.About,
                                title=_(u'About Chandler'),
                                helpString=_(u'About Chandler...')),
                            ]) # Menu HelpMenu
                    ]), # MenuBar MenuBar
            StatusBar.template('StatusBar'),
            ReminderTimer.template('ReminderTimer',
                                   event=ReminderTimerEvent),
            BoxContainer.template('ToolbarContainer',
                orientationEnum='Vertical',
                childrenBlocks=[
                    Toolbar.template('ApplicationBar',
                        stretchFactor=0.0,
                        toolSize=SizeType(26, 26),
                        buttonsLabeled=True,
                        separatorWidth=20,
                        childrenBlocks=[
                            ToolbarItem.template('ApplicationBarAllButton',
                                event=ApplicationBarAllEvent,
                                bitmap='ApplicationBarAll.png',
                                title=_(u"All"),
                                toolbarItemKind='Radio',
                                helpString=_(u'View all items')),
                            ToolbarItem.template('ApplicationBarMailButton',
                                event=ApplicationBarMailEvent,
                                bitmap='ApplicationBarMail.png',
                                title=_(u'Mail'),
                                toolbarItemKind='Radio',
                                helpString=_(u'View only mail')),
                            ToolbarItem.template('ApplicationBarTaskButton',
                                event=ApplicationBarTaskEvent,
                                bitmap='ApplicationBarTask.png',
                                title=_(u'Tasks'),
                                toolbarItemKind='Radio',
                                helpString=_(u'View only tasks')),
                            ToolbarItem.template('ApplicationBarEventButton',
                                event=ApplicationBarEventEvent,
                                bitmap='ApplicationBarEvent.png',
                                title=_(u'Calendar'),
                                selected=True,
                                toolbarItemKind='Radio',
                                helpString=_(u'View only events')),
                            ToolbarItem.template('ApplicationSeparator1',
                                toolbarItemKind='Separator'),
                            ToolbarItem.template('ApplicationBarSyncButton',
                                event=SyncAllEvent,
                                bitmap='ApplicationBarSync.png',
                                title=_(u'Sync All'),
                                toolbarItemKind='Button',
                                helpString=_(u'Get new Mail and synchronize with other Chandler users')),
                            ToolbarItem.template('ApplicationBarNewButton',
                                event=NewNoteEvent,
                                bitmap='ApplicationBarNew.png',
                                title=_(u'New'),
                                toolbarItemKind='Button',
                                helpString=_(u'Create a new Item')),
                            ToolbarItem.template('ApplicationSeparator2',
                                toolbarItemKind='Separator'),
                            ToolbarItem.template('ApplicationBarSendButton',
                                event=globalBlocks.SendShareItem,
                                bitmap='ApplicationBarSend.png',
                                title=messages.SEND,
                                toolbarItemKind='Button',
                                helpString=_(u'Send the selected Item')),
                            ]), # Toolbar ApplicationBar
                    BoxContainer.template('SidebarContainerContainer',
                        border=RectType(4, 0, 0, 0),
                        childrenBlocks=[
                            SplitterWindow.template('SidebarContainer',
                                stretchFactor=0.0,
                                border=RectType(0, 0, 0, 4.0),
                                childrenBlocks=[
                                    Sidebar,
                                    BoxContainer.template('PreviewAndMiniCalendar',
                                        orientationEnum='Vertical',
                                        childrenBlocks=[
                                            PreviewArea.template('PreviewArea',
                                                contents=app.allEventsCollection,
                                                calendarContainer=None,
                                                timeCharacterStyle = \
                                                    CharacterStyle.update(parcel, 
                                                                          'PreviewTimeStyle', 
                                                                          fontSize=10,
                                                                          fontStyle = 'bold'),
                                                eventCharacterStyle = \
                                                    CharacterStyle.update(parcel, 
                                                                          'PreviewEventStyle', 
                                                                          fontSize=11),
                                                stretchFactor=0.0),
                                            MiniCalendar.template('MiniCalendar',
                                                contents=app.allEventsCollection,
                                                calendarContainer = None,
                                                stretchFactor=0.0),
                                            ]) # BoxContainer PreviewAndMiniCalendar
                                    ]), # SplitterWindow SidebarContainer
                            TrunkParentBlock.template('SidebarTPB',
                                trunkDelegate=SidebarTrunkDelegateInstance,
                                TPBDetailItem=app.allCollection,
                                TPBSelectedItem=app.allCollection,
                                TPBDetailItemCollection=app.allCollection),
                            ]) # BoxContainer SidebarContainerContainer
                    ]), # BoxContainer ToolbarContainer
            ]) # MainView MainView
    mainview = mainview.install(parcel)

    MainTrunkDelegate = TrunkDelegate.update(parcel, 'MainTrunkDelegate')

    MainTPB = TrunkParentBlock.template('MainTPB',
                                        TPBDetailItem=mainview,
                                        TPBSelectedItem=mainview,
                                        childrenBlocks=[mainview],
                                        trunkDelegate=MainTrunkDelegate).install(parcel)

    # need to hook up cpia view here, but for now it will come in
    # via parcel.xml
    MainViewRoot = FrameWindow.update(parcel, 'MainViewRoot',
                                      size=SizeType(1024,720),
                                      views=[mainview],
                                      childrenBlocks=[MainTPB])


    # Add certstore UI
    schema.synchronize(repositoryView, "osaf.framework.certstore.blocks")

    return mainview

