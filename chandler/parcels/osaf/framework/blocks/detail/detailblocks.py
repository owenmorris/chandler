"""

Detail Blocks - detail view parcel initialization

includes a few public utilities: any detail view client can use these to help
assure consistent alignment...

More docs to come, but the key points...
 - Adding to the detail view means annotating your Kind with a L{BranchSubtree}, 
   which adds a list of rootBlocks that should appear if an item of
   that Kind is displayed.
 - An item can inherit from multiple Kinds; each block in the 
   L{BranchSubtree}'s rootBlocks list has a 'position' attribute that 
   determines the ordering in the resulting detail view. 
 - The block hierarchies you create will likely look like:
     (area)
        (label)
        (spacer)
        (Attribute Editor)

I've created functions (L{makeSubtree}, L{makeArea}, L{makeSpacer}, 
L{makeEditor}) to simplify the process for the common case; there are lots of 
examples below in the basic pim Kinds' subtrees.
"""

from Detail import *
from osaf.framework.blocks import *
import osaf.pim
from i18n import OSAFMessageFactory as _
from osaf.pim.structs import SizeType, RectType


_uniqueNameIndicies = {} 
def uniqueName(parcel, prefix=''):
    """ 
    Return an item name unique in this parcel. Used when we don't
    need to refer to an item by name. 

    @@@ pje pointed out that this may still be perilous.

    @param parcel: The parcel we'll create the item in
    @type parcel: Parcel
    @param prefix: A base for the name, to which this method will add a number
    to make it unique
    @type prefix: String
    @returns: A name that doesn't currently exist in this parcel's namespace
    @rtype: String
    """
    global _uniqueNameIndicies
    i = _uniqueNameIndicies.get(parcel.namespace, 0)
    while True:
        i += 1
        name = "%s%s" % (prefix, i)
        if not parcel.hasChild(name):
            break
    _uniqueNameIndicies[parcel.namespace] = i
    return name

def makeArea(parcel, name, stretchFactor=None, border=None, minimumSize=None, 
             baseClass=ContentItemDetail, **kwds):
    """
    Make a block template that'll contain one horizontal slice of the detail view
    
    Call .install(parcel) on the resulting template, either directly or after
    building up a list of templates, to actually instantiate the item in the
    parcel.
    
    @param parcel: The parcel that the block will go into
    @type parcel: Parcel
    @param name: A unique name for this block
    @type name: String
    @param stretchFactor: Optionally, override the default stretchFactor on 
    the new block
    @type stretchFactor: float
    @param border: Optionally, override the default border on the new block
    @type border: Rect
    @param minimumSize: Optionally, override the default minimumSize of the new 
    block
    @type minimumSize: Size
    @param baseClass: Optionally, specify the base class of the new block; defaults
    to ContentItemDetail.
    @type baseClass: class
    @returns: The new block template.
    """
    return baseClass.template(name,
                              stretchFactor=stretchFactor or 0.0,
                              minimumSize=minimumSize or SizeType(300, 24),
                              border=border or RectType(0, 0, 0, 6),
                              **kwds)

def makeLabel(parcel, label=u'', borderTop=5, border=None):
    """
    Make a StaticText label template for use in the detail view.
    
    Call .install(parcel) on the resulting template, either directly or after
    building up a list of templates, to actually instantiate the item in the
    parcel.
    
    @param parcel: The parcel that the label block will go into
    @type parcel: Parcel
    @param label: The label to be displayed (usually specified as "_(u'something')"
    to allow internationalization)
    @type label: Unicode
    @param borderTop: Optionally, specify a top border of 5, with 0 border on the
    other sides
    @type borderTop: Integer
    @param border: Optionally, specify all four sides of the border on the new 
    label block.
    @type border: Rect
    @returns: The new label block template.
    """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)
    border = border or RectType(borderTop, 0, 0, 0)
    return StaticText.template(uniqueName(parcel, 'Label'),
                               title=label,
                               characterStyle=blocks.LabelStyle,
                               textAlignmentEnum='Right',
                               stretchFactor=0.0,
                               minimumSize=SizeType(60, -1),
                               border=border)

