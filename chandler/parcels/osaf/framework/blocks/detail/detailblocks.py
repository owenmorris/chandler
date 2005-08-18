
from Detail import *
from osaf.framework.blocks import *
from osaf.pim.item_collections import ItemCollection
import osaf.pim

def installParcel(parcel, oldVersion=None):
    """ Instantiate all the blocks, events, etc for the detail view. """
    
    # First, register all the custom attribute editors 
    registerAttributeEditors(parcel, oldVersion)
    
    # Make all the 'global' stuff
    makeRootStuff(parcel, oldVersion)
    
    # Make the MarkupBar
    makeMarkupBar(parcel, oldVersion)
    
    # Make the various kind-specific subtrees
    makeNoteSubtree(parcel, oldVersion)
    makeMailSubtree(parcel, oldVersion)
    makeCalendarEventSubtree(parcel, oldVersion)
    makeItemCollectionSubtree(parcel, oldVersion)
    makeEmptySubtree(parcel, oldVersion)

_presentationStyleID = 0 # used to give each presentationStyle a unique name
def installPresentationStyle(parcel, name=None, **kwds):
    """ Build and return a PresentationStyle """
    if name is None:
        global _presentationStyleID
        _presentationStyleID += 1
        name = 'PresentationStyle_%d' % _presentationStyleID
    ps = PresentationStyle.update(parcel, name, **kwds)
    return ps

_spacerID = 0 # used to give each spacer a unique name
def makeSpacerBlock(parcel, size, name=None, **kwds):
    if name is None:
        global _spacerID
        _spacerID += 1
        name = 'Spacer_%d' % _spacerID
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)
    spacer = \
        StaticText.template(name,
                            title='',
                            characterStyle=blocks.LabelStyle,
                            stretchFactor=0.0,
                            minimumSize=size, **kwds)
    return spacer

def installSpacerBlock(parcel, size, name=None, **kwds):
    spacerTemplate = makeSpacerBlock(parcel, size, name, **kwds)
    return spacerTemplate.install(parcel)

def registerAttributeEditors(parcel, oldVersion):
    # make the detail view's attribute editors at repository-init time
    # If you edit this dictionary, please keep it in alphabetical order by key.
    aeList = {
        'DateTime+calendarDateOnly': 'CalendarDateAttributeEditor',
        'DateTime+calendarTimeOnly': 'CalendarTimeAttributeEditor',
        'EmailAddress+outgoing': 'OutgoingEmailAddressAttributeEditor',
        'RecurrenceRuleSet+custom': 'RecurrenceCustomAttributeEditor',
        'RecurrenceRuleSet+ends': 'RecurrenceEndsAttributeEditor',
        'RecurrenceRuleSet+occurs': 'RecurrenceAttributeEditor',
        'TimeDelta+reminderPopup': 'ReminderDeltaAttributeEditor',
    }
    for typeName, className in aeList.items():
        AttributeEditorMapping.update(parcel, typeName, className=\
                                      __name__ + '.' + className)
    
def makeRootStuff(parcel, oldVersion):
    # The detail view is notified of changes in the single item we stick
    # into this item collection
    dvSelectedItemCollection = \
        ItemCollection.update(parcel, 'DetailViewSelectedItemCollection',
                              displayName=_(u'DetailViewSelectedItemCollection'),
                              _rule="")
        
    # The DetailTrunkCache starts each specific DetailTrunk by cloning this stub.
    detailRoot = DetailRootBlock.template('DetailRoot',
                                          orientationEnum='Vertical',
                                          size=SizeType(80, 20),
                                          minimumSize=SizeType(80, 40),
                                          eventBoundary=True,
                                          contents=dvSelectedItemCollection)
    detailRoot.install(parcel)
    
    # Our Resynchronize event.
    resyncEvent = \
        BlockEvent.template('Resynchronize',
            dispatchEnum='SendToBlockByName',
            dispatchToBlockName='DetailRoot').install(parcel)
 
    # A few spacer blocks, copied by other parcel.xml blocks.
    installSpacerBlock(parcel, SizeType(-1, 6), name='TopSpacer', position=0.01)
    installSpacerBlock(parcel, SizeType(8, -1), name='HorizontalSpacer')

