__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.detail"

import sys
import application
from application import schema
from osaf.framework.attributeEditors import \
     AttributeEditorMapping, DateTimeAttributeEditor, \
     DateAttributeEditor, TimeAttributeEditor, \
     ChoiceAttributeEditor, StaticStringAttributeEditor
from osaf.framework.blocks import \
     Block, ContainerBlocks, ControlBlocks, DynamicContainerBlocks, \
     Trunk, TrunkSubtree
import osaf.framework.sharing.Sharing as Sharing
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.calendar.Recurrence as Recurrence
from osaf.contentmodel.contacts import Contact, ContactName
import osaf.contentmodel.Notes as Notes
from osaf.contentmodel import ContentItem
import application.dialogs.Util as Util
import application.dialogs.AccountPreferences as AccountPreferences
import osaf.mail.constants as MailConstants
import osaf.mail.sharing as MailSharing
import osaf.mail.message as MailMessage
from repository.item.Item import Item
import repository.item.Query as Query
import wx
import sets
import logging
from PyICU import DateFormat, SimpleDateFormat, ICUError, ParsePosition
from datetime import datetime, time, timedelta

"""
Detail.py
Classes for the ContentItem Detail View
"""

logger = logging.getLogger("detail")
logger.setLevel(logging.INFO)

def installParcel(parcel, oldVersion=None):
    # Declare our attribute editors at repository-init time
    #
    # If you modify this list, please keep it in alphabetical order by type string.
    # Also, note that there are more attribute editors custom to the detail 
    # view; they're declared in its installParcel method.
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

class DetailTrunkSubtree(TrunkSubtree):
    """All our subtrees are of this kind, so we can find 'em."""

class DetailRootBlock (ControlBlocks.ContentItemDetail):
    """
      Root of the Detail View.
    """
    # @@@ There's a lot of overlap between onSetContentsEvent and onSelectItemEvent, and scrungy old
    # code related to selection down the block tree - we'll revisit it all in 0.6

    selection = schema.One(schema.Item, initialValue = None)

    schema.addClouds(
        copying = schema.Cloud(byRef=[selection])
    )

    def onSetContentsEvent (self, event):
        logger.debug("DetailRoot.onSetContentsEvent: %s", event.arguments['item'])
        self.__changeSelection(event.arguments['item'])

    def onSelectItemEvent (self, event):
        """
          A DetailTrunk is an event boundary; this keeps all the events 
        sent between blocks of the Detail View to ourselves.
        """
        logger.debug("DetailRoot.onSelectItemEvent: %s", event.arguments['item'])
        
        # Finish changes to previous selected item 
        self.finishSelectionChanges () 
        
        # Remember the new selected ContentItem.
        self.__changeSelection(event.arguments['item'])
 
        # Synchronize to this item; this'll swap in an appropriate detail trunk.
        self.synchronizeWidget()
        if __debug__:
            dumpSelectItem = False
            if dumpSelectItem:
                self.dumpShownHierarchy ('onSelectItemEvent')

    def unRender(self):
        # There's a wx bug on Mac (2857) that causes EVT_KILL_FOCUS events to happen
        # after the control's been deleted, which makes it impossible to grab
        # the control's state on the way out. To work around this, the control
        # does nothing in its EVT_KILL_FOCUS handler if it's being deleted,
        # and we'll force the final update here.
        #logger.debug("DetailRoot: unrendering.")
        self.finishSelectionChanges() 
        
        # then call our parent which'll do the actual unrender, triggering the
        # no-op EVT_KILL_FOCUS.
        super(DetailRootBlock, self).unRender()
        
    def __changeSelection(self, item):
        self.selection = item
        
        # Make sure the itemcollection that we monitor includes only the selected item.
        if item is not None and (len(self.contents.inclusions) != 1 or \
                                 self.contents.inclusions.first() is not item):
            self.contents.inclusions.clear()
            self.contents.add(item)

    def selectedItem(self):
        # return the item being viewed
        return self.selection    

    def detailRoot (self):
        # we are the detail root object
        return self

    def synchronizeDetailView(self, item):
        """
          We have an event boundary inside us, which keeps all
        the events sent between blocks of the Detail View to
        ourselves.
          When we get a SelectItem event, we jump across
        the event boundary and call synchronizeItemDetail on each
        block to give it a chance to update the widget with data
        from the Item.
          Notify container blocks before their children.
          
          @@@DLD - find a better way to broadcast inside my boundary.
        """
        def reNotifyInside(block, item):
            notifySelf = len(block.childrenBlocks) == 0 # True if no children
            try:
                # process from the children up
                for child in block.childrenBlocks:
                    notifySelf = reNotifyInside (child, item) or notifySelf
            except AttributeError:
                pass
            try:
                syncMethod = type(block).synchronizeItemDetail
            except AttributeError:
                if notifySelf:
                    block.synchronizeWidget()
            else:
                notifySelf = syncMethod(block, item) or notifySelf
            return notifySelf

        needsLayout = False
        children = self.childrenBlocks
        for child in children:
            needsLayout = reNotifyInside(child, item) or needsLayout
        wx.GetApp().needsUpdateUI = True
        if needsLayout:
            try:
                sizer = self.widget.GetSizer()
            except AttributeError:
                pass
            else:
                if sizer:
                    sizer.Layout()

    if __debug__:
        def dumpShownHierarchy (self, methodName=''):
            """ Like synchronizeDetailView, but just dumps info about which
            blocks are currently shown.
            """
            def reNotifyInside(block, item, indent):
                if not isinstance(block, DynamicContainerBlocks.ToolbarItem):
                    if block.isShown:
                        print indent + '+' + block.blockName
                    else:
                        print indent + '-' + block.blockName
                try:
                    # process from the children up
                    for child in block.childrenBlocks:
                        reNotifyInside (child, item, indent + '  ')
                except AttributeError:
                    pass
            item= self.selectedItem()
            try:
                itemDescription = item.itsKind.itsName + ' '
            except AttributeError:
                itemDescription = ''
            try:
                itemDescription += str (item)
            except:
                itemDescription += str (item.itsName)
            print methodName + " " + itemDescription
            print "-------------------------------"
            reNotifyInside(self, item, '')
            print

    def synchronizeWidget (self):
        item= self.selectedItem()
        super(DetailRootBlock, self).synchronizeWidget ()
        self.synchronizeDetailView(item)
        if __debug__:
            dumpSynchronizeWidget = False
            if dumpSynchronizeWidget:
                self.dumpShownHierarchy ('synchronizeWidget')

    def onResynchronizeEvent(self, event):
        logger.debug("onResynchronizeEvent: resynching")
        self.synchronizeWidget()

    def onResynchronizeEventUpdateUI(self, event):
        pass

    def onDestroyWidget (self):
        # Hack - @@@DLD - remove when wxWidgets issue is resolved.
        # set ourself to be shown, to work around Windows DetailView garbage problem.
        def showReentrant (block):
            block.isShown = True
            for child in block.childrenBlocks:
                showReentrant (child)
        super(DetailRootBlock, self).onDestroyWidget ()
        showReentrant (self)

    def onSendShareItemEventUpdateUI(self, event):    
        item = self.selectedItem()
        enabled = False
        label = _("Send")
        if item is not None:            
            if isinstance(item, ItemCollection.ItemCollection):
                # It's a collection: label should read "Send", or "Send to new" if it's already shared.
                enabled = len(item.invitees) > 0
                try:
                    renotify = Sharing.isShared (item)
                except AttributeError:
                    pass
                else:
                    if renotify:
                        label = _("Send to new")
            elif isinstance(item, Mail.MailMessageMixin) and item.isOutbound:
                # It's mail. Has it been sent already?
                sent = False
                try:
                    sent = item.deliveryExtension.state == "SENT"
                except AttributeError:
                    pass
                if sent:
                    label = _("Sent")
                else:
                    # Not sent yet - enable it if it's outbound and we have valid addressees?
                    enabled = len(item.toAddress) > 0
        
        event.arguments['Enable'] = enabled    
        event.arguments ['Text'] = label
            
    def onSendShareItemEvent (self, event):
        """
          Send or Share the current item.
        """
        self.finishSelectionChanges () # finish changes to previous selected item 
        item = self.selectedItem()

        # Make sure we have all the accounts; returns False if the user cancels
        # out and we don't.
        if not Sharing.ensureAccountSetUp(self.itsView):
            return

        # preflight the send/share request
        # mail items and collections need their sender and recievers set up
        message = None
        if isinstance (item, ItemCollection.ItemCollection):
            try:
                whoTo = item.invitees
            except AttributeError:
                whoTo = []
            if len (whoTo) == 0:
                message = _('Please specify who to share this collection with in the "to" field.')
        elif isinstance (item, Mail.MailMessageMixin):
            if item.ItemWhoFromString() == '':
                item.whoFrom = item.getCurrentMeEmailAddress()
            try:
                whoTo = item.toAddress
            except AttributeError:
                whoTo = []
            if len (whoTo) == 0:
                message = _('Please specify who to send this message to in the "to" field.')
                
        if message:
            Util.ok(wx.GetApp().mainFrame,
             _("No Receivers"), message)
        else:
            item.shareSend() # tell the ContentItem to share/send itself.

    def finishSelectionChanges (self):
        """ 
          Need to finish any changes to the selected item
        that are in progress.
        @@@DLD - find a better way to commit widget changes
        Maybe trigger an EVT_KILL_FOCUS event?
        """
        focusBlock = self.getFocusBlock()
        try:
            focusBlock.saveTextValue (validate=True)
        except AttributeError:
            pass

    def onCollectionChanged (self, action):
        """
        When our item collection has changed, we need to synchronize ourselves.
        (We suppress this if we're in the midst of stamping; our item's in an 
        inconsistent state.)
        """
        if not getattr(self, "ignoreCollectionChangedWhileStamping", False):
            # logger.debug("DetailRoot: onCollectionChanged")
            self.synchronizeWidget()
    
