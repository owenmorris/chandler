from application import schema
from i18n import OSAFMessageFactory as _
from osaf.framework.blocks.calendar import (
    CalendarContainer, CalendarControl, CanvasSplitterWindow,
    AllDayEventsCanvas, TimedEventsCanvas
    )

from osaf import pim
from osaf.framework.blocks import *
from osaf.framework.blocks.detail import DetailTrunkSubtree

def make_summaryblocks(parcel):
    view = parcel.itsView
    detailblocks = schema.ns('osaf.framework.blocks.detail', view)
    app = schema.ns('osaf.app', view)
    blocks = schema.ns('osaf.framework.blocks', view)
    
    # Our detail views share the same delegate instance
    detailTrunkDelegate = \
        detail.DetailTrunkDelegate.update(parcel,
                                          'DetailTrunkDelegateInstance',
                                          trunkStub=detailblocks.DetailRoot)
    
    SplitterWindow.template('TableSummaryViewTemplate',
        eventBoundary=True,
        orientationEnum="Vertical",
        splitPercentage=0.65,
        childrenBlocks=[
            Table.template('TableSummaryView',
                contents=app.allCollection,
                characterStyle=blocks.SummaryRowStyle,
                headerCharacterStyle=blocks.SummaryHeaderStyle,
                hasGridLines=True,
                columnHeadings=
                    [u'', _(u'who'), _(u'about'), _(u'date')],
                columnData=
                    [u'itsKind', u'who', u'about', u'date'],
                columnWidths=
                    [20, 130, 130, 130],
                columnReadOnly=
                    [True, True, False, True],
                selection=[[0,0]]),
            TrunkParentBlock.template('TableSummaryDetailTPB',
                trunkDelegate=detailTrunkDelegate)
            ]).install(parcel) # SplitterWindow TableSummaryViewTemplate


    TimeZoneChange = \
        BlockEvent.template('TimeZoneChange',
                            'BroadcastEverywhere').install(parcel)

    DefaultCharacterStyle = \
        CharacterStyle.update(parcel, 'DefaultCharacterStyle',
                              fontFamily='DefaultUIFont')

    DefaultSmallBoldStyle = \
        CharacterStyle.update(parcel, 'DefaultSmallBoldStyle',
                              fontFamily='DefaultUIFont',
                              fontSize=10.0,
                              fontStyle='bold')

    DefaultBigStyle = \
        CharacterStyle.update(parcel, 'DefaultBigStyle',
                              fontFamily='DefaultUIFont',
                              fontSize=12.0)

    DefaultBoldStyle = \
        CharacterStyle.update(parcel, 'DefaultBoldStyle',
                              fontFamily='DefaultUIFont',
                              fontStyle='bold')

    DefaultBigBoldStyle = \
        CharacterStyle.update(parcel, 'DefaultBigBoldStyle',
                              fontFamily='DefaultUIFont',
                              fontSize=13,
                              fontStyle='bold')

    # save the template because we'll need it for later
    MainCalendarControlT = \
        calendar.CalendarControl.template('MainCalendarControl',
                                          tzCharacterStyle=DefaultCharacterStyle,
                                          stretchFactor=0)
    MainCalendarControl = MainCalendarControlT.install(parcel)
    
    CalendarSummaryView = \
        CalendarContainer.template('CalendarSummaryView',
                calendarControl=MainCalendarControl,
                monthLabelStyle=DefaultBigBoldStyle,
                eventLabelStyle=DefaultCharacterStyle,
                eventTimeStyle=DefaultSmallBoldStyle,
                legendStyle=DefaultCharacterStyle,
                orientationEnum='Vertical',
                eventsForNamedLookup=[TimeZoneChange]).install(parcel)
    
    SplitterWindow.template('CalendarSummaryViewTemplate',
        eventBoundary=True,
        orientationEnum='Vertical',
        splitPercentage=0.65,
        childrenBlocks=[
            CalendarContainer.template('CalendarSummaryView',
                childrenBlocks=[
                    MainCalendarControlT,
                    CanvasSplitterWindow.template('MainCalendarCanvasSplitter',
                        # as small as possible; AllDayEvents's
                        # SetMinSize() should override?
                        splitPercentage=0.06,
                        orientationEnum='Horizontal',
                        stretchFactor=1,
                        calendarControl=MainCalendarControl,
                        childrenBlocks=[
                            calendar.AllDayEventsCanvas.template('AllDayEvents',
                                calendarContainer=CalendarSummaryView,
                                contents=app.allCollection),
                            calendar.TimedEventsCanvas.template('TimedEvents',
                                calendarContainer=CalendarSummaryView,
                                contents=app.allCollection)
                            ]),
                    ]),
            TrunkParentBlock.template('CalendarDetailTPB',
                trunkDelegate=detailTrunkDelegate)
            ]).install(parcel)
    
    CalendarControl.update(parcel, 'MainCalendarControl',
                           calendarContainer=CalendarSummaryView)
                                
    # Precache detail views for the basic pim types (and "DetailTrunkSubtree",
    # which is the key used for the None item)
    for keyType in (pim.Note, pim.CalendarEvent, pim.Task,
                    pim.mail.MailMessage, DetailTrunkSubtree):
        detailTrunkDelegate.getTrunkForKeyItem(keyType.getKind(view))
    
