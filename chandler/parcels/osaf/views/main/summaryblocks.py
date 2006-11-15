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
from osaf import pim
import wx.grid

# IndexDefinition subclasses for the dashboard indexes
# These all create 'compare' indexes for now, and add the comparison function
# to ContentItem - the functions take two items. Eventually, they'll probably
# be rewritten as 'method' indexes; the functions will take two UUIDs and won't 
# need to be added to ContentItem.
def compareForDashboardTaskColumn(item1, item2):
    return (cmp(not pim.has_stamp(item1, pim.TaskStamp), 
                not pim.has_stamp(item2, pim.TaskStamp)) or
            cmp(getattr(item1, 'triageStatus', pim.TriageEnum.done), 
                getattr(item2, 'triageStatus', pim.TriageEnum.done)) or
            cmp(getattr(item1, 'triageStatusChanged', 0), 
                getattr(item2, 'triageStatusChanged', 0)))
pim.ContentItem.compareForDashboardTaskColumn = compareForDashboardTaskColumn

class TaskColumnIndexDefinition(pim.IndexDefinition):
    def makeIndexOn(self, collection):
        collection.addIndex(self.itsName, 'compare',
                            compare='compareForDashboardTaskColumn',
                            monitor=(pim.ContentItem.displayName.name,
                                     pim.ContentItem.triageStatus.name,
                                     pim.ContentItem.triageStatusChanged.name,))

def compareForDashboardCommunicationColumn(item1, item2):
    def readUnreadNeedsReplyState(item):
        if not getattr(item, 'read', False):
            return 0
        if getattr(item, 'needsReply', False):
            return 1
        return 2
    return (cmp(readUnreadNeedsReplyState(item1), readUnreadNeedsReplyState(item2)) or
            cmp(getattr(item1, 'triageStatus', pim.TriageEnum.done), 
                getattr(item2, 'triageStatus', pim.TriageEnum.done)) or
            cmp(getattr(item1, 'triageStatusChanged', 0), 
                getattr(item2, 'triageStatusChanged', 0)))
pim.ContentItem.compareForDashboardCommunicationColumn = compareForDashboardCommunicationColumn

class CommunicationColumnIndexDefinition(pim.IndexDefinition):
    def makeIndexOn(self, collection):
        collection.addIndex(self.itsName, 'compare',
                            compare='compareForDashboardCommunicationColumn',
                            monitor=(pim.ContentItem.read.name,
                                     pim.ContentItem.needsReply.name,
                                     pim.ContentItem.triageStatus.name,
                                     pim.ContentItem.triageStatusChanged.name,))

def compareForDashboardCalendarColumn(item1, item2):
    def remState(item):
        if pim.Remindable(item).getUserReminder(expiredToo=True) is not None:
            return 0
        if pim.has_stamp(item, pim.EventStamp):
            return 1
        return 2
    return (cmp(remState(item1), remState(item2)) or
            cmp(getattr(item1, 'displayDate', pim.Reminder.farFuture), 
                getattr(item2, 'displayDate', pim.Reminder.farFuture)) or
            cmp(getattr(item1, 'triageStatus', pim.TriageEnum.done), 
                getattr(item2, 'triageStatus', pim.TriageEnum.done)) or
            cmp(getattr(item1, 'triageStatusChanged', 0), 
                getattr(item2, 'triageStatusChanged', 0)))
pim.ContentItem.compareForDashboardCalendarColumn = compareForDashboardCalendarColumn
        
class CalendarColumnIndexDefinition(pim.IndexDefinition):
    def makeIndexOn(self, collection):
        collection.addIndex(self.itsName, 'compare',
                            compare='compareForDashboardCalendarColumn',
                            monitor=(pim.Remindable.reminders.name,
                                     pim.Stamp.stamp_types.name,
                                     pim.ContentItem.displayDate.name,
                                     pim.ContentItem.triageStatus.name,
                                     pim.ContentItem.triageStatusChanged.name,))

