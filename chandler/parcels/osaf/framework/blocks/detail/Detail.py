__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application
import application.Globals as Globals
import osaf.framework.blocks.Block as Block
import osaf.framework.blocks.DynamicContainerBlocks as DynamicContainerBlocks
import osaf.framework.blocks.ControlBlocks as ControlBlocks
import repository.persistence.XMLRepositoryView as XMLRepositoryView
import osaf.contentmodel.mail.Mail as Mail
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.calendar.Calendar as Calendar
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.contacts.Contacts as Contacts
import wx

"""
Detail.py
Classes for the ContentItem Detail View
"""

class DetailParcel (application.Parcel.Parcel):
    pass

class DetailRoot (ControlBlocks.ContentItemDetail):
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
        self.synchronizeDetailView(item)

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
            try:
                block.synchronizeItemDetail(item)
            except AttributeError:
                pass
            try:
                for child in block.childrenBlocks:
                    reNotifyInside(child, item)
            except AttributeError:
                pass
        reNotifyInside(self, item)
    
    def synchronizeWidget (self):
        super(DetailRoot, self).synchronizeWidget ()
        item= self.selectedItem()
        self.synchronizeDetailView(item)
        
class DetailTrunk(ControlBlocks.ContentItemDetail):
    """
      First Child of the Detail Root.
    """
    def selectedItem (self):
        # return the ContentItem being viewed
        return self.parentBlock.selectedItem()

class DetailSyncronizer(object):
    """
      Mixin class that handles synchronizeWidget and
    the SelectionChanged event by calling synchronizeItemDetail.
    Most client classes will only have to implement
    synchronizeItemDetail.
    """
    def selectedItem (self):
        # return the ContentItem being viewed
        return self.parentBlock.selectedItem()

    def relayoutParents (self):
        # relayout the parent block
        block = self
        while (not block.eventBoundary and block.parentBlock):
            block = block.parentBlock
            block.synchronizeWidget()

    def synchronizeItemNone (self):
        # called instead of synchronizeItemDetail when there is no selected item.
        pass
    
    def synchronizeItemDetail (self, item):
        # override this method to draw your block's detail portion of this Item.
        raise NotImplementedError, "%s.synchronizeItemDetail()" % (type(self))
    
class StaticTextLabel(DetailSyncronizer, ControlBlocks.StaticText):
    def synchronizeItemNone(self):
        self.widget.SetLabel ('')  
    
class DateTimeBlock (StaticTextLabel):
    """
    Date and Time associated with the Content Item
    Currently this is static text, but soon it will need to be editable
    """
    def synchronizeItemDetail (self, item):
        """
          Display the item in the wxWidget.
        """
        widget = self.widget
        theDate = item.date # get the redirected date attribute
        theDate = str(theDate)
        widget.SetLabel(theDate)

class Headline (StaticTextLabel):
    """Headline, or Title field of the Content Item, as static text"""
    def synchronizeItemDetail (self, item):
        """
          Display the item's HeadLine in the wxWidget.
        """
        self.widget.SetLabel (item.about)
        
class StaticTextAttribute(StaticTextLabel):
    """
      Static Text that displays the name of the selected item's Attribute
    """
    def synchronizeItemDetail (self, item):
        whoRedirect = item.getAttributeAspect(self.whichAttribute(), 'redirectTo')
        if whoRedirect is None:
            whoRedirect = '  '
        else:
            whoRedirect = ' ' + whoRedirect + ': '
        self.widget.SetLabel (whoRedirect)
        # relayout the parent block
        self.relayoutParents() 

    def whichAttribute(self):
        # override to define the attribute to be used
        raise NotImplementedError, "%s.whichAttribute()" % (type(self))

class ToString (StaticTextAttribute):
    def whichAttribute(self):
        return 'who'

class FromString (StaticTextAttribute):
    def whichAttribute(self):
        return 'whoFrom'

class MarkupBar (DetailSyncronizer, DynamicContainerBlocks.Toolbar):
    """   
      Markup Toolbar, for quick control over Items.
    Doesn't need to synchronizeItemDetail, because
    the individual ToolbarItems synchronizeItemDetail.
    """
    def synchronizeItemDetail (self, item):
        pass
    
    def onToolPressStub (self, notification):
        tool = notification.data['sender']
        if tool.itsName == 'SharingButton':
            #self.parentBlock.Notify("EnableSharing")
            pass
    
    def selectedItem (self):
        # return the ContentItem being viewed
        return self.parentBlock.selectedItem()

    def onButtonPressed (self, notification):
        # Rekind the item by adding or removing the associated aspect
        tool = notification.data['sender']
        # DLDTBD - use self instead of bar here, once block copy problem is fixed.
        bar = tool.dynamicParent
        item = bar.selectedItem()
        if item is not None:
            aspectKind = tool.stampAspectKind()
            if bar.widget.GetToolState(tool.toolID):
                operation = 'add'
            else:
                operation = 'remove'
            item.StampKind(operation, aspectKind)
            # DLDTBD - notify the world that the item has a new kind.
            self.relayoutParents()        