class DetailTrunkDelegate (Trunk.TrunkDelegate):
    """ 
    Delegate for the trunk builder on DetailRoot; the cache key is the given item's Kind
    """    

    # A stub block to copy as the root of each tree-of-blocks we build.
    trunkStub = schema.One(Block.Block)

    schema.addClouds(
        copying = schema.Cloud(byRef=[trunkStub])
    )

    def _mapItemToCacheKeyItem(self, item):
        """ 
        Overrides to use the item's kind as our cache key
        """
        if item is None:
            # We use the subtree kind itself as the key for displaying "nothing";
            # Mimi wants a particular look when no item is selected; we've got a 
            # particular tree of blocks defined in parcel.xml for this Kind,
            # which will never get used for a real Item.
            return DetailTrunkSubtree.getKind(self.itsView), False
        else:
            return item.itsKind, False
    
    def _makeTrunkForCacheKey(self, keyItem):
        """ 
        Handle a cache miss; build and return the detail tree-of-blocks for this keyItem, a Kind. 
        """
        # Walk through the keys we have subtrees for, and collect subtrees to use;
        # we decide to use a subtree if _includeSubtree returns True for it.
        # Each subtree we find has children that are the blocks that are to be 
        # collected and sorted (by their 'position' attribute, then their paths
        # to be deterministic in the event of a tie) into the tree we'll use.
        # Blocks without 'position' attributes will naturally be sorted to the end.
        # If we were given a reference to a 'stub' block, we'll copy that and use
        # it as the root of the tree; otherwise, it's assumed that we'll only find
        # one subtree for our key, and use it directly.
        
        # (Yes, I wrote this as a double nested list comprehension with filtering, 
        # but I couldn't decide how to work in a lambda function, so I backed off and
        # opted for clarity.)
        decoratedSubtreeList = [] # each entry will be (position, path, subtreechild)
        for subtree in self._getSubtrees():
            if keyItem.isKindOf(subtree.key) and subtree.hasLocalAttributeValue('rootBlocks'):
                for block in subtree.rootBlocks:
                    entryTobeSorted = (block.getAttributeValue('position', default=sys.maxint), 
                                       block.itsPath,
                                       self._copyItem(block))
                    decoratedSubtreeList.append(entryTobeSorted) 
                
        if len(decoratedSubtreeList) == 0:
            assert False, "Don't know how to build a trunk for this kind!"
            # (We can continue here - we'll end up just caching an empty view.)

        decoratedSubtreeList.sort()
        
        # Copy our stub block and move the new kids on(to) the block.
        trunk = self._copyItem(self.trunkStub)
        trunk.childrenBlocks.extend([ block for position, path, block in decoratedSubtreeList ])
            
        return trunk    
    
    def _getSubtrees(self):
        """
        Get a list of mappings from kind to subtree; by default, we generate it once at startup
        """
        try:
            subtrees = self.subtreeList
        except AttributeError:
            subtrees = list(DetailTrunkSubtree.iterItems(self.itsView))
            self.subtreeList = subtrees
        return subtrees
        
