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

def makeSummaryBlocks(parcel):
    from application import schema
    from i18n import ChandlerMessageFactory as _
    from osaf.framework.blocks.calendar import (
        CalendarContainer, CalendarControl, CanvasSplitterWindow,
        AllDayEventsCanvas, TimedEventsCanvas
        )

    from osaf import pim

    from Dashboard import DashboardBlock
    
    view = parcel.itsView
    detailblocks = schema.ns('osaf.views.detail', view)
    pim_ns = schema.ns('osaf.pim', view)
    blocks = schema.ns('osaf.framework.blocks', view)
    repositoryView = parcel.itsView
    
    iconColumnWidth = 23 # temporarily not 20, to work around header bug 6168

    # Index definitions that the dashboard will use; each inherits
    # from a master index on the ContentItem kind collection.
    def makeColumnAndIndexes(colName, **kwargs):
        # Make the master index
        indexName = kwargs['indexName']
        attributes = kwargs.pop('attributes')
        pim_ns.contentItems.addIndex(indexName, 'attribute',
                                     attributes=attributes)
    
        # Create an IndexDefinition that will later be used to
        # build sub-indexes off this master, when the user clicks on the column.
        pim.IndexDefinition.update(parcel, indexName)
    
        # Create the column
        return Column.update(parcel, colName, **kwargs)

    taskColumn = makeColumnAndIndexes('SumColTask',
        icon='ColHTask',
        valueType = 'stamp',
        stamp=pim.TaskStamp,
        width=iconColumnWidth,
        useSortArrows=False,
        readOnly=True,
        indexName='%s.taskStatus' % __name__,
        attributeName='taskStatus',
        attributes=[
            # @@@ need to order on task-ness somehow:
            # pim.TaskStamp.taskStatus.name, 
            pim.ContentItem.triageStatus.name, 
            pim.ContentItem.triageStatusChanged.name,
        ])

    commColumn = makeColumnAndIndexes('SumColMail',
        icon='ColHMail',
        valueType='stamp',
        stamp=pim.mail.MailStamp,
        width=iconColumnWidth,
        useSortArrows=False,
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
        scaleColumn=True,
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
        scaleColumn=True,
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
        readOnly = True,
        indexName = '%s.calendarStatus' % __name__,
        attributeName = 'calendarStatus',
        attributes=[
            # pim.EventStamp.calendarStatus.name, 
            pim.ContentItem.triageStatus.name, 
            pim.ContentItem.triageStatusChanged.name,
        ])

    dateColumn = makeColumnAndIndexes('SumColDate',
        heading = _(u'Date'),
        width = 100,
        scaleColumn = True,
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
    
