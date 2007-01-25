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


import PyLucene, wx
from osaf import pim, search
from i18n import ChandlerMessageFactory as _
from application import schema
from application.dialogs import Util
from osaf.usercollections import UserCollection
from osaf.framework.blocks import (
    AddToSidebarEvent, BlockEvent, NewItemEvent, NewBlockWindowEvent,
    ClassParameterizedEvent, ChoiceEvent)

from osaf import pim
from osaf.framework.blocks.Block import Block
from repository.item.Item import MissingClass


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
        dispatchEnum = 'SendToBlockByReference'
        # destinatinBlockReference is assigned in makeMakeView
        # because of a circular dependence
        ).install(parcel)
    
    NewItemEvent.update(
        parcel, 'NewItem',
        blockName = 'NewItem')

    NewItemEvent.update(
        parcel, 'NewNote',
        blockName = 'NewNote',
        classParameter = osaf.pim.notes.Note)

    BlockEvent.template(
        'RunSelectedScript',
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    # Event to put "Scripts" in the Sidebar
    BlockEvent.template('AddScriptsToSidebar').install(parcel)

    BlockEvent.template('AddSharingLogToSidebar').install(parcel)

    BlockEvent.template('CompactRepository').install(parcel)

    BlockEvent.template('IndexRepository').install(parcel)

    BlockEvent.template('UnsubscribeSidebarCollection').install(parcel)

    BlockEvent.template('SharingPublishFreeBusy').install(parcel)

    BlockEvent.template('SharingUnpublishFreeBusy').install(parcel)

    BlockEvent.template('CopyFreeBusyURL').install(parcel)

    BlockEvent.template('ShowPyCrust').install(parcel)

    ClassParameterizedEvent.template(
        'ApplicationBarMail',
        methodName = 'onClassParameterizedEvent',
        classParameter = osaf.pim.mail.MailStamp,
        dispatchToBlockName = 'Sidebar').install(parcel)

    BlockEvent.template(
        'ShowHideStatusBar',
        methodName = 'onShowHideEvent',
        dispatchToBlockName = 'StatusBar').install(parcel)

    BlockEvent.template('EnableSections').install(parcel)

    BlockEvent.template('EnableTimezones').install(parcel)

    # "Item" menu events
    BlockEvent.template(
        'FocusTogglePrivate',
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    ClassParameterizedEvent.template(
        'FocusStampMessage',
        methodName = 'onFocusStampEvent',
        classParameter = osaf.pim.mail.MailStamp,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    ClassParameterizedEvent.template(
        'FocusStampTask',
        methodName = 'onFocusStampEvent',
        classParameter = osaf.pim.tasks.TaskStamp,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    ClassParameterizedEvent.template(
        'FocusStampCalendar',
        methodName = 'onFocusStampEvent',
        classParameter = osaf.pim.calendar.Calendar.EventStamp,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    ClassParameterizedEvent.template(
        'ReplyMessage',
        methodName = 'onReplyEvent',
        classParameter = osaf.pim.mail.MailStamp,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    ClassParameterizedEvent.template(
        'ReplyAllMessage',
        methodName = 'onReplyAllEvent',
        classParameter = osaf.pim.mail.MailStamp,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    ClassParameterizedEvent.template(
        'ForwardMessage',
        methodName = 'onForwardEvent',
        classParameter = osaf.pim.mail.MailStamp,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    BlockEvent.template('SharingSubscribeToCollection').install(parcel)

    BlockEvent.template('CheckRepository').install(parcel)

    BlockEvent.template('CheckAndRepairRepository').install(parcel)

    BlockEvent.template('i18nMailTest').install(parcel)

    BlockEvent.template('ShowI18nManagerDebugWindow').install(parcel)

    BlockEvent.template('ShowMeAddressCollectionDebugWindow').install(parcel)

    BlockEvent.template('ShowLogWindow').install(parcel)

    BlockEvent.template('ActivateWebserver').install(parcel)

    BlockEvent.template('BackgroundSyncAll').install(parcel)

    BlockEvent.template('BackgroundSyncGetOnly').install(parcel)

    BlockEvent.template('ToggleReadOnlyMode').install(parcel)

    BlockEvent.template('EditMyName').install(parcel)

    BlockEvent.template('GetNewMail',
                       commitAfterDispatch = True).install(parcel)

    BlockEvent.template('ManageSidebarCollection').install(parcel)

    BlockEvent.template('StopProfiler').install(parcel)

    BlockEvent.template('ShowPyShell').install(parcel)

    BlockEvent.template('SaveSettings').install(parcel)

    BlockEvent.template('RestoreSettings').install(parcel)

    BlockEvent.template('EditAccountPreferences').install(parcel)

    BlockEvent.template(
        'ShowHideSidebar',
        methodName = 'onShowHideEvent',
        dispatchToBlockName = 'SidebarContainer').install(parcel)

    BlockEvent.template('ReloadParcels').install(parcel)

    BlockEvent.template(
        'ReloadStyles',
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'MainView').install(parcel)

    BlockEvent.template(
        'Triage',
        commitAfterDispatch = True,
        dispatchEnum = 'SendToBlockByName',
        dispatchToBlockName = 'DashboardSummaryView').install(parcel)

    ClassParameterizedEvent.template(
        'ApplicationBarAll',
        methodName = 'onClassParameterizedEvent',
        dispatchToBlockName = 'Sidebar').install(parcel)

    NewItemEvent.update(
        parcel, 'NewMailMessage',
        blockName = 'NewMailMessage',
        classParameter = osaf.pim.mail.MailStamp)

    ClassParameterizedEvent.template(
        'ApplicationBarEvent',
        methodName = 'onClassParameterizedEvent',
        classParameter = osaf.pim.calendar.Calendar.EventStamp,
        dispatchToBlockName = 'Sidebar').install(parcel)

    NewItemEvent.update(
        parcel, 'NewCalendar',
        blockName = 'NewCalendar',
        classParameter = osaf.pim.calendar.Calendar.EventStamp)

    BlockEvent.template(
        'Delete',
        commitAfterDispatch = True,
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    BlockEvent.template('ShareSidebarCollection').install(parcel)

    BlockEvent.template('StartProfiler').install(parcel)

    BlockEvent.template('SetLoggingLevelCritical').install(parcel)

    BlockEvent.template('SetLoggingLevelError').install(parcel)

    BlockEvent.template('SetLoggingLevelWarning').install(parcel)

    BlockEvent.template('SetLoggingLevelInfo').install(parcel)

    BlockEvent.template('SetLoggingLevelDebug').install(parcel)

    BlockEvent.template('RestoreShares').install(parcel)

    BlockEvent.template('SyncPrefs').install(parcel)

    BlockEvent.template('RestoreShares').install(parcel)

    BlockEvent.template('SyncCollection').install(parcel)

    BlockEvent.template(
        'ToggleMine',
        dispatchToBlockName = 'Sidebar').install(parcel)

    BlockEvent.template('SharingImportDemoCalendar').install(parcel)

    BlockEvent.template(
        'ShowHideApplicationBar',
        methodName = 'onShowHideEvent',
        dispatchToBlockName = 'ApplicationBar').install(parcel)

    NewItemEvent.update(
        parcel, 'NewTask',
        blockName = 'NewTask',
        classParameter = osaf.pim.tasks.TaskStamp)

    BlockEvent.template('GenerateContentItems',
                        commitAfterDispatch = True).install(parcel)

    ChoiceEvent.template(
        'ChooseChandlerMainView',
        methodName = 'onChoiceEvent',
        choice = 'MainView',
        dispatchToBlockName = 'MainViewRoot').install(parcel)

    BlockEvent.template('ExportIcalendar').install(parcel)

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
        
    BlockEvent.template('GenerateContentItemsFromFile',
                       commitAfterDispatch = True).install(parcel)

    ClassParameterizedEvent.template(
        'ApplicationBarTask',
        methodName = 'onClassParameterizedEvent',
        classParameter = osaf.pim.tasks.TaskStamp,
        dispatchToBlockName = 'Sidebar').install(parcel)

    BlockEvent.template('EmptyTrash').install(parcel)

    BlockEvent.template('UnpublishSidebarCollection').install(parcel)

    BlockEvent.template('MimeTest').install(parcel)

    BlockEvent.template('SyncWebDAV').install(parcel)

    BlockEvent.template('WxTestHarness').install(parcel)

    BlockEvent.template('ImportIcalendar',
                       commitAfterDispatch = True).install(parcel)

    BlockEvent.template('CopyCollectionURL').install(parcel)

    BlockEvent.template('TakeOnlineOffline').install(parcel)
    BlockEvent.template('TakeMailOnlineOffline').install(parcel)

    ChoiceEvent.template(
        'ChooseCPIATestMainView',
        methodName = 'onChoiceEvent',
        choice = 'CPIATestMainView',
        dispatchToBlockName = 'MainViewRoot').install(parcel)

    ChoiceEvent.template(
        'ChooseCPIATest2MainView',
        methodName = 'onChoiceEvent',
        choice = 'CPIATest2MainView',
        dispatchToBlockName = 'MainViewRoot').install(parcel)

    BlockEvent.template(
        'RequestSelectSidebarItem',
        dispatchToBlockName = 'Sidebar').install(parcel)
    
    BlockEvent.template('SendMail').install(parcel)
                  
    BlockEvent.template(
        'QuickEntry',
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    BlockEvent.template(
        'SendShareItem',
        dispatchEnum = 'FocusBubbleUp').install(parcel)

    BlockEvent.template('ShareItem').install(parcel)
                  
    BlockEvent.template(
        'SelectedDateChanged',
        dispatchEnum = 'BroadcastEverywhere').install(parcel)
    
    BlockEvent.template(
        'DayMode',
        dispatchEnum = 'BroadcastEverywhere').install(parcel)
        
    blockViewer = schema.ns("osaf.views.blockviewer", repositoryView)
    
    NewBlockWindowEvent.update(
        parcel, 'ShowBlockViewer',
        blockName = 'ShowBlockViewer',
        treeOfBlocks = blockViewer.BlockViewerFrameWindow)

    repositoryViewer = schema.ns("osaf.views.repositoryviewer", repositoryView)

    NewBlockWindowEvent.update(
        parcel, 'ShowRepositoryViewer',
        blockName = 'ShowBlockViewer',
        treeOfBlocks = repositoryViewer.RepositoryViewerFrameWindow)

