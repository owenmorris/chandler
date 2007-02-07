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

"""
Detail Blocks - detail view parcel initialization

Includes a few public utilities: any detail view client can use these to help
assure consistent alignment.

More docs to come, but the key points:

 - Adding to the detail view means annotating your Kind with
   a L{BranchSubtree}, which adds a list of rootBlocks that
   should appear if an item of that Kind is displayed.
 - An item can inherit from multiple Kinds; each block in the
   L{BranchSubtree}'s rootBlocks list has a 'position' attribute
   that determines the ordering in the resulting detail view.
 - The block hierarchies you create will likely look like::
     (area)
        (label)
        (spacer)
        (Attribute Editor)

I've created functions (L{makeSubtree}, L{makeArea}, L{makeSpacer},
L{makeEditor}) to simplify the process for the common case; there
are lots of examples below in the basic pim Kinds' subtrees.
"""

from detail import *
from osaf.framework.blocks import *
import osaf.pim
from i18n import ChandlerMessageFactory as _
from osaf.pim.structs import SizeType, RectType
from osaf.pim.mail import MailStamp


_uniqueNameIndicies = {} 
def uniqueName(parcel, prefix=''):
    """ 
    Return an item name unique in this parcel. Used when we don't
    need to refer to an item by name. 

    Note: @@@ pje pointed out that this may still be perilous.

    @param parcel: The parcel we'll create the item in
    @type parcel: Parcel
    @param prefix: A base for the name, to which this method will add a number
                   to make it unique
    @type prefix: String
    @return: A name that doesn't currently exist in this parcel's namespace
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
    Make a block template that'll contain one horizontal slice of
    the detail view.

    Call .install(parcel) on the resulting template, either directly
    or after building up a list of templates, to actually instantiate
    the item in the parcel.
    
    @param parcel: The parcel that the block will go into
    @type parcel: Parcel
    @param name: A unique name for this block
    @type name: String
    @param stretchFactor: Optionally, override the default stretchFactor
                          on the new block
    @type stretchFactor: float
    @param border: Optionally, override the default border on the new block
    @type border: Rect
    @param minimumSize: Optionally, override the default minimumSize of
                        the new block
    @type minimumSize: Size
    @param baseClass: Optionally, specify the base class of the new block;
                      defaults to ContentItemDetail.
    @type baseClass: class
    @return: The new block template.
    """
    return baseClass.template(name,
                              stretchFactor=stretchFactor or 0.0,
                              minimumSize=minimumSize or SizeType(300, 24),
                              border=border or RectType(0, 0, 0, 6),
                              **kwds)

def makeLabel(parcel, label=u'', borderTop=5, border=None, width=60, 
              textAlignmentEnum=None, **kwds):
    """
    Make a StaticText label template for use in the detail view.
    
    Call .install(parcel) on the resulting template, either directly
    or after building up a list of templates, to actually instantiate
    the item in the parcel.
    
    @param parcel: The parcel that the label block will go into
    @type parcel: Parcel
    @param label: The label to be displayed (usually specified as
                  "_(u'something')" to allow internationalization)
    @type label: Unicode
    @param borderTop: Optionally, specify a top border of 5, with 0 border
                      on the other sides
    @type borderTop: Integer
    @param border: Optionally, specify all four sides of the border on
                   the new label block.
    @type border: Rect
    @param width: Optionally, override the default width (60)
                  (eventually, this'll be ignored and the label will
                  measure itself).
    @type width: Integer
    @return: The new label block template.
    """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)
    border = border or RectType(borderTop, 0, 0, 0)
    textAlignmentEnum = textAlignmentEnum or 'Right'
    return StaticText.template(uniqueName(parcel, 'Label'),
                               title=label,
                               characterStyle=blocks.LabelStyle,
                               textAlignmentEnum=textAlignmentEnum,
                               stretchFactor=0.0,
                               minimumSize=SizeType(width, -1),
                               border=border, **kwds)

