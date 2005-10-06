
from osaf.framework.blocks import *
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

def make_mainview(parcel):

    # calling this 'events' for now because we might move
    # these specific events to their own place
    globalevents = schema.ns("osaf.framework.blocks", parcel.itsView)
    repositoryViewer = schema.ns("osaf.views.repositoryviewer", parcel.itsView)
    demo = schema.ns("osaf.views.demo", parcel.itsView)
    app  = schema.ns("osaf.app", parcel.itsView)

    ReminderItems = \
        pim.FilteredCollection.update(parcel, 'ReminderItems',
                                      displayName=_(u'Reminder Items'),
                                      indexName='reminderTime',
                                      source=app.events,
                                      filterExpression=u'item.hasLocalAttributeValue(\'reminderTime\')',
                                      filterAttributes=['reminderTime'])

    # these reference each other... ugh!
    RTimer = ReminderTimer.template('ReminderTimer').install(parcel)
    
    ReminderTimerEvent = \
        BlockEvent.template('ReminderTime',
                            'SendToBlockByReference',
                            destinationBlockReference=RTimer).install(parcel)
    
    ReminderTimer.update(parcel, 'ReminderTimer',
                         event=ReminderTimerEvent,
                         contents=ReminderItems)

    # from //parcels/osaf/views/main
    NewNoteEvent = \
        KindParameterizedEvent.template('NewNote',
            methodName='onNewEvent',
            kindParameter=osaf.pim.notes.Note.getKind(parcel.itsView),
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    RunSelectedScriptEvent = \
        BlockEvent.template('RunSelectedScript',
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
            kindParameter=osaf.pim.mail.MailMessageMixin.getKind(parcel.itsView),
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='Sidebar').install(parcel)
    # from //parcels/osaf/views/main
    ShowHideStatusBarEvent = \
        BlockEvent.template('ShowHideStatusBar',
            methodName='onShowHideEvent',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='StatusBar').install(parcel)
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
    ActivateWebserverEvent = \
        BlockEvent.template('ActivateWebserver',
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
            kindParameter=osaf.pim.mail.MailMessage.getKind(parcel.itsView),
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    EditCollectionRuleEvent = \
        BlockEvent.template('EditCollectionRule',
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
    # from //parcels/osaf/views/main
    ApplicationBarEventEvent = \
        KindParameterizedEvent.template('ApplicationBarEvent',
            methodName='onKindParameterizedEvent',
            kindParameter=osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(parcel.itsView),
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='Sidebar').install(parcel)
    # from //parcels/osaf/views/main
    NewCalendarEvent = \
        KindParameterizedEvent.template('NewCalendar',
            methodName='onNewEvent',
            kindParameter=osaf.pim.calendar.Calendar.CalendarEvent.getKind(parcel.itsView),
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
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
    SyncCollectionEvent = \
        BlockEvent.template('SyncCollection',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
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
            kindParameter=osaf.pim.tasks.Task.getKind(parcel.itsView),
            commitAfterDispatch=True,
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='MainView').install(parcel)
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
            selectFirstItemInBlockNamed = 'Sidebar',
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
            kindParameter=osaf.pim.tasks.TaskMixin.getKind(parcel.itsView),
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='Sidebar').install(parcel)
    # from //parcels/osaf/views/main
    AddDemoViewEvent = \
        ModifyCollectionEvent.template('AddDemoView',
            methodName='onModifyCollectionEvent',
            dispatchToBlockName='MainView',
            commitAfterDispatch=True,
            items=[demo.BlockDemoView],
            dispatchEnum='SendToBlockByName').install(parcel)
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
    ChooseCPIATestMainViewEvent = \
        ChoiceEvent.template('ChooseCPIATestMainView',
            dispatchEnum='SendToBlockByName',
            methodName='onChoiceEvent',
            choice='CPIATestMainView',
            dispatchToBlockName='MainViewRoot').install(parcel)
    EnableBusyBarsEvent = \
        BlockEvent.template('EnableBusyBars',
            dispatchEnum='SendToBlockByName',
            methodName='onEnableBusyBars',
            dispatchToBlockName='MiniCalendar').install(parcel)

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
                                event=globalevents.PrintPreview,
                                title=_(u'Print Preview')),
                            MenuItem.template('PrintItem',
                                event=globalevents.Print,
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
                                helpString= messages.ACCOUNT_PREFERENCES),
                            MenuItem.template('FileSeparator4',
                                menuItemKind='Separator'),
                            MenuItem.template('QuitItem',
                                event=globalevents.Quit,
                                title=_(u'Quit'),
                                accel=_(u'Ctrl+Q'),
                                helpString=_(u'Quit Chandler')),
                            ]), # Menu FileMenu
                    Menu.template('EditMenu',
                        title=_(u'&Edit'),
                        childrenBlocks=[
                            MenuItem.template('UndoItem',
                                event=globalevents.Undo,
                                title=messages.UNDO,
                                accel=_(u'Ctrl+Z'),
                                helpString=_(u"Can't Undo")),
                            MenuItem.template('RedoItem',
                                event=globalevents.Redo,
                                title=messages.REDO,
                                accel=_(u'Ctrl+Y'),
                                helpString=_(u"Can't Redo")),
                            MenuItem.template('EditSeparator1',
                                menuItemKind='Separator'),
                            MenuItem.template('CutItem',
                                event=globalevents.Cut,
                                title=messages.CUT,
                                accel=_(u'Ctrl+X')),
                            MenuItem.template('CopyItem',
                                event=globalevents.Copy,
                                title=messages.COPY,
                                accel=_(u'Ctrl+C')),
                            MenuItem.template('PasteItem',
                                event=globalevents.Paste,
                                title=messages.PASTE,
                                accel=_(u'Ctrl+V')),
                            MenuItem.template('ClearItem',
                                event=globalevents.Clear,
                                title=messages.CLEAR),
                            MenuItem.template('SelectAllItem',
                                event=globalevents.SelectAll,
                                title=messages.SELECT_ALL,
                                accel=_(u'Ctrl+A'),
                                helpString=messages.SELECT_ALL),
                            MenuItem.template('EditSeparator2',
                                menuItemKind='Separator'),
                            MenuItem.template('RemoveItem',
                                event=globalevents.Remove,
                                title=_(u'Remove'),
                                helpString=_(u'Move the current item to the trash')),
                            MenuItem.template('DeleteItem',
                                event=DeleteEvent,
                                title=_(u'Move to Trash'),
                                helpString=_(u'Move the current item to the trash')),
                            MenuItem.template('EmptyTrashItem',
                                event=EmptyTrashEvent,
                                title=_(u'Empty Trash'),
                                helpString=_(u'Remove all items from the Trash collection')),
                            ]), # Menu EditMenu
                    Menu.template('ViewMenu',
                        title=_(u'&View'),
                        childrenBlocks=[
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
                            MenuItem.template('StampMessageItem',
                                title=_(u'Send as Message'),
                                helpString=_(u'Stamp with Message attributes')),
                            MenuItem.template('StampTaskItem',
                                title=_(u'Put on Taskpad'),
                                helpString=_(u'Stamp with Task attributes')),
                            MenuItem.template('StampEventItem',
                                title=_(u'Put on Calendar'),
                                helpString=_(u'Stamp with Calendar Event attributes')),
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
                                title=_(u'Copy URL to clipboard'),
                                helpString=_(u"Copy the selected collection's URL to the clipboard")),
                            MenuItem.template('SyncCollectionItem',
                                event=SyncCollectionEvent,
                                title=_(u'Sync collection'),
                                helpString=_(u'Synchronize a shared collection')),
                            MenuItem.template('RenameItem',
                                title=_(u'Rename'),
                                helpString=_(u'Rename the selected collection')),
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
                            MenuItem.template('EditCollectionRuleItem',
                                event=EditCollectionRuleEvent,
                                title=u'Edit collection rule...',
                                helpString=u'Edit the rule of a collection'),
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
                            MenuItem.template('ActivateWebserverItem',
                                event=ActivateWebserverEvent,
                                title=u'Activate built-in webserver',
                                helpString=u'Activates the built-in webserver at localhost:1888'),
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
                                    MenuItem.template('AddDemoViewItem',
                                        event=AddDemoViewEvent,
                                        title=u'Add Block Demo View (Unstable)',
                                        helpString=u'Adds the block demo view to the sidebar (Known to be unstable on some systems)'),
                                    MenuItem.template('AddRepositoryViewItem',
                                        event=AddRepositoryViewEvent,
                                        title=u'Add Repository Viewer',
                                        helpString=u'Adds the repository viewer to the sidebar'),
                                    MenuItem.template('AddCPIAViewItem',
                                        event=AddCPIAViewEvent,
                                        title=u'Add CPIA Viewer',
                                        helpString=u'Adds the CPIA viewer to the sidebar'),
                                    ]), # Menu AddAdditionalViews
                            MenuItem.template('Enable Busy Bars',
                                event=EnableBusyBarsEvent,
                                title=u'EnableBusyBars',
                                helpString=u'Enable busy bars in the minicalendar'),
                            ]), # Menu TestMenu
                    Menu.template('HelpMenu',
                        title=_(u'&Help'),
                        childrenBlocks=[
                            MenuItem.template('AboutChandlerItem',
                                event=globalevents.About,
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
                                label=_(u"All"),
                                toolbarItemKind='Radio',
                                helpString=_(u'No Filter')),
                            ToolbarItem.template('ApplicationBarMailButton',
                                event=ApplicationBarMailEvent,
                                bitmap='ApplicationBarMail.png',
                                title=_(u'Messages'),
                                label=_(u'Mail'),
                                toolbarItemKind='Radio',
                                helpString=_(u'Mail Messages Filter')),
                            ToolbarItem.template('ApplicationBarTaskButton',
                                event=ApplicationBarTaskEvent,
                                bitmap='ApplicationBarTask.png',
                                title=_(u'Taskpad'),
                                label=_(u'Tasks'),
                                toolbarItemKind='Radio',
                                helpString=_(u'Tasks Filter')),
                            ToolbarItem.template('ApplicationBarEventButton',
                                event=ApplicationBarEventEvent,
                                bitmap='ApplicationBarEvent.png',
                                title=_(u'Calendar'),
                                selected=True,
                                label=_(u'Calendar'),
                                toolbarItemKind='Radio',
                                helpString=_(u'Calendar Events Filter')),
                            ToolbarItem.template('ApplicationSeparator1',
                                toolbarItemKind='Separator'),
                            ToolbarItem.template('ApplicationBarSyncButton',
                                event=SyncAllEvent,
                                bitmap='ApplicationBarSync.png',
                                title=_(u'Sync'),
                                label=_(u'Sync All'),
                                toolbarItemKind='Button',
                                helpString=_(u'Get new Mail and synchronize with other Chandler users')),
                            ToolbarItem.template('ApplicationBarNewButton',
                                event=NewNoteEvent,
                                bitmap='ApplicationBarNew.png',
                                title=_(u'New'),
                                label=_(u'New'),
                                toolbarItemKind='Button',
                                helpString=_(u'Create a new Item')),
                            ToolbarItem.template('ApplicationSeparator2',
                                toolbarItemKind='Separator'),
                            ToolbarItem.template('ApplicationBarSendButton',
                                event=globalevents.SendShareItem,
                                bitmap='ApplicationBarSend.png',
                                title=messages.SEND,
                                label=messages.SEND,
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
                                    SidebarBlock.template('Sidebar',
                                        columnReadOnly=[False],
                                        columnHeadings=[u''],
                                        border=RectType(0, 0, 4, 0),
                                        editRectOffsets=[17, -17, 0],
                                        buttons=[IconButton, SharingButton],
                                        selection=[[0,0]],
                                        contents=app.sidebarSelectionCollection,
                                        selectedItemToView=app.allCollection,
                                        elementDelegate='osaf.views.main.SideBar.SidebarElementDelegate',
                                        hideColumnHeadings=True,
                                        columnWidths=[150],
                                        columnData=[u'displayName'],
                                        filterKind=osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(parcel.itsView)),
                                    BoxContainer.template('PreviewAndMiniCalendar',
                                        orientationEnum='Vertical',
                                        childrenBlocks=[
                                            PreviewArea.template('PreviewArea',
                                                contents=app.allCollection,
                                                characterStyle= \
                                                    CharacterStyle.update(parcel, 'PreviewStyle', fontSize=11),
                                                stretchFactor=0.0),
                                            MiniCalendar.template('MiniCalendar',
                                                contents=app.allCollection,
                                                stretchFactor=0.0),
                                            ]) # BoxContainer PreviewAndMiniCalendar
                                    ]), # SplitterWindow SidebarContainer
                            TrunkParentBlock.template('SidebarTPB',
                                trunkDelegate=SidebarTrunkDelegateInstance,
                                TPBDetailItem=app.allCollection,
                                TPBSelectedItem=app.allCollection),
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

    # XXX TEMPORARY XXX
    # some scripting things here - moved from osaf.framework.scripting
    # because it was causing a circular dependency

    # keeping this, even though it refers to this parcel,
    # because this code will eventuall end up somewhere else
    main   = schema.ns('osaf.views.main', parcel)

    # "Scripts" Set
    scripts = pim.KindCollection.update(parcel, "scriptsSet")
    scripts.kind = scripting.Script.getKind(parcel.itsView)

    scriptsSet = pim.InclusionExclusionCollection.update(parcel, "scriptsInclusionExclusionCollection",
         displayName = _(u"Scripts"),
         renameable = False,
         private = False
         ).setup(source=scripts, trash=None)
    
    return mainview
