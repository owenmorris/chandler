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
import osaf.contentmodel.contacts.Contacts as Contacts
import application.dialogs.Util as Util
import repository.item.Query as Query
import mx.DateTime as DateTime
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
        self.finishSelectionChanges () # finish changes to previous selected item 
        super(DetailRoot, self).onSelectionChangedEvent(notification)
        item= self.selectedItem()
        assert item is notification.data['item'], "can't track selection in DetailRoot.onSelectionChangedEvent"
        self.synchronizeWidget()
        if __debug__:
            dumpSelectionChanged = False
            if dumpSelectionChanged:
                self.dumpShownHierarchy ('onSelectionChangedEvent')

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
        self.synchronizeDetailView(item)
        super(DetailRoot, self).synchronizeWidget ()
        if __debug__:
            dumpSynchronizeWidget = False
            if dumpSynchronizeWidget:
                self.dumpShownHierarchy ('synchronizeWidget')
        
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
        # preflight the send/share request
        # mail items and collections need their recievers set up
        try:
            whoTo = item.who
        except AttributeError:
            whoTo = []
        if len (whoTo) == 0:
            if isinstance (item, ItemCollection.ItemCollection):
                message = _('Please specify who to share this collection with in the "to" field.')
            elif isinstance (item, Mail.MailMessageMixin):
                message = _('Please specify who to send this message to in the "to" field.')
            else:
                message = _('Please specify receivers.')
            Util.ok(Globals.wxApplication.mainFrame,
             _("No Receivers"), message)
        else:
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

    def finishSelectionChanges (self):
        """ 
          Need to finish any changes to the selected item
        that are in progress.
        """
        focusBlock = self.getFocusBlock()
        try:
            focusBlock.saveFocusData()
        except AttributeError:
            pass

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
            widget.Show (shouldShow)
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
        """

        # get the user's address strings into a list
        addresses = addressesString.split(',')

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
    def shouldShow (self, item):
        # only shown for non-CalendarEventMixin kinds
        calendarMixinKind = Calendar.CalendarParcel.getCalendarEventMixinKind()
        return not item.isItemOf (calendarMixinKind)

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
        try:
            kindName = item.itsKind.displayName
        except AttributeError:
            kindName = item.itsKind.itsName
        kindName = '(' + kindName +')'
        return kindName
        
class StaticRedirectAttribute (StaticTextLabel):
    """
      Static Text that displays the name of the selected item's Attribute
    """
    # map internal attribute names into nicer display strings
    # DLDTBD - display mapping should come out of the repository
    displayMapping = {"displayName": "title",
                      "fromAddress": "from",
                      "toAddress": "to",
                      }
                      
    def shouldShow (self, item):
        contactKind = Contacts.ContactsParcel.getContactKind ()
        if item is None or item.isItemOf (contactKind):
            return False
        return True

    def staticTextLabelValue (self, item):
        redirectName = self.whichAttribute ()
        try:
            redirectAttr = item.getAttributeAspect(redirectName, 'redirectTo')
        except AttributeError:
            redirectAttr = redirectName
        if redirectAttr is None:
            redirectAttr = redirectName
        # lookup better names for display of some attributes
        try:
            redirectAttr = self.displayMapping[redirectAttr]
        except KeyError:
            pass
        if len (redirectAttr) > 0:
            redirectAttr = redirectAttr + _(' ')
        return redirectAttr

class LabeledTextAttributeBlock (ControlBlocks.ContentItemDetail):
    def synchronizeItemDetail(self, item):
        whichAttr = self.selectedItemsAttribute
        contactKind = Contacts.ContactsParcel.getContactKind ()
        if item is None or item.isItemOf (contactKind):
            self.isShown = False
        else:
            self.isShown = item.itsKind.hasAttribute(whichAttr)
        self.synchronizeWidget()

    def shouldShow (self, item):
        contactKind = Contacts.ContactsParcel.getContactKind ()
        if item is None or item.isItemOf (contactKind):
            return False
        return True

class EmailAddressBlock (DetailSynchronizer, LabeledTextAttributeBlock):
    def shouldShow (self, item):
        # if the item is a Contact, we should show ourself
        contactKind = Contacts.ContactsParcel.getContactKind ()
        shouldShow = item.isItemOf (contactKind)
        return shouldShow

def ItemCollectionOrMailMessageMixin (item):
    # if the item is a MailMessageMixin, or an ItemCollection,
    # then return True
    mailKind = Mail.MailParcel.getMailMessageMixinKind ()
    isCollection = isinstance (item, ItemCollection.ItemCollection)
    isOneOrOther = isCollection or item.isItemOf (mailKind)
    return isOneOrOther

class ToAndFromBlock (DetailSynchronizer, LabeledTextAttributeBlock):
    def shouldShow (self, item):
        # if the item is a MailMessageMixin, or an ItemCollection,
        # then we should show ourself
        return ItemCollectionOrMailMessageMixin (item)

class StaticToFromText (StaticTextLabel):
    def shouldShow (self, item):
        # if the item is a MailMessageMixin, or an ItemCollection,
        # then we should show ourself
        return ItemCollectionOrMailMessageMixin (item)

    def staticTextLabelValue (self, item):
        label = self.title + _(' ')
        return label

class MarkupBar (DetailSynchronizer, DynamicContainerBlocks.Toolbar):
    """   
      Markup Toolbar, for quick control over Items.
    Doesn't need to synchronizeItemDetail, because
    the individual ToolbarItems synchronizeItemDetail.
    """
    def shouldShow (self, item):
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
    
    def saveFocusData (self):
        # called to save away the data in the UI focus block
        self.saveTextValue()
        
    def onLoseFocus (self, event):
        # called when we lose focus, to save away the data
        self.saveFocusData()
        event.Skip()
        
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

        # remember the old value for nice change detection
        oldWhoString = item.ItemWhoString ()

        # parse the addresses and get/create/validate
        processedAddresses, validAddresses = self.parseEmailAddresses (item, toFieldString)

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
        widget.SetValue (processedAddresses)

    def loadAttributeIntoWidget (self, item, widget):
        whoString = item.ItemWhoString ()
        widget.SetValue (whoString)

    def shouldShow (self, item):
        return ItemCollectionOrMailMessageMixin (item)

class FromEditField (EditTextAttribute):
    """Edit field containing the sender's contact"""
    def shouldShow (self, item):
        return ItemCollectionOrMailMessageMixin (item)

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
            value = 'untitled'
        widget.SetValue(value)