def makeSpacer(parcel, size=None, width=-1, height=-1, 
               name=None, baseClass=ControlBlocks.StaticText, **kwds):
    """
    Make a spacer block template for use in the detail view.
    
    Call .install(parcel) on the resulting template, either directly or after
    building up a list of templates, to actually instantiate the item in the
    parcel.
    
    @param parcel: The parcel that the spacer block will go into
    @type parcel: Parcel
    @param size: The size of the spacer block (handy if you want to specify both 
    dimensions)
    @type size: Size
    @param width: The width of the spacer block (handy if you want the default height)
    @type width: Integer
    @param height: The height of the spacer block (handy if you want the default width)
    @type height: Integer
    @param name: A unique name within this parcel for the spacer block. One will 
    be automatically generated if you don't specify one.
    @type name: String
    @param baseClass: Optionally, specify the base class of the new block; defaults
    to StaticText, but a subclass of SynchronizedSpacerBlock can be used if the 
    spacer's visibility needs to be conditioned on data in the item being displayed.
    @type baseClass: class
    @returns: The new spacer block template.
    """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)
    size = size or SizeType(width, height)
    return baseClass.template(name or uniqueName(parcel, 'Spacer'),
                                title=u'',
                                characterStyle=blocks.LabelStyle,
                                stretchFactor=0.0,
                                minimumSize=size, **kwds)

def makeEditor(parcel, name, viewAttribute, border=None, 
               baseClass=DetailSynchronizedAttributeEditorBlock,
               characterStyle=None,
               presentationStyle=None, **kwds):
    """
    Make an Attribute Editor block template for the detail view.
    
    Call .install(parcel) on the resulting template, either directly or after
    building up a list of templates, to actually instantiate the item in the
    parcel.
    
    @param parcel: The parcel that the L{AEBlock} will go into
    @type parcel: Parcel
    @param name: A unique name within this parcel for the L{AEBlock}.
    @type name: String
    @param viewAttribute: The name of the attribute to be edited by this editor.
    @type viewAttribute: String
    @param border: Optionally, override the default border on the new block
    @type border: Rect
    @param baseClass: Optionally, specify the base class of the new block; defaults
    to L{DetailSynchronizedAttributeEditorBlock}.
    @type baseClass: class
    @param characterStyle: override the default L{CharacterStyle} on the new block.
    @type characterStyle: CharacterStyle
    @param presentationStyle: Optional dictionary for customizing the selection of
    this block's attribute editor, or for customizing the behavior of that editor.
    This dictionary is processed into a new L{PresentationStyle} instance.
    @type presentationStyle: dict
    @param kwds: Other keyword arguments to be passed in creation of the new block.
    @type kwds: dict
    @returns: The new attribute editor block template.
    """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)
    ps = presentationStyle is not None \
       and PresentationStyle.update(parcel, 
                                    uniqueName(parcel, 'PresentationStyle'),
                                    **presentationStyle) \
       or None
    border = border or RectType(2, 2, 2, 2)

    # We need to find the Resynchronize event... it's in the given parcel if
    # we're building the detail view, or we'll get the detail view's namespace
    # if we're building an editor for another parcel. (We do it this way 'cuz
    # it'd be bad to schema.ns the detail view while building the detail view.)
    try:
        resyncEvent = parcel['Resynchronize']
    except KeyError:
        detailParcelPath = '.'.join(__name__.split('.')[:-1])
        resyncEvent = schema.ns(detailParcelPath, parcel.itsView).Resynchronize

    ae = baseClass.template(name, viewAttribute=viewAttribute,
                            characterStyle=characterStyle or blocks.TextStyle,
                            presentationStyle=ps, border=border, 
                            changeEvent=resyncEvent, **kwds)
    return ae