def makeSpacer(parcel, size=None, width=-1, height=-1, 
               name=None, baseClass=ControlBlocks.StaticText, **kwds):
    """
    Make a spacer block template for use in the detail view.
    
    Call .install(parcel) on the resulting template, either directly
    or after building up a list of templates, to actually instantiate
    the item in the parcel.
    
    @param parcel: The parcel that the spacer block will go into
    @type parcel: Parcel
    @param size: The size of the spacer block (handy if you want to
                 specify both dimensions)
    @type size: Size
    @param width: The width of the spacer block 
                  (handy if you want the default height)
    @type width: Integer
    @param height: The height of the spacer block
                   (handy if you want the default width)
    @type height: Integer
    @param name: A unique name within this parcel for the spacer block.
                 One will be automatically generated if you don't specify one.
    @type name: String
    @param baseClass: Optionally, specify the base class of the new block;
                      defaults to StaticText, but a subclass of
                      SynchronizedSpacerBlock can be used if the spacer's
                      visibility needs to be conditioned on data in the
                      item being displayed.
    @type baseClass: class
    @return: The new spacer block template.
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

    Call .install(parcel) on the resulting template, either directly
    or after building up a list of templates, to actually instantiate
    the item in the parcel.

    @param parcel: The parcel that the L{AEBlock} will go into
    @type parcel: Parcel
    @param name: A unique name within this parcel for the L{AEBlock}.
    @type name: String
    @param viewAttribute: The name of the attribute to be edited by
                          this editor.
    @type viewAttribute: String
    @param border: Optionally, override the default border on
                   the new block
    @type border: Rect
    @param baseClass: Optionally, specify the base class of the new block;
                      defaults to L{DetailSynchronizedAttributeEditorBlock}.
    @type baseClass: class
    @param characterStyle: Override the default L{CharacterStyle} on
                           the new block.
    @type characterStyle: CharacterStyle
    @param presentationStyle: Optional dictionary for customizing the
                              selection of this block's attribute editor,
                              or for customizing the behavior of that editor.
                              This dictionary is processed into a new
                              L{PresentationStyle} instance.
    @type presentationStyle: dict
    @param kwds: Other keyword arguments to be passed in creation of
                 the new block.
    @type kwds: dict
    @return: The new attribute editor block template.
    """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)
    ps = presentationStyle is not None \
       and PresentationStyle.update(parcel, 
                                    uniqueName(parcel, 'PresentationStyle'),
                                    **presentationStyle) \
       or None
    border = border or RectType(2, 2, 2, 2)

    ae = baseClass.template(name, viewAttribute=viewAttribute,
                            characterStyle=characterStyle or blocks.TextStyle,
                            presentationStyle=ps, border=border, **kwds)
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
    """
    Instantiate all the blocks, events, etc for the detail view.
    """

    # First, register all the custom attribute editors 
    registerAttributeEditors(parcel, oldVersion)
    
    # Make all the 'global' stuff
    makeRootStuff(parcel, oldVersion)
    
    # Make the MarkupBar
    makeMarkupBar(parcel, oldVersion)
    
    # Make the various kind-specific subtrees
    makeNoteSubtree(parcel, oldVersion)
    makeEmptySubtree(parcel, oldVersion)
                      
def registerAttributeEditors(parcel, oldVersion):
    # make the detail view's attribute editors at repository-init time
    # If you edit this dictionary, please keep it in alphabetical order by key.
    aeDict = {
        'DateTime+calendarDateOnly': 'CalendarDateAttributeEditor',
        'DateTimeTZ+calendarDateOnly': 'CalendarDateAttributeEditor',
        'DateTime+calendarTimeOnly': 'CalendarTimeAttributeEditor',
        'DateTimeTZ+calendarTimeOnly': 'CalendarTimeAttributeEditor',
        'EmailAddress+outbound': 'OutboundEmailAddressAttributeEditor',
        'NoneType+appearsIn': 'AppearsInAttributeEditor',
        'RecurrenceRuleSet+custom': 'RecurrenceCustomAttributeEditor',
        'RecurrenceRuleSet+ends': 'RecurrenceEndsAttributeEditor',
        'RecurrenceRuleSet+occurs': 'RecurrenceAttributeEditor',
        'SmartCollection+appearsIn': 'AppearsInAttributeEditor',
        'Reminder+reminderType': 'ReminderTypeAttributeEditor',
        'TimeDelta+reminderUnits': 'ReminderUnitsAttributeEditor',
        'TimeDelta+reminderScale': 'ReminderScaleAttributeEditor',
    }
    AttributeEditorMapping.register(parcel, aeDict, __name__)
    
