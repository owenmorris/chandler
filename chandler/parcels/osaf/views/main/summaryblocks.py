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
from i18n import ChandlerMessageFactory as _
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

class WhoAttributeEditor(attributeEditors.StringAttributeEditor):
    def GetTextToDraw(self, item, attributeName):
        prefix, theText, isSample = \
            super(WhoAttributeEditor, self).GetTextToDraw(item, attributeName)
        
        if not isSample:
            # OVerride the prefix if we have one we recognize
            # (these are in order of how frequently I think they'll occur)
            # Note that there's a space at the end of each one, which separates
            # the prefix from the value.
            whoSource = getattr(item, 'displayWhoSource', '')
            if len(whoSource) > 0:
                if whoSource == 'creator': # ContentItem
                    prefix = _(u'cr ')
                #elif whoSource == '?': # @@@ not sure where 'edited by' will come from
                    #prefix = _(u'ed')
                #elif whoSource == '?': # @@@ not sure where 'updated by' will come from
                    #prefix = _(u'up')
                elif whoSource == 'to': # Mail
                    prefix = _(u'to ')
                elif whoSource == 'from': # Mail
                    prefix = _(u'fr ')
                elif whoSource == 'owner': # Flickr
                    prefix = _(u'ow ')
                elif whoSource == 'author': # Feeds
                    prefix = _(u'au ')
            
        return (prefix, theText, isSample)