def makeSubtree(parcel, kindOrClass, rootBlocks):
    """
    Make a BranchSubtree annotation for this Kind, containing
    these top-level blocks.
    """
    if not isinstance(kindOrClass, schema.Kind):
        kindOrClass = kindOrClass.getKind(parcel.itsView)
    BranchSubtree(kindOrClass).rootBlocks = rootBlocks

#
# The detail view parcel itself
#
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
    makeEmptySubtree(parcel, oldVersion)
                      
def registerAttributeEditors(parcel, oldVersion):
    # make the detail view's attribute editors at repository-init time
    # If you edit this dictionary, please keep it in alphabetical order by key.
    aeList = {
        'DateTime+calendarDateOnly': 'CalendarDateAttributeEditor',
        'DateTime+calendarTimeOnly': 'CalendarTimeAttributeEditor',
        'EmailAddress+outbound': 'OutboundEmailAddressAttributeEditor',
        'NoneType+appearsIn': 'AppearsInAttributeEditor',
        'ListCollection+appearsIn': 'AppearsInAttributeEditor',
        'RecurrenceRuleSet+custom': 'RecurrenceCustomAttributeEditor',
        'RecurrenceRuleSet+ends': 'RecurrenceEndsAttributeEditor',
        'RecurrenceRuleSet+occurs': 'RecurrenceAttributeEditor',
        'TimeDelta+reminder': 'ReminderAttributeEditor',
    }
    for typeName, className in aeList.items():
        AttributeEditorMapping.update(parcel, typeName, className=\
                                      __name__ + '.' + className)
    
def makeRootStuff(parcel, oldVersion):
    # The BranchPoint mechanism starts each specific detail view by cloning 
    # this stub.
    detailRoot = DetailRootBlock.template('DetailRoot',
                                          orientationEnum='Vertical',
                                          size=SizeType(80, 20),
                                          minimumSize=SizeType(80, 40),
                                          eventBoundary=True)
    detailRoot.install(parcel)
     
    # Our Resynchronize event.
    resyncEvent = BlockEvent.template('Resynchronize',
                                      dispatchEnum='SendToBlockByName',
                                      dispatchToBlockName='DetailRoot'
                                      ).install(parcel)

    # A few spacer blocks, copied by other parcel.xml blocks.
    # @@@ Should go away when parcel.xml conversion is complete!
    makeSpacer(parcel, height=6, name='TopSpacer', position=0.01).install(parcel)
    makeSpacer(parcel, width=8, name='HorizontalSpacer').install(parcel)

def makeMarkupBar(parcel, oldVersion):
    """ Build the markup bar. """
    
    # Predeclare this - we'll flesh it out below.
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

    readOnly = \
        BlockEvent.template('ReadOnly',
                            'SendToBlockByReference',
                            destinationBlockReference=markupBar).install(parcel)

    # The buttons.
    mailMessageButton = \
        MailMessageButtonBlock.template('MailMessageButton',
                                        title=messages.STAMP_MAIL,
                                        bitmap="MarkupBarMail.png",
                                        toolbarItemKind='Button',
                                        toggle=True,
                                        helpString=messages.STAMP_MAIL_HELP,
                                        event=buttonPressed)
    
    taskStamp = \
        TaskStampBlock.template('TaskStamp',
                                title=messages.STAMP_TASK,
                                bitmap="MarkupBarTask.png",
                                toolbarItemKind='Button',
                                toggle=True,
                                helpString=messages.STAMP_TASK_HELP,
                                event=buttonPressed)
                        
    calendarStamp = \
        CalendarStampBlock.template('CalendarStamp',
                                    title=messages.STAMP_CALENDAR,
                                    bitmap="MarkupBarEvent.png",
                                    toolbarItemKind='Button',
                                    toggle=True,
                                    helpString=messages.STAMP_CALENDAR_HELP,
                                    event=buttonPressed)

    privateSwitchButton = \
        PrivateSwitchButtonBlock.template('PrivateSwitchButton',
                                    title=messages.PRIVATE,
                                    bitmap="MarkupBarPrivate.png",
                                    toolbarItemKind='Button',
                                    toggle=True,
                                    helpString=messages.PRIVATE,
                                    event=togglePrivate)

    readOnlyIcon = \
        ReadOnlyIconBlock.template('ReadOnlyIcon',
                                    title=messages.READONLY,
                                    bitmap="MarkupBarReadOnly.png",
                                    disabledBitmap="MarkupBarReadWrite.png",
                                    toolbarItemKind='Status',
                                    helpString=messages.READONLY,
                                    event=readOnly)

    # Finally, (re-)do the bar itself.
    markupBar = MarkupBarBlock.template('MarkupBar',
                                        childrenBlocks=[mailMessageButton,
                                                        taskStamp,
                                                        calendarStamp,
                                                        privateSwitchButton,
                                                        readOnlyIcon],
                                        position=0.0,
                                        toolSize=SizeType(20, 20),
                                        separatorWidth=16,
                                        stretchFactor=0.0).install(parcel)
    
