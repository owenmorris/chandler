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


from application import schema, styles
from osaf.framework.blocks import *
from osaf import pim
from osaf.framework import attributeEditors
from util.MultiStateButton import BitmapInfo, MultiStateBitmapCache
from application.dialogs import RecurrenceDialog
from chandlerdb.util.c import UUID
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

class TriageAttributeEditor(attributeEditors.BaseAttributeEditor):
    # Set this to '' to show/edit the "real" triageStatus everywhere.
    editingAttribute = 'unpurgedTriageStatus'

    def Draw (self, dc, rect, (item, attributeName), isInSelection=False):
        # Get the value we'll draw, and its label
        item = RecurrenceDialog.getProxy(u'ui', item, createNew=False)
        value = getattr(item, self.editingAttribute or attributeName, '')
        label = value and pim.getTriageStatusName(value) or u''

        # Paint our box in the right color
        backgroundColor = styles.cfg.get('summary', 'SectionSample_%s_%s'
                                         % (attributeName, value)) or '#000000'
        dc.SetPen(wx.WHITE_PEN)
        brush = wx.Brush(backgroundColor, wx.SOLID)
        dc.SetBrush(brush)
        dc.DrawRectangleRect(rect)

        # Draw the text
        dc.SetBackgroundMode (wx.TRANSPARENT)
        dc.SetTextForeground(wx.WHITE)
        (labelWidth, labelHeight, labelDescent, ignored) = dc.GetFullTextExtent(label)
        labelTop = rect.y + ((rect.height - labelHeight) / 2)
        labelLeft = rect.x + ((rect.width - labelWidth) / 2)
        dc.DrawText(label, labelLeft, labelTop)

    def OnMouseChange(self, event, cell, isIn, isDown, (item, attributeName)):
        """
        Handle live changes of mouse state related to our cell.
        """
        attributeName = self.editingAttribute or attributeName
        # Note down-ness changes; eat the event if the downness changed, and
        # trigger an advance if appropriate.
        if isDown != getattr(self, 'wasDown', False):
            if isIn and not isDown:
                oldValue = self.GetAttributeValue(item, attributeName)
                newValue = pim.getNextTriageStatus(oldValue)
                self.SetAttributeValue(item, attributeName, newValue)                
            if isDown:
                self.wasDown = True
            else:
                del self.wasDown
        else:
            event.Skip()

    def ReadOnly (self, (item, attribute)):
        # @@@ For now, treat recurring events as readOnly.
        return super(TriageAttributeEditor, self).ReadOnly((item, attribute)) \
               or (pim.has_stamp(item, pim.EventStamp) and \
                   pim.EventStamp(item).isRecurring())

class ReminderColumnAttributeEditor(attributeEditors.IconAttributeEditor):    
    def makeStates(self):
        states = [
            BitmapInfo(stateName="SumEvent.Unstamped",
                       normal=attributeEditors.IconAttributeEditor.noImage,
                       selected=attributeEditors.IconAttributeEditor.noImage,
                       rollover="EventTicklerRollover",
                       rolloverselected="EventTicklerRolloverSelected",
                       mousedown="EventTicklerMousedown",
                       mousedownselected="EventTicklerMousedownSelected"),
            BitmapInfo(stateName="SumEvent.Stamped",
                       normal="EventStamped",
                       selected="EventStampedSelected",
                       rollover="EventTicklerRollover",
                       rolloverselected="EventTicklerRolloverSelected",
                       mousedown="EventTicklerMousedown",
                       mousedownselected="EventTicklerMousedownSelected"),
            BitmapInfo(stateName="SumEvent.Tickled",
                       normal="EventTickled",
                       selected="EventTickledSelected",
                       rollover="EventTicklerRollover",
                       rolloverselected="EventTicklerRolloverSelected",
                       mousedown="EventTicklerMousedown",
                       mousedownselected="EventTicklerMousedownSelected"),
        ]
        return states
    
    def GetAttributeValue(self, item, attributeName):
        if pim.Remindable(item).getUserReminder(expiredToo=True):
            return "SumEvent.Tickled"
        return pim.has_stamp(item, pim.EventStamp) and \
               "SumEvent.Stamped" or "SumEvent.Unstamped"

    def SetAttributeValue(self, item, attributeName, value):
        # Don't bother implementing this - the only changes made in
        # this editor are done via advanceState
        pass
            
    def advanceState(self, item, attributeName):
        # If there is one, remove the existing reminder
        remindable = pim.Remindable(item)
        if remindable.getUserReminder(expiredToo=False) is not None:
            remindable.userReminderTime = None
            return

        # No existing one -- create one.
        # @@@ unless this is a recurring event, for now.
        if pim.has_stamp(item, pim.EventStamp) and pim.EventStamp(item).isRecurring():
            return # ignore the click.
        remindable.userReminderTime = pim.Reminder.defaultTime()
        
    def ReadOnly (self, (item, attribute)):
        """
        Until the Detail View supports read-only reminders, always allow
        reminders to be removed.
        
        """
        return False