def makeRootStuff(parcel, oldVersion):
    # The BranchPoint mechanism starts each specific detail view by cloning 
    # this stub.
    detailRoot = DetailRootBlock.template('DetailRoot',
                                          orientationEnum='Vertical',
                                          size=SizeType(80, 20),
                                          minimumSize=SizeType(80, 40),
                                          eventBoundary=True)
    detailRoot.install(parcel)

def makeCalendarArea(parcel, oldVersion):
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)

    locationArea = \
        CalendarLocationAreaBlock.template('CalendarLocationArea',
            childrenBlocks=[
                makeSpacer(parcel, SizeType(0, 22)),
                makeEditor(parcel, 'CalendarLocation',
                           viewAttribute=pim.EventStamp.location.name,
                           presentationStyle={'sampleText': _(u'location'),
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
                makeLabel(parcel, _(u'&all-day'), borderTop=4),
                makeSpacer(parcel, width=allDaySpacerWidth),
                makeEditor(parcel, 'EditAllDay',
                    viewAttribute=pim.EventStamp.allDay.name,
                    stretchFactor=0.0,
                    minimumSize=SizeType(16,-1))])

    startTimeArea = \
        makeArea(parcel, 'CalendarStartTimeArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'sta&rts'), borderTop=4),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditCalendarStartDate',
                    viewAttribute=pim.EventStamp.startTime.name,
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
                    viewAttribute=pim.EventStamp.startTime.name,
                    presentationStyle={'format': 'calendarTimeOnly'},
                    stretchFactor=0.0,
                    size=SizeType(85, -1))])
    
    endTimeArea = \
        makeArea(parcel, 'CalendarEndTimeArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'en&ds'), borderTop=4),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditCalendarEndDate',
                    viewAttribute=pim.EventStamp.endTime.name,
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
                    viewAttribute=pim.EventStamp.endTime.name,
                    presentationStyle={'format': 'calendarTimeOnly'},
                    stretchFactor=0.0,
                    size=SizeType(85, -1))])

    timeZoneArea = \
        makeArea(parcel, 'CalendarTimeZoneArea',
            baseClass=CalendarTimeZoneAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'time &zone')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditTimeZone',
                    baseClass=CalendarTimeZoneAEBlock,
                    viewAttribute=pim.EventStamp.startTime.name,
                    presentationStyle={'format': 'timeZoneOnly'},
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1))])

    transparencyArea = \
        makeArea(parcel, 'CalendarTransparencyArea',
            baseClass=CalendarTransparencyAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'stat&us')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditTransparency',
                    baseClass=CalendarTransparencyAEBlock,
                    viewAttribute=pim.EventStamp.transparency.name,
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
                makeLabel(parcel, _(u'&occurs')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditRecurrence',
                    viewAttribute=pim.EventStamp.rruleset.name,
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
                    viewAttribute=pim.EventStamp.rruleset.name,
                    presentationStyle={'format': 'custom'},
                    minimumSize=SizeType(300, -1))])
                                           
    recurrenceEndArea = \
        makeArea(parcel, 'CalendarRecurrenceEndArea',
            baseClass=CalendarRecurrenceEndAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'ends')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditRecurrenceEnd',
                    viewAttribute=pim.EventStamp.rruleset.name,
                    presentationStyle={'format': 'ends'},
                    stretchFactor=0.0,
                    size=SizeType(75, -1))])
 
    timeDescriptionArea = \
        makeArea(parcel, 'CalendarTimeDescriptionArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'when'), borderTop=2),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'TimeDescription',
                    viewAttribute=pim.EventStamp.timeDescription.name,
                    readOnly=True,
                    )])
    
    timeEditArea = \
        makeArea(parcel, 'CalendarTimeEditArea',
            orientationEnum='Vertical',
            childrenBlocks=[
                allDayArea,
                makeSpacer(parcel, height=4),
                startTimeArea,
                makeSpacer(parcel, height=1),
                endTimeArea,
                makeSpacer(parcel, height=7,
                           baseClass=CalendarTimeZoneSpacerBlock),
                timeZoneArea,
                makeSpacer(parcel, height=7,
                           baseClass=CalendarTransparencySpacerBlock),
                transparencyArea,
                makeSpacer(parcel, height=7,
                           baseClass=CalendarRecurrencePopupSpacerBlock),
                recurrencePopupArea,
                makeSpacer(parcel, height=1,
                           baseClass=CalendarRecurrenceCustomSpacerBlock),
                recurrenceCustomArea,
                recurrenceEndArea,
            ])
    
    return makeArea(parcel, 'CalendarDetails',
            baseClass=EventAreaBlock,
            orientationEnum='Vertical',
            position=0.8,
            childrenBlocks = [
                locationArea,
                makeSpacer(parcel, height=4),
                #timeDescriptionArea,
                timeEditArea]).install(parcel)
 