class TriageAttributeEditor(attributeEditors.BaseAttributeEditor):
    # Set this to '' to show/edit the "real" triageStatus everywhere.
    editingAttribute = 'unpurgedTriageStatus'

    def Draw (self, grid, dc, rect, (item, attributeName), isInSelection=False):
        # Get the value we'll draw, and its label
        item = RecurrenceDialog.getProxy(u'ui', item, createNew=False)
        value = getattr(item, self.editingAttribute or attributeName, '')
        label = (pim.getTriageStatusName(value).upper() if value else u'')

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
        dc.SetFont(Styles.getFont(grid.blockItem.triageStatusCharacterStyle))
        (labelWidth, labelHeight, labelDescent, ignored) = dc.GetFullTextExtent(label)
        labelTop = rect.y + ((rect.height - labelHeight) / 2)
        labelLeft = rect.x + ((rect.width - labelWidth) / 2)
        dc.DrawText(label, labelLeft, labelTop)

    def OnMouseChange(self, event):
        """
        Handle live changes of mouse state related to our cell; return True
        if we want the mouse captured for future updates.
        """
        # Note down-ness changes; eat the event if the downness changed, and
        # trigger an advance if appropriate.
        isDown = event.LeftDown()
        if isDown != getattr(self, 'wasDown', False):
            if not isDown and event.isInCell:
                item, attributeName = event.getCellValue()
                attributeName = self.editingAttribute or attributeName
                oldValue = self.GetAttributeValue(item, attributeName)
                newValue = pim.getNextTriageStatus(oldValue)
                self.SetAttributeValue(item, attributeName, newValue)
                event.Skip(False) # Eat the event
            if isDown:
                self.wasDown = True
            else:
                del self.wasDown
        return False # we don't want capture

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
    ("PlainDraft", True),
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
            # Each pair has these variations in common
            args = { 
                'rollover': '%sRollover' % name,
                'rolloverselected': '%sRolloverSelected' % name,
                'mousedown': '%sMousedown' % name,
                'mousedownselected': '%sMousedownSelected' % name
            }
            
            # Do Unread
            addState("%sUnread" % name, selected='%sUnreadSelected' % name, 
                     **args)

            # Do Read, whether it has 'read' icon or not.
            if hasRead:
                addState("%sRead" % name, selected='%sReadSelected' % name, 
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
        # Cycle through: Unread, Read, NeedsReply
        wasUnread = currentValue.find("Unread") != -1
        if currentValue.find("NeedsReply") != -1:
            if wasUnread:
                # Shouldn't happen (if it's needsReply, it oughta be read),
                # but map it to Unread anyway.
                return currentValue.replace("NeedsReply", "")
            return currentValue.replace("ReadNeedsReply", "Unread")
        # It wasn't needsReply. If it was "Unread", mark it "read"
        if wasUnread:
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
        'Text+who': 'WhoAttributeEditor',
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
        format='who',
        attributes=[
            pim.ContentItem.displayWho.name,
            pim.ContentItem.triageStatus.name, 
            pim.ContentItem.triageStatusChanged.name,
        ])
    
    titleColumn = makeColumnAndIndexes('SumColAbout',
        heading=_(u'Title'),
        width=120,
        scaleColumn = wx.grid.Grid.GRID_COLUMN_SCALABLE,
        indexName='%s.displayName' % __name__,
        attributeName='displayName',
        attributes=[
            pim.ContentItem.displayName.name, 
            pim.ContentItem.triageStatus.name, 
            pim.ContentItem.triageStatusChanged.name,
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
        collapsedSections=set([str(pim.TriageEnum.later), str(pim.TriageEnum.done)]), 
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
                prefixCharacterStyle = blocks.SummaryPrefixStyle,
                triageStatusCharacterStyle = blocks.SummaryTriageStatusStyle,
                sectionLabelCharacterStyle = blocks.SummarySectionLabelStyle,
                sectionCountCharacterStyle = blocks.SummarySectionCountStyle,
                rowHeight = 19,
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
    

if __name__ == "__main__":
    # Code to generate a web page for checking the communications column's
    # icon mappings. To generate "icontest.html" in your $CHANDLERHOME, do:
    #   cd $CHANDLERHOME; UNIT_TESTING=True $CHANDLERBIN/release/RunPython.bat parcels/osaf/views/main/summaryblocks.py
    # (leave off the .bat if you're not on windows)
    # Then, view file:///path/to/your/CHANDLERHOME/icontest.html
    # in your browser.
    import os, itertools
    from util.MultiStateButton import allVariations

    # URL to ChandlerHome in ViewCVS
    viewCVS = "http://viewcvs.osafoundation.org/chandler/trunk/chandler"
    
    # Relative path to the images we'll use
    imageDir = "Chandler.egg-info/resources/images"
    if True:
        # Refer to the images in ViewCVS (so I can paste the resulting HTML
        # into a wiki page, for instance)
        imagePrefix = "%s/Chandler.egg-info/resources/images" % viewCVS
    else:
        # Just reference the images relatively.
        imagePrefix = imageDir
        
    # First, we add a "dump" method to BitMapInfo
    def BitmapInfoDump(self, variation):
        v = getattr(self, variation, None)
        if v is None:
            return "(None)"
        else:
            if v == "pixel":
                v = "pixel.gif"
            else:
                v += ".png"
            return '<img height=32 width=42 src="%s/%s"><br/><font size=-1>%s</font>' % (imagePrefix, v, v)
    BitmapInfo.dump = BitmapInfoDump

    # A utility routine to columnize a list:
    # list(columnnize(list("abcdefghi"), 3)) returns
    # [('a', 'd', 'g'),
    #  ('b', 'e', 'h'),
    #  ('c', 'f', None)]
    # which we need for the icon table HTML.
    def columnize(seq, colCount, default=None):
        cols = []
        overFlow = len(seq) % colCount 
        if overFlow:
            seq.extend([default] * (colCount - overFlow))
            
        colLength = len(seq) / colCount
        cols = [ seq[(c * colLength):((c+1) * colLength)]
                 for c in xrange(colCount) ]        
        return itertools.izip(*cols)
        
    f = open("icontest.html", 'w')
    f.write("""<p>
This is a dump of the icon states in the dashboard task, communications, and 
event columns. See the notes at the bottom of <a href="%s/parcels/osaf/views/main/summaryblocks.py?view=markup">
parcels/osaf/views/main/summaryblocks.py</a> to see how it was created.
</p>""" % viewCVS)
    
    # The variations we'll do are all except these two
    variationList = list(allVariations)
    variationList.remove("disabled")
    variationList.remove("focus")
    
    for cls, iconPrefix in ((TaskColumnAttributeEditor, "Task"),
                            (CommunicationsColumnAttributeEditor, "Mail"),
                            (ReminderColumnAttributeEditor, "Event")):
        f.write("\n<h3>%s</h3>\n" % iconPrefix)
        f.write('<table width="100%" bgcolor="#339933">\n  <tr>\n    <td>&nbsp;</td>\n')
        for v in variationList:
            f.write("    <td align=middle><i>%s</i></td>\n" % v)
        f.write('  </tr>\n')
        setattr(cls, '__init__', lambda *args, **kwds: None)
        states = cls().makeStates()
        for s in states:
            f.write("  <tr>\n")
            f.write("    <td>%s</td>\n" % s.stateName)
            for v in variationList:
                f.write("    <td align=middle>%s</td>\n" % s.dump(v))
            f.write("  </tr>\n")
        f.write("</table>\n")
    
        f.write('&nbsp;<br>&nbsp;<br><table width="100%" bgcolor="#339933">\n')
        images = [ im for im in os.listdir(imageDir) if im.startswith(iconPrefix)]
        images.sort()    
        for rowImages in columnize(images, 4):
            f.write('  <tr>\n')
            for img in rowImages:
                if img is not None:
                    f.write('    <td valign="middle"><img height=32 width=42 src="%s/%s"><font size=-1>%s</font></td>\n' % (imagePrefix, img, img))
                else:
                    f.write('    <td>&nbsp;</td>\n')
            f.write('  </tr>\n')
        f.write("</table>\n")
    #f.write("</body>\n")
    f.close()
