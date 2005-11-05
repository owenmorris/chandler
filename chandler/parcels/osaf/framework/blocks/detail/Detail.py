__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"
__parcel__ = "osaf.framework.blocks.detail"

import sys
import application
from application import schema
from osaf import pim
from osaf.framework.attributeEditors import \
     AttributeEditorMapping, DateTimeAttributeEditor, \
     DateAttributeEditor, TimeAttributeEditor, \
     ChoiceAttributeEditor, StaticStringAttributeEditor
from osaf.framework.blocks import \
     Block, ContainerBlocks, ControlBlocks, MenusAndToolbars, \
     FocusEventHandlers, Trunk, TrunkSubtree, debugName
from osaf import sharing
import osaf.pim.mail as Mail
import osaf.pim.items as items
from osaf.pim.tasks import TaskMixin
import osaf.pim.calendar.Calendar as Calendar
import osaf.pim.calendar.Recurrence as Recurrence
from osaf.pim.contacts import ContactName
from osaf.pim.collections import ListCollection
from osaf.pim import ContentItem
import application.dialogs.Util as Util
import application.dialogs.AccountPreferences as AccountPreferences
import application.dialogs.RecurrenceDialog as RecurrenceDialog
import osaf.mail.constants as MailConstants
import osaf.mail.sharing as MailSharing
import osaf.mail.message as MailMessage
from repository.item.Item import Item
from repository.item.Monitors import Monitors
import wx
import sets
import logging
from PyICU import DateFormat, SimpleDateFormat, ICUError, ParsePosition
from datetime import datetime, time, timedelta
from i18n import OSAFMessageFactory as _
from osaf import messages

"""
Detail.py
Classes for the ContentItem Detail View
"""

logger = logging.getLogger(__name__)

class DetailTrunkSubtree(TrunkSubtree):
    """All our subtrees are of this kind, so we can find 'em."""