class DetailSynchronizer(Item):
    """
      Mixin class that handles synchronizeWidget and
    the SelectItem event by calling synchronizeItemDetail.
    Most client classes will only have to implement
    synchronizeItemDetail.
    """
    def detailRoot (self):
        # Cruise up the parents looking for someone who can return the detailRoot
        block = self
        while True:
            try:
                return block.parentBlock.detailRoot()
            except AttributeError:
                block = block.parentBlock
        else:
            assert False, "Detail Synchronizer can't find the DetailRoot!"
        

    def onSetContentsEvent (self, event):
        self.contents = event.arguments['item']

    def selectedItem (self):
        # return the selected item
        return getattr(self, 'contents', None)

    def finishSelectionChanges (self):
        # finish any changes in progress in editable text fields.
        self.detailRoot().finishSelectionChanges ()

    def synchronizeItemDetail (self, item):
        # if there is an item, we should show ourself, else hide
        if item is None:
            shouldShow = False
        else:
            shouldShow = self.shouldShow (item)
        return self.show(shouldShow)
    
    def shouldShow (self, item):
        return item is not None

    def show (self, shouldShow):
        # if the show status has changed, tell our widget, and return True
        try:
            widget = self.widget
        except AttributeError:
            return False
        if shouldShow != widget.IsShown():
            # we have a widget
            # make sure widget shown state is what we want
            if shouldShow:
                widget.Show (shouldShow)
            else:
                widget.Hide()
            self.isShown = shouldShow
            return True
        return False

    def whichAttribute(self):
        # define the attribute to be used
        return self.parentBlock.selectedItemsAttribute

    def parseEmailAddresses(self, item, addressesString):
        """
          Parse the email addresses in addressesString and return
        a tuple with: (the processed string, a list of EmailAddress
        items created/found for those addresses).
        @@@DLD - seems like the wrong place to parse Email Address list strings
        """

        # get the user's address strings into a list
        addresses = []
        tmp = addressesString.split(',')
   
        for val in tmp:
            #Many people are use to entering ';' in an email client
            #so if one or more ';' are found treat as an email address
            #divider
            if val.find(';') != -1:
                addresses.extend(val.split(';'))
            else:
                addresses.append(val)


        # build a list of all processed addresses, and all valid addresses
        validAddresses = []
        processedAddresses = []

        # convert the text addresses into EmailAddresses
        for address in addresses:
            whoAddress = item.getEmailAddress (address)
            if whoAddress is None:
                processedAddresses.append (address + '?')
            else:
                processedAddresses.append (str (whoAddress))
                validAddresses.append (whoAddress)

        # prepare the processed addresses return value
        processedResultString = ', '.join (processedAddresses)

        return (processedResultString, validAddresses)

class StaticTextLabel (DetailSynchronizer, ControlBlocks.StaticText):
    def staticTextLabelValue (self, item):
        theLabel = self.title
        return theLabel

    def synchronizeLabel (self, value):
        label = self.widget.GetLabel ()
        relayout = label != value
        if relayout:
            self.widget.SetLabel (value)
        return relayout

    def synchronizeItemDetail (self, item):
        hasChanged = super(StaticTextLabel, self).synchronizeItemDetail(item)
        if self.isShown:
            labelChanged = self.synchronizeLabel(self.staticTextLabelValue(item))
            hasChanged = hasChanged or labelChanged
        return hasChanged

# gets redirectTo for an attribute name, or just returns the attribute
# name if a there is no redirectTo
def GetRedirectAttribute(item, defaultAttr):
    attributeName = item.getAttributeAspect(defaultAttr, 'redirectTo');
    if attributeName is None:
        attributeName = defaultAttr
    return attributeName

        
class StaticRedirectAttribute (StaticTextLabel):
    """
      Static text label that displays the attribute value
    """
    def staticTextLabelValue (self, item):
        try:
            value = item.getAttributeValue(GetRedirectAttribute(item, self.whichAttribute()))
            theLabel = str(value)
        except AttributeError:
            theLabel = ""
        return theLabel
        
class StaticRedirectAttributeLabel (StaticTextLabel):
    """
      Static Text that displays the name of the selected item's Attribute
    """
    def staticTextLabelValue (self, item):
        redirectAttr = GetRedirectAttribute(item, self.whichAttribute ())
        # lookup better names for display of some attributes
        if item.hasAttributeAspect (redirectAttr, 'displayName'):
            redirectAttr = item.getAttributeAspect (redirectAttr, 'displayName')
        return redirectAttr

class LabeledTextAttributeBlock (ControlBlocks.ContentItemDetail):
    """
      basic class for a block in the detail view typically containing:
        * a label (e.g. a StaticText with "Title:")
        * an attribute value (e.g. in an EditText with the value of item.title)
      it also handles visibility of the block, depending on if the attribute
      exists on the item or not
    """ 
    def synchronizeItemDetail(self, item):
        whichAttr = self.selectedItemsAttribute
        self.isShown = item is not None and item.itsKind.hasAttribute(whichAttr)
        self.synchronizeWidget()

class DetailSynchronizedLabeledTextAttributeBlock (DetailSynchronizer, LabeledTextAttributeBlock):
    pass

class DetailSynchronizedContentItemDetail(DetailSynchronizer, ControlBlocks.ContentItemDetail):
    pass

class DetailSynchronizedAttributeEditorBlock (DetailSynchronizer, ControlBlocks.AEBlock):
    
    # temporary fix until AEBlocks update themselves automatically
    def synchronizeItemDetail(self, item):
        super(DetailSynchronizedAttributeEditorBlock, self).synchronizeItemDetail(item)
        
        # tell the AE block to update itself
        if self.isShown:
            self.synchronizeWidget()

    def saveTextValue (self, validate=False):
        # Tell the AE to save itself
        self.saveValue()

    def OnDataChanged (self):
        self.saveTextValue()

def ItemCollectionOrMailMessageMixin (item):
    # if the item is a MailMessageMixin, or an ItemCollection,
    # then return True
    mailKind = Mail.MailMessageMixin.getKind (item.itsView)
    isCollection = isinstance (item, ItemCollection.ItemCollection)
    isOneOrOther = isCollection or item.isItemOf (mailKind)
    return isOneOrOther

