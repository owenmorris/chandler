#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

from application import schema
from osaf.framework.blocks import *
from osaf import pim
from osaf.framework import attributeEditors
from util.MultiStateButton import BitmapInfo
from util.triagebuttonimageprovider import TriageButtonImageProvider
from i18n import ChandlerMessageFactory as _
from wx import grid as wxGrid
from chandlerdb.util.c import Nil
from osaf.communicationstatus import CommunicationStatus

# IndexDefinition subclasses for the dashboard indexes
#
# Most fall back on the triage ordering if their primary terms are equal;
# they inherit from this:
class TriageColumnIndexDefinition(pim.MethodIndexDefinition):
    findParams = (
        # We'll return one pair of these or the other, depending on whether
        # sectionTriageStatus exists on the item.
        ('_triageStatus', pim.TriageEnum.now),
        ('_triageStatusChanged', 0),
        ('_sectionTriageStatus', None),
        ('_sectionTriageStatusChanged', 0),
    )

    def getCompareTuple(self, uuid):
        """
        Load all four triage values, but return only the pair 
        we're supposed to use.
        """
        values = self.itsView.findInheritedValues(uuid, *self.findParams)
        # We'll use sectionTriageStatus if it's there, else triageStatus
        return values[0:2] if values[2] is None else values[2:4]

    def compare(self, index, u1, u2, vals):
        if u1 in vals:
            v1 = vals[u1]
        else:
            v1 = self.getCompareTuple(u1)
        if u2 in vals:
            v2 = vals[u2]
        else:
            v2 = self.getCompareTuple(u2)
        return cmp(v1, v2)

    def compare_init(self, index, u, vals):
        return self.getCompareTuple(u)

class DelegatingIndexDefinition(pim.MethodIndexDefinition):
    """
    Base class for indexes that fall back on the triagestatus index
    if their own comparison comes up equal
    """
    def getCompareTuple(self, uuid):
        return self.itsView.findInheritedValues(uuid, *self.findParams)

    def compare(self, index, u1, u2, vals):
        if u1 in vals:
            v1 = vals[u1]
        else:
            v1 = self.getCompareTuple(u1)
        if u2 in vals:
            v2 = vals[u2]
        else:
            v2 = self.getCompareTuple(u2)
        result = cmp(v1, v2)
        
        if not result:
            # compare subindex position instead; we cache it under a stringized
            # version of the UUID
            u1p = str(u1)
            if u1p in vals:
                v1 = vals[u1p]
            else:
                v1 = vals['position'](u1)
            u2p = str(u2)
            if u2p in vals:
                v2 = vals[u2p]
            else:
                v2 = vals['position'](u2)
            result = v1 - v2
        return result

    def compare_init(self, index, u, vals):
        positionMethod = index.getSuperIndex().skipList.position
        vals['position'] = positionMethod
        vals[str(u)] = positionMethod(u)
        return self.getCompareTuple(u)

    def makeIndexOn(self, collection, kind=None):
        """ Create the index we describe on this collection """
        
        monitoredAttributes = (self.attributes or [])
        
        # We need to include inheritFrom in the attributes we monitor,
        # else (especially at Occurrence creation time) items don't get
        # re-indexed properly when they inherit attribute values from
        # their "rich relatives" (ovaltofu's term).
        if not 'inheritFrom' in monitoredAttributes:
            monitoredAttributes = ('inheritFrom',) + tuple(monitoredAttributes)
        
        # @@@ This could be generalized to delegate to indexes other than
        # our own triagestatus index, but since this is all we need for now,
        # put off building the extra infrastructure.
        collection.addIndex(self.itsName, 'method',
                            method=(self, 'compare'),
                            superindex=(collection,
                                        collection.__collection__,
                                        "%s.triage" % __name__),
                            monitor=monitoredAttributes,
                            kind=kind)
    
class TaskColumnIndexDefinition(DelegatingIndexDefinition):
    findParams = [
        (pim.Stamp.stamp_types.name, Nil),
        ('displayName', u''),
    ]
    def getCompareTuple(self, uuid):
        stamp_types, displayName = \
            self.itsView.findInheritedValues(uuid, *self.findParams)
        return (pim.TaskStamp in stamp_types, displayName)