def makeMarkupBar(parcel, oldVersion):
    markupBar = MarkupBarBlock.template('MarkupBar').install(parcel)
    
    # The events.
    buttonPressed = \
        BlockEvent.template('ButtonPressed',
                            'SendToBlockByReference',
                            destinationBlockReference=markupBar).install(parcel)
    togglePrivate = \
        BlockEvent.template('TogglePrivate',
                            'SendToBlockByReference',
                            destinationBlockReference=markupBar).install(parcel)
    
    # The buttons.
    mailMessageButton = \
        MailMessageButtonBlock.template('MailMessageButton',
                                        title=_(u"Send as message"),
                                        bitmap="MarkupBarMail.png",
                                        toolbarItemKind='Button',
                                        toggle=True,
                                        helpString=_(u'Send this item as a mail message'),
                                        event=buttonPressed)
    
    taskStamp = \
        TaskStampBlock.template('TaskStamp',
                                title=_(u"Put on Taskpad"),
                                bitmap="MarkupBarTask.png",
                                toolbarItemKind='Button',
                                toggle=True,
                                helpString=_(u'Put this item onto the Taskpad'),
                                event=buttonPressed)
                        
    calendarStamp = \
        CalendarStampBlock.template('CalendarStamp',
                                    title=_(u"Put on Calendar"),
                                    bitmap="MarkupBarEvent.png",
                                    toolbarItemKind='Button',
                                    toggle=True,
                                    helpString=_(u'Put this item onto the Calendar'),
                                    event=buttonPressed)

    separator = \
        ToolbarItem.template('ToolbarItemSeparator',
                             toolbarItemKind='Separator')

    privateSwitchButton = \
        PrivateSwitchButtonBlock.template('PrivateSwitchButton',
                                    title=_(u"Never share this item"),
                                    bitmap="MarkupBarPrivate.png",
                                    toolbarItemKind='Button',
                                    toggle=True,
                                    helpString=_(u'Never share this item'),
                                    event=togglePrivate)

    # Finally, do the bar itself.
    markupBar = MarkupBarBlock.template('MarkupBar',
                                        childrenBlocks=[mailMessageButton,
                                                        taskStamp,
                                                        calendarStamp,
                                                        separator,
                                                        privateSwitchButton],
                                        position=0.0,
                                        toolSize=SizeType(20, 20),
                                        separatorWidth=16,
                                        stretchFactor=0.0)
    markupBar.install(parcel)
    
def makeNoteSubtree(parcel, oldVersion):
    """ Build the subtree (and related stuff) for Note """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)

    # First, the headline AEBlock and the area it sits in
    headlineAEBlock = DetailSynchronizedAttributeEditorBlock.template(\
        'HeadlineBlock',
        characterStyle=blocks.BigTextStyle,
        presentationStyle=installPresentationStyle(parcel, \
            sampleText=u'', # empty sample means "use displayname"
            editInPlace=True),
        viewAttribute=u'about',
        border=RectType(2, 2, 2, 2))
    headlineArea = \
        blocks.ContentItemDetail.template('HeadlineArea',
            childrenBlocks = [
                makeSpacerBlock(parcel, SizeType(0,22)),
                headlineAEBlock],
            position=0.5,
            minimumSize=SizeType(300,10),
            stretchFactor=0.0,
            border=RectType(0,6,0,6)).install(parcel)
    
    # Then, the Note AEBlock and its area
    notesBlock = \
        DetailSynchronizedAttributeEditorBlock.template('NotesBlock',
            position=0.9,
            characterStyle=blocks.TextStyle,
            presentationStyle=installPresentationStyle(parcel, \
                lineStyleEnum='MultiLine'),
            viewAttribute=u'bodyString',
            border=RectType(2, 2, 2, 2)).install(parcel)
    
    # Finally, the subtree
    notesSubtree = \
        DetailTrunkSubtree.update(parcel, 'NoteSubtree',
            key=osaf.pim.Note.getKind(),
            rootBlocks=[
                parcel['TopSpacer'],
                parcel['MarkupBar'],
                headlineArea, 
                installSpacerBlock(parcel, SizeType(-1, 7), position=0.8999),
                notesBlock])      