# These flag bits govern the sort position of each communications state:
# Update     =         1
# In         =        1
# Out        =       1
# Draft      =      1
# Queued     =     1
# Sent       =    1
# NeedsReply =   1
# Read       =  1
# Error      = 1
updateBit = 1
inBit = updateBit * 2
outBit = inBit * 2
draftBit = outBit * 2
queuedBit = draftBit * 2
sentBit = queuedBit * 2
needsReplyBit = sentBit * 2
readBit = needsReplyBit * 2
errorBit = readBit * 2

# For each bit, the attribute that contributes to it
# @@@ The ones given as strings are just placeholders.
bitSources = (
    (updateBit, 'isUpdate'),
    (inBit, 'toMe'),
    (outBit, 'fromMe'),
    (draftBit, 'isDraft'),
    (queuedBit, 'isQueued'),
    (sentBit, 'isSent'),
    (needsReplyBit, pim.ContentItem.needsReply.name),
    (readBit, pim.ContentItem.read.name),
    (errorBit, 'error'),
)

# All the attribute names from the above, to use for 
# monitoring on the index we build
bitSourceAttributes = map(lambda x: x[1], bitSources)

# Each entry in this list corresponds to a row in the icon grid in 
# the spec. Each will have "Read", "Unread", and "NeedsReply" tacked on
# when we ask the domain model.       
statePairNames = (
    # Base name, True if it shows an icon when 'read'
    ("Plain", False),
    ("InDraft", True),
    ("In", False),
    ("OutDraft", True),
    ("Out", False),
    ("OutdateDraft", True),
    ("Outdate", False),
    ("IndateDraft", True),
    ("Indate", False),
    ("Queued", True),
    ("Error", True),
)

def getItemCommState(itemOrUUID):
    """ Given an item or a UUID, determine its communications state """
    result = 0
    if isinstance(itemOrUUID, UUID):
        values = view.findValues(itemOrUUID, bitSourceAttributes)
        for (bit, ignored), v in izip(bitSources, values):
            if v:
                result |= bit
    else:        
        for (bit, attributeName) in bitSources:
            if getattr(itemOrUUID, attributeName, False):
                result |= bit
    return result

def getCommStateName(commState):
    """ Return the actual name for this state """
    
    read = (commState & readBit) and "Read" or "Unread"
    needsReply = (commState & needsReplyBit) and "NeedsReply" or ""

    # These don't depend on in vs out, so check them first.
    if commState & errorBit:
        return "Error%s%s" % (read, needsReply)
    if commState & queuedBit:
        return "Queued%s%s" % (read, needsReply)
    
    # Note In vs Out (Out wins if both) vs Plain (if neither, we're done).
    if commState & outBit:
        inOut = "Out"
        #  # and keep going...
    elif commState & inBit:
        inOut = "In"
        # and keep going...
    else:
        return "Plain%s%s" % (read, needsReply)
    
    # We're Out or In -- do Updating and Draft.
    updating = (commState & updateBit) and "date" or ""
    draft = (commState & draftBit) and "Draft" or ""    
    return "%s%s%s%s" % (inOut, updating, draft, needsReply)
    
