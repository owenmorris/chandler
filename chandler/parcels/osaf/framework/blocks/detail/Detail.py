__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import application.Globals as Globals
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.DynamicContainerBlocks as DynamicContainerBlocks
import osaf.framework.blocks.ControlBlocks as ControlBlocks
import osaf.framework.sharing.Sharing as Sharing
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.calendar.Calendar as Calendar
import repository.item.Query as Query
import wx

"""
Detail.py
Classes for the ContentItem Detail View
"""

class DetailParcel (application.Parcel.Parcel):
    pass

class DetailRoot (ControlBlocks.SelectionContainer):
    """
      Root of the Detail View.
    """
    def onSelectionChangedEvent (self, notification):
        """
          We have an event boundary inside us, which keeps all
        the events sent between blocks of the Detail View to
        ourselves.
          When we get a SelectionChanged event, we jump across
        the event boundary and call synchronizeItemDetail on each
        block to give it a chance to synchronize on the details of
        the Item.  
          Notify container blocks before their children.
        """
        super(DetailRoot, self).onSelectionChangedEvent(notification)
        item= self.selectedItem()
        assert item is notification.data['item'], "can't track selection in DetailRoot.onSelectionChangedEvent"
        self.synchronizeWidget()

    def synchronizeDetailView(self, item):
        """
          We have an event boundary inside us, which keeps all
        the events sent between blocks of the Detail View to
        ourselves.
          When we get a SelectionChanged event, we jump across
        the event boundary and call synchronizeItemDetail on each
        block to give it a chance to synchronize on the details of
        the Item.  
          Notify container blocks before their children.
          
          DLDTBD - find a better way to broadcast inside my boundary.
        """
        def reNotifyInside(block, item):
            notifyParent = False
            try:
                # process from the children up
                for child in block.childrenBlocks:
                    notify = reNotifyInside (child, item)
                    notifyParent = notifyParent or notify
            except AttributeError:
                pass
            try:
                notify = block.synchronizeItemDetail(item)
                notifyParent = notifyParent or notify
            except AttributeError:
                if notifyParent:
                    block.synchronizeWidget()
            return notifyParent

        children = self.childrenBlocks
        for child in children:
            child.isShown = item is not None
            reNotifyInside(child, item)
    
    def synchronizeWidget (self):
        item= self.selectedItem()
        self.synchronizeDetailView(item)
        super(DetailRoot, self).synchronizeWidget ()
        
    def onDestroyWidget (self):
        # Hack - DLDTBD - remove when wxWidgets issue is resolved.
        # set ourself to be shown, to work around Windows DetailView garbage problem.
        def showReentrant (block):
            block.isShown = True
            for child in block.childrenBlocks:
                showReentrant (child)
        super(DetailRoot, self).onDestroyWidget ()
        showReentrant (self)

    def onSendShareItemEvent (self, notification):
        item = self.selectedItem()
        item.shareSend() # tell the ContentItem to share/send itself.

    def resynchronizeDetailView (self):
        # Called to resynchronize the whole Detail View
        # Called when an itemCollection gets new sharees,
        #  because the Notify button should then be enabled.
        # DLDTBD - devise a block-dependency-notification scheme.
        item= self.selectedItem()
        self.synchronizeDetailView(item)

    """
    This is a copy of the global NULL event
    We need to have a copy here, because of limitations
    in our XLM parsing and template copy mechanism.
    It's a long story.  
    Some day we should remove this
    code and use the global event in Main instead.
    """
    def onNULLEvent (self, notification):
        """ The NULL Event handler """
        pass

    def onNULLEventUpdateUI (self, notification):
        """ The NULL Event is always disabled """
        notification.data ['Enable'] = False

class DetailSynchronizer(object):
    """
      Mixin class that handles synchronizeWidget and
    the SelectionChanged event by calling synchronizeItemDetail.
    Most client classes will only have to implement
    synchronizeItemDetail.
    """
    def selectedItem (self):
        # delegate to our parent until we get outside our event boundary
        return self.parentBlock.selectedItem()

    def resynchronizeDetailView (self):
        # delegate to our parent until we get to the DetailRoot.
        self.parentBlock.resynchronizeDetailView ()

    def relayoutParents (self):
        # relayout the parent block
        block = self
        while (not block.eventBoundary and block.parentBlock):
            block = block.parentBlock
            block.synchronizeWidget()

    def synchronizeItemDetail (self, item):
        # if there is an item, we should show ourself, else hide
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
            widget.Show (shouldShow)
            self.isShown = shouldShow
            return True
        return False

    def whichAttribute(self):
        # define the attribute to be used
        return self.parentBlock.selectedItemsAttribute

    def nonEditableIfSharedCollection (self, item):
        # make editable/noneditable based on shared collection status
        if isinstance (item, ItemCollection.ItemCollection):
            shouldAllowEdits = not Sharing.isShared (item)
            self.widget.SetEditable (shouldAllowEdits)