def makeCalendarEventSubtree(parcel, oldVersion):
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)

    locationArea = \
        CalendarLocationAreaBlock.template('CalendarLocationArea',
            childrenBlocks=[
                makeSpacerBlock(parcel, SizeType(0, 22)),
                DetailSynchronizedAttributeEditorBlock.template('CalendarLocation',
                    characterStyle=blocks.TextStyle,
                    #minimumSize=SizeType(300,22),
                    presentationStyle=installPresentationStyle(parcel,
                        sampleText=u'',
                        editInPlace=True),
                    viewAttribute=u'location',
                    border=RectType(2, 2, 2, 2))],
            stretchFactor=0.0,
            minimumSize=SizeType(300,10),
            border=RectType(0, 6, 0, 6))

    allDayArea = \
        CalendarAllDayAreaBlock.template('CalendarAllDayArea',
            childrenBlocks=[
                StaticText.template('CalDetailsAllDayLabel',
                    title=_(u'all-day'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(4, 0, 0, 0)),            
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('EditAllDay',
                    stretchFactor=0.0,
                    viewAttribute=u'allDay',
                    minimumSize=SizeType(16,-1),
                    border=RectType(2, 2, 2, 2),
                    event=parcel['Resynchronize'])],
            stretchFactor=0.0,
            border=RectType(0, 0, 0, 6))
    
    startTimeArea = \
        ContentItemDetail.template('CalendarStartTimeArea',
            childrenBlocks=[
                StaticText.template('StaticCalendarStart',
                    title=_(u'starts'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(4, 0, 0, 0)),            
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('EditCalendarStartDate',
                    characterStyle=blocks.TextStyle,
                    presentationStyle=installPresentationStyle(parcel, 
                        format='calendarDateOnly'),
                    viewAttribute=u'startTime',
                    stretchFactor=0.0,
                    size=SizeType(75, -1),
                    border=RectType(2, 2, 2, 2),
                    event=parcel['Resynchronize']),
                CalendarAtLabelBlock.template('CalendarStartAtLabel',
                    title=_(u'at'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Center',
                    stretchFactor=0.0,
                    border=RectType(4, 4, 0, 4)),
                DetailSynchronizedAttributeEditorBlock.template('EditCalendarStartTime',
                    characterStyle=blocks.TextStyle,
                    presentationStyle=installPresentationStyle(parcel, 
                        format='calendarTimeOnly'),
                    viewAttribute=u'startTime',
                    stretchFactor=0.0,
                    size=SizeType(85, -1),
                    border=RectType(2, 2, 2, 2),
                    event=parcel['Resynchronize'])],
            minimumSize=SizeType(300, 24),
            stretchFactor=0.0,
            border=RectType(0, 0, 0, 6))
    
    endTimeArea = \
        ContentItemDetail.template('CalendarEndTimeArea',
            childrenBlocks=[
                StaticText.template('StaticCalendarEnd',
                    title=_(u'ends'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(4, 0, 0, 0)),            
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('EditCalendarEndDate',
                    characterStyle=blocks.TextStyle,
                    presentationStyle=installPresentationStyle(parcel, 
                        format='calendarDateOnly'),
                    viewAttribute=u'endTime',
                    stretchFactor=0.0,
                    size=SizeType(75, -1),
                    border=RectType(2, 2, 2, 2),
                    event=parcel['Resynchronize']),
                CalendarAtLabelBlock.template('CalendarEndAtLabel',
                    title=_(u'at'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Center',
                    stretchFactor=0.0,
                    border=RectType(4, 4, 0, 4)),
                DetailSynchronizedAttributeEditorBlock.template('EditCalendarEndTime',
                    characterStyle=blocks.TextStyle,
                    presentationStyle=installPresentationStyle(parcel, 
                        format='calendarTimeOnly'),
                    viewAttribute=u'endTime',
                    stretchFactor=0.0,
                    size=SizeType(85, -1),
                    border=RectType(2, 2, 2, 2),
                    event=parcel['Resynchronize'])],
            minimumSize=SizeType(300, 24),
            stretchFactor=0.0,
            border=RectType(0, 0, 0, 6))

    timeZoneArea = \
        CalendarTimeZoneAreaBlock.template('CalendarTimeZoneArea',
            childrenBlocks=[
                StaticText.template('CalTimeZoneLabel',
                    title=_(u'time zone'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(5, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('EditTimeZone',
                    characterStyle=blocks.TextStyle,
                    viewAttribute=u'startTime',
                    presentationStyle=installPresentationStyle(parcel, 
                        format='timeZoneOnly'),
                    stretchFactor=0.0,
                    size=SizeType(75, -1),
                    border=RectType(2, 2, 2, 2),
                    event=parcel['Resynchronize'])],
            stretchFactor=0.0,
            minimumSize=SizeType(300, 24),
            border=RectType(0, 0, 0, 6))

    transparencyArea = \
        ContentItemDetail.template('CalendarTransparencyArea',
            childrenBlocks=[
                StaticText.template('CalDetailsTransparencyLabel',
                    title=_(u'status'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(5, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('EditTransparency',
                    viewAttribute=u'transparency',
                    presentationStyle=installPresentationStyle(parcel,
                        format='popup',
                        # It'd be nice to not maintain the transparency choices 
                        # separately from the enum values; currently, the 
                        # choices must match the enum's items and ordering.
                        # @@@ XXX i18n!
                        choices=[_(u'Confirmed'), _(u'Tentative'), _(u'FYI')]),
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1),
                    border=RectType(2, 2, 2, 2))],
            stretchFactor=0.0,
            minimumSize=SizeType(300, 24),
            border=RectType(0, 0, 0, 6))
  
    recurrencePopupArea = \
        CalendarRecurrencePopupAreaBlock.template('CalendarRecurrencePopupArea',
            childrenBlocks=[
                StaticText.template('CalOccursLabel',
                    title=_(u'occurs'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(5, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('EditRecurrence',
                    viewAttribute=u'rruleset',
                    presentationStyle=installPresentationStyle(parcel,
                        format='occurs',
                        # These choices must match the enumerated indexes in the
                        # RecurrenceAttributeEditor python code
                        choices=[_(u'Once'), _(u'Daily'), _(u'Weekly'), 
                                 _(u'Monthly'), _(u'Yearly'), _(u'Custom...')]),
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1),
                    border=RectType(2, 2, 2, 2),
                    event=parcel['Resynchronize'])],
            stretchFactor=0.0,
            minimumSize=SizeType(300, 24),
            border=RectType(0, 0, 0, 6))
                                                  
    recurrenceCustomArea = \
        CalendarRecurrenceCustomAreaBlock.template('CalendarRecurrenceCustomArea',
            childrenBlocks=[
                StaticText.template('CalCustomLabel',
                    title=u'', # no label.
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(2, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('CalCustomValue',
                    viewAttribute=u'rruleset',
                    presentationStyle=installPresentationStyle(parcel,
                        format='custom'),
                    stretchFactor=1.0,
                    minimumSize=SizeType(300, -1),
                    border=RectType(2, 2, 2, 2),
                    event=parcel['Resynchronize'])],
            stretchFactor=0.0,
            minimumSize=SizeType(300, 24),
            border=RectType(0, 0, 0, 6))
                                           
    recurrenceEndArea = \
        CalendarRecurrenceEndAreaBlock.template('CalendarRecurrenceEndArea',
            childrenBlocks=[
                StaticText.template('CalRecurrenceEndLabel',
                    title=_(u'ends'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(5, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('EditRecurrenceEnd',
                    viewAttribute=u'rruleset',
                    characterStyle=blocks.TextStyle,
                    presentationStyle=installPresentationStyle(parcel,
                        format='ends'),
                    stretchFactor=0.0,
                    size=SizeType(75, -1),
                    border=RectType(2, 2, 2, 2))],
            stretchFactor=0.0,
            minimumSize=SizeType(300, 24),
            border=RectType(0, 0, 0, 6))

    reminderArea = \
        CalendarReminderAreaBlock.template('CalendarReminderArea',
            childrenBlocks=[
                StaticText.template('CalDetailsReminderLabel',
                    title=_(u'alarm'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(5, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('EditReminder',
                    viewAttribute=u'reminderDelta',
                    presentationStyle=installPresentationStyle(parcel,
                        format='reminderPopup',
                        # @@@ XXX i18n: the code assumes that if the value
                        # starts with a digit, it's a number of minutes; if not,
                        # it's None.
                        choices=[_(u'None'), _(u'1 minute'), _(u'5 minutes'), 
                                 _(u'10 minutes'), _(u'30 minutes'), 
                                 _(u'60 minutes'), _(u'90 minutes')]),
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1),
                    border=RectType(2, 2, 2, 2))],
            stretchFactor=0.0,
            minimumSize=SizeType(300, 24),
            border=RectType(0, 0, 0, 6))
 
    calendarDetails = \
        ContentItemDetail.template('CalendarDetails',
            childrenBlocks = [
                locationArea,
                makeSpacerBlock(parcel, SizeType(-1, 4)),
                allDayArea,
                makeSpacerBlock(parcel, SizeType(-1, 4)),
                startTimeArea,
                makeSpacerBlock(parcel, SizeType(-1, 1)),
                endTimeArea,
                makeSpacerBlock(parcel, SizeType(-1, 7)),
                timeZoneArea,
                makeSpacerBlock(parcel, SizeType(-1, 1)),
                transparencyArea,
                makeSpacerBlock(parcel, SizeType(-1, 7)),
                recurrencePopupArea,
                makeSpacerBlock(parcel, SizeType(-1, 1)),
                recurrenceCustomArea,
                recurrenceEndArea,
                makeSpacerBlock(parcel, SizeType(-1, 7)),
                reminderArea],
            orientationEnum='Vertical',
            stretchFactor=0.0,
            #event=parcel['Resynchronize'],
            position=0.8).install(parcel)

    calendarEventSubtree = \
        DetailTrunkSubtree.update(parcel, 'CalendarEventSubtree',
            key=osaf.pim.CalendarEventMixin.getKind(),
            rootBlocks=[calendarDetails])
 
def makeMailSubtree(parcel, oldVersion):
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)    
    fromArea = \
        DetailSynchronizedLabeledTextAttributeBlock.template('FromArea',
            childrenBlocks=[
                StaticText.template('FromString',
                    title=u'from',
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(4, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('FromEditField',
                    #presentationStyle=installPresentationStyle(parcel, 
                        #format='outgoing'),
                    viewAttribute=u'fromAddress',
                    border=RectType(2, 2, 2, 2))],
            position=0.1,
            selectedItemsAttribute=u'whoFrom',
            stretchFactor=0.0,
            border=RectType(0, 0, 0, 6)).install(parcel)
    
    toMailArea = \
        DetailSynchronizedLabeledTextAttributeBlock.template('ToMailArea',
            childrenBlocks=[
                StaticText.template('ToString',
                    title=u'to',
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(60, -1),
                    border=RectType(4, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                DetailSynchronizedAttributeEditorBlock.template('ToMailEditField',
                    viewAttribute=u'toAddress',
                    border=RectType(2, 2, 2, 2))],
            position=0.1,
            selectedItemsAttribute=u'who',
            stretchFactor=0.0,
            border=RectType(0, 0, 6, 6)).install(parcel)

    
    acceptShareButton = \
        AcceptShareButtonBlock.template('AcceptShareButton').install(parcel)
        # (We'll flesh out this definition below; we predeclare it for the event.)        
    acceptShareEvent = \
        BlockEvent.template('AcceptShare',
            'SendToBlockByReference',
            destinationBlockReference=acceptShareButton).install(parcel)

    acceptShareButton = \
        AcceptShareButtonBlock.template('AcceptShareButton',
            title=_(u'Accept this sharing invitation'),
            buttonKind='Text',
            position=0.88,
            stretchFactor=0.0,
            size=SizeType(80, 30),
            minimumSize=SizeType(220, 24),
            alignmentEnum='alignCenter',
            event=acceptShareEvent,
            border=RectType(6, 6, 6, 6)).install(parcel)
    
    attachmentArea = \
        AttachmentAreaBlock.template('AttachmentArea',
            childrenBlocks=[
                StaticText.template('AttachmentString',
                    title=_(u'attachments'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Right',
                    stretchFactor=0.0,
                    minimumSize=SizeType(70, 24),
                    border=RectType(4, 0, 0, 0)),
                makeSpacerBlock(parcel, SizeType(8, -1)),
                AttachmentTextFieldBlock.template('AttachmentTextField',
                    characterStyle=blocks.TextStyle,
                    lineStyleEnum='MultiLine',
                    readOnly=True,
                    textAlignmentEnum='Left',
                    minimumSize=SizeType(100, 48),
                    border=RectType(2, 2, 2, 2))],
            position=0.95,
            stretchFactor=0.0,
            border=RectType(0, 0, 0, 6)).install(parcel)
    
    mailSubtree = \
        DetailTrunkSubtree.update(parcel, 'MailSubtree',
            key=osaf.pim.mail.MailMessageMixin.getKind(),
            rootBlocks=[
                fromArea, 
                toMailArea,
                acceptShareButton,
                attachmentArea])

def makeItemCollectionSubtree(parcel, oldVersion):
    # @@@ BJS I didn't bother porting the item collection subtree from
    # parcel.xml because we're not using it now, and the UI will probably
    # change before we start using it again.
    pass

def makeEmptySubtree(parcel, oldVersion):
  # An empty panel, used when there's no item selected in the detail view
  emptyPanel = EmptyPanelBlock.template('EmptyPanel').install(parcel)
  noneSubtree = DetailTrunkSubtree.update(parcel, 'NoDetailView',
                                          key=DetailTrunkSubtree.getKind(),
                                          rootBlocks=[emptyPanel])
