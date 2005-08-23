from Detail import *
from osaf.framework.blocks import *
from osaf.pim.item_collections import ItemCollection
import osaf.pim
from i18n import OSAFMessageFactory as _

#
# A few public utilities: any detail view client can use these to help
# assure consistent alignment...
#
# More docs to come, but the key points:
# - Adding to the detail view means creating a DetailTrunkSubtree, which
#   maps a Kind to a list of rootBlocks that should appear if an item of
#   that Kind is displayed.
# - An item can inherit from multiple Kinds; each block in the 
#   DetailTrunkSubtree's rootBlocks list has a 'position' attribute that 
#   determines the ordering in the resulting detail view. 
# - The block hierarchies you create will likely look like:
#      (area)
#         (label)
#         (spacer)
#         (Attribute Editor)
#   I've created functions (makeArea, makeSpacer, makeEditor) to simplify
#   the process for the common case; there are lots of examples below in the
#   basic pim Kinds' subtrees.
#

_uniqueNameIndex = 0
def uniqueName(parcel, prefix=''):
    """ 
    Return an item name unique in this parcel. Used when we don't
    need to refer to an item by name. """
    while True:
        global _uniqueNameIndex
        _uniqueNameIndex += 1
        name = "%s%s" % (prefix, _uniqueNameIndex)
        if not parcel.hasChild(name):
            return name

def makeArea(parcel, name, stretchFactor=None, border=None, minimumSize=None, 
             baseClass=ContentItemDetail, **kwds):
    """
    Make one horizontal slice of the detail view
    """
    return baseClass.template(name,
                              stretchFactor=stretchFactor or 0.0,
                              minimumSize=minimumSize or SizeType(300, 24),
                              border=border or RectType(0, 0, 0, 6),
                              **kwds)

def makeLabel(parcel, label=u'', borderTop=5, border=None):
    """ Make a StaticText label template. """
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
               name=None, baseClass=StaticText, **kwds):
    """ 
    Make a spacer block template. Size can be specified as a SizeType, or as
    individual height or width. 
    """
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)
    size = size or SizeType(width, height)
    return baseClass.template(name or uniqueName(parcel, 'Spacer'),
                                title='',
                                characterStyle=blocks.LabelStyle,
                                stretchFactor=0.0,
                                minimumSize=size, **kwds)

def makeEditor(parcel, name, viewAttribute, border=None, 
               baseClass=DetailSynchronizedAttributeEditorBlock,
               characterStyle=None,
               presentationStyle=None, **kwds):
    """
    Make an Attribute Editor block template for the detail view.
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
                            presentationStyle=ps, border=border,
                            event=parcel['Resynchronize'], **kwds)
    return ae
          
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
    makeItemCollectionSubtree(parcel, oldVersion)
    makeEmptySubtree(parcel, oldVersion)
                      
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

    # Finally, (re-)do the bar itself.
    markupBar = MarkupBarBlock.template('MarkupBar',
                                        childrenBlocks=[mailMessageButton,
                                                        taskStamp,
                                                        calendarStamp,
                                                        separator,
                                                        privateSwitchButton],
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
    
    # Then, the Note AEBlock
    notesBlock = makeEditor(parcel, 'NotesBlock',
                            viewAttribute=u'bodyString',
                            presentationStyle={'lineStyleEnum': 'MultiLine'},
                            position=0.9).install(parcel)
    
    # Finally, the subtree
    notesSubtree = \
        DetailTrunkSubtree.update(parcel, 'NoteSubtree',
            key=osaf.pim.Note.getKind(),
            rootBlocks=[
                makeSpacer(parcel, height=6, position=0.01).install(parcel),
                parcel['MarkupBar'],
                headlineArea, 
                makeSpacer(parcel, height=7, position=0.8999).install(parcel),
                notesBlock])      

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
                    size=SizeType(75, -1))])

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
                                    _(u'Monthly'), _(u'Yearly'), 
                                    _(u'Custom...')]},
                    stretchFactor=0.0,
                    minimumSize=SizeType(100, -1))])

    recurrenceCustomArea = \
        makeArea(parcel, 'CalendarRecurrenceCustomArea',
            baseClass=CalendarRecurrenceCustomAreaBlock,
            childrenBlocks=[
                makeLabel(parcel, _(u''), borderTop=2), # leave label blank.
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
                    viewAttribute=u'reminderDelta',
                    presentationStyle={
                        'format': 'reminderPopup',
                        # @@@ XXX i18n: the code assumes that if the value
                        # starts with a digit, it's a number of minutes; if not,
                        # it's None.
                        'choices': [_(u'None'), _(u'1 minute'), _(u'5 minutes'), 
                                    _(u'10 minutes'), _(u'30 minutes'), 
                                    _(u'60 minutes'), _(u'90 minutes')]},
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
                           baseClass=CalendarConditionalLabelBlock),
                timeZoneArea,
                makeSpacer(parcel, height=7),
                transparencyArea,
                makeSpacer(parcel, height=7),
                recurrencePopupArea,
                makeSpacer(parcel, height=1),
                recurrenceCustomArea,
                recurrenceEndArea,
                makeSpacer(parcel, height=7),
                reminderArea]).install(parcel)

    calendarEventSubtree = \
        DetailTrunkSubtree.update(parcel, 'CalendarEventSubtree',
            key=osaf.pim.CalendarEventMixin.getKind(),
            rootBlocks=[calendarDetails])
 
def makeMailSubtree(parcel, oldVersion):
    blocks = schema.ns("osaf.framework.blocks", parcel.itsView)    
    fromArea = \
        makeArea(parcel, 'FromArea',
            childrenBlocks=[
                makeLabel(parcel, u'from'),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'FromEditField',
                    #presentationStyle={'format': 'outgoing'},
                    viewAttribute=u'fromAddress')],
            position=0.1).install(parcel)
    
    toMailArea = \
        makeArea(parcel, 'ToArea',
            childrenBlocks=[
                makeLabel(parcel, u'to'),
                makeSpacer(parcel, width=8),
                makeEditor(parcel, 'ToMailEditField',
                    viewAttribute=u'toAddress')],
            position=0.11,
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
                makeLabel(parcel, 'attachments'),
                makeSpacer(parcel, width=8),
                AttachmentTextFieldBlock.template('AttachmentTextField',
                    characterStyle=blocks.TextStyle,
                    lineStyleEnum='MultiLine',
                    readOnly=True,
                    textAlignmentEnum='Left',
                    minimumSize=SizeType(100, 48),
                    border=RectType(2, 2, 2, 2))],
            position=0.95).install(parcel)
    
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
