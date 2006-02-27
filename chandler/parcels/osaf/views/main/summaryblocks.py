from application import schema
from i18n import OSAFMessageFactory as _
from osaf.framework.blocks.calendar import (
    CalendarContainer, CalendarControl, CanvasSplitterWindow,
    AllDayEventsCanvas, TimedEventsCanvas
    )

from osaf import pim
from osaf.framework.blocks import *

def makeSummaryBlocks(parcel):
    view = parcel.itsView
    detailblocks = schema.ns('osaf.framework.blocks.detail', view)
    pim_ns = schema.ns('osaf.pim', view)
    blocks = schema.ns('osaf.framework.blocks', view)
    
    # Our detail views share the same delegate instance and contents collection
    detailBranchPointDelegate = detail.DetailBranchPointDelegate.update(
        parcel, 'DetailBranchPointDelegateInstance',
        branchStub = detailblocks.DetailRoot)
    #detailContentsCollection = pim.ListCollection.update(
        #parcel, 'DetailContentsCollection')
    
    SplitterWindow.template(
        'TableSummaryViewTemplate',
        eventBoundary = True,
        orientationEnum = "Vertical",
        splitPercentage = 0.65,
        childrenBlocks = [
            Table.template('TableSummaryView',
                contents = pim_ns.allCollection,
                characterStyle = blocks.SummaryRowStyle,
                headerCharacterStyle = blocks.SummaryHeaderStyle,
                columnHeadings = 
                    [u'', _(u'who'), _(u'about'), _(u'date'), _(u'Triage')],
                columnData = 
                    [u'itsKind', u'who', u'about', u'date', u'triageStatus'],
                columnWidths = 
                    [20, 130, 130, 130, 20],
                columnReadOnly = 
                    [True, True, False, True, False],
                elementDelegate = 'osaf.views.main.SectionedGridDelegate',
                selection = [[0,0]]),
            BranchPointBlock.template('TableSummaryDetailBranchPointBlock',
                delegate = detailBranchPointDelegate,
                #contents = detailContentsCollection
                )
            ]).install(parcel) # SplitterWindow TableSummaryViewTemplate


    TimeZoneChange = BlockEvent.template(
        'TimeZoneChange',
        'BroadcastEverywhere').install(parcel)

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
    # which is the key used for the None item)
    for keyType in (pim.Note, pim.CalendarEvent, pim.Task,
                    pim.mail.MailMessage, Block.Block):
        detailBranchPointDelegate.getBranchForKeyItem(keyType.getKind(view))
    