class EditHeadlineRedirectAttribute (EditRedirectAttribute):
    """
    An attribute-based edit field
    Doesn't show for contacts.
    """
    def shouldShow (self, item):
        # don't show if the item is a Contact
        contactKind = Contacts.ContactsParcel.getContactKind ()
        shouldShow = not item.isItemOf (contactKind)
        return shouldShow

class SendShareButton (DetailSynchronizer, ControlBlocks.Button):
    def shouldShow (self, item):
        # if the item is a MailMessageMixin, we should show ourself
        shouldShow = item.isItemOf(Mail.MailParcel.getMailMessageMixinKind())
        # if the item is a collection, we should show ourself
        shouldShow = shouldShow or isinstance (item, ItemCollection.ItemCollection)
        return shouldShow

    def synchronizeItemDetail (self, item):
        # if the button should be visible, enable/disable
        # changed for 0.4 - always enabled to avoid user confusion.
        if item is not None and self.shouldShow (item):
            shouldEnable = True
            if isinstance (item, ItemCollection.ItemCollection):
                # collection: label should read "Notify"
                label = "Notify"
                # change the button label if the collection is already shared
                try:
                    renotify = Sharing.isShared (item)
                except AttributeError:
                    pass
                else:
                    if renotify:
                        label = "Renotify"
            else:
                # not a collection, so it's probably Mail
                label = "Send"
                try:
                    dateSent = item.dateSent
                except AttributeError:
                    dateSent = None
                if dateSent is not None:
                    label = "Sent"
            self.widget.Enable (shouldEnable)
            self.widget.SetLabel (label)
        return super (SendShareButton, self).synchronizeItemDetail (item)

"""
Classes to support Contact details
"""

class ContactFullNameBlock (DetailSynchronizer, LabeledTextAttributeBlock):
    def shouldShow (self, item):
        # if the item is a Contact, we should show ourself
        contactKind = Contacts.ContactsParcel.getContactKind ()
        shouldShow = item.isItemOf (contactKind)
        return shouldShow

class ContactFullNameEditField (EditRedirectAttribute):
    """
    An attribute-based edit field for contactName:fullName
    The actual value is stored in an contactName object.
    """
    def saveAttributeFromWidget(self, item, widget):
        contactName = item.getAttributeValue (self.whichAttribute())
        widgetString = widget.GetValue()
        contactName.setAttributeValue('fullName', widgetString)
        names = widgetString.split (' ')
        if len (names) > 0:
            contactName.firstName = names[0]
        if len (names) > 1:
            contactName.lastName = names[-1]
        # put the fullName into any emailAddress objects connected to this item.
        try:
            item.homeSection.fullName = widgetString
            item.homeSection.emailAddress.fullName = widgetString
        except AttributeError:
            pass
        try:
            item.workSection.fullName = widgetString
            item.workSection.emailAddress.fullName = widgetString
        except AttributeError:
            pass


    def loadAttributeIntoWidget(self, item, widget):
        value = ''
        try:
            contactName = item.getAttributeValue (self.whichAttribute())
            value = contactName.getAttributeValue ('emailAddress')
        except AttributeError:
            pass
        if value == '':
            value = item.ItemWhoString ()
        widget.SetValue(value)

    def shouldShow (self, item):
        # if the item is a Contact, we should show ourself
        contactKind = Contacts.ContactsParcel.getContactKind ()
        shouldShow = item.isItemOf (contactKind)
        return shouldShow

class StaticEmailAddressAttribute (StaticRedirectAttribute):
    """
      Static Text that displays the name of the selected item's Attribute.
    Customized for EmailAddresses
    """
    def staticTextLabelValue (self, item):
        label = self.title + _(' ')
        return label

    def shouldShow (self, item):
        # if the item is a Contact, we should show ourself
        contactKind = Contacts.ContactsParcel.getContactKind ()
        shouldShow = item.isItemOf (contactKind)
        return shouldShow