class StaticTextLabel (DetailSynchronizer, ControlBlocks.StaticText):
    def staticTextLabelValue (self, item):
        """ Override to provide the value of the static text label """
        raise NotImplementedError, "%s.staticTextLabelValue()" % (type(self))

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

class DateTimeBlock (StaticTextLabel):
    """
    Date and Time associated with the Content Item
    Currently this is static text, but soon it will need to be editable
    """
    def staticTextLabelValue (self, item):
        """
          return the item's date.
        """
        try:
            theDate = item.date # get the redirected date attribute
        except AttributeError:
            theDate = "No date specified"
        else:
            theDate = str(theDate)
        return theDate

class KindLabel (StaticTextLabel):
    """Shows the Kind of the Item as static text"""
    def staticTextLabelValue (self, item):
        """
          Display the item's Kind in the wxWidget.
        """
        return item.itsKind.displayName
        
class StaticRedirectAttribute (StaticTextLabel):
    """
      Static Text that displays the name of the selected item's Attribute
    """
    def staticTextLabelValue (self, item):
        redirectName = self.whichAttribute ()
        redirectAttr = item.getAttributeAspect(redirectName, 'redirectTo')
        if redirectAttr is None:
            redirectAttr = '  '
        else:
            redirectAttr = ' ' + redirectAttr + ': '
        return redirectAttr

class LabeledTextAttributeBlock (ControlBlocks.ContentItemDetail):
    def synchronizeItemDetail(self, item):
        whichAttr = self.selectedItemsAttribute
        if item is None:
            self.isShown = False
        else:
            self.isShown = item.itsKind.hasAttribute(whichAttr)
        self.synchronizeWidget()

class MarkupBar (DetailSynchronizer, DynamicContainerBlocks.Toolbar):
    """   
      Markup Toolbar, for quick control over Items.
    Doesn't need to synchronizeItemDetail, because
    the individual ToolbarItems synchronizeItemDetail.
    """
    def shouldShow (self, item):
        if item is None:
            return False
        # if the item is a collection, we should not show ourself
        shouldShow = not isinstance (item, ItemCollection.ItemCollection)
        return shouldShow

    def onButtonPressed (self, notification):
        # Rekind the item by adding or removing the associated Mixin Kind
        tool = notification.data['sender']
        item = self.selectedItem()
        isANoteKind = item.isItemOf(ContentModel.ContentModel.getNoteKind())
        if not isANoteKind:
            return
        if item is not None:
            mixinKind = tool.stampMixinKind()
            if self.widget.GetToolState(tool.toolID):
                operation = 'add'
            else:
                operation = 'remove'
            item.StampKind(operation, mixinKind)
            # notify the world that the item has a new kind.
            block = self
            while block.eventBoundary == False:
                block = block.parentBlock
            block.parentBlock.synchronizeWidget()

    def onButtonPressedUpdateUI (self, notification):
        item = self.selectedItem()
        if item is not None:
            enable = item.isItemOf(ContentModel.ContentModel.getNoteKind())
        else:
            enable = False
        notification.data ['Enable'] = enable

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
        self.dynamicParent.widget.ToggleTool(self.toolID, shouldToggleBasedOnKind)
        return False

class MailMessageButton (DetailStampButton):
    """
      Mail Message Stamping button in the Markup Bar
    """
    def stampMixinClass(self):
        return Mail.MailMessageMixin
    
    def stampMixinKind(self):
        return Mail.MailParcel.getMailMessageMixinKind()
    
class CalendarStamp (DetailStampButton):
    """
      Calendar button in the Markup Bar
    """
    def stampMixinClass(self):
        return Calendar.CalendarEventMixin

    def stampMixinKind(self):
        return Calendar.CalendarParcel.getCalendarEventMixinKind()

class TaskStamp (DetailStampButton):
    """
      Task button in the Markup Bar
    """
    def stampMixinClass(self):
        return Task.TaskMixin

    def stampMixinKind(self):
        return Task.TaskParcel.getTaskMixinKind()

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
        return widget

    def onKeyUp (self, event):
        self.saveTextValue()

    def saveTextValue (self):
        # save the user's edits into item's attibute
        item = self.selectedItem()
        widget = self.widget
        if item and widget:
            self.saveAttributeFromWidget(item, widget)
        
    def loadTextValue (self, item):
        # load the edit text from our attribute into the field
        if not item:
            item = self.selectedItem()
        if item:
            widget = self.widget
            self.loadAttributeIntoWidget(item, widget)
        
    def onLoseFocus (self, notification):
        # called when we lose focus, to save away the text
        self.saveTextValue()
        
    def OnDataChanged (self):
        # Notification that an edit operation has taken place
        self.saveTextValue()

    def synchronizeItemDetail (self, item):
        self.loadTextValue(item)
        return super(EditTextAttribute, self).synchronizeItemDetail(item)
            
    def saveAttributeFromWidget (self, item, widget):  
       # subclasses need to override this method
       raise NotImplementedError, "%s.SaveAttributeFromWidget()" % (type(self))

    def loadAttributeIntoWidget (self, item, widget):  
       # subclasses need to override this method
       raise NotImplementedError, "%s.LoadAttributeIntoWidget()" % (type(self))