def makeMailArea(parcel, oldVersion):
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)    
    inboundFromArea = \
        makeArea(parcel, 'InboundFromArea',
            baseClass=InboundOnlyAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'from')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailInboundFrom',
                    viewAttribute=MailStamp.fromAddress.name,
                    presentationStyle={'editInPlace': True,
                                        'maxLineCount': 3})],
            position=0.1).install(parcel)

    toArea = \
        makeArea(parcel, 'ToArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'to')), # XXX "&to" conflicts with Test menu
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailTo',
                    viewAttribute=MailStamp.toAddress.name,
                    presentationStyle={'editInPlace': True,
                                        'sampleText': _(u'Add addressees'),
                                        'maxLineCount': 3})],
            position=0.11).install(parcel)
    ccArea = \
        makeArea(parcel, 'CcArea',
            childrenBlocks=[
                makeLabel(parcel, _(u'cc')), # XXX "&cc" conflicts with Collection menu
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailCc',
                    viewAttribute=MailStamp.ccAddress.name,
                    presentationStyle={'editInPlace': True,
                                        'maxLineCount': 3})],
            position=0.111).install(parcel)
    bccArea = \
        makeArea(parcel, 'BccArea',
            baseClass=OutboundOnlyAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'bcc')), # XXX no conflicts with "&bcc" but still does not work because we mess with the controls
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailBcc',
                    viewAttribute=MailStamp.bccAddress.name,
                    presentationStyle={'editInPlace': True,
                                        'maxLineCount': 3})],
            position=0.112,
            border=RectType(0, 0, 6, 6)).install(parcel)

    '''
    sendAsArea = \
        makeArea(parcel, 'SendAsArea',
            baseClass=SendAsAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'send as')),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailOutboundFrom',
                    presentationStyle={'format': 'outbound'},
                    viewAttribute=MailStamp.fromAddress.name)],
            position=0.113).install(parcel)
    '''
    outboundFromArea = \
        makeArea(parcel, 'OutboundFromArea',
            baseClass=OutboundOnlyAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'send as')), # XXX "&send as" conflicts with Share menu
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditMailOutboundFrom',
                    presentationStyle={'format': 'outbound'},
                    viewAttribute=MailStamp.fromAddress.name)],
            position=0.113).install(parcel)

    #acceptShareButton = \
        #AcceptShareButtonBlock.template('AcceptShareButton').install(parcel)
        ## (We'll flesh out this definition below; we predeclare it for the event.)        
    #acceptShareEvent = \
        #BlockEvent.template('AcceptShare',
            #'SendToBlockByReference',
            #destinationBlockReference=acceptShareButton).install(parcel)

    #acceptShareButton = \
        #AcceptShareButtonBlock.template('AcceptShareButton',
            #title=_(u'Accept this sharing invitation'),
            #buttonKind='Text',
            #position=0.88,
            #stretchFactor=0.0,
            #size=SizeType(80, 30),
            #minimumSize=SizeType(220, 24),
            #alignmentEnum='alignCenter',
            #event=acceptShareEvent,
            #border=RectType(6, 6, 6, 6)).install(parcel)
    
    #attachmentArea = \
        #makeArea(parcel, 'AttachmentArea',
            #baseClass=AttachmentAreaBlock,
            #childrenBlocks=[
                #makeLabel(parcel, _(u'attachments')),
                #makeSpacer(parcel, width=8),
                #AttachmentTextFieldBlock.template('AttachmentTextField',
                    #characterStyle=blocks.TextStyle,
                    #lineStyleEnum='MultiLine',
                    #readOnly=True,
                    #textAlignmentEnum='Left',
                    #minimumSize=SizeType(100, 48),
                    #border=RectType(2, 2, 2, 2))],
            #position=0.98).install(parcel)
    
    return makeArea(parcel, 'MailDetails',
            baseClass=MailAreaBlock,
            orientationEnum='Vertical',
            position=0.1,
            childrenBlocks = [
                inboundFromArea, 
                toArea,
                ccArea,
                bccArea,
                outboundFromArea,
                # @@@ Disabled until we resume work on sharing invitations
                # acceptShareButton,
                # @@@ disabled until we rewrite the attachment AE.
                # attachmentArea,
            ]).install(parcel)