class DetailStampButton (DetailSyncronizer, DynamicContainerBlocks.ToolbarItem):
    """
      Common base class for the stamping buttons in the Markup Bar
    """
    def stampAspectClass(self):
        # return the class of this stamp's aspect (bag of kind-specific attributes)
        raise NotImplementedError, "%s.stampAspectClass()" % (type(self))
    
    def stampAspectKind(self):
        # return the kind of this stamp's aspect (bag of kind-specific attributes)
        raise NotImplementedError, "%s.stampAspectKind()" % (type(self))
    
    def synchronizeItemDetail (self, item):
        # toggle this button to reflect the kind of the selected item
        shouldToggleBasedOnClass = isinstance(item, self.stampAspectClass())
        shouldToggleBasedOnKind = item.itsKind.isKindOf(self.stampAspectKind())
        assert shouldToggleBasedOnClass == shouldToggleBasedOnKind, \
               "Class/Kind mismatch for class %s, kind %s" % (item.__class__, item.itsKind)
        self.dynamicParent.widget.ToggleTool(self.toolID, shouldToggleBasedOnKind)

    def synchronizeItemNone (self):
        # called instead of synchronizeItemDetail when there is no selected item.
        self.synchronizeItemDetail (None)

class SharingButton (DetailStampButton):
    """
      Sharing button in the Markup Bar
    """
    def stampAspectClass(self):
        return Mail.MailMessageAspect
    
    def stampAspectKind(self):
        return Mail.MailParcel.getMailMessageAspectKind()
    
class CalendarStamp (DetailStampButton):
    """
      Calendar button in the Markup Bar
    """
    def stampAspectClass(self):
        return Calendar.CalendarEventAspect

    def stampAspectKind(self):
        return Calendar.CalendarParcel.getCalendarEventAspectKind()

class TaskStamp (DetailStampButton):
    """
      Task button in the Markup Bar
    """
    def stampAspectClass(self):
        return Task.TaskAspect

    def stampAspectKind(self):
        return Task.TaskParcel.getTaskAspectKind()
        
class FromAndToArea (DetailSyncronizer, ControlBlocks.ContentItemDetail):
    def synchronizeItemDetail (self, item):
        # if the item's not a Note, then we should show ourself
        shouldShow = not isinstance (item, Notes.Note)
        self.show(shouldShow)
        # relayout the parent block if it's safe to do so
        
    def synchronizeItemNone(self):
        self.show(False)
    
    def show(self, shouldShow):
        # if the show status has changed, tell our widget, and our parent
        if shouldShow != self.isShown:
            try:
                widget = self.widget
            except AttributeError:
                return
            # we have a widget
            if shouldShow:
                widget.Show(True)
                self.isShown = True
            else:
                widget.Show(False)
                self.isShown = False
            self.relayoutParents()
        
class EditTextAttribute (DetailSyncronizer, ControlBlocks.EditText):
    """
    EditText field connected to some attribute of a ContentItem
    Override LoadAttributeIntoWidget, SaveAttributeFromWidget in subclasses
    """
    def instantiateWidget (self):
        widget = super (EditTextAttribute, self).instantiateWidget()
        # We need to save off the changed widget's data into the block periodically
        # Currently looks like OnLoseFocus is not getting called every time we lose focus,
        #   only when focus moves to another EditText block.
        widget.Bind(wx.EVT_KEY_UP, self.onKeyUp)
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
        self.widget.Show(True)
        self.loadTextValue(item)
            
    def synchronizeItemNone (self):
        self.widget.Show(False)
            
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
    def saveAttributeFromWidget (self, item, widget):  
        textType = item.getAttributeAspect('body', 'type')
        widgetText = widget.GetValue()
        if widgetText:
            item.body = textType.makeValue(widgetText)
        
    def loadAttributeIntoWidget (self, item, widget):  
        if item.hasAttributeValue("body"):
            # get the character string out of the Text LOB
            noteBody = item.body
            if isinstance(noteBody, XMLRepositoryView.XMLText):
                # Read the unicode stream from the XML
                noteBody = noteBody.getInputStream().read()
            widget.SetValue(noteBody)
        else:
            widget.Clear()

class ToEditField (EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def saveAttributeFromWidget(self, item, widget):  
        toFieldString = widget.GetValue()
        # DLDTBD - need to parse the string and lookup the contacts
        #  because it's really the contacts that are stored in the "who" attribute!
       
    def loadAttributeIntoWidget (self, item, widget):
        whoContacts = item.who # get redirected who list
        try:
            numContacts = len(whoContacts)
        except:
            numContacts = 0            
        if numContacts > 0:
            whoNames = []
            for whom in whoContacts.values():
                whoNames.append(whom.getItemDisplayName())
            whoString = ', '.join(whoNames)
        else:
            whoString = ''
            if isinstance(whoContacts, Contacts.ContactName):
                whoString = whoContacts.firstName + ' ' + whoContacts.lastName
        widget.SetValue(whoString)

class FromEditField (EditTextAttribute):
    """Edit field containing the sender's contact"""
    def saveAttributeFromWidget(self, item, widget):  
        pass       
    def loadAttributeIntoWidget(self, item, widget):
        pass

