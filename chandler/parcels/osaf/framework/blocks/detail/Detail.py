__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository.parcel.Parcel as Parcel
import application.Globals as Globals
import osaf.framework.blocks.ControlBlocks as ControlBlocks
import wx

"""
Detail.py
Classes for the ContentItem Detail View
"""

class DetailParcel(Parcel.Parcel):
    pass

class Headline(ControlBlocks.StaticText):
    """Headline, or Title field of the Content Item, as static text"""
    def OnSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWidget.
        """
        item = notification.data['item']
        widget = self.widget
        widget.SetLabel(item.getAbout())
        
class DateTimeBlock(ControlBlocks.StaticText):
    """
    Date and Time associated with the Content Item
    Currently this is static text, but soon it will need to be editable
    """
    def OnSelectionChangedEvent (self, notification):
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
        widget.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        widget.Bind(wx.EVT_KILL_FOCUS, self.OnLoseFocus)
        return widget

    def OnKeyUp(self, event):
        self.SaveTextValue()

    def SelectedItem(self):
        # return the ContentItem being viewed
        return self.parentBlock.SelectedItem()
    
    def SaveTextValue(self):
        # save the user's edits into item's attibute
        item = self.SelectedItem()
        widget = self.widget
        if item and widget:
            self.SaveAttributeFromWidget(item, widget)
        
    def LoadTextValue(self, item):
        # load the edit text from our attribute into the field
        if not item:
            item = self.SelectedItem()
        if item:
            widget = self.widget
            self.LoadAttributeIntoWidget(item, widget)
        
    def OnLoseFocus(self, notification):
        # called when we lose focus, to save away the text
        self.SaveTextValue()
        
    def OnSelectionChangedEvent (self, notification):
        """
          Display the item in the wxWidget.
        """
        item = notification.data['item']
        self.synchronizeWidget(item)    # make sure we use the new item    
        
    def synchronizeWidget (self, item=None):
        # optional second parameter is the new item to synchronize to
        # lets us avoid a race condition getting the new item from the parent block
        super(EditTextAttribute, self).synchronizeWidget()
        if not Globals.wxApplication.ignoreSynchronizeWidget:
            self.LoadTextValue(item)
            
    def SaveAttributeFromWidget(self, item, widget):  
       # subclasses need to override this method
       # DLDTBD - log an error message
       print "NotImplementedError - %s.SaveAttributeFromWidget()" % (type(self))
       raise NotImplementedError, "%s.SaveAttributeFromWidget()" % (type(self))

    def LoadAttributeIntoWidget(self, item, widget):  
       # subclasses need to override this method
       print "NotImplementedError - %s.LoadAttributeIntoWidget()" % (type(self))
       raise NotImplementedError, "%s.LoadAttributeIntoWidget()" % (type(self))

class NoteBody(EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def SaveAttributeFromWidget(self, item, widget):  
        textType = item.getAttributeAspect('body', 'type')
        widgetText = widget.GetValue()
        if widgetText:
            item.body = textType.makeValue(widgetText)
        
    def LoadAttributeIntoWidget(self, item, widget):  
        if hasattr(item, "body"):
            # get the character string out of the Text LOB
            noteText = item.body
            noteString = noteText.getInputStream().read()
            widget.SetValue(noteString)
        else:
            widget.Clear()

class ToEditField(EditTextAttribute):
    """
    Body attribute of a ContentItem, e.g. a Note
    """
    def SaveAttributeFromWidget(self, item, widget):  
        toFieldString = widget.GetValue()
        # DLDTBD - need to parse the string and lookup the contacts
        #  because it's really the contacts that are stored in the "who" attribute!
        if toFieldString:
            item.setAttributeValue(item.whoAttribute, toFieldString)
       
    def LoadAttributeIntoWidget(self, item, widget):
        toFieldString = item.getWho()
        widget.SetValue(toFieldString)

class FromEditField(EditTextAttribute):
    """Edit field containing the sender's contact"""
    def SaveAttributeFromWidget(self, item, widget):  
        pass       
    def LoadAttributeIntoWidget(self, item, widget):
        pass