def makeMarkupBar(parcel, oldVersion):
    """
    Build the markup bar.
    """

    # Each button just sends this event to itself.
    buttonPressed = BlockEvent.template('ButtonPressed',
                                    dispatchEnum='SendToSender',
                                    commitAfterDispatch=True).install(parcel)

    # The buttons.
    triageStamp = \
        DetailTriageButton.template('TriageStamp',
                                title=messages.STAMP_TRIAGE,
                                icon="TriageDone",
                                helpString=messages.STAMP_TRIAGE_HELP,
                                event=buttonPressed,
                                viewAttribute='unpurgedTriageStatus',
                                stretchFactor=0.0,
                                minimumSize=SizeType(41, 20))

    markupSpacer1 = ControlBlocks.StaticText.template('MarkupSpacer1',
                                    title=u'',
                                    stretchFactor=0.0,
                                    minimumSize=SizeType(30, 18))

    mailMessageButton = \
        MailMessageButtonBlock.template('MailMessageButton',
                                        title=messages.STAMP_MAIL,
                                        icon="MarkupMail",
                                        helpString=messages.STAMP_MAIL_HELP,
                                        event=buttonPressed,
                                        stretchFactor=0.0,
                                        minimumSize=SizeType(30, 18))

    taskStamp = \
        TaskStampButtonBlock.template('TaskStamp',
                                title=messages.STAMP_TASK,
                                icon="MarkupTask",
                                helpString=messages.STAMP_TASK_HELP,
                                event=buttonPressed,
                                stretchFactor=0.0,
                                minimumSize=SizeType(30, 18))

    calendarStamp = \
        CalendarStampButtonBlock.template('CalendarStamp',
                                    title=messages.STAMP_CALENDAR,
                                    icon="MarkupEvent",
                                    helpString=messages.STAMP_CALENDAR_HELP,
                                    event=buttonPressed,
                                    stretchFactor=0.0,
                                    minimumSize=SizeType(30, 18))

    markupSpacer2 = ControlBlocks.StaticText.template('MarkupSpacer2',
                                    title=u'',
                                    stretchFactor=0.0,
                                    minimumSize=SizeType(30, 18))

    privateSwitchButton = \
        PrivateSwitchButtonBlock.template('PrivateSwitchButton',
                                    title=messages.PRIVATE,
                                    icon="MarkupPrivate",
                                    helpString=messages.PRIVATE,
                                    viewAttribute=u'private',
                                    event=buttonPressed,
                                    stretchFactor=0.0,
                                    minimumSize=SizeType(30, 18))

    markupSpacer3 = ControlBlocks.StaticText.template('MarkupSpacer3',
                                    title=u'',
                                    stretchFactor=1.0)

    readOnlyIcon = \
        ReadOnlyIconBlock.template('ReadOnlyIcon',
                                    title=messages.READONLY,
                                    icon="MarkupReadOnly",
                                    helpString=messages.READONLY,
                                    event=buttonPressed,
                                    stretchFactor=0.0,
                                    minimumSize=SizeType(30, 18))

    markupBar = ControlBlocks.ContentItemDetail.template('MarkupBar',
                                    childrenBlocks=[triageStamp,
                                                    markupSpacer1,
                                                    mailMessageButton,
                                                    taskStamp,
                                                    calendarStamp,
                                                    markupSpacer2,
                                                    privateSwitchButton,
                                                    markupSpacer3,
                                                    readOnlyIcon],
                                    position=0.0,
                                    toolSize=SizeType(30, 18),
                                    separatorWidth=16,
                                    stretchFactor=0.0).install(parcel)

