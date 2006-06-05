from osaf.usercollections import UserCollection
from osaf.framework.blocks import *

def makeMainEvents(parcel):

    from application import schema
    import osaf.pim.notes
    import osaf.pim.calendar
    import osaf.pim.mail
    import osaf.pim.tasks
    from osaf import pim, messages

    repositoryView = parcel.itsView

    BlockEvent.template(
        'ReminderTime',
        'SendToBlockByReference'
        # destinatinBlockReference is assigned in makeMakeView
        # because of a circular dependence
        ).install(parcel)
    
    NewItemEvent.update(
        parcel, 'NewItem',
        blockName = 'NewItem')

    NewItemEvent.update(
        parcel, 'NewNote',
        blockName = 'NewNote',
        kindParameter = osaf.pim.notes.Note.getKind(repositoryView))

    BlockEvent.template(
        'RunSelectedScript',
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    # Event to put "Scripts" in the Sidebar
    BlockEvent.template(
        'AddScriptsToSidebar',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'BackupRepository',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'CompactRepository',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'UnsubscribeSidebarCollection',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'SharingPublishFreeBusy',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'SharingUnpublishFreeBusy',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'CopyFreeBusyURL',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ShowPyCrust',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    KindParameterizedEvent.template(
        'ApplicationBarMail',
        methodName = 'onKindParameterizedEvent',
        kindParameter = osaf.pim.mail.MailMessageMixin.getKind(repositoryView),
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'Sidebar').install(parcel)

    BlockEvent.template(
        'ShowHideStatusBar',
        methodName = 'onShowHideEvent',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'StatusBar').install(parcel)

    BlockEvent.template(
        'EnableSections',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'EnableTimezones',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    # "Item" menu events
    BlockEvent.template(
        'FocusTogglePrivate',
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    KindParameterizedEvent.template(
        'FocusStampMessage',
        methodName = 'onFocusStampEvent',
        kindParameter = osaf.pim.mail.MailMessageMixin.getKind(repositoryView),
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    KindParameterizedEvent.template(
        'FocusStampTask',
        methodName = 'onFocusStampEvent',
        kindParameter = osaf.pim.tasks.TaskMixin.getKind(repositoryView),
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    KindParameterizedEvent.template(
        'FocusStampCalendar',
        methodName = 'onFocusStampEvent',
        kindParameter = osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(repositoryView),
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    BlockEvent.template(
        'SharingSubscribeToCollection',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'CheckRepository',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'i18nMailTest',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ShowLogWindow',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ActivateWebserver',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ActivateBackgroundSyncing',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'CommitRepository',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'GetNewMail',
        commitAfterDispatch = True,
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ManageSidebarCollection',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'StopProfiler',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ShowPyShell',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'EditAccountPreferences',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ShowHideSidebar',
        methodName = 'onShowHideEvent',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'SidebarContainer').install(parcel)

    BlockEvent.template(
        'ReloadParcels',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    KindParameterizedEvent.template(
        'ApplicationBarAll',
        methodName = 'onKindParameterizedEvent',
        kindParameter = None,
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'Sidebar').install(parcel)

    NewItemEvent.update(
        parcel, 'NewMailMessage',
        blockName = 'NewMailMessage',
        kindParameter = osaf.pim.mail.MailMessage.getKind(repositoryView))

    KindParameterizedEvent.template(
        'ApplicationBarEvent',
        methodName = 'onKindParameterizedEvent',
        kindParameter = osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(repositoryView),
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'Sidebar').install(parcel)

    NewItemEvent.update(
        parcel, 'NewCalendar',
        blockName = 'NewCalendar',
        kindParameter = osaf.pim.calendar.Calendar.CalendarEvent.getKind(repositoryView))

    BlockEvent.template(
        'Delete',
        commitAfterDispatch = True,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    repositoryViewer = schema.ns("osaf.views.repositoryviewer", repositoryView)
    
    AddToSidebarEvent.update(
        parcel, 'AddCPIAView',
        blockName = 'AddCPIAView',
        items = [repositoryViewer.CPIAView],
        copyItems = False)

    BlockEvent.template(
        'ShareSidebarCollection',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'StartProfiler',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'LoadLoggingConfig',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'SearchWindow',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'RestoreShares',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'SyncCollection',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ToggleMine',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'Sidebar').install(parcel)

    BlockEvent.template(
        'SharingImportDemoCalendar',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ShowHideApplicationBar',
        methodName = 'onShowHideEvent',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'ApplicationBar').install(parcel)

    NewItemEvent.update(
        parcel, 'NewTask',
        blockName = 'NewTask',
        kindParameter = osaf.pim.tasks.Task.getKind(repositoryView))

    BlockEvent.template(
        'GenerateContentItems',
        commitAfterDispatch = True,
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    AddToSidebarEvent.update(
        parcel, 'AddRepositoryView',
        blockName = 'AddRepositoryView',
        items = [repositoryViewer.RepositoryView],
        copyItems = False)

    ChoiceEvent.template(
        'ChooseChandlerMainView',
        dispatchEnum = 'SendToBlockByName',
        methodName = 'onChoiceEvent',
        choice = 'MainView',
        dispatchToBlockName = 'MainViewRoot').install(parcel)

    BlockEvent.template(
        'ExportIcalendar',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'SyncAll',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    untitledCollection = pim.SmartCollection.update(parcel,
        'untitledCollection',
        displayName=messages.UNTITLED)

    AddToSidebarEvent.update(
        parcel, 'NewCollection',
        blockName = 'NewCollection',
        editAttributeNamed = 'displayName',
        sphereCollection = schema.ns('osaf.pim', repositoryView).mine,
        items = [untitledCollection])
        
    AddToSidebarEvent.update(
        parcel, 'AddAllAdditionalViews',
        blockName = 'AddAllAdditionalViews',
        items = [repositoryViewer.RepositoryView, repositoryViewer.CPIAView],
        copyItems = False)

    BlockEvent.template(
        'GenerateContentItemsFromFile',
        commitAfterDispatch = True,
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    KindParameterizedEvent.template(
        'ApplicationBarTask',
        methodName = 'onKindParameterizedEvent',
        kindParameter = osaf.pim.tasks.TaskMixin.getKind(repositoryView),
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'Sidebar').install(parcel)

    BlockEvent.template(
        'EmptyTrash',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'UnpublishSidebarCollection',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'MimeTest',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'SyncWebDAV',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'WxTestHarness',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'ImportIcalendar',
        commitAfterDispatch = True,
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'CopyCollectionURL',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'TakeOnlineOffline',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    ChoiceEvent.template(
        'ChooseCPIATestMainView',
        dispatchEnum = 'SendToBlockByName',
        methodName = 'onChoiceEvent',
        choice = 'CPIATestMainView',
        dispatchToBlockName = 'MainViewRoot').install(parcel)

    BlockEvent.template(
        'RequestSelectSidebarItem',
        'SendToBlockByName',
        dispatchToBlockName = 'Sidebar').install(parcel)
    
    BlockEvent.template(
        'SendMail',
        'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)
                  
    BlockEvent.template(
        'SendShareItem',
        'FocusBubbleUp').install(parcel)

    BlockEvent.template(
        'ShareItem',
        'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)
                  
    BlockEvent.template(
        'SelectedDateChanged',
        'BroadcastEverywhere').install(parcel)
        
    BlockEvent.template(
        'DayMode',
        'BroadcastEverywhere').install(parcel)
        