class CommunicationColumnIndexDefinition(DelegatingIndexDefinition):
    def getCompareTuple(self, uuid):
        commState = CommunicationStatus.getItemCommState(uuid, self.itsView)
        return (commState,)
    
class CalendarColumnIndexDefinition(DelegatingIndexDefinition):
    findParams = (
        (pim.Stamp.stamp_types.name, Nil),
        (pim.Remindable.reminders.name, None),
        ('displayDate', pim.Reminder.farFuture),
    )

    def getCompareTuple(self, uuid):
        stamp_types, reminders, displayDate = \
            self.itsView.findInheritedValues(uuid, *self.findParams)
            
        # We need to do this:
        #   hasUserReminder = item.getUserReminder(expiredToo=True) is not None
        # while avoiding loading the items. @@@ Note: This code matches the 
        # implementation of Remindable.getUserReminder - be sure to change 
        # that if you change this!
            
        def hasAUserReminder(remList):
            if remList is not None:
                for reminderUUID in remList.iterkeys():
                    userCreated = self.itsView.findValue(reminderUUID, 'userCreated', False)
                    if userCreated:
                        return True
            return False
        hasUserReminder = hasAUserReminder(reminders)

        if hasUserReminder:
            reminderState = 0
        elif pim.EventStamp in stamp_types:
            reminderState = 1
        else:
            reminderState = 2
                
        return (reminderState, displayDate)


class WhoColumnIndexDefinition(DelegatingIndexDefinition):
    findParams = (
        ('displayWho', u''),
    )

    def getCompareTuple(self, uuid):
        displayWho, = self.itsView.findInheritedValues(uuid, *self.findParams)
        return (displayWho.lower(),)


class TitleColumnIndexDefinition(DelegatingIndexDefinition):
    findParams = (
        ('displayName', u''),
    )

    def getCompareTuple(self, uuid):
        displayName, = self.itsView.findInheritedValues(uuid, *self.findParams)
        return (displayName.lower(),)


class DateColumnIndexDefinition(DelegatingIndexDefinition):
    findParams = (
        ('displayDate', pim.Reminder.farFuture),
    )

class WhoAttributeEditor(attributeEditors.StringAttributeEditor):
    def GetTextToDraw(self, item, attributeName):
        prefix, theText, isSample = \
            super(WhoAttributeEditor, self).GetTextToDraw(item, attributeName)
        
        if not isSample:
            # Override the prefix if we have one we recognize
            # (these are in order of how frequently I think they'll occur)
            # Note that there's a space at the end of each one, which separates
            # the prefix from the value.
            whoSource = getattr(item, 'displayWhoSource', '')
            if len(whoSource) > 0:
                if whoSource == 'creator': # ContentItem
                    # L10N: short for "creator".
                    #       displayed in the summary table
                    #       view next to the who column.
                    prefix = _(u'cr ')
                    # L10N: short for "editor".
                    #       displayed in the summary table
                    #       view next to the who column.
                elif whoSource == 'editor': # CommunicationStatus
                    prefix = _(u'ed ')
                    # L10N: short for "updater".
                    #       displayed in the summary table
                    #       view next to the who column.
                elif whoSource == 'updater': # CommunicationStatus
                    prefix = _(u'up ')
                    # L10N  displayed in the summary table
                    #       view next to the who column.
                elif whoSource == 'to': # CommunicationStatus
                    prefix = _(u'to ')
                elif whoSource == 'from': # CommunicationStatus
                    # L10N: short for "from".
                    #       displayed in the summary table
                    #       view next to the who column.
                    prefix = _(u'fr ')
                elif whoSource == 'owner': # Flickr
                    # L10N: short for "owner".
                    #       displayed in the summary table
                    #       view next to the who column.
                    prefix = _(u'ow ')
                elif whoSource == 'author': # Feeds
                    # L10N: short for "author".
                    #       displayed in the summary table
                    #       view next to the who column.
                    prefix = _(u'au ')
            
        return (prefix, theText, isSample)

dashboardTriageButtonBitmapProvider = TriageButtonImageProvider("Triage.Now.png")

class TriageColumn(Column):
    def getWidth(self):
        return dashboardTriageButtonBitmapProvider.getImageSize()[0]