def makeNoteSubtree(parcel, oldVersion):
    """ Build the subtree (and related stuff) for Note """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)

    # First, the headline AEBlock and the area it sits in
    headlineAEBlock = makeEditor(parcel, 'HeadlineBlock',
                                 viewAttribute=u'about',
                                 characterStyle=blocks.BigTextStyle,
                                 presentationStyle={
                                     # empty sample means "use displayname"
                                     'sampleText': u'',
                                     'editInPlace': True })
    headlineArea = \
        makeArea(parcel, 'HeadlineArea',
            childrenBlocks = [
                makeSpacer(parcel, SizeType(0,22)),
                headlineAEBlock],
            position=0.5,
            border=RectType(0,6,0,6)).install(parcel)

    # Appears in block
    appearsInArea = \
        makeArea(parcel, 'AppearsInArea',
            viewAttribute=u'collections',
            border=RectType(0,0,0,0),
            childrenBlocks=[
                # (the label is added as part of the string for now)
                #makeLabel(parcel, _(u'appears in'), borderTop=2),
                #makeSpacer(parcel, width=8),
                makeEditor(parcel, 'AppearsIn',
                           viewAttribute=u'collections',
                           border=RectType(0,2,2,2),
                           presentationStyle={'format': 'appearsIn'})],
            position=0.95).install(parcel)    

    # Then, the Note AEBlock
    notesBlock = makeEditor(parcel, 'NotesBlock',
                            viewAttribute=u'bodyString',
                            presentationStyle={'lineStyleEnum': 'MultiLine'},
                            position=0.9).install(parcel)

    # Finally, the subtree
    makeSubtree(parcel, osaf.pim.Note, [
        makeSpacer(parcel, height=6, position=0.01).install(parcel),
        parcel['MarkupBar'],
        headlineArea, 
        makeSpacer(parcel, height=7, position=0.8999).install(parcel),
        notesBlock,
        appearsInArea,
    ])