class MarkupBarBlock(DetailSynchronizer, DynamicContainerBlocks.Toolbar):
    """
      Markup Toolbar, for quick control over Items.
    Doesn't need to synchronizeItemDetail, because
    the individual ToolbarItems synchronizeItemDetail.
    """
    def shouldShow (self, item):
        # if the item is a collection, we should not show ourself
        shouldShow = not isinstance (item, ItemCollection.ItemCollection)
        return shouldShow

    def onButtonPressedEvent (self, event):
        # Rekind the item by adding or removing the associated Mixin Kind
        self.finishSelectionChanges () # finish changes to editable fields 
        tool = event.arguments['sender']
        item = self.selectedItem()
        
        if not item or not self._isStampable(item):
            return
            
        mixinKind = tool.stampMixinKind()
        if not item.itsKind.isKindOf(mixinKind):
            operation = 'add'
        else:
            operation = 'remove'
        
        # Suppress our on-change processing to avoid issues with 
        # notifications midway through stamping. See bug 2739.
        self.detailRoot().ignoreCollectionChangedWhileStamping = True
        item.StampKind(operation, mixinKind)
        del self.detailRoot().ignoreCollectionChangedWhileStamping
        
        # notify the world that the item has a new kind.
        self.detailRoot().parentBlock.widget.wxSynchronizeWidget()

    def onButtonPressedEventUpdateUI(self, event):
        item = self.selectedItem()
        enable = item is not None and self._isStampable(item) and \
               item.isAttributeModifiable('itsKind')
        event.arguments ['Enable'] = enable

    def onTogglePrivateEvent(self, event):
        item = self.selectedItem()
        if item is not None:
            tool = event.arguments['sender']
            if not item.isPrivate and \
               item.getSharedState() != ContentItem.UNSHARED:
                # Marking a shared item as "private" could act weird...
                # Are you sure?
                caption = _("Change the privacy of a shared item?")
                msg = _("Other people may be subscribed to share this item; " \
                        "are you sure you want to mark it as private?")
                if not Util.yesNo(wx.GetApp().mainFrame, caption, msg):
                    # No: Put the not-private state back in the toolbarItem
                    self.widget.ToggleTool(tool.toolID, False)
                    return
            item.isPrivate = self.widget.GetToolState(tool.toolID)
            
    def onTogglePrivateEventUpdateUI(self, event):
        item = self.selectedItem()            
        enable = item is not None and item.isAttributeModifiable('isPrivate')
        event.arguments ['Enable'] = enable

    def _isStampable(self, item):
        # for now, any ContentItem is stampable. This may change if Mixin rules/policy change
        return item.isItemOf(ContentModel.ContentItem.getKind(self.itsView))

class DetailStampButton (DetailSynchronizer, DynamicContainerBlocks.ToolbarItem):
    """
      Common base class for the stamping buttons in the Markup Bar
    """
    def stampMixinClass(self):
        # return the class of this stamp's Mixin Kind (bag of kind-specific attributes)
        raise NotImplementedError, "%s.stampMixinClass()" % (type(self))
    
    def stampMixinKind(self):
        # return the Mixin Kind of this stamp
        raise NotImplementedError, "%s.stampMixinKind()" % (type(self))
    
    def synchronizeItemDetail (self, item):
        # toggle this button to reflect the kind of the selected item
        shouldToggleBasedOnClass = isinstance(item, self.stampMixinClass())
        shouldToggleBasedOnKind = item.isItemOf(self.stampMixinKind())
        assert shouldToggleBasedOnClass == shouldToggleBasedOnKind, \
               "Class/Kind mismatch for class %s, kind %s" % (item.__class__, item.itsKind)
        # @@@DLD remove workaround for bug 1712 - ToogleTool doesn't work on mac when bar hidden
        if shouldToggleBasedOnKind:
            self.dynamicParent.show (True) # if we're toggling a button down, the bar must be shown
            
        self.dynamicParent.widget.ToggleTool(self.toolID, shouldToggleBasedOnKind)
        return False

class MailMessageButtonBlock(DetailStampButton):
    """
      Mail Message Stamping button in the Markup Bar
    """
    def stampMixinClass(self):
        return Mail.MailMessageMixin
    
    def stampMixinKind(self):
        return Mail.MailMessageMixin.getKind(self.itsView)
    
class CalendarStampBlock(DetailStampButton):
    """
      Calendar button in the Markup Bar
    """
    def stampMixinClass(self):
        return Calendar.CalendarEventMixin

    def stampMixinKind(self):
        return Calendar.CalendarEventMixin.getKind(self.itsView)

class TaskStampBlock(DetailStampButton):
    """
      Task button in the Markup Bar
    """
    def stampMixinClass(self):
        return Task.TaskMixin

    def stampMixinKind(self):
        return Task.TaskMixin.getKind(self.itsView)


class PrivateSwitchButtonBlock(DetailSynchronizer, DynamicContainerBlocks.ToolbarItem):
    """
      "Never share" button in the Markup Bar
    """
    def synchronizeItemDetail (self, item):
        # toggle this button to reflect the privateness of the selected item        
        # @@@DLD remove workaround for bug 1712 - ToogleTool doesn't work on mac when bar hidden
        if item.isPrivate:
            self.dynamicParent.show (True) # if we're toggling a button down, the bar must be shown
        self.dynamicParent.widget.ToggleTool(self.toolID, item.isPrivate)
        return False
        