class TriageAttributeEditor(attributeEditors.IconAttributeEditor):
    def __init__(self, *args, **kwds):
        kwds['bitmapProvider'] = dashboardTriageButtonBitmapProvider
        super(TriageAttributeEditor, self).__init__(*args, **kwds)

    def makeStates(self):
        # The state name has the state in lowercase, which matches the "name"
        # attribute of the various TriageEnums. The state values are mixed-case,
        # which matches the actual icon filenames.
        states = [ BitmapInfo(stateName="Triage.%s" % s.lower(),
                       normal="Triage.%s" % s,
                       selected="Triage.%s" % s,
                       rollover="Triage.%s.Rollover" % s,
                       rolloverselected="Triage.%s.Rollover" % s,
                       mousedown="Triage.%s.Mousedown" % s,
                       mousedownselected="Triage.%s.Mousedown" % s)
                   for s in "Now", "Later", "Done" ]
        return states
        
    def GetAttributeValue(self, item, attributeName):
        # Determine what state this item is in. 
        value = item.triageStatus
        return value
        
    def mapValueToIconState(self, value):
        return "Triage.%s" % value.name
    
    def advanceState(self, item, attributeName):
        oldValue = item.triageStatus
        newValue = pim.getNextTriageStatus(oldValue)
        item = pim.proxy.CHANGE_THIS(item)
        
        item.setTriageStatus(newValue, pin=True)
        item.resetAutoTriageOnDateChange()

    def OnMouseChange(self, event):
        # Override double-click behaviour a la Bug 11911
        if event.LeftDClick():
            item, attributeName = event.getCellValue()
            # We only advance once, because the single-click will have
            # taken care of one advance.
            self.advanceState(item, attributeName)
            event.Skip(False)
        else:
            return super(TriageAttributeEditor, self).OnMouseChange(event)

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
        # We want the icon shown to match the date displayed in the date column,
        # so just pick a value based on the date we're displaying.
        displayDateSource = getattr(item, 'displayDateSource', None)
        if displayDateSource == 'reminder':
            return "SumEvent.Tickled"
        return displayDateSource == 'startTime' and \
               "SumEvent.Stamped" or "SumEvent.Unstamped"

    def SetAttributeValue(self, item, attributeName, value):
        # Don't bother implementing this - the only changes made in
        # this editor are done via advanceState
        pass
            
    def getToolTip(self, item, attributeName):
        state = self.GetAttributeValue(item, attributeName)
        if state == "SumEvent.Tickled":
            return _(u"Remove custom alarm")
        else:
            return _(u"Add custom alarm")
        return None

    def advanceState(self, item, attributeName):
        item = pim.CHANGE_THIS(item)
        # If there is one, remove the existing reminder
        if item.getUserReminder(expiredToo=False) is not None:
            item.userReminderTime = None
            return

        # No existing one -- create one.
        item.userReminderTime = pim.Reminder.defaultTime(item.itsView)
        
    def ReadOnly (self, (item, attribute)):
        """
        Until the Detail View supports read-only reminders, always allow
        reminders to be removed.
        
        """
        return False

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

def getCommStateName(commState):
    """ Return the actual name for this state """
    
    read = (commState & CommunicationStatus.READ) and "Read" or "Unread"
    needsReply = (commState & CommunicationStatus.NEEDS_REPLY) and "NeedsReply" or ""

    # These don't depend on in vs out, so check them first.
    if commState & CommunicationStatus.ERROR:
        return "Error%s%s" % (read, needsReply)
    if commState & CommunicationStatus.QUEUED:
        return "Queued%s%s" % (read, needsReply)
    
    # Note In vs Out (Out wins if both) vs Plain (if neither, we're done).
    draft = (commState & CommunicationStatus.DRAFT) and "Draft" or ""    
    if commState & CommunicationStatus.OUT:
        inOut = "Out"
        #  # and keep going...
    elif commState & CommunicationStatus.IN:
        inOut = "In"
        # and keep going...
    else:
        return "Plain%s%s%s" % (draft, read, needsReply)
    
    # We're Out or In -- do Updating and Draft.
    updating = (commState & CommunicationStatus.UPDATE) and "date" or ""
    return "%s%s%s%s%s" % (inOut, updating, draft, read, needsReply)

        
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
        return getCommStateName(CommunicationStatus(item).status)

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
    
    def getToolTip(self, item, attributeName):
        nextState = self.getNextValue(item, attributeName,
                                      self.GetAttributeValue(item, attributeName))
        if nextState.find("NeedsReply") != -1:
            return _(u"Mark as Needs reply")
        elif nextState.find("Unread") != -1:
            return _(u"Mark as Unread")
        return _(u"Mark as Read")

    def advanceState(self, item, attributeName):
        # changes to read/unread/needs reply should apply to all occurrences
        item = getattr(item, 'proxiedItem', item)
        item = pim.EventStamp(item).getMaster().itsItem
        
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

    def getToolTip(self, item, attributeName):
        state = self.GetAttributeValue(item, attributeName)
        if state == "SumTask.Stamped":
            return _(u"Remove star")
        else:
            return _(u"Add star")
        return None

    def advanceState(self, item, attributeName):
        if not self.ReadOnly((item, attributeName)):
            isStamped = pim.has_stamp(item, pim.TaskStamp)
            newValue = self._getStateName(not isStamped)
            self.SetAttributeValue(item, attributeName, newValue)