def makeCalendarEventSubtree(parcel, oldVersion):
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)

    locationArea = \
        CalendarLocationAreaBlock.template('CalendarLocationArea',
            childrenBlocks=[
                makeSpacer(parcel, SizeType(0, 22)),
                makeEditor(parcel, 'CalendarLocation',
                           viewAttribute=u'location',
                           presentationStyle={'sampleText': u'',
                                              'editInPlace': True})],
            stretchFactor=0.0,
            minimumSize=SizeType(300,10),
            border=RectType(0, 6, 0, 6))

    if '__WXMSW__' in wx.PlatformInfo:
        allDaySpacerWidth = 8
    else:
        allDaySpacerWidth = 6

    allDayArea = \
        makeArea(parcel, 'CalendarAllDayArea',
            baseClass=CalendarAllDayAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'all-day'), borderTop=4),
                makeSpacer(parcel, width=allDaySpacerWidth),
                makeEditor(parcel, 'EditAllDay',
                    viewAttribute=u'allDay',
                    stretchFactor=0.0,
                    minimumSize=SizeType(16,-1))])

    startTimeArea = \
        makeArea(parcel, 'CalendarStartTimeArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'starts'), borderTop=4),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditCalendarStartDate',
                    viewAttribute=u'startTime',
                    presentationStyle={'format': 'calendarDateOnly'},
                    stretchFactor=0.0,
                    size=SizeType(75, -1)),
                CalendarConditionalLabelBlock.template('CalendarStartAtLabel',
                    title=_(u'at'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Center',
                    stretchFactor=0.0,
                    border=RectType(4, 4, 0, 4)),
                makeEditor(parcel, 'EditCalendarStartTime',
                    baseClass=CalendarTimeAEBlock,
                    viewAttribute=u'startTime',
                    presentationStyle={'format': 'calendarTimeOnly'},
                    stretchFactor=0.0,
                    size=SizeType(85, -1))])
    
    endTimeArea = \
        makeArea(parcel, 'CalendarEndTimeArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'ends'), borderTop=4),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditCalendarEndDate',
                    viewAttribute=u'endTime',
                    presentationStyle={'format': 'calendarDateOnly'},
                    stretchFactor=0.0,
                    size=SizeType(75, -1)),
                CalendarConditionalLabelBlock.template('CalendarEndAtLabel',
                    title=_(u'at'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Center',
                    stretchFactor=0.0,
                    border=RectType(4, 4, 0, 4)),
                makeEditor(parcel, 'EditCalendarEndTime',
                    baseClass=CalendarTimeAEBlock,
                    viewAttribute=u'endTime',
                    presentationStyle={'format': 'calendarTimeOnly'},
                    stretchFactor=0.0,
                    size=SizeType(85, -1))])

    timeZoneArea = \
        makeArea(parcel, 'CalendarTimeZoneArea',
            baseClass=CalendarTimeZoneAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'time zone')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditTimeZone',
                    baseClass=CalendarTimeAEBlock,
                    viewAttribute=u'startTime',
                    presentationStyle={'format': 'timeZoneOnly'},
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1))])

    transparencyArea = \
        makeArea(parcel, 'CalendarTransparencyArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'status')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditTransparency',
                    viewAttribute=u'transparency',
                    presentationStyle={
                        'format': 'popup',
                        # It'd be nice to not maintain the transparency choices 
                        # separately from the enum values; currently, the 
                        # choices must match the enum's items and ordering.
                        # @@@ XXX i18n!
                        'choices': [_(u'Confirmed'), _(u'Tentative'), _(u'FYI')]},
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1))])
  
    recurrencePopupArea = \
        makeArea(parcel, 'CalendarRecurrencePopupArea',
            baseClass=CalendarRecurrencePopupAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'occurs')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditRecurrence',
                    viewAttribute=u'rruleset',
                    presentationStyle={
                        'format': 'occurs',
                        # These choices must match the enumerated indexes in the
                        # RecurrenceAttributeEditor python code
                        'choices': [_(u'Once'), _(u'Daily'), _(u'Weekly'),
                                    _(u'Biweekly'), _(u'Monthly'), _(u'Yearly'),
                                    _(u'Custom...')]},
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1))])

    recurrenceCustomArea = \
        makeArea(parcel, 'CalendarRecurrenceCustomArea',
            baseClass=CalendarRecurrenceCustomAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, u'', borderTop=2), # leave label blank.
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'CalCustomValue',
                    viewAttribute=u'rruleset',
                    presentationStyle={'format': 'custom'},
                    minimumSize=SizeType(300, -1))])
                                           
    recurrenceEndArea = \
        makeArea(parcel, 'CalendarRecurrenceEndArea',
            baseClass=CalendarRecurrenceEndAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'ends')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditRecurrenceEnd',
                    viewAttribute=u'rruleset',
                    presentationStyle={'format': 'ends'},
                    stretchFactor=0.0,
                    size=SizeType(75, -1))])

    reminderArea = \
        makeArea(parcel, 'CalendarReminderArea',
            baseClass=CalendarReminderAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'alarm'), borderTop=5),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditReminder',
                    viewAttribute=u'reminderInterval',
                    presentationStyle={
                        # @@@ XXX i18n: the code assumes that if the value
                        # starts with a digit, it's a number of minutes; if not,
                        # it's None.
                        'choices': [_(u'None'), _(u'1 minute'), _(u'5 minutes'), 
                                    _(u'10 minutes'), _(u'30 minutes'), 
                                    _(u'60 minutes'), _(u'90 minutes')],
                        'format' : 'reminder'
                    },
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1))])
 
    calendarDetails = \
        makeArea(parcel, 'CalendarDetails',
            orientationEnum='Vertical',
            position=0.8,
            childrenBlocks = [
                locationArea,
                makeSpacer(parcel, height=4),
                allDayArea,
                makeSpacer(parcel, height=4),
                startTimeArea,
                makeSpacer(parcel, height=1),
                endTimeArea,
                makeSpacer(parcel, height=7,
                           baseClass=CalendarTimeZoneSpacerBlock),
                timeZoneArea,
                makeSpacer(parcel, height=7),
                transparencyArea,
                makeSpacer(parcel, height=7,
                           baseClass=CalendarRecurrencePopupSpacerBlock),
                recurrencePopupArea,
                makeSpacer(parcel, height=1,
                           baseClass=CalendarRecurrenceCustomSpacerBlock),
                recurrenceCustomArea,
                recurrenceEndArea,
                makeSpacer(parcel, height=7,
                           baseClass=CalendarReminderSpacerBlock),
                reminderArea]).install(parcel)

    makeSubtree(parcel, osaf.pim.CalendarEventMixin, [ calendarDetails ])
 