class EditTextAttribute (DetailSynchronizer, ControlBlocks.EditText):
    """
    EditText field connected to some attribute of a ContentItem
    Override LoadAttributeIntoWidget, SaveAttributeFromWidget in subclasses
    """
    def instantiateWidget (self):
        widget = super (EditTextAttribute, self).instantiateWidget()
        # We need to save off the changed widget's data into the block periodically
        # Hopefully OnLoseFocus is getting called every time we lose focus.
        widget.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocus)
        widget.Bind(wx.EVT_KEY_UP, self.onKeyPressed)
        return widget

    def saveTextValue (self, validate=False):
        # save the user's edits into item's attibute
        item = self.selectedItem()
        try:
            widget = self.widget
        except AttributeError:
            widget = None
        if item is not None and widget is not None:
            self.saveAttributeFromWidget(item, widget, validate=validate)
        
    def loadTextValue (self, item):
        # load the edit text from our attribute into the field
        if item is None:
            item = self.selectedItem()
        if item is not None:
            widget = self.widget
            self.loadAttributeIntoWidget(item, widget)
    
    def onLoseFocus (self, event):
        # called when we get an event; to saves away the data and skips the event
        self.saveTextValue (validate=True)
        event.Skip()
        
    def onKeyPressed (self, event):
        # called when we get an event; to saves away the data and skips the event
        self.saveTextValue(validate = event.m_keyCode == wx.WXK_RETURN and self.lineStyleEnum != "MultiLine")
        event.Skip()
        
    def OnDataChanged (self):
        # event that an edit operation has taken place
        self.saveTextValue()

    def synchronizeItemDetail (self, item):
        self.loadTextValue(item)
        return super(EditTextAttribute, self).synchronizeItemDetail(item)
            
    def saveAttributeFromWidget (self, item, widget, validate):  
       # subclasses need to override this method
       raise NotImplementedError, "%s.SaveAttributeFromWidget()" % (type(self))

    def loadAttributeIntoWidget (self, item, widget):  
       # subclasses need to override this method
       raise NotImplementedError, "%s.LoadAttributeIntoWidget()" % (type(self))

class EditToAddressTextAttribute (EditTextAttribute):
    """
    An editable address attribute that resyncs the DV when changed
    """
    def saveAttributeFromWidget(self, item, widget, validate):
        if validate:
            toFieldString = widget.GetValue().strip('?')

    
            # parse the addresses and get/create/validate
            processedAddresses, validAddresses = self.parseEmailAddresses (item, toFieldString)
    
            # reassign the list to the attribute
            try:
                item.setAttributeValue (self.whichAttribute (), validAddresses)
            except:
                pass
    
            # redisplay the processed addresses in the widget
            widget.SetValue (processedAddresses)

    def loadAttributeIntoWidget (self, item, widget):
        if self.shouldShow (item):
            try:
                whoContacts = item.getAttributeValue (self.whichAttribute ())
            except AttributeError:
                whoContacts = ''
            try:
                numContacts = len(whoContacts)
            except TypeError:
                numContacts = -1
            if numContacts == 0:
                whoString = ''
            elif numContacts > 0:
                whoNames = []
                for whom in whoContacts.values():
                    whoNames.append (str (whom))
                whoString = ', '.join(whoNames)
            else:
                whoString = str (whoContacts)
                if isinstance(whoContacts, ContactName):
                    names = []
                    if len (whoContacts.firstName):
                        names.append (whoContacts.firstName)
                    if len (whoContacts.lastName):
                        names.append (whoContacts.lastName)
                    whoString = ' '.join(names)
            widget.SetValue (whoString)

class ToMailEditField (EditToAddressTextAttribute):
    """
    'To' attribute of a Mail ContentItem, e.g. who it's sent to
    """
    def whichAttribute(self):
        # define the attribute to be used
        return 'toAddress'

class SharingArea (DetailSynchronizedLabeledTextAttributeBlock):
    """ an area visible only when the item (a collection) is shared """
    def shouldShow (self, item):
        return item is not None and Sharing.isShared(item)
                
class ParticipantsTextFieldBlock(EditTextAttribute):
    """
    'participants' attribute of an ItemCollection, e.g. who it's already been shared with.
    Read only, at least for now.
    """
    def loadAttributeIntoWidget (self, item, widget):
        share = Sharing.getShare(item)
        if share is not None:
            sharees = sets.Set(share.sharees)
            sharees.add(share.sharer)
            value = ", ".join([ str(sharee) for sharee in list(sharees) ])
            widget.SetValue(value)

    def saveAttributeFromWidget (self, item, widget, validate):  
        # It's read-only, but we have to override this method.
        pass
    
class InviteEditFieldBlock(EditToAddressTextAttribute):
    """
    'invitees' attribute of an ItemCollection, e.g. who we're inviting to share it.
    """
    def whichAttribute(self):
        # define the attribute to be used
        return 'invitees'

class EditSharingActiveBlock(DetailSynchronizer, ControlBlocks.CheckBox):
    """
      "Sharing Active" checkbox on item collections
    """
    def synchronizeItemDetail (self, item):
        hasChanged = super(EditSharingActiveBlock, self).synchronizeItemDetail(item)
        if item is not None and self.isShown:
            share = Sharing.getShare(item)
            if share is not None:
                self.widget.SetValue(share.active)
        return hasChanged
    
    def onToggleSharingActiveEvent (self, event):
        item = self.selectedItem()
        if item is not None:
            share = Sharing.getShare(item)
            if share is not None:
                share.active = self.widget.GetValue() == wx.CHK_CHECKED

class FromEditField (EditTextAttribute):
    """Edit field containing the sender's contact"""
    def saveAttributeFromWidget(self, item, widget, validate):  
        pass

    def loadAttributeIntoWidget(self, item, widget):
        """
          Load the widget based on the attribute associated with whoFrom.
        """
        try:
            whoFrom = item.whoFrom
        except AttributeError:
            whoFrom = None

        if whoFrom is None:
            # Hack to set up whoFrom for Items with no value... like ItemCollections
            # Can't set the whoFrom at creation time, because many start life at
            # system startup before the user account is setup.
            if item.itsKind.hasAttribute ('whoFrom'):
                try:
                    # Determine which kind of item to assign based on the
                    # types of the redirected-to attributes:
                    type = item.getAttributeAspect('whoFrom', 'type')
                    contactKind = Contact.getKind(self.itsView)
                    if type is contactKind:
                        item.whoFrom = item.getCurrentMeContact(item.itsView)
                    else:
                        emailAddressKind = Mail.EmailAddress.getKind(self.itsView)
                        if type is emailAddressKind:
                            item.whoFrom = item.getCurrentMeEmailAddress()
                except AttributeError:
                    pass

        try:
            whoString = item.ItemWhoFromString ()
        except AttributeError:
            whoString = ''
        widget.SetValue (whoString)
        # logger.debug("FromEditField: Got '%s' after Set '%s'" % (widget.GetValue(), whoString))