class NoteBody (EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def shouldShow (self, item):
        if item is None:
            return False
        # need to show even if there is no value, so we test
        # the kind to see if it knows about the attribute.
        knowsBody = item.itsKind.hasAttribute("body")
        return knowsBody

    def saveAttributeFromWidget (self, item, widget):  
        textType = item.getAttributeAspect('body', 'type')
        widgetText = widget.GetValue()
        if widgetText:
            item.body = textType.makeValue(widgetText)
        
    def loadAttributeIntoWidget (self, item, widget):  
        if item.hasAttributeValue("body"):
            # get the character string out of the Text LOB
            noteBody = item.ItemBodyString ()
            widget.SetValue(noteBody)
        else:
            widget.Clear()

class ToEditField (EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def saveAttributeFromWidget(self, item, widget):  
        toFieldString = widget.GetValue()

        # get the user's address strings into a list
        addresses = toFieldString.split(',')

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

        # remember the old value for nice change detection
        oldWhoString = item.ItemWhoString ()

        # reassign the list to the attribute
        try:
            item.who = validAddresses
        except:
            pass

        # Detect changes from none to some, and resynchronizeDetailView
        #  so we can reenable the Notify button when sharees are added.
        if isinstance (item, ItemCollection.ItemCollection):
            whoString = item.ItemWhoString ()
            oneEmpty = len (whoString) == 0 or len (oldWhoString) == 0
            oneOK = len (whoString) > 0 or len (oldWhoString) > 0
            if oneEmpty and oneOK:
                self.resynchronizeDetailView ()

        # redisplay the processed addresses in the widget
        widget.SetValue (', '.join (processedAddresses))

    def loadAttributeIntoWidget (self, item, widget):
        whoString = item.ItemWhoString ()
        widget.SetValue (whoString)

        # also update editability based on shared collection status
        self.nonEditableIfSharedCollection (item)

class FromEditField (EditTextAttribute):
    """Edit field containing the sender's contact"""
    def saveAttributeFromWidget(self, item, widget):  
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
            # Can't set the whoFrom at creation time, because many start life in
            # XML before the user account is setup.
            if item.itsKind.hasAttribute ('whoFrom'):
                meAddress = item.getCurrentMeEmailAddress ()
                if meAddress is not None:
                    item.whoFrom = meAddress

        try:
            whoString = item.ItemWhoFromString ()
        except AttributeError:
            whoString = ''
        widget.SetValue (whoString)

class EditRedirectAttribute (EditTextAttribute):
    """
    An attribute-based edit field
    Our parent block knows which attribute we edit.
    """
    def saveAttributeFromWidget(self, item, widget):
        item.setAttributeValue(self.whichAttribute(), widget.GetValue())

    def loadAttributeIntoWidget(self, item, widget):
        try:
            value = item.getAttributeValue(self.whichAttribute())
        except AttributeError:
            value = ''
        widget.SetValue(value)

        # also update editablility based on shared collection status
        self.nonEditableIfSharedCollection (item)

class SendShareButton (DetailSynchronizer, ControlBlocks.Button):
    def shouldShow (self, item):
        if item is None:
            return False
        # if the item is a MailMessageMixin, we should show ourself
        shouldShow = item.isItemOf(Mail.MailParcel.getMailMessageMixinKind())
        # if the item is a collection, we should show ourself
        shouldShow = shouldShow or isinstance (item, ItemCollection.ItemCollection)
        return shouldShow

    def synchronizeItemDetail (self, item):
        # if the button should be visible, enable/disable
        if self.shouldShow (item):
            if isinstance (item, ItemCollection.ItemCollection):
                # collection: label should read "Notify"
                label = "Notify"
                # disable this button if the collection is already shared
                try:
                    shouldEnable = not Sharing.isShared (item)
                except AttributeError:
                    shouldEnable = True
                else:
                    if not shouldEnable:
                        label = "Shared"
                # disable the button if no sharees
                try:
                    sharees = item.sharees
                except AttributeError:
                    sharees = []
                shouldEnable = shouldEnable and len (sharees) > 0
            else:
                # not a collection, so it's probably Mail
                label = "Send"
                shouldEnable = True
                try:
                    dateSent = item.dateSent
                except AttributeError:
                    dateSent = None
                if dateSent is not None:
                    label = "Sent"
                    shouldEnable = False
            self.widget.Enable (shouldEnable)
            self.widget.SetLabel (label)
        return super (SendShareButton, self).synchronizeItemDetail (item)