def makeMailSubtree(parcel, oldVersion):
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)    
    outboundFromArea = \
        makeArea(parcel, 'OutboundFromArea',
            baseClass=OutboundOnlyAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'from')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailOutboundFrom',
                    presentationStyle={'format': 'outbound'},
                    viewAttribute=u'fromAddress')],
            position=0.1).install(parcel)
    inboundFromArea = \
        makeArea(parcel, 'InboundFromArea',
            baseClass=InboundOnlyAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'from')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailInboundFrom',
                    viewAttribute=u'fromAddress')],
            position=0.1).install(parcel)

    toArea = \
        makeArea(parcel, 'ToArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'to')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailTo',
                    viewAttribute=u'toAddress')],
            position=0.11).install(parcel)
    ccArea = \
        makeArea(parcel, 'CcArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'cc')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailCc',
                    viewAttribute=u'ccAddress')],
            position=0.111).install(parcel)
    bccArea = \
        makeArea(parcel, 'BccArea',
            baseClass=OutboundOnlyAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'bcc')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailBcc',
                    viewAttribute=u'bccAddress')],
            position=0.112,
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
        makeArea(parcel, 'AttachmentArea',
            baseClass=AttachmentAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'attachments')),
                makeSpacer(parcel, width=8),
                AttachmentTextFieldBlock.template('AttachmentTextField',
                    characterStyle=blocks.TextStyle,
                    lineStyleEnum='MultiLine',
                    readOnly=True,
                    textAlignmentEnum='Left',
                    minimumSize=SizeType(100, 48),
                    border=RectType(2, 2, 2, 2))],
            position=0.95).install(parcel)
    
    makeSubtree(parcel, osaf.pim.mail.MailMessageMixin, [
        outboundFromArea, 
        inboundFromArea, 
        toArea,
        ccArea,
        bccArea,
        # @@@ Disabled until we resume work on sharing invitations
        # acceptShareButton,
        attachmentArea,
    ])
    
def makeEmptySubtree(parcel, oldVersion):
  # An empty panel, used when there's no item selected in the detail view
  # (We use the Block kind as the key, though it's not a content kind)
  emptyPanel = EmptyPanelBlock.template('EmptyPanel').install(parcel)
  makeSubtree(parcel, Block.Block, [ emptyPanel ])