class EditRedirectAttribute (EditTextAttribute):
    """
    An attribute-based edit field
    Our parent block knows which attribute we edit.
    """
    def saveAttributeFromWidget(self, item, widget, validate):
        if validate:
            item.setAttributeValue(self.whichAttribute(), widget.GetValue())

    def loadAttributeIntoWidget(self, item, widget):
        try:
            value = item.getAttributeValue(self.whichAttribute())
        except AttributeError:
            value = _('untitled')
        if widget.GetValue() != value:
            widget.SetValue(value)

class StaticEmailAddressAttribute (StaticRedirectAttributeLabel):
    """
      Static Text that displays the name of the selected item's Attribute.
    Customized for EmailAddresses
    """
    def staticTextLabelValue (self, item):
        label = self.title
        return label

class EditEmailAddressAttribute (EditRedirectAttribute):
    """
    An attribute-based edit field for email addresses
    The actual value is stored in an emailaddress 'section' object
    for home or work.
    """
    def saveAttributeFromWidget(self, item, widget, validate):
        if validate:
            section = item.getAttributeValue (self.whichAttribute())
            widgetString = widget.GetValue()
            processedAddresses, validAddresses = self.parseEmailAddresses (item, widgetString)
            section.emailAddresses = validAddresses
            for address in validAddresses:
                try:
                    address.fullName = section.fullName
                except AttributeError:
                    pass
            widget.SetValue (processedAddresses)

    def loadAttributeIntoWidget(self, item, widget):
        value = ''
        try:
            section = item.getAttributeValue (self.whichAttribute())
            value = section.getAttributeValue ('emailAddresses')
        except AttributeError:
            value = {}
        # convert the email address list to a nice string.
        whoNames = []
        for whom in value.values():
            whoNames.append (str (whom))
        whoString = ', '.join(whoNames)
        widget.SetValue(whoString)


class AttachmentAreaBlock(DetailSynchronizedLabeledTextAttributeBlock):
    """ an area visible only when the item (a mail message) has attachments """
    def shouldShow (self, item):
        return item is not None and item.hasAttachments()
    
class AttachmentTextFieldBlock(EditTextAttribute):
    """
    A read-only list of email attachments, for now.
    """
    def loadAttributeIntoWidget (self, item, widget):
        # For now, just list the attachments' filenames
        if item is None or not item.hasAttachments():
            value = ""
        else:
            value = ", ".join([ attachment.filename for attachment in item.getAttachments() if hasattr(attachment, 'filename') ])
        widget.SetValue(value)
    
    def saveAttributeFromWidget (self, item, widget, validate):  
        # It's read-only, but we have to override this method.
        pass
    
    
class AcceptShareButtonBlock(DetailSynchronizer, ControlBlocks.Button):
    def shouldShow (self, item):
        showIt = False
        if item is not None and item.isInbound:
            try:
                MailSharing.getSharingHeaderInfo(item)
            except:       
                pass
            else:
                showIt = True
        # logger.debug("AcceptShareButton.shouldShow = %s", showIt)
        return showIt

    def onAcceptShareEvent(self, event):
        url, collectionName = MailSharing.getSharingHeaderInfo(self.selectedItem())
        statusBlock = wx.GetApp().mainFrame.GetStatusBar().blockItem
        statusBlock.setStatusMessage( _('Subscribing to collection...') )
        wx.Yield()
        share = Sharing.Share(view=self.itsView)
        share.configureInbound(url)
        share.get()
        statusBlock.setStatusMessage( _('Subscribed to collection') )
    
        # @@@ Remove this when the sidebar autodetects new collections
        collection = share.contents
        mainView = application.Globals.views[0]
        mainView.postEventByName ("AddToSidebarWithoutCopyingAndSelectFirst", {'items':[collection]})

    def onAcceptShareEventUpdateUI(self, event):
        # If we're already sharing it, we should disable the button and change the text.
        enabled = True
        item = self.selectedItem()
        try:
            url, collectionName = MailSharing.getSharingHeaderInfo(item)
            existingSharedCollection = Sharing.findMatchingShare(self.itsView, url)
        except:
            enabled = True
        else:
            if existingSharedCollection is not None:
                self.widget.SetLabel(_("(Already sharing this collection)"))
                enabled = False
        event.arguments['Enable'] = enabled

# Classes to support CalendarEvent details - first, areas that show/hide
# themselves based on readonlyness and attribute values

class CalendarAllDayAreaBlock(DetailSynchronizedContentItemDetail):
    def shouldShow (self, item):
        return item.isAttributeModifiable('allDay')

# @@@ For now, just inherit from ContentItemDetail; when we don't, 
#     layout gets funny on Mac (bug 3543). By turning this off,
#     I'm reopening bug 2976: location will be shown even for
#     readonly shares.
class CalendarLocationAreaBlock(ControlBlocks.ContentItemDetail):
    pass
#class CalendarLocationArea(DetailSynchronizedContentItemDetail):
    #def shouldShow (self, item):
        #return item.isAttributeModifiable('location') \
               #or hasattr(item, 'location')

class CalendarAtLabel (StaticTextLabel):
    def shouldShow (self, item):
        return item.isAttributeModifiable('startTime') \
               and not item.allDay
        
class CalendarTimeAEBlock(DetailSynchronizedAttributeEditorBlock):
    def shouldShow (self, item):
        return item.isAttributeModifiable('startTime') \
               and not item.allDay

class CalendarReminderAreaBlock(DetailSynchronizedContentItemDetail):
    def shouldShow (self, item):
        return item.isAttributeModifiable('reminderTime') \
               or hasattr(item, 'reminderTime')

# Centralize the recurrence blocks' visibility decisions
showPopup = 1
showCustom = 2
showEnds = 4
def recurrenceVisibility(item):
    result = 0
    freq = RecurrenceAttributeEditor.mapRecurrenceFrequency(item)
    modifiable = item.isAttributeModifiable('rruleset')
    
    # Show the popup only if it's modifiable, or if it's not
    # modifiable but not the default value.
    if modifiable or (freq != RecurrenceAttributeEditor.onceIndex):
        result |= showPopup
            
    if freq == RecurrenceAttributeEditor.customIndex:
        # We'll show the "custom" flag only if we're custom, duh.
        result |= showCustom
    elif freq != RecurrenceAttributeEditor.onceIndex:
        # We're not custom and not "once": We'll show "ends" if we're 
        # modifiable, or if we have an "ends" value.
        if modifiable:
            result |= showEnds
        else:
            try:
                endDate = item.rruleset.rrules.first().until
            except AttributeError:
                pass
            else:
                result |= showEnds
    return result
    