class EditEmailAddressAttribute (EditRedirectAttribute):
    """
    An attribute-based edit field for email addresses
    The actual value is stored in an emailaddress 'section' object
    for home or work.
    """
    def shouldShow (self, item):
        # if the item is a Contact, we should show ourself
        contactKind = Contacts.ContactsParcel.getContactKind ()
        shouldShow = item.isItemOf (contactKind)
        return shouldShow

    def saveAttributeFromWidget(self, item, widget):
        section = item.getAttributeValue (self.whichAttribute())
        widgetString = widget.GetValue()
        processedAddresses, validAddresses = self.parseEmailAddresses (item, widgetString)
        section.setAttributeValue('emailAddresses', validAddresses)
        for address in validAddresses:
            address.fullName = section.fullName
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

"""
Classes to support CalendarEvent details
"""
class CalendarEventBlock (DetailSynchronizer, LabeledTextAttributeBlock):
    def shouldShow (self, item):
        # only shown for CalendarEventMixin kinds
        calendarMixinKind = Calendar.CalendarParcel.getCalendarEventMixinKind()
        return item.isItemOf (calendarMixinKind)

class StaticTimeAttribute (StaticTextLabel):
    def shouldShow (self, item):
        # only shown for CalendarEventMixin kinds
        calendarMixinKind = Calendar.CalendarParcel.getCalendarEventMixinKind()
        shouldShow = item.isItemOf (calendarMixinKind)
        return shouldShow

    def staticTextLabelValue (self, item):
        timeLabel = self.title + _(' ')
        return timeLabel


class EditTimeAttribute (EditRedirectAttribute):
    """
    An attribute-based edit field for Time Values
    Our parent block knows which attribute we edit.
    """
    timeFormat = '%Y-%m-%d %I:%M %p'
    def shouldShow (self, item):
        # only shown for CalendarEventMixin kinds
        calendarMixinKind = Calendar.CalendarParcel.getCalendarEventMixinKind()
        return item.isItemOf (calendarMixinKind)

    def saveAttributeFromWidget(self, item, widget):
        """"
          Update the attribute from the user edited string in the widget.
        """
        dateString = widget.GetValue().strip('?')
        try:
            # convert to Date/Time
            theDate = DateTime.Parser.DateTimeFromString (dateString)
        except ValueError: 
            pass
        except DateTime.RangeError:
            pass
        try:
            # save the new Date/Time
            whichTimeAttribute = self.whichAttribute()
            if 'start' in whichTimeAttribute:
                item.ChangeStart (theDate)
            else:
                item.setAttributeValue(whichTimeAttribute, theDate)
        except:
            # DLDTBD figure out reasonable exceptions to catch during conversion
            dateString = dateString + '?'
        else:
            dateString = theDate.strftime (self.timeFormat)

        # redisplay the processed Date/Time in the widget
        widget.SetValue(dateString)


    def loadAttributeIntoWidget(self, item, widget):
        """"
          Update the widget display based on the value in the attribute.
        """
        try:
            dateTime = item.getAttributeValue(self.whichAttribute())
        except AttributeError:
            value = ''
        else:
            value = dateTime.strftime (self.timeFormat)
        widget.SetValue (value)

class StaticDurationAttribute (StaticTextLabel):
    """
      Static Text that displays the name of the selected item's Attribute
    """
    def shouldShow (self, item):
        # only shown for CalendarEventMixin kinds
        calendarMixinKind = Calendar.CalendarParcel.getCalendarEventMixinKind()
        return item.isItemOf (calendarMixinKind)

    def staticTextLabelValue (self, item):
        durationLabel = self.title + _(' ')
        return durationLabel

class EditDurationAttribute (EditRedirectAttribute):
    """
    An attribute-based edit field for Duration Values
    Our parent block knows which attribute we edit.
    """
    durationFormat = '%I:%M'
    def shouldShow (self, item):
        # only shown for CalendarEventMixin kinds
        calendarMixinKind = Calendar.CalendarParcel.getCalendarEventMixinKind()
        return item.isItemOf (calendarMixinKind)

    def saveAttributeFromWidget(self, item, widget):
        """"
          Update the attribute from the user edited string in the widget.
        """
        durationString = widget.GetValue().strip('?')
        try:
            # convert to Date/Time
            theDuration = DateTime.Parser.DateTimeDeltaFromString (durationString)
        except ValueError: 
            pass
        try:
            # save the new duration
            item.duration = theDuration
        except:
            # DLDTBD figure out reasonable exceptions to catch during conversion
            durationString = dateString + '?'
        else:
            durationString = theDuration.strftime (self.durationFormat)

        # redisplay the processed Date/Time in the widget
        widget.SetValue(durationString)


    def loadAttributeIntoWidget(self, item, widget):
        """"
          Update the widget display based on the value in the attribute.
        """
        try:
            theDuration = item.duration
        except AttributeError:
            value = '?'
        else:
            value = theDuration.strftime (self.durationFormat)
        widget.SetValue (value)


