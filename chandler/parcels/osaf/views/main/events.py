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


from osaf.framework.blocks import (
    AddToSidebarEvent, BlockEvent, NewItemEvent, NewBlockWindowEvent,
    ClassParameterizedEvent, ChoiceEvent, ViewEvent)
from osaf.framework.blocks.calendar import CalendarViewEvent


def makeMainEvents(parcel):

    from application import schema
    import osaf.pim.notes
    import osaf.pim.calendar
    import osaf.pim.mail
    import osaf.pim.tasks
    from osaf import pim, messages

    repositoryView = parcel.itsView

    # NewItemEvent's commitAfterDispatch defaults to True
    NewItemEvent.update(parcel, 'NewItem',
                        blockName = 'NewItem')

    NewItemEvent.update(parcel, 'NewNote',
                        blockName = 'NewNote',
                        classParameter = osaf.pim.notes.Note)

    NewItemEvent.update(parcel, 'NewMailMessage',
                        blockName = 'NewMailMessage',
                        classParameter = osaf.pim.mail.MailStamp)

    NewItemEvent.update(parcel, 'NewCalendar',
                        blockName = 'NewCalendar',
                        classParameter = osaf.pim.calendar.Calendar.EventStamp)

    NewItemEvent.update(parcel, 'DisplayMailMessage',
                        blockName = 'DisplayMailMessage',
                        dispatchEnum = 'SendToBlockByName',
                        dispatchToBlockName = 'MainView',
                        collection = schema.ns("osaf.pim", repositoryView).outCollection)

    BlockEvent.template('ReminderTime',
                        dispatchEnum = 'SendToBlockByReference'
                        # destinatinBlockReference is assigned in makeMakeView
                        # because of a circular dependence
                        ).install(parcel)
    
    BlockEvent.template('AddSharingLogToSidebar',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('ResetShare',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('RecordSetDebugging',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('SwitchRepository').install(parcel)

    BlockEvent.template('CreateRepository').install(parcel),

    BlockEvent.template('CompactRepository').install(parcel)

    BlockEvent.template('IndexRepository').install(parcel)

    BlockEvent.template('UnsubscribePublishedCollection',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('UnpublishCollection',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('UnsubscribeCollection',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('ShowHideStatusBar',
                        methodName = 'onShowHideEvent',
                        dispatchToBlockName = 'StatusBar').install(parcel)

    BlockEvent.template('SyncManager',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('EnableTimezones',
                        commitAfterDispatch = True).install(parcel)

    # "Item" menu events
    BlockEvent.template('FocusTogglePrivate',
                        dispatchEnum = 'FocusBubbleUp',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('MarkAsRead',
                        dispatchEnum = 'FocusBubbleUp',
                        commitAfterDispatch = True).install(parcel)

    ClassParameterizedEvent.template('FocusStampMessage',
                                     methodName = 'onFocusStampEvent',
                                     classParameter = osaf.pim.mail.MailStamp,
                                     dispatchEnum = 'FocusBubbleUp',
                                     commitAfterDispatch = True).install(parcel)

    ClassParameterizedEvent.template('FocusStampTask',
                                     methodName = 'onFocusStampEvent',
                                     classParameter = osaf.pim.tasks.TaskStamp,
                                     dispatchEnum = 'FocusBubbleUp',
                                     commitAfterDispatch = True).install(parcel)

    ClassParameterizedEvent.template('FocusStampCalendar',
                                     methodName = 'onFocusStampEvent',
                                     classParameter = osaf.pim.calendar.Calendar.EventStamp,
                                     dispatchEnum = 'FocusBubbleUp',
                                     commitAfterDispatch = True).install(parcel)

    ClassParameterizedEvent.template('ReplyMessage',
                                     methodName = 'onReplyEvent',
                                     classParameter = osaf.pim.mail.MailStamp,
                                     dispatchEnum = 'FocusBubbleUp',
                                     commitAfterDispatch = True).install(parcel)

    ClassParameterizedEvent.template('ReplyAllMessage',
                                     methodName = 'onReplyAllEvent',
                                     classParameter = osaf.pim.mail.MailStamp,
                                     dispatchEnum = 'FocusBubbleUp',
                                     commitAfterDispatch = True).install(parcel)

    ClassParameterizedEvent.template('ForwardMessage',
                                     methodName = 'onForwardEvent',
                                     classParameter = osaf.pim.mail.MailStamp,
                                     dispatchEnum = 'FocusBubbleUp',
                                     commitAfterDispatch = True).install(parcel)

    BlockEvent.template('SubscribeToCollection',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('CheckRepository').install(parcel)

    BlockEvent.template('CheckAndRepairRepository').install(parcel)

    BlockEvent.template('i18nMailTest',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('ShowLogWindow').install(parcel)

    BlockEvent.template('ActivateWebserver').install(parcel)

    BlockEvent.template('ShowActivityViewer').install(parcel)

    BlockEvent.template('GetNewMail',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('ManageSidebarCollection').install(parcel)

    BlockEvent.template('SaveSettings').install(parcel)

    BlockEvent.template('RestoreSettings',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('EditAccountPreferences').install(parcel)

    BlockEvent.template('LocalePicker').install(parcel)

    BlockEvent.template('ConfigureProxies').install(parcel)

    BlockEvent.template('ProtectPasswords',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('ShowHideSidebar',
                        methodName = 'onShowHideEvent',
                        dispatchToBlockName = 'SidebarContainer').install(parcel)

    BlockEvent.template('Triage',
                        dispatchToBlockName = 'DashboardSummaryView',
                        commitAfterDispatch = True).install(parcel)

    ClassParameterizedEvent.template('ApplicationBarAll',
                                     methodName = 'onClassParameterizedEvent',
                                     dispatchToBlockName = 'Sidebar').install(parcel)

    ClassParameterizedEvent.template('ApplicationBarEvent',
                                     methodName = 'onClassParameterizedEvent',
                                     classParameter = osaf.pim.calendar.Calendar.EventStamp,
                                     dispatchToBlockName = 'Sidebar').install(parcel)

    ClassParameterizedEvent.template('ApplicationBarTask',
                                     methodName = 'onClassParameterizedEvent',
                                     classParameter = osaf.pim.tasks.TaskStamp,
                                     dispatchToBlockName = 'Sidebar').install(parcel)

    BlockEvent.template('PublishCollection').install(parcel)

    BlockEvent.template('SetLoggingLevelCritical').install(parcel)

    BlockEvent.template('SetLoggingLevelError').install(parcel)

    BlockEvent.template('SetLoggingLevelWarning').install(parcel)

    BlockEvent.template('SetLoggingLevelInfo').install(parcel)

    BlockEvent.template('SetLoggingLevelDebug').install(parcel)

    BlockEvent.template('RestoreShares').install(parcel)

    BlockEvent.template('SyncPrefs').install(parcel)

    BlockEvent.template('SyncCollection').install(parcel)

    BlockEvent.template('ToggleMine',
                        dispatchToBlockName = 'Sidebar',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('DumpToFile').install(parcel)

    BlockEvent.template('ObfuscatedDumpToFile').install(parcel)

    BlockEvent.template('ReloadFromFile',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('ShowHideApplicationBar',
                        methodName = 'onShowHideEvent',
                        dispatchToBlockName = 'ApplicationBar').install(parcel)

    BlockEvent.template('SyncAll').install(parcel)

    untitledCollection = pim.SmartCollection.update(parcel,
                                                    'untitledCollection',
                                                    displayName=messages.UNTITLED)

    AddToSidebarEvent.update(
        parcel, 'NewCollection',
        blockName = 'NewCollection',
        editAttributeNamed = 'displayName',
        sphereCollection = schema.ns('osaf.pim', repositoryView).mine,
        item = untitledCollection)
        
    BlockEvent.template('EmptyTrash',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('SyncWebDAV').install(parcel)

    BlockEvent.template('ImportICalendar').install(parcel)
    BlockEvent.template('ExportICalendar').install(parcel)

    BlockEvent.template('CollectionInvite').install(parcel)

    BlockEvent.template('TakeOnlineOffline',
                       commitAfterDispatch = True).install(parcel)

    BlockEvent.template('TakeAllOnlineOffline').install(parcel)
    
    BlockEvent.template('TakeMailOnlineOffline').install(parcel)

    BlockEvent.template('TakeSharesOnlineOffline').install(parcel)

    BlockEvent.template('RequestSelectSidebarItem',
                        dispatchToBlockName = 'Sidebar').install(parcel)
    
    BlockEvent.template('SendMail',
                       commitAfterDispatch = True).install(parcel)

    BlockEvent.template('QuickEntry',
                        dispatchEnum = 'FocusBubbleUp').install(parcel)

    BlockEvent.template('Search',
                        commitAfterDispatch = True,
                        dispatchEnum = 'FocusBubbleUp').install(parcel)
                        
    BlockEvent.template('SwitchToQuickEntry',
                        commitAfterDispatch = True,
                        dispatchEnum = 'FocusBubbleUp').install(parcel)

    BlockEvent.template('SendShareItem',
                        commitAfterDispatch = True,
                        dispatchEnum = 'FocusBubbleUp').install(parcel)

    BlockEvent.template('SelectedDateChanged',
                        dispatchEnum = 'BroadcastEverywhere').install(parcel)
    
    BlockEvent.template('DayMode',
                        dispatchEnum = 'BroadcastEverywhere').install(parcel)
        
    CalendarViewEvent.template('ViewAsDayCalendar',
                               viewTemplatePath = 'osaf.views.main.CalendarSummaryViewTemplate',
                               methodName = 'onViewEvent',
                               dayMode = 'day',
                               dispatchToBlockName = 'SidebarBranchPointBlock').install(parcel)

    CalendarViewEvent.template('ViewAsWeekCalendar',
                               viewTemplatePath = 'osaf.views.main.CalendarSummaryViewTemplate',
                               methodName = 'onViewEvent',
                               dayMode = 'week',
                               dispatchToBlockName = 'SidebarBranchPointBlock').install(parcel)

    CalendarViewEvent.template('ViewAsMultiWeek',
                       viewTemplatePath = 'osaf.views.main.MultiWeekViewTemplate',
                       methodName = 'onViewEvent',
                       dayMode = 'multiweek',
                       dispatchToBlockName = 'SidebarBranchPointBlock').install(parcel)

    ViewEvent.template('ViewAsDashboard',
                       viewTemplatePath = 'Dashboard',
                       methodName = 'onViewEvent',
                       dispatchToBlockName = 'SidebarBranchPointBlock').install(parcel)

    BlockEvent.template('DuplicateSidebarSelection',
                        methodName = 'onDuplicateEvent',
                        dispatchToBlockName = 'Sidebar',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('RenameCollection',
                        methodName = 'onRenameEvent',
                        dispatchToBlockName = 'Sidebar',
                        commitAfterDispatch = True).install(parcel),
    
    BlockEvent.template('DeleteCollection',
                        methodName = 'onDeleteEvent',
                        dispatchToBlockName = 'Sidebar',
                        commitAfterDispatch = True).install(parcel),

    BlockEvent.template('DeleteInActiveView',
                        methodName = 'onDeleteEvent',
                        dispatchEnum = 'ActiveViewBubbleUp',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('RemoveInActiveView',
                        dispatchEnum = 'ActiveViewBubbleUp',
                        methodName = 'onRemoveEvent',
                        commitAfterDispatch = True).install(parcel),

    BlockEvent.template('CutInActiveView',
                        dispatchEnum = 'ActiveViewBubbleUp',
                        methodName = 'onCutEvent',
                        commitAfterDispatch = True).install(parcel),

    BlockEvent.template('CopyInActiveView',
                        dispatchEnum = 'ActiveViewBubbleUp',
                        methodName = 'onCopyEvent',
                        commitAfterDispatch = True).install(parcel),

    BlockEvent.template('DuplicateInActiveView',
                        dispatchEnum = 'ActiveViewBubbleUp',
                        methodName = 'onDuplicateEvent',
                        commitAfterDispatch = True).install(parcel),

    BlockEvent.template('PasteInActiveView',
                        dispatchEnum = 'ActiveViewBubbleUp',
                        methodName = 'onPasteEvent',
                        commitAfterDispatch = True).install(parcel),

    BlockEvent.template('BrowsePlugins',
                        dispatchToBlockName = 'PluginsMenu').install(parcel)

    BlockEvent.template('InstallPlugins',
                        dispatchToBlockName = 'PluginsMenu',
                        commitAfterDispatch = True).install(parcel)

    BlockEvent.template('Plugin',
                        dispatchToBlockName = 'PluginsMenu',
                        commitAfterDispatch = True).install(parcel)

    AddToSidebarEvent.update(
        parcel, 'SaveResults',
        blockName = 'SaveResults',
        editAttributeNamed = 'displayName',
        sphereCollection = schema.ns('osaf.pim', repositoryView).mine,
        item = schema.ns('osaf.pim', repositoryView).searchResults)
        