class CommunicationsColumnAttributeEditor(attributeEditors.IconAttributeEditor):
    def makeStates(self):
        states = []
        def addState(name, **kwds):
            args = {}
            for state in ("Normal", "Selected", "Rollover", "RolloverSelected", 
                         "Mousedown", "MousedownSelected"):
                lcState = state.lower()
                if not kwds.has_key(lcState):
                    # If a given state isn't specified, build the name automatically
                    args[lcState] = "Mail%s%s" % (name, 
                                                  state != "Normal" and state or '')
                elif kwds[lcState] is None:
                    # If a given state is specified as None, use a blank image.
                    args[lcState] = attributeEditors.IconAttributeEditor.noImage
                else:
                    # Use the given name, but prepend "Mail" to it because that's
                    # how the files are named.
                    args[lcState] = "Mail%s" % kwds[lcState]
            states.append(BitmapInfo(stateName=name, **args))

        # Build pairs of states (Read and Unread)
        for name, hasRead in statePairNames:
            namePrefix = (name != "Plain") and name or ''
            # Each pair has these variations in common
            args = { 
                'rollover': '%sRollover' % namePrefix,
                'rolloverselected': '%sRolloverSelected' % namePrefix,
                'mousedown': '%sMousedown' % namePrefix,
                'mousedownselected': '%sMousedownSelected' % namePrefix
            }
            
            # Do Unread
            addState("%sUnread" % name, selected='%sUnreadSelected' % namePrefix, 
                     **args)

            # Do Read, whether it has 'read' icon or not.
            if hasRead:
                addState("%sRead" % name, selected='%sReadSelected' % namePrefix, 
                         **args)
            else:
                addState("%sRead" % name, normal=None, selected=None, **args)
            
        # Do NeedsReply by itself
        addState("NeedsReply")

        return states

    def mapValueToIconState(self, state):
        # We use one set of icons for all the NeedsReply states.
        if state.find("NeedsReply") != -1:
            return "NeedsReply"
        return state
        
    def GetAttributeValue(self, item, attributeName):
        # Determine what state this item is in. 
        return getCommStateName(getItemCommState(item))        

    def SetAttributeValue(self, item, attributeName, value):
        # Don't bother implementing this - the only changes made in
        # this editor are done via advanceState
        pass

    def getNextValue(self, item, attributeName, currentValue):
        wasUnread = currentValue.find("Unread") != -1
        if currentValue.find("NeedsReply") != -1:
            if wasUnread:
                return currentValue.replace("UnreadNeedsReply", "Read")
            return currentValue.replace("NeedsReply", "")
        # It wasn't needsReply. If it was "Unread", mark it "read"
        if wasUnread: # yes, "NeedsReply" is next, and mark it read, too.
            return currentValue.replace("Unread", "Read")
        
        # Otherwise, it's Read -> ReadNeedsReply.
        return currentValue.replace("Read", "ReadNeedsReply")
    
    def advanceState(self, item, attributeName):
        oldState = self.GetAttributeValue(item, attributeName)
        if oldState.find("NeedsReply") != -1:
            item.read = False
            item.needsReply = False
        elif oldState.find("Unread") != -1:
            item.read = True
            item.needsReply = False
        else: # make it needs-reply (and make sure it's read).
            item.read = True
            item.needsReply = True
        
class TaskColumnAttributeEditor(attributeEditors.IconAttributeEditor):
    def _getStateName(self, isStamped):
        return isStamped and "SumTask.Stamped" or "SumTask.Unstamped"
        
    def makeStates(self):
        states = []
        for (state, normal, selected) in ((False, attributeEditors.IconAttributeEditor.noImage,
                                                  attributeEditors.IconAttributeEditor.noImage),
                                          (True, "TaskStamped",
                                                 "TaskStampedSelected")):
            bmInfo = BitmapInfo()
            bmInfo.stateName = self._getStateName(state)
            bmInfo.normal = normal
            bmInfo.selected = selected
            bmInfo.rollover = "TaskRollover"
            bmInfo.rolloverselected = "TaskRolloverSelected"
            bmInfo.mousedown = "TaskMousedown"
            bmInfo.mousedownselected = "TaskMousedownSelected"
            states.append(bmInfo)

        return states

    def ReadOnly(self, (item, attributeName)):
        # Our "attributeName" is a Stamp; substitute a real attribute.
        readOnly = super(TaskColumnAttributeEditor, self).ReadOnly((item, 'body'))

        return readOnly
    
    def GetAttributeValue(self, item, attributeName):
        isStamped = pim.has_stamp(item, pim.TaskStamp)
        return self._getStateName(isStamped)
    
    def SetAttributeValue(self, item, attributeName, value):
        isStamped = pim.has_stamp(item, pim.TaskStamp)
        if isStamped != (value == self._getStateName(True)):
            # Stamp or unstamp the item
            if isinstance(item, pim.TaskStamp.targetType()):
                stampedObject = pim.TaskStamp(item)
                if isStamped:
                    stampedObject.remove()
                else:
                    stampedObject.add()

    def advanceState(self, item, attributeName):
        if not self.ReadOnly((item, attributeName)):
            isStamped = pim.has_stamp(item, pim.TaskStamp)
            newValue = self._getStateName(not isStamped)
            self.SetAttributeValue(item, attributeName, newValue)


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
    
    # Register our attribute editors.
    # If you edit this dictionary, please keep it in alphabetical order by key.
    aeDict = {
        'EventStamp': 'ReminderColumnAttributeEditor',
        'MailStamp': 'CommunicationsColumnAttributeEditor',
        'TaskStamp': 'TaskColumnAttributeEditor',
        'TriageEnum': 'TriageAttributeEditor',
    }
    attributeEditors.AttributeEditorMapping.register(parcel, aeDict, __name__)
    
    
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
    