def makeNoteSubtree(parcel, oldVersion):
    """
    Build the subtree (and related stuff) for Note.
    """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)

    bylineArea = \
        makeArea(parcel, 'BylineArea',
            childrenBlocks=[
                makeEditor(parcel, 'BylineBlock',
                    baseClass=BylineAEBlock,
                    viewAttribute='byline',
                    presentationStyle={'format' : 'static'})],
            position=0.4,
            border=RectType(0, 6, 6, 6)).install(parcel)

    errorArea = \
        makeArea(parcel, 'ErrorArea',
            baseClass=ErrorAEBlock,
            childrenBlocks=[
                makeEditor(parcel, 'ErrorArea',
                    viewAttribute='error',
                    presentationStyle={'format' : 'static'})],
            position=0.4,
            border=RectType(0, 0, 6, 6)).install(parcel)

    # First, the headline AEBlock and the area it sits in
    headlineAEBlock = makeEditor(parcel, 'HeadlineBlock',
                                 viewAttribute=u'displayName',
                                 characterStyle=blocks.BigTextStyle,
                                 presentationStyle={
                                     'sampleText': _(u'enter title'),
                                     'editInPlace': True })
    headlineArea = \
        makeArea(parcel, 'HeadlineArea',
            childrenBlocks = [
                makeSpacer(parcel, SizeType(0,22)),
                headlineAEBlock],
            position=0.5,
            border=RectType(0,6,0,6)).install(parcel)

    # Next, three rows of reminder stuff:
    # alarm {none/before/after/custom popup}
    #       [units] {minutes/hours/days popup}
    #       [date] at [time]
    reminderTypeArea = \
        makeArea(parcel, 'ReminderTypeArea',
            baseClass=ReminderTypeAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u'alar&m'), borderTop=5),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditReminderType',
                    baseClass=ReminderAEBlock,
                    viewAttribute=pim.Remindable.reminders.name,
                    presentationStyle={ 'format': 'reminderType' },
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1))],
            position=0.81).install(parcel)
    reminderRelativeArea = \
        makeArea(parcel, 'ReminderRelativeArea',
            baseClass=ReminderRelativeAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, u'', borderTop=5),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditReminderUnits',
                    baseClass=ReminderAEBlock,
                    viewAttribute=pim.EventStamp.userReminderInterval.name,
                    presentationStyle={ 'format': 'reminderUnits' },
                    stretchFactor=0.0,
                    size=SizeType(35, -1)),
                makeSpacer(parcel, width=4),
                makeEditor(parcel, 'EditReminderScale',
                    baseClass=ReminderAEBlock,
                    viewAttribute=pim.EventStamp.userReminderInterval.name,
                    presentationStyle={ 'format': 'reminderScale' },
                    stretchFactor=0.0,
                    minimumSize=SizeType(80, -1)),
                ],
            position=0.82).install(parcel)
    reminderAbsoluteArea = \
        makeArea(parcel, 'ReminderAbsoluteArea',
            baseClass=ReminderAbsoluteAreaBlock,
            childrenBlocks=[                
                makeLabel(parcel, u'', borderTop=4),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'EditReminderDate',
                    baseClass=ReminderAEBlock,
                    viewAttribute=pim.Remindable.userReminderTime.name,
                    presentationStyle={'format': 'dateOnly'},
                    stretchFactor=0.0,
                    size=SizeType(75, -1)),
                StaticTextLabel.template('ReminderAtLabel',
                    title=_(u'at'),
                    characterStyle=blocks.LabelStyle,
                    textAlignmentEnum='Center',
                    stretchFactor=0.0,
                    border=RectType(4, 4, 0, 4)),
                makeEditor(parcel, 'EditReminderTime',
                    baseClass=ReminderAEBlock,
                    viewAttribute=pim.Remindable.userReminderTime.name,
                    presentationStyle={'format': 'timeOnly'},
                    stretchFactor=0.0,
                    size=SizeType(85, -1)),
                ],
            position=0.82).install(parcel)



    # The Note AEBlock
    notesBlock = makeEditor(parcel, 'NotesBlock',
                            viewAttribute=u'body',
                            presentationStyle={'lineStyleEnum': 'MultiLine'},
                            position=0.9).install(parcel)

    # Appears in block
    appearsInArea = \
        makeArea(parcel, 'AppearsInArea',
            viewAttribute=u'appearsIn',
            border=RectType(0,0,0,0),
            childrenBlocks=[
                # (the label is added as part of the string for now)
                #makeLabel(parcel, _(u'appears in'), borderTop=2),
                #makeSpacer(parcel, width=8),
                makeEditor(parcel, 'AppearsIn',
                           baseClass=AppearsInAEBlock,
                           viewAttribute=u'appearsIn',
                           border=RectType(0,2,2,2),
                           presentationStyle={'format': 'appearsIn'})],
            position=0.9999).install(parcel)    

    # A timer block we use for triggering "unread' -> 'read'
    unreadTimeout = BlockEvent.template('UnreadTimeout',
                                        dispatchEnum = 'SendToSender').install(parcel)
    unreadTimer = UnreadTimer.template("unreadTimerBlock",
                                       event=unreadTimeout,
                                       position=0.999).install(parcel)
    
    # Finally, the subtree. Note that the actual vertical ordering will be
    # determined by the 'position' attribute of each thing in the list.
    makeSubtree(parcel, osaf.pim.Note, [
        parcel['MarkupBar'],
        makeSpacer(parcel, height=6, position=0.01).install(parcel),
        bylineArea,
        errorArea,
        headlineArea, 
        makeSpacer(parcel, height=7, baseClass=ReminderSpacerBlock,
                   position=0.809999).install(parcel),
        reminderTypeArea,
        reminderRelativeArea,
        reminderAbsoluteArea,
        makeSpacer(parcel, height=7, position=0.8999).install(parcel),
        makeCalendarArea(parcel, oldVersion),
        makeMailArea(parcel, oldVersion),
        notesBlock,
        appearsInArea,
        unreadTimer,
    ])

def makeEmptySubtree(parcel, oldVersion):
  # An empty panel, used when there's no item selected in the detail view
  # (We use the Block kind as the key, though it's not a content kind)
  emptyPanel = EmptyPanelBlock.template('EmptyPanel').install(parcel)
  makeSubtree(parcel, Block.Block, [ emptyPanel ])
