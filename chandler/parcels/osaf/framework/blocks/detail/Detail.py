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
import wx

"""
Detail.py
Classes for the ContentItem Detail View
"""

class DetailParcel(application.Parcel.Parcel):
    pass

class Headline(ControlBlocks.StaticText):
    """Headline, or Title field of the Content Item, as static text"""
    def onSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWidget.
        """
        self.widget.SetLabel (notification.data ['item'].about)
        
class DateTimeBlock(ControlBlocks.StaticText):
    """
    Date and Time associated with the Content Item
    Currently this is static text, but soon it will need to be editable
    """
    def onSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWidget.
        """
        item = notification.data['item']
        widget = self.widget
        widget.SetLabel(item.getDate())
        
class EditTextAttribute(ControlBlocks.EditText):
    """
    EditText field connected to some attribute of a ContentItem
    Override LoadAttributeIntoWidget, SaveAttributeFromWidget in subclasses
    """
    def instantiateWidget(self):
        widget = super (EditTextAttribute, self).instantiateWidget()
        # We need to save off the changed widget's data into the block periodically
        # Currently looks like OnLoseFocus is not getting called every time we lose focus,
        #   only when focus moves to another EditText block.
        widget.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        widget.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocus)
        return widget

    def onKeyUp(self, event):
        self.saveTextValue()

    def selectedItem(self):
        # return the ContentItem being viewed
        return self.parentBlock.selectedItem()
    
    def saveTextValue(self):
        # save the user's edits into item's attibute
        item = self.selectedItem()
        widget = self.widget
        if item and widget:
            self.saveAttributeFromWidget(item, widget)
        
    def loadTextValue(self, item):
        # load the edit text from our attribute into the field
        if not item:
            item = self.selectedItem()
        if item:
            widget = self.widget
            self.loadAttributeIntoWidget(item, widget)
        
    def onLoseFocus(self, notification):
        # called when we lose focus, to save away the text
        self.saveTextValue()
        
    def onSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWidget.
        """
        item = notification.data['item']
        self.synchronizeWidget(item)    # make sure we use the new item    

    def OnDataChanged (self):
        # Notification that an edit operation has taken place
        self.saveTextValue()

    def synchronizeWidget (self, item=None):
        # optional second parameter is the new item to synchronize to
        # lets us avoid a race condition getting the new item from the parent block
        super(EditTextAttribute, self).synchronizeWidget()
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            self.loadTextValue(item)
            
    def saveAttributeFromWidget(self, item, widget):  
       # subclasses need to override this method
       raise NotImplementedError, "%s.SaveAttributeFromWidget()" % (type(self))

    def loadAttributeIntoWidget(self, item, widget):  
       # subclasses need to override this method
       raise NotImplementedError, "%s.LoadAttributeIntoWidget()" % (type(self))

class NoteBody(EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def saveAttributeFromWidget(self, item, widget):  
        textType = item.getAttributeAspect('body', 'type')
        widgetText = widget.GetValue()
        if widgetText:
            item.body = textType.makeValue(widgetText)
        
    def loadAttributeIntoWidget(self, item, widget):  
        if item.hasAttributeValue("body"):
            # get the character string out of the Text LOB
            noteBody = item.body
            if isinstance(noteBody, XMLRepositoryView.XMLText):
                # Read the unicode stream from the XML
                noteBody = noteBody.getInputStream().read()
            widget.SetValue(noteBody)
        else:
            widget.Clear()

class ToEditField(EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def saveAttributeFromWidget(self, item, widget):  
        toFieldString = widget.GetValue()
        # DLDTBD - need to parse the string and lookup the contacts
        #  because it's really the contacts that are stored in the "who" attribute!
        if toFieldString:
            item.who = toFieldString
       
    def loadAttributeIntoWidget(self, item, widget):
        widget.SetValue(item.who)

class FromEditField(EditTextAttribute):
    """Edit field containing the sender's contact"""
    def saveAttributeFromWidget(self, item, widget):  
        pass       
    def loadAttributeIntoWidget(self, item, widget):
        pass

class MarkupBar(DynamicContainerBlocks.Toolbar):
    """   Markup Toolbar, for quick control over Items
    """
    def onToolPressStub(self, notification):
        tool = notification.data['sender']
        if tool.itsName == 'SharingButton':
            #self.parentBlock.Notify("EnableSharing")
            pass
    

    