def makeSummaryBlocks(parcel):
    from osaf.framework.blocks.calendar import (
        CalendarContainer, CalendarControl, MultiWeekControl,
        CanvasSplitterWindow, AllDayEventsCanvas, TimedEventsCanvas,
        MultiWeekContainer
        )

    from Dashboard import DashboardBlock
    
    view = parcel.itsView
    detailblocks = schema.ns('osaf.views.detail', view)
    pim_ns = schema.ns('osaf.pim', view)
    blocks = schema.ns('osaf.framework.blocks', view)
    main = schema.ns("osaf.views.main", view)
    repositoryView = parcel.itsView
    
    # Register our attribute editors.
    # If you edit this dictionary, please keep it in alphabetical order by key.
    aeDict = {
        'EventStamp': 'ReminderColumnAttributeEditor',
        'MailStamp': 'CommunicationsColumnAttributeEditor',
        'TaskStamp': 'TaskColumnAttributeEditor',
        'Text+who': 'WhoAttributeEditor',
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
        baseClass = kwargs.pop('baseClass', pim.AttributeIndexDefinition)
        columnClass = kwargs.pop('columnClass', Column)
        indexDefinition = baseClass.update(parcel, 
                                           indexName,
                                           useMaster=useMaster,
                                           attributes=attributes)

        # If we want master indexes precreated, here's where
        # to do it.
        if useMaster: indexDefinition.makeMasterIndex()
            
        # Create the column
        return columnClass.update(parcel, colName, **kwargs)

    # We have to build the triage column first, because the other columns 
    # delegate to its index
    triageColumn = makeColumnAndIndexes('SumColTriage',
        icon = 'ColHTriageStatus',
        useSortArrows = False,
        defaultSort = True,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_FIXED_SIZE,
        columnClass = TriageColumn,
        attributeName = 'sectionTriageStatus',
        indexName = '%s.triage' % __name__,
        baseClass=TriageColumnIndexDefinition,
        attributes=list(dict(TriageColumnIndexDefinition.findParams)))
        
    taskColumn = makeColumnAndIndexes('SumColTask',
        icon='ColHTask',
        valueType = 'stamp',
        stamp=pim.TaskStamp,
        width=iconColumnWidth,
        useSortArrows=False,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly=True,
        indexName='%s.taskStatus' % __name__,
        baseClass=TaskColumnIndexDefinition,
        attributes=list(dict(TaskColumnIndexDefinition.findParams)),)

    commColumn = makeColumnAndIndexes('SumColMail',
        icon='ColHMail',
        valueType='stamp',
        stamp=pim.mail.MailStamp,
        width=iconColumnWidth,
        useSortArrows=False,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly=True,
        indexName=CommunicationStatus.status.name,
        attributeName=CommunicationStatus.status.name,
        baseClass=CommunicationColumnIndexDefinition,
        attributes=list(dict(CommunicationStatus.attributeValues)),)

    whoColumn = makeColumnAndIndexes('SumColWho',
        heading=_(u'Who'),
        width=85,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_SCALABLE,
        readOnly=True,
        indexName='%s.displayWho' % __name__,
        attributeName='displayWho',
        attributeSourceName = 'displayWhoSource',
        format='who',
        baseClass=WhoColumnIndexDefinition,
        attributes=list(dict(WhoColumnIndexDefinition.findParams)),)
    
    titleColumn = makeColumnAndIndexes('SumColAbout',
        heading=_(u'Title'),
        width=120,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_SCALABLE,
        indexName='%s.displayName' % __name__,
        attributeName='displayName',
        baseClass=TitleColumnIndexDefinition,
        attributes=list(dict(TitleColumnIndexDefinition.findParams)),)

    reminderColumn = makeColumnAndIndexes('SumColCalendarEvent',
        icon = 'ColHEvent',
        valueType = 'stamp',
        stamp = pim.EventStamp,
        useSortArrows = False,
        width = iconColumnWidth,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly = True,
        indexName = '%s.calendarStatus' % __name__,
        baseClass=CalendarColumnIndexDefinition,
        attributes=list(dict(CalendarColumnIndexDefinition.findParams)) + \
                   ['displayDateSource'])

    dateColumn = makeColumnAndIndexes('SumColDate',
        heading = _(u'Date'),
        width = 115,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_SCALABLE,
        readOnly = True,
        attributeName = 'displayDate',
        attributeSourceName = 'displayDateSource',
        indexName = '%s.displayDate' % __name__,
        baseClass=DateColumnIndexDefinition,
        attributes=list(dict(DateColumnIndexDefinition.findParams)) + \
                   ['displayDateSource'])

    rankColumn = makeColumnAndIndexes('SumColRank',
        heading = _(u'Rank'),
        valueType = 'None',
        defaultSort = True,
        useSortArrows = False,
        useMaster = False,
        width = 46,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_SCALABLE,
        readOnly = True,
        indexName ='%s.rank' % __name__,
        format='rank',
        baseClass = pim.NumericIndexDefinition,
        attributes = [])

    # Our detail views share the same delegate instance and contents collection
    detailBranchPointDelegate = detailblocks.DetailBranchPointDelegate.update(
        parcel, 'DetailBranchPointDelegateInstance',
        branchStub = detailblocks.DetailRoot)

    iconColumnWidth = 23 # temporarily not 20, to work around header bug 6168
    DashboardSummaryViewTemplate = SplitterWindow.template(
        'DashboardSummaryViewTemplate',
        eventBoundary = True,
        orientationEnum = "Vertical",
        splitPercentage = 0.65,
        childBlocks = [
            BoxContainer.template('DashboardSummaryContainer',
                orientationEnum = 'Vertical',
                childBlocks = [
                    DashboardBlock.template('DashboardSummaryView',
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
                        sectionLabelCharacterStyle = blocks.SummarySectionLabelStyle,
                        sectionCountCharacterStyle = blocks.SummarySectionCountStyle,
                        rowHeight = 19,
                        elementDelegate = 'osaf.views.main.SectionedGridDelegate',
                        defaultEditableAttribute = u'displayName',
                        emptyContentsShow = False,
                        contextMenu = "ItemContextMenu",
                        miniCalendar = main.MiniCalendar,
                        activeView = True),
                    HTML.template('SummaryEmptyDashBoardView',
                        text = u'<html><body><center>&nbsp;<br>&nbsp;<br>%s</center></body></html>' % _(u'0 items'),
                        treatAsURL = False,
                        contextMenu = "ItemContextMenu",
                        emptyContentsShow = True)
                ]
            ),
            BranchPointBlock.template('DashboardDetailBranchPointBlock',
                delegate = detailBranchPointDelegate)
        ]).install(parcel) # SplitterWindow DashboardSummaryViewTemplate

    searchRankColumn = makeColumnAndIndexes('SearchColRank',
        heading = _(u'Rank'),
        valueType = 'None',
        defaultSort = True,
        useSortArrows = False,
        useMaster = False,
        width = 39,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_NON_SCALABLE,
        readOnly = True,
        indexName ='%s.rank' % __name__,
        format='rank',
        baseClass = pim.NumericIndexDefinition,
        attributes = [])

    searchTaskColumn = makeColumnAndIndexes('SearchColTask',
        icon='ColHTask',
        valueType = 'stamp',
        stamp=pim.TaskStamp,
        width=iconColumnWidth,
        useSortArrows=False,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly=True,
        indexName='%s.taskStatus' % __name__,
        baseClass=TaskColumnIndexDefinition,
        attributes=list(dict(TaskColumnIndexDefinition.findParams)),)

    searchCommColumn = makeColumnAndIndexes('SearchColMail',
        icon='ColHMail',
        valueType='stamp',
        stamp=pim.mail.MailStamp,
        width=iconColumnWidth,
        useSortArrows=False,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly=True,
        indexName=CommunicationStatus.status.name,
        attributeName=CommunicationStatus.status.name,
        baseClass=CommunicationColumnIndexDefinition,
        attributes=list(dict(CommunicationStatus.attributeValues)),)

    searchWhoColumn = makeColumnAndIndexes('SearchColWho',
        heading=_(u'Who'),
        width=100,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_SCALABLE,
        readOnly=True,
        indexName='%s.displayWho' % __name__,
        attributeName='displayWho',
        attributeSourceName = 'displayWhoSource',
        format='who',
        baseClass=WhoColumnIndexDefinition,
        attributes=list(dict(WhoColumnIndexDefinition.findParams)),)
    
    searchTitleColumn = makeColumnAndIndexes('SearchColAbout',
        heading=_(u'Title'),
        width=120,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_SCALABLE,
        indexName='%s.displayName' % __name__,
        attributeName='displayName',
        baseClass=TitleColumnIndexDefinition,
        attributes=list(dict(TitleColumnIndexDefinition.findParams)),)

    searchReminderColumn = makeColumnAndIndexes('SearchColCalendarEvent',
        icon = 'ColHEvent',
        valueType = 'stamp',
        stamp = pim.EventStamp,
        useSortArrows = False,
        width = iconColumnWidth,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_FIXED_SIZE,
        readOnly = True,
        indexName = '%s.calendarStatus' % __name__,
        baseClass=CalendarColumnIndexDefinition,
        attributes=list(dict(CalendarColumnIndexDefinition.findParams)) + \
                   ['displayDateSource'])

    searchDateColumn = makeColumnAndIndexes('SearchColDate',
        heading = _(u'Date'),
        width = 100,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_SCALABLE,
        readOnly = True,
        attributeName = 'displayDate',
        attributeSourceName = 'displayDateSource',
        indexName = '%s.displayDate' % __name__,
        baseClass=DateColumnIndexDefinition,
        attributes=list(dict(DateColumnIndexDefinition.findParams)) + \
                   ['displayDateSource'])

    searchTriageColumn = makeColumnAndIndexes('SearchColTriage',
        icon = 'ColHTriageStatus',
        useSortArrows = False,
        width = 39,
        scaleColumn = wxGrid.Grid.GRID_COLUMN_FIXED_SIZE,
        collapsedSections=set([str(pim.TriageEnum.later), str(pim.TriageEnum.done)]), 
        attributeName = 'sectionTriageStatus',
        indexName = '%s.triage' % __name__,
        baseClass=TriageColumnIndexDefinition,
        attributes=list(dict(TriageColumnIndexDefinition.findParams)))
        
    SplitterWindow.template(
        'SearchResultsViewTemplate',
        orientationEnum = "Vertical",
        splitPercentage = 0.65,
        eventBoundary = True,
        childBlocks = [
            BoxContainer.template('SearchResultsSummaryContainer',
                orientationEnum = 'Vertical',
                childBlocks = [
                    DashboardBlock.template('SearchResultsSummaryView',
                        contents = pim_ns.allCollection,
                        scaleWidthsToFit = True,
                        columns = [
                            searchRankColumn,
                            searchTaskColumn,
                            searchCommColumn,
                            searchWhoColumn,
                            searchTitleColumn,
                            searchReminderColumn,
                            searchDateColumn,
                            searchTriageColumn                    
                        ],
                        characterStyle = blocks.SummaryRowStyle,
                        headerCharacterStyle = blocks.SummaryHeaderStyle,
                        prefixCharacterStyle = blocks.SummaryPrefixStyle,
                        sectionLabelCharacterStyle = blocks.SummarySectionLabelStyle,
                        sectionCountCharacterStyle = blocks.SummarySectionCountStyle,
                        rowHeight = 19,
                        elementDelegate = 'osaf.views.main.SectionedGridDelegate',
                        defaultEditableAttribute = u'displayName',
                        miniCalendar = main.MiniCalendar,
                        emptyContentsShow = False,
                        activeView = True),
                    HTML.template('SearchResultsEmptyDashBoardView',
                        text = u'<html><body><center>&nbsp;<br>&nbsp;<br>%s</center></body></html>' % _(u'0 items'),
                        treatAsURL = False,
                        emptyContentsShow = True)
                ]
            ),
            BranchPointBlock.template('SearchResultsSummaryDetailBranchPointBlock',
                delegate = detailBranchPointDelegate)
        ]
    ).install(parcel) # SplitterWindow SearchResultsViewTemplate

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
    MainMultiWeekControlTemplate = MultiWeekControl.template(
        'MainMultiWeekControl',
        tzCharacterStyle = DefaultCharacterStyle,
        dayMode = 'multiweek',
        stretchFactor = 0)

    MainMultiWeekControl = MainMultiWeekControlTemplate.install(parcel)

    MultiWeekDetailBranchPointBlock = BranchPointBlock.template(
        'MultiWeekDetailBranchPointBlock',
        delegate = detailBranchPointDelegate,
        ).install(parcel)

    MultiWeekCalendarView = MultiWeekContainer.template(
        'MultiWeekCalendarView',
        calendarControl = MainMultiWeekControl,
        monthLabelStyle = blocks.BigTextStyle,
        eventLabelStyle = DefaultCharacterStyle,
        eventTimeStyle = DefaultSmallBoldStyle,
        legendStyle = DefaultCharacterStyle,
        orientationEnum = 'Vertical',
        dayMode = 'multiweek',
        eventsForNamedLookup = [TimeZoneChange]).install(parcel)
    
    SplitterWindow.template('MultiWeekViewTemplate',
        eventBoundary = True,
        orientationEnum = 'Vertical',
        splitPercentage = 0.65,
        treeController = MainMultiWeekControl,
        childBlocks = [
            MultiWeekContainer.template('MultiWeekCalendarView',
                childBlocks = [
                    MainMultiWeekControlTemplate,
                    calendar.MultiWeekCanvas.template('MultiWeekCanvas',
                        calendarContainer = MultiWeekCalendarView,
                        contextMenu = "ItemContextMenu",
                        miniCalendar = main.MiniCalendar,
                        dayMode = 'multiweek',
                        activeView = True)
                    ]),
            MultiWeekDetailBranchPointBlock
            ]).install(parcel)
    
    MultiWeekControl.update(
        parcel, 'MainMultiWeekControl',
        calendarContainer = MultiWeekCalendarView)
                                

    # save the template because we'll need it for later
    MainCalendarControlT = CalendarControl.template(
        'MainCalendarControl',
        tzCharacterStyle = DefaultCharacterStyle,
        stretchFactor = 0)
    
    MainCalendarControl = MainCalendarControlT.install(parcel)

    CalendarDetailBranchPointBlock = BranchPointBlock.template(
        'CalendarDetailBranchPointBlock',
        delegate = detailBranchPointDelegate,
        ).install(parcel)

    WelcomeEvent = schema.ns('osaf.app', view).WelcomeEvent
    CalendarDetailBranchPointBlock.selectedItem = WelcomeEvent

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
        treeController = MainCalendarControl,
        childBlocks = [
            CalendarContainer.template('CalendarSummaryView',
                childBlocks = [
                    MainCalendarControlT,
                    CanvasSplitterWindow.template('MainCalendarCanvasSplitter',
                        # as small as possible; AllDayEvents's
                        # SetMinSize() should override?
                        splitPercentage = 0.06,
                        orientationEnum = 'Horizontal',
                        calendarControl = MainCalendarControl,
                        childBlocks = [
                            calendar.AllDayEventsCanvas.template('AllDayEvents',
                                calendarContainer = CalendarSummaryView,
                                contextMenu = "ItemContextMenu"),
                            calendar.TimedEventsCanvas.template('TimedEvents',
                                calendarContainer = CalendarSummaryView,
                                contextMenu = "ItemContextMenu",
                                miniCalendar = main.MiniCalendar,
                                activeView = True)
                            ]),
                    ]),
            CalendarDetailBranchPointBlock
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
    #   cd $CHANDLERHOME; $CHANDLERBIN/release/RunPython.bat parcels/osaf/views/main/summaryblocks.py
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