def makeSummaryBlocks(parcel):
    from application import schema
    from i18n import ChandlerMessageFactory as _
    from osaf.framework.blocks.calendar import (
        CalendarContainer, CalendarControl, CanvasSplitterWindow,
        AllDayEventsCanvas, TimedEventsCanvas
        )

    from Dashboard import DashboardBlock
    
    view = parcel.itsView
    detailblocks = schema.ns('osaf.views.detail', view)
    pim_ns = schema.ns('osaf.pim', view)
    blocks = schema.ns('osaf.framework.blocks', view)
    repositoryView = parcel.itsView
    
    iconColumnWidth = 23 # temporarily not 20, to work around header bug 6168    
    
    def makeColumnAndIndexes(colName, **kwargs):
        # Create an IndexDefinition that will be used later (when the user
        # clicks on the column header) to build the actual index.
        # By default, we always create index defs that will lazily create a
        # master index when the subindex is needed.
        indexName = kwargs['indexName']
        attributes = kwargs.pop('attributes', [])
        useCompare = kwargs.pop('useCompare', False)
        useMaster = kwargs.pop('useMaster', True)
        baseClass = kwargs.pop('baseClass', pim.IndexDefinition)
        baseClass.update(parcel, indexName,
                         useMaster=useMaster,
                         attributes=attributes)

        # Create the column
        return Column.update(parcel, colName, **kwargs)

    taskColumn = makeColumnAndIndexes('SumColTask',
        icon='ColHTask',
        valueType = 'stamp',
        stamp=pim.TaskStamp,
        width=iconColumnWidth,
        useSortArrows=False,
        scaleColumn = wx.grid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly=True,
        indexName='%s.taskStatus' % __name__,
        baseClass=TaskColumnIndexDefinition)

    commColumn = makeColumnAndIndexes('SumColMail',
        icon='ColHMail',
        valueType='stamp',
        stamp=pim.mail.MailStamp,
        width=iconColumnWidth,
        useSortArrows=False,
        scaleColumn = wx.grid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly=True,
        indexName='%s.communicationStatus' % __name__,
        attributeName='communicationStatus',
        attributes=[
            # pim.mail.MailStamp.communicationStatus.name, 
            pim.ContentItem.triageStatus.name, 
            pim.ContentItem.triageStatusChanged.name,
        ])

    whoColumn = makeColumnAndIndexes('SumColWho',
        heading=_(u'Who'),
        width=100,
        scaleColumn = wx.grid.Grid.GRID_COLUMN_SCALABLE,
        readOnly=True,
        indexName='%s.displayWho' % __name__,
        attributeName='displayWho',
        attributeSourceName = 'displayWhoSource',
        attributes=[
            pim.ContentItem.displayWho.name,
            pim.ContentItem.displayDate.name,
        ])
    
    titleColumn = makeColumnAndIndexes('SumColAbout',
        heading=_(u'Title'),
        width=120,
        scaleColumn = wx.grid.Grid.GRID_COLUMN_SCALABLE,
        indexName='%s.displayName' % __name__,
        attributeName='displayName',
        attributes=[
            pim.ContentItem.displayName.name, 
            pim.ContentItem.displayDate.name,
        ])

    reminderColumn = makeColumnAndIndexes('SumColCalendarEvent',
        icon = 'ColHEvent',
        valueType = 'stamp',
        stamp = pim.EventStamp,
        useSortArrows = False,
        width = iconColumnWidth,
        scaleColumn = wx.grid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly = True,
        indexName = '%s.calendarStatus' % __name__,
        baseClass=CalendarColumnIndexDefinition)

    dateColumn = makeColumnAndIndexes('SumColDate',
        heading = _(u'Date'),
        width = 100,
        scaleColumn = wx.grid.Grid.GRID_COLUMN_SCALABLE,
        readOnly = True,
        attributeName = 'displayDate',
        attributeSourceName = 'displayDateSource',
        indexName = '%s.displayDate' % __name__,
        attributes=[
            pim.ContentItem.displayDate.name, 
            pim.ContentItem.triageStatus.name, 
            pim.ContentItem.triageStatusChanged.name,
        ])
    
    triageColumn = makeColumnAndIndexes('SumColTriage',
        icon = 'ColHTriageStatus',
        useSortArrows = False,
        defaultSort = True,
        width = 40,
        scaleColumn = wx.grid.Grid.GRID_COLUMN_FIXED_SIZE,
        attributeName = 'triageStatus',
        indexName = '%s.triageStatus' % __name__,
        attributes=[
            pim.ContentItem.triageStatus.name, 
            pim.ContentItem.triageStatusChanged.name,
        ])
        
    # Our detail views share the same delegate instance and contents collection
    detailBranchPointDelegate = detailblocks.DetailBranchPointDelegate.update(
        parcel, 'DetailBranchPointDelegateInstance',
        branchStub = detailblocks.DetailRoot)
    #detailContentsCollection = pim.ListCollection.update(
        #parcel, 'DetailContentsCollection')
    iconColumnWidth = 23 # temporarily not 20, to work around header bug 6168
    SplitterWindow.template(
        'TableSummaryViewTemplate',
        eventBoundary = True,
        orientationEnum = "Vertical",
        splitPercentage = 0.65,
        childrenBlocks = [
            DashboardBlock.template('TableSummaryView',
                contents = pim_ns.allCollection,
                scaleWidthsToFit = True,
                columns = [
                    taskColumn,
                    commColumn,
                    whoColumn,
                    titleColumn,
                    reminderColumn,
                    dateColumn,
                    triageColumn                    
                ],
                characterStyle = blocks.SummaryRowStyle,
                headerCharacterStyle = blocks.SummaryHeaderStyle,
                elementDelegate = 'osaf.views.main.SectionedGridDelegate',
                       defaultEditableAttribute = u'displayName',
                selection = [[0,0]]),
            BranchPointBlock.template('TableSummaryDetailBranchPointBlock',
                delegate = detailBranchPointDelegate,
                #contents = detailContentsCollection
                )
            ]).install(parcel) # SplitterWindow TableSummaryViewTemplate


    TimeZoneChange = BlockEvent.template(
        'TimeZoneChange',
        dispatchEnum = 'BroadcastEverywhere').install(parcel)

    DefaultCharacterStyle = CharacterStyle.update(
        parcel, 'DefaultCharacterStyle',
        fontFamily = 'DefaultUIFont')

    DefaultSmallBoldStyle = CharacterStyle.update(
        parcel, 'DefaultSmallBoldStyle',
        fontFamily = 'DefaultUIFont',
        fontSize = 10.0,
        fontStyle = 'bold')

    DefaultBigStyle = CharacterStyle.update(
        parcel, 'DefaultBigStyle',
        fontFamily = 'DefaultUIFont',
        fontSize = 12.0)

    DefaultBoldStyle = CharacterStyle.update(
        parcel, 'DefaultBoldStyle',
        fontFamily = 'DefaultUIFont',
        fontStyle = 'bold')

    DefaultBigBoldStyle = CharacterStyle.update(
        parcel, 'DefaultBigBoldStyle',
        fontFamily = 'DefaultUIFont',
        fontSize = 13,
        fontStyle = 'bold')

    # save the template because we'll need it for later
    MainCalendarControlT = calendar.CalendarControl.template(
        'MainCalendarControl',
        tzCharacterStyle = DefaultCharacterStyle,
        stretchFactor = 0)

    MainCalendarControl = MainCalendarControlT.install(parcel)

    CalendarDetailBranchPointBlock = BranchPointBlock.template(
        'CalendarDetailBranchPointBlock',
        delegate = detailBranchPointDelegate,
        #contents = detailContentsCollection
        ).install(parcel)

    WelcomeEvent = schema.ns('osaf.app', view).WelcomeEvent
    CalendarDetailBranchPointBlock.selectedItem = WelcomeEvent
    #detailContentsCollection.clear()
    #detailContentsCollection.add(WelcomeEvent)

    CalendarSummaryView = CalendarContainer.template(
        'CalendarSummaryView',
        calendarControl = MainCalendarControl,
        monthLabelStyle = blocks.BigTextStyle,
        eventLabelStyle = DefaultCharacterStyle,
        eventTimeStyle = DefaultSmallBoldStyle,
        legendStyle = DefaultCharacterStyle,
        orientationEnum = 'Vertical',
        eventsForNamedLookup = [TimeZoneChange]).install(parcel)
    
    SplitterWindow.template('CalendarSummaryViewTemplate',
        eventBoundary = True,
        orientationEnum = 'Vertical',
        splitPercentage = 0.65,
        childrenBlocks = [
            CalendarContainer.template('CalendarSummaryView',
                childrenBlocks = [
                    MainCalendarControlT,
                    CanvasSplitterWindow.template('MainCalendarCanvasSplitter',
                        # as small as possible; AllDayEvents's
                        # SetMinSize() should override?
                        splitPercentage = 0.06,
                        orientationEnum = 'Horizontal',
                        stretchFactor = 1,
                        calendarControl = MainCalendarControl,
                        childrenBlocks = [
                            calendar.AllDayEventsCanvas.template('AllDayEvents',
                                calendarContainer = CalendarSummaryView),
                            calendar.TimedEventsCanvas.template('TimedEvents',
                                calendarContainer = CalendarSummaryView)
                            ]),
                    ]),
            BranchPointBlock.template('CalendarDetailBranchPointBlock',
                delegate = detailBranchPointDelegate)
            ]).install(parcel)
    
    CalendarControl.update(
        parcel, 'MainCalendarControl',
        calendarContainer = CalendarSummaryView)
                                
    # Precache detail views for the basic pim types (and "Block",
    # which is the key used for the None item). Note that the basic
    # stamps (Event, Task, Mail) are now covered by Note
    for keyType in (pim.Note, Block.Block):
        detailBranchPointDelegate.getBranchForKeyItem(
                            schema.itemFor(keyType, view))
    