class DetailRootBlock (FocusEventHandlers, ControlBlocks.ContentItemDetail):
    """
      Root of the Detail View.
    """
    def onSetContentsEvent (self, event):
        # logger.debug("DetailRoot.onSetContentsEvent: %s", event.arguments['item'])
        Block.Block.finishEdits()
        self.setContentsOnBlock(event.arguments['item'])

    item = property(fget=ControlBlocks.getProxiedContentsItem, 
                    doc="Return the selected item, or None")
    
    def unRender(self):
        # There's a wx bug on Mac (2857) that causes EVT_KILL_FOCUS events to happen
        # after the control's been deleted, which makes it impossible to grab
        # the control's state on the way out. To work around this, the control
        # does nothing in its EVT_KILL_FOCUS handler if it's being deleted,
        # and we'll force the final update here.
        #logger.debug("DetailRoot: unrendering.")
        Block.Block.finishEdits()
        
        # then call our parent which'll do the actual unrender, triggering the
        # no-op EVT_KILL_FOCUS.
        super(DetailRootBlock, self).unRender()
        
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
            
            if notifySelf:
                #logger.debug("SyncDetailView: syncWidgeting %s",
                             #getattr(block, 'blockName', '?'))
                block.synchronizeWidget()
                
            syncMethod = getattr(type(block), 'synchronizeItemDetail', None)
            if syncMethod is not None:
                #logger.debug("SyncDetailView: syncItemDetailing %s",
                             #getattr(block, 'blockName', '?'))
                notifySelf = syncMethod(block, item) or notifySelf
            return notifySelf

        needsLayout = False
        children = self.childrenBlocks
        for child in children:
            needsLayout = reNotifyInside(child, item) or needsLayout
        wx.GetApp().needsUpdateUI = True
        if needsLayout:
            self.relayoutSizer()

    def relayoutSizer(self):
        try:
            sizer = self.widget.GetSizer()
        except AttributeError:
            pass
        else:
            if sizer:
                sizer.Layout()
                    
    def Layout(self):
        """ 
        Called (by installTreeOfBlocks) when the detail view's contents
        changes without rerendering
        """
        self.synchronizeDetailView(self.item)

    if __debug__:
        def dumpShownHierarchy (self, methodName=''):
            """ Like synchronizeDetailView, but just dumps info about which
            blocks are currently shown.
            """
            def reNotifyInside(block, item, indent):
                blockName = getattr(block, 'blockName', '?')
                vis = block.isShown and '+' or '-'
                sizerVis = '_'
                widget = getattr(block, 'widget', None)
                if widget is not None:
                    sizer = widget.GetContainingSizer()
                    if sizer is not None:
                        sizerItem = sizer.GetItem(widget)
                        if sizerItem is None:
                            sizerVis = '?' # weird: didn't find a sizeritem for this widget?
                        else:
                            sizerVis = sizerItem.IsShown() and '+' or '-'
                logger.debug('%s%s%s %s' % (indent, vis, sizerVis, blockName))
                #if not isinstance(block, MenusAndToolbars.ToolbarItem):
                    #if block.isShown:
                        #print indent + '+' + block.blockName
                    #else:
                        #print indent + '-' + block.blockName
                try:
                    # process from the children up
                    for child in block.childrenBlocks:
                        reNotifyInside (child, item, indent + '  ')
                except AttributeError:
                    pass
            item = self.item
            try:
                itemDescription = item.itsKind.itsName + ' '
            except AttributeError:
                itemDescription = ''
            try:
                itemDescription += str (item)
            except:
                itemDescription += str (item.itsName)
            logger.debug(methodName + " " + itemDescription)
            logger.debug("-------------------------------")
            #print methodName + " " + itemDescription
            #print "-------------------------------"
            reNotifyInside(self, item, '')
            logger.debug(" ")
            #print

    def synchronizeWidget (self, **hints):
        item = self.item
        # logger.debug("DetailRoot.synchronizeWidget: %s", item)
        # If we're being synchronized on "None", it might be because we're really
        # displaying the None view, or because our selected item got 
        # deleted. Discern by looking at our TrunkParentBlock.
        if item is not None or hasattr(self.parentBlock, 'TPBSelectedItem'):
            super(DetailRootBlock, self).synchronizeWidget (**hints)
            self.synchronizeDetailView(item)
            if __debug__:
                dumpSynchronizeWidget = False
                if dumpSynchronizeWidget:
                    self.dumpShownHierarchy ('synchronizeWidget')
        else:
            # Yep, our item went away. Cheat and tell our parent to 
            # pick a different tree of blocks
            self.parentBlock.postEventByName('SelectItemsBroadcast', 
                                             {'items': []})

    def SelectedItems(self):
        """ 
        Return a list containing the item we're displaying. (This gets
        used for Send)
        """
        return [ self.item ]

    def onResynchronizeEvent(self, event):
        logger.debug("onResynchronizeEvent: resynching")
        self.synchronizeWidget()

    def onResynchronizeEventUpdateUI(self, event):
        pass

    # needed to work around bug 4091
    def onResynchronizeParentEvent(self, event):
        self.parentBlock.synchronizeWidget()

    def onSendShareItemEvent (self, event):
        """ Send or Share the current item. """
        # finish changes to previous selected item, then do it.
        Block.Block.finishEdits()
        super(DetailRootBlock, self).onSendShareItemEvent(event)
    
    def focus(self):
        """
        Put the focus into the Detail View
        """
        # Currently, just set the focus to the Title/Headline/Subject
        # Later we may want to support the "preferred" block for
        #  focus within a tree of blocks.
        titleBlock = self.findBlockByName('HeadlineBlock')
        if titleBlock:
            titleBlock.widget.SetFocus()
            titleBlock.widget.SelectAll()

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

        # The normal case: we have an item, so use its Kind
        # as the key.
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
        
        # Copy our stub block and move the new kids on(to) the block
        trunk = self._copyItem(self.trunkStub)
        trunk.childrenBlocks.extend([ block for position, path, block in decoratedSubtreeList ])
        return trunk
    
    def _getSubtrees(self):
        """
        Get a list of mappings from kind to subtree
        """
        # @@@ Note: we used to cache this here, but when we started
        # caching prebuilt detail views from detailblocks' installParcel, 
        # this list was getting built & cached before all parcels had been
        # loaded, so some subtrees weren't put into the list -- this broke
        # all the non-PIM items (flickr, feeds, amazon), bug 4433.
        # For now, we're going to iterItems every time we need the 
        # list; if this isn't performant, we'll build a refcollection at 
        # installParcel time and add an __init__ DetailTrunkSubtree to 
        # add all new ones to the refcollection (Andi says this would be faster).
        #try:
            #subtrees = self.subtreeList
        #except AttributeError:
            #subtrees = list(DetailTrunkSubtree.iterItems(self.itsView))
            #self.subtreeList = subtrees
        
        subtrees = list(DetailTrunkSubtree.iterItems(self.itsView))
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
        #logger.debug("DetailSynchronizer %s: onSetContentsEvent",
                     #getattr(self, 'blockName', '?'))
        self.setContentsOnBlock(event.arguments['item'])

    item = property(fget=ControlBlocks.getProxiedContentsItem, 
                    doc="Return the selected item, or None")

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
            #logger.debug("DetailSync.show %s: now %s",
                         #getattr(self, 'blockName', '?'),
                         #shouldShow and "visible" or "hidden")
            return True
        return False

    def whichAttribute(self):
        # define the attribute to be used: ours or our parent's
        return getattr(self, 'viewAttribute',
                       getattr(self.parentBlock, 'viewAttribute', u''))

    def attributesToMonitor(self):
        """
        Get the set of attributes that we'll monitor while rendered
        """
        return [ self.whichAttribute() ]

    def render(self):
        super(DetailSynchronizer, self).render()
        # Start monitoring the attributes that affect this block
        item = self.item
        if self.widget is not None and item is not None and \
           not item.isDeleted():
            attrsToMonitor = self.attributesToMonitor()
            if attrsToMonitor is not None:
                # Map the attributes to the real attributes they're based on
                # (this isn't a list comprehension because we're relying on the
                # list-flattening behavior provided by 'update')
                basedAttributes = set()
                for a in attrsToMonitor:
                    if a:
                        basedAttributes.update(item.getBasedAttributes(a))
                if len(basedAttributes):
                    #logger.debug("DetailSynchronizer (%s): Attaching monitors for %s",
                                 #getattr(self, 'blockName', '?'),
                                 #', '.join(basedAttributes))
                    for attr in basedAttributes:
                        Monitors.attach(self, 'onMonitoredValueChanged', 'set', attr)
                    self.widget.monitoredAttributes = basedAttributes

    def onDestroyWidget(self):
        # Stop monitoring
        monitoredAttributes = getattr(self.widget, 'monitoredAttributes', None)
        if monitoredAttributes is not None:
            #logger.debug("DetailSynchronizer (%s): Detaching monitors for %s", 
                         #getattr(self, 'blockName', '?'),
                         #', '.join(self.widget.monitoredAttributes))
            for attr in monitoredAttributes:
                Monitors.detach(self, 'onMonitoredValueChanged', 'set', attr)
        
        super(DetailSynchronizer, self).onDestroyWidget()

    def onMonitoredValueChanged(self, op, item, attribute):
        # Ignore notifications that aren't for us. (Yes, it's not ideal to have 
        # awareness of proxies here, but I'm expecting _lots_ of notifications, 
        # and this seems like the quickest way to reduce overhead, and seems
        # safer than a deeper '==' comparison.)
        ourItem = self.item
        if item in (ourItem, getattr(ourItem, 'proxiedItem', None)):            
            # It's for us - reload the widget
            logger.debug("DetailSynchronizer (%s): Monitor on %s fired; syncing.", 
                         self.blockName, attribute)
            # XXX put a monitor hint here
            self.synchronizeWidget()
            if self.synchronizeItemDetail(ourItem):
                self.detailRoot.relayoutSizer()

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
            theLabel = unicode(value)
        except AttributeError:
            theLabel = u""
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
       - a label (e.g. a StaticText with "Title:")
       - an attribute value (e.g. in an EditText with the value of item.title)
      
      it also handles visibility of the block, depending on if the attribute
      exists on the item or not
    """ 
    def synchronizeItemDetail(self, item):
        whichAttr = self.viewAttribute
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

    def OnDataChanged (self):
        # (this is how we find out about drag-and-dropped text changes!)
        self.saveValue()

    def OnFinishChangesEvent (self, event):
        self.saveValue(validate=True)

class MarkupBarBlock(DetailSynchronizer, MenusAndToolbars.Toolbar):
    """
      Markup Toolbar, for quick control over Items.
    Doesn't need to synchronizeItemDetail, because
    the individual ToolbarItems synchronizeItemDetail.
    """
    def onButtonPressedEvent (self, event):
        # Rekind the item by adding or removing the associated Mixin Kind
        Block.Block.finishEdits()
        tool = event.arguments['sender']
        item = self.item
        
        if not item or not self._isStampable(item):
            return
            
        mixinKind = tool.stampMixinKind()
        if not item.itsKind.isKindOf(mixinKind):
            operation = 'add'
        else:
            operation = 'remove'
        
        # Now change the kind and class of this item
        item.StampKind(operation, mixinKind)
        
        # notify the world that the item has a new kind.
        # This code can be removed when bug 4091 is fixed.
        self.postEventByName('ResyncDetailParent', {})

    def onButtonPressedEventUpdateUI(self, event):
        item = self.item
        enable = item is not None and self._isStampable(item) and \
               item.isAttributeModifiable('displayName')
        event.arguments ['Enable'] = enable

    def onTogglePrivateEvent(self, event):
        item = self.item            
        self.postEventByName("FocusTogglePrivate", {'items': [item]})
        tool = event.arguments['sender']
        self.widget.ToggleTool(tool.toolID, item.private) # in case the user canceled the dialog, reset markupbar buttons

    def onTogglePrivateEventUpdateUI(self, event):
        item = self.item            
        enable = item is not None and item.isAttributeModifiable('displayName')
        event.arguments ['Enable'] = enable

    def _isStampable(self, item):
        # for now, any ContentItem is stampable. This may change if Mixin rules/policy change
        return item.isItemOf(items.ContentItem.getKind(self.itsView))

class DetailStampButton (DetailSynchronizer, MenusAndToolbars.ToolbarItem):
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
               "Class/Kind mismatch for class %s, kind %s" % (item.__class__.__name__, item.itsKind.itsName)
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
        return TaskMixin

    def stampMixinKind(self):
        return TaskMixin.getKind(self.itsView)


class PrivateSwitchButtonBlock(DetailSynchronizer, MenusAndToolbars.ToolbarItem):
    """
      "Never share" button in the Markup Bar
    """
    def synchronizeItemDetail (self, item):
        # toggle this button to reflect the privateness of the selected item        
        # @@@DLD remove workaround for bug 1712 - ToogleTool doesn't work on mac when bar hidden
        if item.private:
            self.dynamicParent.show (True) # if we're toggling a button down, the bar must be shown
        self.dynamicParent.widget.ToggleTool(self.toolID, item.private)
        return False

class ReadOnlyIconBlock(DetailSynchronizer, MenusAndToolbars.ToolbarItem):
    """
      "Read Only" icon in the Markup Bar
    """
    def synchronizeItemDetail (self, item):
        # toggle this icon to reflect the read only status of the selected item
        app = wx.GetApp()

        if item.getSharedState() == ContentItem.READONLY:
            bitmap = app.GetImage(self.bitmap)
            self.widget.SetBitmap(bitmap)
        else:
            try:
                disabledBitmapName = self.disabledBitmap
            except AttributeError:
                disabledBitmap = wx.NullBitmap
            else:
                disabledBitmap = app.GetImage (disabledBitmapName)                
            self.widget.SetBitmap(disabledBitmap)
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

    def saveValue(self, validate=False):
        # save the user's edits into item's attibute
        item = self.item
        try:
            widget = self.widget
        except AttributeError:
            widget = None
        if item is not None and widget is not None:
            self.saveAttributeFromWidget(item, widget, validate=validate)
        
    def loadTextValue (self, item):
        # load the edit text from our attribute into the field
        if item is None:
            item = self.item
        if item is not None:
            widget = self.widget
            self.loadAttributeIntoWidget(item, widget)
    
    def onLoseFocus (self, event):
        # called when we get an event; to saves away the data and skips the event
        self.saveValue(validate=True)
        event.Skip()
        
    def onKeyPressed (self, event):
        # called when we get an event; to saves away the data and skips the event
        self.saveValue(validate = event.m_keyCode == wx.WXK_RETURN and self.lineStyleEnum != "MultiLine")
        event.Skip()
        
    def OnDataChanged (self):
        # event that an edit operation has taken place
        self.saveValue()

    def OnFinishChangesEvent (self, event):
        self.saveValue(validate=True)

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
            # Hack to set up whoFrom for Items with no value... like AbstractCollections
            # Can't set the whoFrom at creation time, because many start life at
            # system startup before the user account is setup.
            if item.itsKind.hasAttribute ('whoFrom'):
                try:
                    # Determine which kind of item to assign based on the
                    # types of the redirected-to attributes:
                    type = item.getAttributeAspect('whoFrom', 'type')
                    contactKind = pim.Contact.getKind(self.itsView)
                    if type is contactKind:
                        item.whoFrom = schema.ns("osaf.app",
                            self.itsView).currentContact.item
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
            value = messages.UNTITLED
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
        url, collectionName = MailSharing.getSharingHeaderInfo(self.item)
        statusBlock = wx.GetApp().mainFrame.GetStatusBar().blockItem
        statusBlock.setStatusMessage( _(u'Subscribing to collection...') )
        wx.Yield()

        # If this code is ever revived, it should call sharing.subscribe(),
        # rather than the following:
        ## share = sharing.Share(view=self.itsView)
        ## share.configureInbound(url)
        ## share.get()

        statusBlock.setStatusMessage( _(u'Subscribed to collection') )
    
        # @@@ Remove this when the sidebar autodetects new collections
        collection = share.contents
        mainView = application.Globals.views[0]
        assert (hasattr (collection, 'color'))
        schema.ns("osaf.app", self).sidebarCollection.add (collection)
        # Need to SelectFirstItem -- DJA

    def onAcceptShareEventUpdateUI(self, event):
        # If we're already sharing it, we should disable the button and change the text.
        enabled = True
        item = self.item
        try:
            url, collectionName = MailSharing.getSharingHeaderInfo(item)
            existingSharedCollection = sharing.findMatchingShare(self.itsView, url)
        except:
            enabled = True
        else:
            if existingSharedCollection is not None:
                self.widget.SetLabel(_("u(Already sharing this collection)"))
                enabled = False
        event.arguments['Enable'] = enabled

def getItemCollectionNames(item, justOne=False):
    """ 
    Get the names of collections that this item belongs to, or just
    the first one (which we use for visibility management) 
    """
    if (item is None or not hasattr(item, 'collections') 
        or item.collections.first() is None):
        return []

    item = getattr(item, 'proxiedItem', item)
    app = schema.ns('osaf.app', item.itsView)
    sidebarCollection = app.sidebarCollection
    allCollection = app.allCollection
    collectionList = []
    for coll in sidebarCollection:
        if coll is allCollection or not item in coll:
            continue
        if justOne:
            return [ coll.displayName ]
        collectionList.append(coll.displayName)
    collectionList.sort()
    return collectionList

class AppearsInAreaBlock(DetailSynchronizedContentItemDetail):
    """
    A block that holds a label, horizontal spacer, and static string 
    listing the collections this item belongs to (presented by the
    AppearsInAttributeEditor, below)
    """    
    def shouldShow(self, item):
        return len(getItemCollectionNames(self.detailRoot().item, True)) > 0

    def onMonitoredValueChanged(self, op, item, attribute):
        # Ignore notifications that aren't for us. (Yes, it's not ideal to have 
        # awareness of proxies here, but I'm expecting _lots_ of notifications, 
        # and this seems like the quickest way to reduce overhead, and seems
        # safer than a deeper '==' comparison.)
        ourItem = self.item
        if item in (ourItem, getattr(ourItem, 'proxiedItem', None)):            
            # It's for us - reload the widget
            haveCollections = len(getItemCollectionNames(ourItem, True)) > 0
            if haveCollections != self.isShown:
                # We need to change visibility; redo the whole detail view 
                # to relayout its sizer.
                #logger.debug("AppearsIn got notification; vis now %s" % haveCollections)
                self.detailRoot().synchronizeDetailView(ourItem)
            elif haveCollections:
                # We already have proper visibility: just update our content
                #logger.debug("AppearsIn got notification; updating value")
                self.synchronizeWidget()
            else:
                pass #logger.debug("AppearsIn got notification; ignoring")

class AppearsInAttributeEditor(StaticStringAttributeEditor):
    """ A read-only list of collections that this item appears in, for now. """
    def GetAttributeValue(self, item, attributeName):
        # @@@ I18N: FYI: I expect the label & names to be separate fields before too long...
        collectionNames = _(", ").join(getItemCollectionNames(item))
        # logger.debug("Returning new appearsin list: %s" % collectionNames)
        return _(u"Appears in: %(collectionNames)s") \
               % {'collectionNames': collectionNames }


# Classes to support CalendarEvent details - first, areas that show/hide
# themselves based on readonlyness and attribute values

class CalendarAllDayAreaBlock(DetailSynchronizedContentItemDetail):
    def shouldShow (self, item):
        return item.isAttributeModifiable('allDay')

class CalendarLocationAreaBlock(DetailSynchronizedContentItemDetail):
    def shouldShow (self, item):
        return item.isAttributeModifiable('location') \
               or hasattr(item, 'location')

class CalendarConditionalLabelBlock(StaticTextLabel):
    def shouldShow (self, item):
        return not item.allDay and \
               (item.isAttributeModifiable('startTime') \
                or not item.anyTime)
        
class CalendarTimeAEBlock (DetailSynchronizedAttributeEditorBlock):
    def shouldShow (self, item):
        return not item.allDay and \
               (item.isAttributeModifiable('startTime') \
                or not item.anyTime)

class CalendarReminderAreaBlock (DetailSynchronizedContentItemDetail):
    def shouldShow (self, item):
        return item.isAttributeModifiable('reminders') \
               or len(item.reminders) > 0

class CalendarTimeZoneSpacerBlock (StaticTextLabel):
    def shouldShow (self, item):
        return not (item.allDay or item.anyTime)

class CalendarTimeZoneAreaBlock (DetailSynchronizedContentItemDetail):
    def shouldShow (self, item):
        return not (item.allDay or item.anyTime)


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

class CalendarRecurrenceCustomSpacerBlock(DetailSynchronizer, ControlBlocks.StaticText):
    def shouldShow (self, item):
        return (recurrenceVisibility(item) & showCustom) != 0

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
            oldValue = getattr(item, attributeName, None)
            # Here, the ICUError covers ICU being unable to handle
            # the input value. ValueErrors can occur when I've seen ICU
            # claims to parse bogus  values like "06/05/0506/05/05" 
            #successfully, which causes fromtimestamp() to throw.)
            try:
                dateTimeValue = DateTimeAttributeEditor.shortDateFormat.parse(
                                    newValueString, referenceDate=oldValue)
            except ICUError, ValueError:
                self._changeTextQuietly(self.control, "%s ?" % newValueString)
                return

            # If this results in a new value, put it back.
            value = datetime.combine(dateTimeValue.date(), oldValue.timetz())
            
            if oldValue != value:
                if attributeName == 'endTime':
                    # Changing the end date or time such that it becomes 
                    # earlier than the existing start date+time will 
                    # change the start date+time to be the same as the 
                    # end date+time (that is, an @time event, or a 
                    # single-day anytime event if the event had already 
                    # been an anytime event).
                    if value < item.startTime:
                        item.startTime = value
                    item.endTime = value
                elif attributeName == 'startTime':
                    item.startTime = value
                else:
                    assert False, "this attribute editor is really just for " \
                                  "start or endtime"

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
        iAmStart = attributeName == 'startTime'
        changed = False
        forceReload = False
        if len(newValueString) == 0:
            # Clearing an event's start time (removing the value in it, causing 
            # it to show "HH:MM") will remove both time values (making it an 
            # anytime event).
            if iAmStart:
                if not item.anyTime:
                    item.anyTime = True
                    changed = True
            else:
                # Clearing an event's end time will make it an at-time event
                zeroTime = timedelta()
                if item.duration != zeroTime:
                    item.duration = zeroTime
                    changed = True
            forceReload = True
        else:
            # We have _something_; parse it.
            oldValue = getattr(item, attributeName)

            try:
                time = DateTimeAttributeEditor.shortTimeFormat.parse(
                    newValueString, referenceDate=oldValue)
            except ICUError, ValueError:
                self._changeTextQuietly(self.control, "%s ?" % newValueString)
                return

            # If we got a new value, put it back.
            value = datetime.combine(oldValue.date(), time.timetz())
            # Preserve the time zone!
            value = value.replace(tzinfo=oldValue.tzinfo)
            if item.anyTime or oldValue != value:
                # Something changed.                
                # Implement the rules for changing one of the four values:
                if item.anyTime:
                    # On an anytime event (single or multi-day; both times 
                    # blank & showing the "HH:MM" hint), entering a valid time 
                    # in either time field will set the other date and time 
                    # field to effect a one-hour event on the corresponding date. 
                    item.anyTime = False
                    if iAmStart:
                        item.startTime = value
                    else:
                        item.startTime = value - timedelta(hours=1)
                    item.duration = timedelta(hours=1)
                else:
                    if not iAmStart:
                        # Changing the end date or time such that it becomes 
                        # earlier than the existing start date+time will change 
                        # the start date+time to be the same as the end 
                        # date+time (that is, an @time event, or a single-day 
                        # anytime event if the event had already been an 
                        # anytime event).
                        if value < item.startTime:
                            item.startTime = value
                    setattr (item, attributeName, value)
                    item.anyTime = False
                changed = True
            
        if changed:
            self.AttributeChanged()
            
        if changed or forceReload:
            # Refresh the value in the control
            self.SetControlValue(self.control, 
                             self.GetAttributeValue(item, attributeName))

class ReminderAttributeEditor(ChoiceAttributeEditor):
    def GetControlValue (self, control):
        """ Get the reminder delta value for the current selection """        
        # @@@ i18n For now, assumes that the menu will be a number of minutes, 
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
                reminderChoice = (minutes == -1) and _(u"1 minute") or (_(u"%(numberOf)i minutes") % {'numberOf': -minutes})
                choiceIndex = control.FindString(reminderChoice)
                # If we can't find the choice, just show "None" - this'll happen if this event's reminder has been "snoozed"
                if choiceIndex == -1:
                    choiceIndex = 0 # the "None" choice
            control.Select(choiceIndex)

    def GetAttributeValue (self, item, attributeName):
        """ Get the value from the specified attribute of the item. """
        return item.reminderInterval

    def SetAttributeValue (self, item, attributeName, value):
        """ Set the value of the attribute given by the value. """
        if not self.ReadOnly((item, attributeName)) and \
           value != self.GetAttributeValue(item, attributeName):

            setattr(item, attributeName, value)
            self.AttributeChanged()

class RecurrenceAttributeEditor(ChoiceAttributeEditor):
    # These are the values we pass around; they're the same as the menu indices.
    # This is a list of the frequency enumeration names (defined in 
    # Recurrence.py's FrequencyEnum) in the order we present
    # them in the menu... plus "once" at the beginning and "custom" at the end.
    # Note that biweekly is not, in fact, a valid FrequencyEnum frequency, it's a
    # special case.
    # These should not be localized!
    menuFrequencies = [ 'once', 'daily', 'weekly', 'biweekly', 'monthly', 'yearly', 'custom']
    onceIndex = menuFrequencies.index('once')
    customIndex = menuFrequencies.index('custom')
    biweeklyIndex = menuFrequencies.index('biweekly')
    weeklyIndex = menuFrequencies.index('weekly')
    
    @classmethod
    def mapRecurrenceFrequency(theClass, item):
        """ Map the frequency of this item to one of our menu choices """
        if item.isCustomRule(): # It's custom if it says it is.
            return RecurrenceAttributeEditor.customIndex
        # Otherwise, try to map its frequency to our menu list
        try:
            rrule = item.rruleset.rrules.first() 
            freq = rrule.freq
            # deal with biweekly special case
            if freq == 'weekly' and rrule.interval == 2:
                return RecurrenceAttributeEditor.biweeklyIndex
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
            # If the old choice was Custom, make sure the user really wants to
            # lose the custom setting
            if oldChoice == RecurrenceAttributeEditor.customIndex:
                caption = _(u"Discard custom recurrence?")
                msg = _(u"The custom recurrence rule on this event will be lost "
                        "if you change it, and you won't be able to restore it."
                        "\n\nAre you sure you want to do this?")
                if not Util.yesNo(wx.GetApp().mainFrame, caption, msg):
                    # No: Reselect 'custom' in the menu
                    self.SetControlValue(control, oldChoice)
                    return

            self.SetAttributeValue(self.item, self.attributeName, 
                                   newChoice)

    def GetAttributeValue (self, item, attributeName):
        index = RecurrenceAttributeEditor.mapRecurrenceFrequency(item)
        return index
    
    def SetAttributeValue (self, item, attributeName, value):
        """ Set the value of the attribute given by the value. """
        assert value != RecurrenceAttributeEditor.customIndex
        # Changing the recurrence period on a non-master item could delete 
        # this very 'item'; if it does, we'll bypass the attribute-changed 
        # notification below...
        if value == RecurrenceAttributeEditor.onceIndex:
            item.removeRecurrence()
        else:
            interval = 1
            if value == RecurrenceAttributeEditor.biweeklyIndex:
                interval = 2
                value = RecurrenceAttributeEditor.weeklyIndex
            duFreq = Recurrence.toDateUtilFrequency(\
                RecurrenceAttributeEditor.menuFrequencies[value])
            rruleset = Recurrence.RecurrenceRuleSet(None, view=item.itsView)
            rruleset.setRuleFromDateUtil(Recurrence.dateutil.rrule.rrule(duFreq,
                                         interval=interval))
            until = item.getLastUntil()
            if until is not None:
                rruleset.rrules.first().until = until
            elif hasattr(rruleset.rrules.first(), 'until'):
                del rruleset.rrules.first().until
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
        
        # If the user removed the string, remove the attribute.
        newValueString = valueString.replace('?','').strip()
        if len(newValueString) == 0 and hasattr(item, 'until'):
            del item.until
        else:
            super(RecurrenceEndsAttributeEditor, self).\
                 SetAttributeValue(item, attributeName, valueString)

class HTMLDetailArea(DetailSynchronizer, ControlBlocks.ItemDetail):
    def synchronizeItemDetail(self, item):
        self.selection = item
        # this ensures that getHTMLText() gets called appropriately on the derived class

        self.synchronizeWidget()

    def getHTMLText(self, item):
        return u"<html><body>" + item + u"</body></html>"


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