class CalendarRecurrencePopupAreaBlock(DetailSynchronizedContentItemDetail):
    def shouldShow(self, item):
        return (recurrenceVisibility(item) & showPopup) != 0

class CalendarRecurrenceSpacer2Area(DetailSynchronizer, ControlBlocks.StaticText):
    def shouldShow(self, item):
        return (recurrenceVisibility(item) & (showPopup | showEnds)) != 0

class CalendarRecurrenceCustomAreaBlock(DetailSynchronizedContentItemDetail):
    def shouldShow (self, item):
        return (recurrenceVisibility(item) & showCustom) != 0

class CalendarRecurrenceEndAreaBlock(DetailSynchronizedContentItemDetail):
    def shouldShow (self, item):
        return (recurrenceVisibility(item) & showEnds) != 0

# Attribute editor customizations

class CalendarDateAttributeEditor(DateAttributeEditor):    
    def SetAttributeValue(self, item, attributeName, valueString):
        newValueString = valueString.replace('?','').strip()
        if len(newValueString) == 0:
            # Attempting to remove the start date field will set its value to the 
            # "previous value" when the value is committed (removing focus or 
            # "enter"). Attempting to remove the end-date field will set its 
            # value to the "previous value" when the value is committed. In 
            # brief, if the user attempts to delete the value for a start date 
            # or end date, it automatically resets to what value was displayed 
            # before the user tried to delete it.
            self.SetControlValue(self.control, 
                                 self.GetAttributeValue(item, attributeName))
        else:
            # First, get ICU to parse it into a float
            try:
                dateValue = DateTimeAttributeEditor.shortDateFormat.parse(newValueString)
            except ICUError:
                self._changeTextQuietly(self.control, "%s ?" % newValueString)
                return
            # Then, convert that float to a datetime (I've seen ICU parse bogus 
            # values like "06/05/0506/05/05", which causes fromtimestamp() 
            # to throw.)
            try:
                dateTimeValue = datetime.fromtimestamp(dateValue)
            except ValueError:
                self._changeTextQuietly(self.control, "%s ?" % newValueString)
                return

            # If this results in a new value, put it back.
            oldValue = getattr(item, attributeName)
            value = datetime.combine(dateTimeValue.date(), oldValue.time())
            if oldValue != value:
                if attributeName == 'startTime':
                    # Changing the start date or time such that the start 
                    # date+time are later than the existing end date+time 
                    # will change the end date & time to preserve the 
                    # existing duration. (This is true even for anytime 
                    # events: increasing the start date by three days 
                    # will increase the end date the same amount.)
                    if value > item.endTime:
                        endTime = value + (item.endTime - item.getEffectiveStartTime())
                    else:
                        endTime = item.endTime
                    item.ChangeStart(value)
                    item.endTime = endTime
                else:
                    # Changing the end date or time such that it becomes 
                    # earlier than the existing start date+time will 
                    # change the start date+time to be the same as the 
                    # end date+time (that is, an @time event, or a 
                    # single-day anytime event if the event had already 
                    # been an anytime event).
                    if value < item.startTime:
                        item.ChangeStart(value)
                    setattr (item, attributeName, value)
                self.AttributeChanged()
                
            # Refresh the value in place
            self.SetControlValue(self.control, 
                                 self.GetAttributeValue(item, attributeName))

