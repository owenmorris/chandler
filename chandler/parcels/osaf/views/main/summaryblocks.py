from osaf.framework.blocks import *

def makeSummaryBlocks(parcel):
    from application import schema
    from i18n import OSAFMessageFactory as _
    from osaf.framework.blocks.calendar import (
        CalendarContainer, CalendarControl, CanvasSplitterWindow,
        AllDayEventsCanvas, TimedEventsCanvas
        )

    from osaf import pim

    from Dashboard import DashboardBlock
    
    view = parcel.itsView
    detailblocks = schema.ns('osaf.framework.blocks.detail', view)
    pim_ns = schema.ns('osaf.pim', view)
    blocks = schema.ns('osaf.framework.blocks', view)
    repositoryView = parcel.itsView
    
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
            DashboardBlock.template('TableSummaryView',
                contents = pim_ns.allCollection,
                scaleWidthsToFit = True,
                columns = [
                    Column.update(parcel, 'SumColTask',
                                  icon = 'SumTaskStamped',
                                  valueType = 'kind',
                                  kind = pim.TaskMixin.getKind(repositoryView),
                                  width = 20,
                                  readOnly = True),
                    Column.update(parcel, 'SumColMail',
                                  icon = 'SumMailStamped',
                                  valueType = 'kind',
                                  kind = pim.mail.MailMessageMixin.getKind(repositoryView),
                                  width = 20,
                                  readOnly = True),
                    Column.update(parcel, 'SumColWho',
                                  heading = _(u'Who'),
                                  attributeName = 'who',
                                  width = 100,
                                  scaleColumn = True,
                                  readOnly = True),
                    Column.update(parcel, 'SumColAbout',
                                  heading = _(u'Title'),
                                  attributeName = 'about',
                                  width = 120,
                                  scaleColumn = True),
                    Column.update(parcel, 'SumColCalendarEvent',
                                  icon = 'SumEventStamped',
                                  valueType = 'kind',
                                  kind = pim.CalendarEventMixin.getKind(repositoryView),
                                  width = 20,
                                  readOnly = True),
                    Column.update(parcel, 'SumColDate',
                                  heading = _(u'Date'),
                                  attributeName = 'date',
                                  width = 100,
                                  scaleColumn = True,
                                  readOnly = True),
                    Column.update(parcel, 'SumColTriage',
                                  heading = _(u'Triage'),
                                  attributeName = 'triageStatus',
                                  width = 40),
                ],
                characterStyle = blocks.SummaryRowStyle,
                headerCharacterStyle = blocks.SummaryHeaderStyle,
                elementDelegate = 'osaf.views.main.SectionedGridDelegate',
                       defaultEditableAttribute = u'about',
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
    # which is the key used for the None item)
    for keyType in (pim.Note, pim.CalendarEvent, pim.Task,
                    pim.mail.MailMessage, Block.Block):
        detailBranchPointDelegate.getBranchForKeyItem(keyType.getKind(view))
    
