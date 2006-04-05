
def makeMainEvents(parcel):

    from osaf.framework.blocks import *
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
    
    NewEvent.template(
        'NewNote',
        methodName = 'onNewEvent',
        kindParameter = osaf.pim.notes.Note.getKind(repositoryView),
        commitAfterDispatch = True,
        dispatchEnum = 'ActiveViewBubbleUp').install(parcel)

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

    NewEvent.template(
        'NewMailMessage',
        methodName = 'onNewEvent',
        kindParameter = osaf.pim.mail.MailMessage.getKind(repositoryView),
        commitAfterDispatch = True,
        dispatchEnum = 'ActiveViewBubbleUp').install(parcel)

    KindParameterizedEvent.template(
        'ApplicationBarEvent',
        methodName = 'onKindParameterizedEvent',
        kindParameter = osaf.pim.calendar.Calendar.CalendarEventMixin.getKind(repositoryView),
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'Sidebar').install(parcel)

    NewEvent.template(
        'NewCalendar',
        methodName = 'onNewEvent',
        kindParameter = osaf.pim.calendar.Calendar.CalendarEvent.getKind(repositoryView),
        commitAfterDispatch = True,
        dispatchEnum = 'ActiveViewBubbleUp').install(parcel)

    BlockEvent.template(
        'Delete',
        commitAfterDispatch = True,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    repositoryViewer = schema.ns("osaf.views.repositoryviewer", repositoryView)
    ModifyCollectionEvent.template(
        'AddCPIAView',
        methodName = 'onModifyCollectionEvent',
        dispatchToBlockName = 'MainView',
        commitAfterDispatch = True,
        items = [repositoryViewer.CPIAView],
        dispatchEnum = 'SendToBlockByName').install(parcel)

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

    NewEvent.template(
        'NewTask',
        methodName = 'onNewEvent',
        kindParameter = osaf.pim.tasks.Task.getKind(repositoryView),
        commitAfterDispatch = True,
        dispatchEnum = 'ActiveViewBubbleUp').install(parcel)

    BlockEvent.template(
        'GenerateContentItems',
        commitAfterDispatch = True,
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    ModifyCollectionEvent.template(
        'AddRepositoryView',
        methodName = 'onModifyCollectionEvent',
        dispatchToBlockName = 'MainView',
        commitAfterDispatch = True,
        items = [repositoryViewer.RepositoryView],
        dispatchEnum = 'SendToBlockByName').install(parcel)

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

    NewEvent.template(
        'NewCollection',
        methodName = 'onNewCollection',
        kindParameter = osaf.pim.SmartCollection.getKind(repositoryView),
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'Sidebar').install(parcel)
        
    BlockEvent.template(
        'ImportImage',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    ModifyCollectionEvent.template(
        'AddAllAdditionalViews',
        methodName = 'onModifyCollectionEvent',
        dispatchToBlockName = 'MainView',
        commitAfterDispatch = True,
        items = [repositoryViewer.RepositoryView, repositoryViewer.CPIAView],
        dispatchEnum = 'SendToBlockByName').install(parcel)

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
        