class CalendarTimeAttributeEditor(TimeAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        noTime = getattr(item, 'allDay', False) \
               or getattr(item, 'anyTime', False)
        if noTime:
            value = u''
        else:
            value = super(CalendarTimeAttributeEditor, self).GetAttributeValue(item, attributeName)
        return value

    def SetAttributeValue(self, item, attributeName, valueString):
        newValueString = valueString.replace('?','').strip()
        if len(newValueString) == 0:
            # Clearing an event's start time (removing the value in it, causing 
            # it to show "HH:MM") will remove the end time value (making it an 
            # anytime event).
            if not item.anyTime:
                item.anyTime = True
                self.AttributeChanged()
            return
        
        # We have _something_; parse it.
        try:
            timeValue = DateTimeAttributeEditor.shortTimeFormat.parse(newValueString)
        except ICUError:
            self._changeTextQuietly(self.control, "%s ?" % newValueString)
            return

        # If we got a new value, put it back.
        oldValue = getattr(item, attributeName)
        value = datetime.combine(oldValue.date(), datetime.fromtimestamp(timeValue).time())
        if item.anyTime or oldValue != value:
            # Something changed.                
            # Implement the rules for changing one of the four values:
            iAmStart = attributeName == 'startTime'
            if item.anyTime:
                # On an anytime event (single or multi-day; both times 
                # blank & showing the "HH:MM" hint), entering a valid time 
                # in either time field will set the other date and time 
                # field to effect a one-hour event on the corresponding date. 
                item.anyTime = False
                if iAmStart:
                    item.ChangeStart(value)
                    item.endTime = value + timedelta(hours=1)
                else:
                    item.ChangeStart(value - timedelta(hours=1))
                    item.endTime = value
            else:
                if iAmStart:
                    # Changing the start date or time such that the start 
                    # date+time are later than the existing end date+time 
                    # will change the end date & time to preserve the 
                    # existing duration. (This is true even for anytime 
                    # events: increasing the start date by three days will 
                    # increase the end date the same amount.)
                    if value > item.endTime:
                        endTime = value + (item.endTime - item.startTime)
                    else:
                        endTime = item.endTime
                    item.ChangeStart(value)
                    item.endTime = endTime
                else:
                    # Changing the end date or time such that it becomes 
                    # earlier than the existing start date+time will change 
                    # the start date+time to be the same as the end 
                    # date+time (that is, an @time event, or a single-day 
                    # anytime event if the event had already been an 
                    # anytime event).
                    if value < item.startTime:
                        item.ChangeStart(value)
                    setattr (item, attributeName, value)
                item.anyTime = False
            
            self.AttributeChanged()
            
        # Refresh the value in the control
        self.SetControlValue(self.control, 
                         self.GetAttributeValue(item, attributeName))

class ReminderDeltaAttributeEditor(ChoiceAttributeEditor):
    def GetControlValue (self, control):
        """ Get the reminder delta value for the current selection """        
        # @@@ For now, assumes that the menu will be a number of minutes, 
        # followed by a space (eg, "1 minute", "15 minutes", etc), or something
        # that doesn't match this (eg, "None") for no-alarm.
        menuChoice = control.GetStringSelection()
        try:
            minuteCount = int(menuChoice.split(u" ")[0])
        except ValueError:
            # "None"
            value = None
        else:
            value = timedelta(minutes=-minuteCount)
        return value

    def SetControlValue (self, control, value):
        """ Select the choice that matches this delta value"""
        # We also take this opportunity to populate the menu
        existingValue = self.GetControlValue(control)
        if existingValue != value or control.GetCount() == 0:            
            # rebuild the list of choices
            choices = self.GetChoices()
            control.Clear()
            control.AppendItems(choices)

            if value is None:
                choiceIndex = 0 # the "None" choice
            else:
                minutes = ((value.days * 1440) + (value.seconds / 60))
                reminderChoice = (minutes == -1) and _("1 minute") or (_("%i minutes") % -minutes)
                choiceIndex = control.FindString(reminderChoice)
                # If we can't find the choice, just show "None" - this'll happen if this event's reminder has been "snoozed"
                if choiceIndex == -1:
                    choiceIndex = 0 # the "None" choice
            control.Select(choiceIndex)

class RecurrenceAttributeEditor(ChoiceAttributeEditor):
    # These are the values we pass around; they're the same as the menu indices.
    # This is a list of the frequency enumeration names, in the order we present
    # them in the menu... plus "once" at the beginning and "custom" at the end.
    menuFrequencies = ['once', 'daily', 'weekly', 'monthly', 'yearly', 'custom']
    onceIndex = menuFrequencies.index('once')
    customIndex = menuFrequencies.index('custom')
    
    @classmethod
    def mapRecurrenceFrequency(theClass, item):
        """ Map the frequency of this item to one of our menu choices """
        if item.isCustomRule(): # It's custom if it says it is.
            return RecurrenceAttributeEditor.customIndex
        # Otherwise, try to map its frequency to our menu list
        try:
            freq = item.rruleset.rrules.first().freq
        except AttributeError:
            # Can't get to the freq attribute, or there aren't any rrules
            # So it's once.
            return RecurrenceAttributeEditor.onceIndex
        else:
            # We got a frequency. Try to map it.
            index = RecurrenceAttributeEditor.menuFrequencies.index(freq)
            if index == -1:
                index = RecurrenceAttributeEditor.customIndex
        return index
    
    def onChoice(self, event):
        control = event.GetEventObject()
        newChoice = self.GetControlValue(control)
        oldChoice = self.GetAttributeValue(self.item, self.attributeName)
        if newChoice != oldChoice:
            self.SetAttributeValue(self.item, self.attributeName, 
                                   newChoice)

    def GetAttributeValue (self, item, attributeName):
        index = RecurrenceAttributeEditor.mapRecurrenceFrequency(item)
        return index
    
    def SetAttributeValue (self, item, attributeName, value):
        """ Set the value of the attribute given by the value. """
        assert value != RecurrenceAttributeEditor.customIndex
        if value == RecurrenceAttributeEditor.onceIndex:
            item.removeRecurrence()
        else:
            duFreq = Recurrence.toDateUtilFrequency(\
                RecurrenceAttributeEditor.menuFrequencies[value])
            rruleset = Recurrence.RecurrenceRuleSet(None, view=item.itsView)
            rruleset.setRuleFromDateUtil(Recurrence.dateutil.rrule.rrule(duFreq))
            rruleset.rrules.first().untilIsDate = True
            item.changeThisAndFuture('rruleset', rruleset)
        self.AttributeChanged()    
    
    def GetControlValue (self, control):
        """ Get the value for the current selection """ 
        choiceIndex = control.GetSelection()
        return choiceIndex

    def SetControlValue (self, control, value):
        """ Select the choice that matches this index value"""
        # We also take this opportunity to populate the menu
        existingValue = self.GetControlValue(control)
        if existingValue != value or control.GetCount() == 0:
            # rebuild the list of choices
            choices = self.GetChoices()
            if self.GetAttributeValue(self.item, self.attributeName) != RecurrenceAttributeEditor.customIndex:
                choices = choices[:-1] # remove "custom"
            control.Clear()
            control.AppendItems(choices)

        control.Select(value)

class RecurrenceCustomAttributeEditor(StaticStringAttributeEditor):
    def GetAttributeValue(self, item, attributeName):
        return item.getCustomDescription()
        
class RecurrenceEndsAttributeEditor(DateAttributeEditor):
    # If we haven't already, remap the configured item & attribute 
    # name to the actual 'until' attribute deep in the recurrence rule.
    # (Because we might be called from within SetAttributeValue,
    # which does the same thing, we just pass through if we're already
    # mapped to 'until')
    def GetAttributeValue(self, item, attributeName):
        if attributeName != 'until':
            attributeName = 'until'
            try:
                item = item.rruleset.rrules.first()
            except AttributeError:
                return u''
        return super(RecurrenceEndsAttributeEditor, self).\
               GetAttributeValue(item, attributeName)
        
    def SetAttributeValue(self, item, attributeName, valueString):
        if attributeName != 'until':
            attributeName = 'until'        
            try:
                item = item.rruleset.rrules.first()
            except AttributeError:
                assert False, "Hey - Setting 'ends' on an event without a recurrence rule?"
        
        super(RecurrenceEndsAttributeEditor, self).\
             SetAttributeValue(item, attributeName, valueString)

class HTMLDetailArea(DetailSynchronizer, ControlBlocks.ItemDetail):
    def synchronizeItemDetail(self, item):
        self.selection = item
        # this ensures that getHTMLText() gets called appropriately on the derived class
        self.synchronizeWidget()
        
    def getHTMLText(self, item):
        return "<html><body>" + str(item) + "</body></html>"


class EmptyPanelBlock(ControlBlocks.ContentItemDetail):
    """
    A bordered panel, which we use when no item is selected in the calendar
    """
    def instantiateWidget (self):
        # Make a box with a sunken border - wxBoxContainer will take care of
        # getting the background color from our attribute.
        style = '__WXMAC__' in wx.PlatformInfo \
              and wx.BORDER_SIMPLE or wx.BORDER_STATIC
        widget = ContainerBlocks.wxBoxContainer(self.parentBlock.widget, -1,
                                                wx.DefaultPosition, 
                                                wx.DefaultSize, 
                                                style)
        widget.SetBackgroundColour(wx.WHITE)
        return widget

