from application import schema
from i18n import OSAFMessageFactory as _

def make_summaryblocks(parcel):
    
    from osaf.framework.blocks.calendar import (
        CalendarContainer, CalendarControl, CanvasSplitterWindow,
        AllDayEventsCanvas, TimedEventsCanvas
        )
    
    from osaf.framework.blocks import *
    
    view = parcel.itsView
    detailblocks = schema.ns('osaf.framework.blocks.detail', view)
    app = schema.ns('osaf.app', view)
    blocks = schema.ns('osaf.framework.blocks', view)
    
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
                columnHeaderings=
                    [_(''), _('who'), _('about'), _('date')],
                columnData=
                    ['itsKind', 'who', 'about', 'date'],
                columnWidths=
                    [20, 130, 130, 130],
                columnReadOnly=
                    [True, True, False, True],
                selection=[[0,0]]),
            TrunkParentBlock.template('TableSummaryDetailTPB',
                trunkDelegate=\
                    detail.DetailTrunkDelegate.update(parcel,
                        'TableSummaryDetailTrunkDelegate',
                         trunkStub=detailblocks.DetailRoot))
            ]).install(parcel) # SplitterWindow TableSummaryViewTemplate


    TimeZoneChange = \
        BlockEvent.template('TimeZoneChange',
                            'BroadcastEverywhere').install(parcel)
    
    TimeZoneStyle = \
        CharacterStyle.update(parcel, 'TimeZoneStyle',
                              fontFamily='DefaultUIFont',
                              fontSize=11)
    DefaultCharacterStyle = \
        CharacterStyle.update(parcel, 'DefaultCharacterStyle',
                              fontFamily='DefaultUIFont')

    DefaultBoldStyle = \
        CharacterStyle.update(parcel, 'DefaultBoldStyle',
                              fontFamily='DefaultUIFont',
                              fontStyle='bold')

    DefaultBigBoldStyle = \
        CharacterStyle.update(parcel, 'DefaultBigBoldStyle',
                              fontFamily='DefaultUIFont',
                              fontSize=13,
                              fontStyle='bold')

    MainCalendarControlT = \
        calendar.CalendarControl.template('MainCalendarControl',
                                          tzCharacterStyle=TimeZoneStyle,
                                          stretchFactor=0)
    MainCalendarControl = MainCalendarControlT.install(parcel)
    
    CalendarSummaryView = \
        CalendarContainer.template('CalendarSummaryView',
                calendarControl=MainCalendarControl,
                characterStyle=DefaultCharacterStyle,
                boldCharacterStyle=DefaultBoldStyle,
                bigBoldCharacterStyle=DefaultBigBoldStyle,
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
                        splitPercentage=0.01,
                        orientationEnum='Horizontal',
                        stretchFactor=1,
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
                trunkDelegate= \
                    detail.DetailTrunkDelegate.update(parcel,
                        'CalendarDetailTrunkDelegate',
                        trunkStub=detailblocks.DetailRoot))
            ]).install(parcel)
    
    CalendarControl.update(parcel, 'MainCalendarControl',
                           calendarContainer=CalendarSummaryView)
                                
        
