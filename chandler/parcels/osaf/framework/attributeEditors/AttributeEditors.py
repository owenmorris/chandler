__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os, cStringIO
import wx
from wx.lib.scrolledpanel import ScrolledPanel
from osaf.pim.tasks import TaskMixin
import osaf.pim.calendar.Calendar as Calendar
import osaf.pim.mail as Mail
from osaf.pim.calendar.TimeZone import TimeZoneInfo

import repository.item.ItemHandler as ItemHandler
from repository.util.Lob import Lob
from osaf.framework.blocks import DragAndDrop, DrawingUtilities, Styles
import logging
from operator import itemgetter
from datetime import datetime, time, timedelta
from PyICU import DateFormat, DateFormatSymbols, SimpleDateFormat, ICUError, ParsePosition, ICUtzinfo
from osaf.framework.blocks.Block import ShownSynchronizer, wxRectangularChild
from osaf.pim.items import ContentItem
from application import schema
from i18n import OSAFMessageFactory as _
from osaf import messages

logger = logging.getLogger(__name__)

#
# The attribute editor registration mechanism:
# For each editor, there's one or more AttributeEditorMapping objects that
# map a string to the editor classname. Each one maps a differe

class AttributeEditorMapping(schema.Item):
    className = schema.One(schema.Bytes)

def installParcel(parcel, oldVersion=None):
    """ Do initial registry of attribute editors """
    # This creates individual AttributeEditor objects, which map
    # a type string (their itsName attribute) to a class name.
    # The resulting AttributeEditor objects are found each runtime using
    # a kind query, below.
    #
    # Only add core classes in this parcel to this list (imitate the mechanism
    # if you have your own; the detail view does this.)
    # 
    # If you do modify this list, please keep it in alphabetical 
    # order by type string.
    aeList = {
        '_default': 'RepositoryAttributeEditor',
        'Boolean': 'CheckboxAttributeEditor',
        'Contact': 'ContactAttributeEditor',
        'ContactName': 'ContactNameAttributeEditor', 
        'ContentItem': 'StringAttributeEditor', 
        'DateTime': 'DateTimeAttributeEditor', 
        'DateTime+dateOnly': 'DateAttributeEditor', 
        'DateTime+timeOnly': 'TimeAttributeEditor',
        'DateTime+timeZoneOnly': 'TimeZoneAttributeEditor',
        'EmailAddress': 'EmailAddressAttributeEditor',
        'Integer': 'StringAttributeEditor',
        'Item': 'ItemNameAttributeEditor',
        'Kind': 'StampAttributeEditor',
        'image/jpeg': 'LobImageAttributeEditor',
        'Location': 'LocationAttributeEditor',
        'SharingStatusEnum': 'EnumAttributeEditor',
        'Text': 'StringAttributeEditor',
        'Text+static': 'StaticStringAttributeEditor',
        'Timedelta': 'TimeDeltaAttributeEditor',
        'TimeTransparencyEnum': 'ChoiceAttributeEditor',
    }
    for typeName, className in aeList.items():
        AttributeEditorMapping.update(parcel, typeName, className=\
                                      __name__ + '.' + className)

_TypeToEditorInstances = {}
_TypeToEditorClasses = {}

def getSingleton (typeName):
    """ Get (and cache) a single shared Attribute Editor for this type. """
    try:
        instance = _TypeToEditorInstances [typeName]
    except KeyError:
        aeClass = _getAEClass (typeName)
        instance = aeClass()
        _TypeToEditorInstances [typeName] = instance
    return instance

def getInstance (typeName, item, attributeName, readOnly, presentationStyle):
    """ Get a new unshared instance of the Attribute Editor for this type (and optionally, format). """
    try:
        format = presentationStyle.format
    except AttributeError:
        format = None
    if typeName == "Lob" and hasattr(item, attributeName):
        typeName = getattr(item, attributeName).mimetype
    aeClass = _getAEClass(typeName, readOnly, format)
    #logger.debug("getAEClass(%s [%s, %s]%s) --> %s", 
                 #attributeName, typeName, format, 
                 #readOnly and ", readOnly" or "", aeClass)
    instance = aeClass()        
    return instance

def _getAEClass (type, readOnly=False, format=None):
    """ Return the attribute editor class for this type """
    # Once per run, build a map of type -> class
    global _TypeToEditorClasses
    if len(_TypeToEditorClasses) == 0:
        aeKind = AttributeEditorMapping.getKind(wx.GetApp().UIRepositoryView)
        for ae in aeKind.iterItems():
            _TypeToEditorClasses[ae.itsName] = ae.className
        assert _TypeToEditorClasses['_default'] is not None, "Default AttributeEditorMapping doesn't exist ('_default')"
            
    # Try several ways to find an appropriate editor:
    # - If we're readOnly, try "+readOnly" before we try without it.
    # - If we have a format, try "+format" before we try without it.
    # - If those fail, just try the type itself.
    # - Failing that, use _default.
    def generateEditorTags():
        if format is not None:
            if readOnly:
                yield "%s+%s+readOnly" % (type, format)
            yield "%s+%s" % (type, format)
        if readOnly:
            yield "%s+readOnly" % type
        yield type
        logger.warn("AttributeEditors.getAEClass: using %s for %s/%s",
                    _TypeToEditorClasses['_default'], type, format)
        yield "_default"
    classPath = None
    for key in generateEditorTags():
        classPath = _TypeToEditorClasses.get(key)
        if classPath is not None:
            break
    assert classPath is not None
    
    parts = classPath.split (".")
    assert len(parts) >= 2, " %s isn't a module and class" % classPath
    className = parts.pop ()
    module = __import__ ('.'.join(parts), globals(), locals(), className)
    assert module.__dict__[className], "Class %s doesn't exist" % classPath
    aeClass = module.__dict__[className]
    return aeClass

class BaseAttributeEditor (object):
    """ Base class for Attribute Editors. """
        
    def ReadOnly (self, (item, attribute)):
        """ Return True if this Attribute Editor refuses to edit """
        # By default, everything's editable if the item says it is.
        return not item.isAttributeModifiable(attribute)

    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        """ Draw the value of the attribute in the specified rect of the dc """
        raise NotImplementedError
    
    def IsFixedWidth(self):
        """
        Return True if this control is of fixed size, and shouldn't be 
        expanded to fill its space
        """
        # Most classes that don't use a TextCtrl will be fixed width, so we
        # default to True.
        return True
    
    def EditInPlace(self):
        """ 
        Will this attribute editor change controls when the user clicks on it?
        """
        return False
    
    def CreateControl (self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):
        """ 
        Create and return a control to use for displaying (forEdit=False)
        or editing (forEdit=True) the attribute value.
        """
        raise NotImplementedError
    
    def BeginControlEdit (self, item, attributeName, control):
        """ 
        Load this attribute into the editing control. 
        """
        pass # do nothing by default

    def EndControlEdit (self, item, attributeName, control):
        """ Save the control's value into this attribute. """
        # Do nothing by default.
        pass        
    
    def GetControlValue (self, control):
        """ Get the value from the control. """
        value = control.GetValue()
        return value

    def SetControlValue (self, control, value):
        """ Set the value in the control. """
        control.SetValue (value)

    def GetAttributeValue (self, item, attributeName):
        """ Get the value from the specified attribute of the item. """
        return getattr(item, attributeName, None)

    def SetAttributeValue (self, item, attributeName, value):
        """ Set the value of the attribute given by the value. """
        if not self.ReadOnly((item, attributeName)):
            setattr(item, attributeName, value)
            self.AttributeChanged()
    
    def SetChangeCallback(self, callback):
        """ 
        Set the callback function that we'll use to notify about attribute
        value changes. 
        """
        self.changeCallBack = callback

    def AttributeChanged(self):
        """ Called by the attribute editor when it changes the underlying
            value. """
        # We shouldn't notify about the change if this item's gone...
        if self.item.isDeleted():
            return
        try:
            callback = self.changeCallBack
        except AttributeError:
            pass
        else:
            if callback is not None:
                callback()

class DragAndDropTextCtrl(ShownSynchronizer,
                 DragAndDrop.DraggableWidget,
                 DragAndDrop.DropReceiveWidget,
                 DragAndDrop.TextClipboardHandler,
                 wx.TextCtrl):
    def __init__(self, *arguments, **keywords):
        super (DragAndDropTextCtrl, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
                      
    def OnMouseEvents(self, event):
        # trigger a Drag and Drop if we're a single line and all selected
        if self.IsSingleLine() and event.LeftDown():
            selStart, selEnd = self.GetSelection()
            if selStart==0 and selEnd>1 and selEnd==self.GetLastPosition():
                if event.LeftIsDown(): # still down?
                    # have we had the focus for a little while?
                    if hasattr(self, 'focusedSince'):
                        if datetime.now() - self.focusedSince > timedelta(seconds=.2):
                            # Try Dragging the text
                            result = self.DoDragAndDrop()
                            if result != wx.DragMove and result != wx.DragCopy:
                                # Drag not allowed - set an insertion point instead
                                hit, row, column = self.HitTest(event.GetPosition())
                                if hit != wx.TE_HT_UNKNOWN:
                                    self.SetInsertionPoint(self.XYToPosition(row, column))
                                else:
                                    self.SetInsertionPointEnd() # workaround for bug 4116
                            return # don't skip, eat the click.
        event.Skip()

    def OnSetFocus(self, event):
        self.focusedSince = datetime.now()
        event.Skip()        

    def OnKillFocus(self, event):
        # when grid creates the control, it never gets the EVT_SET_FOCUS
        if hasattr(self, 'focusedSince'):
            del self.focusedSince
        event.Skip()        
    
    def OnRightClick(self, event):
        """ Build and display our context menu """
        # @@@ In the future, it might be nice to base this menu
        # on CPIA mechanisms, but we don't need that for now.
        menu = wx.Menu()
        menu.Append(wx.ID_UNDO, messages.UNDO)
        menu.Append(wx.ID_REDO, messages.REDO)
        menu.AppendSeparator()
        menu.Append(wx.ID_CUT, messages.CUT)
        menu.Append(wx.ID_COPY, messages.COPY)
        menu.Append(wx.ID_PASTE, messages.PASTE)
        menu.Append(wx.ID_CLEAR, messages.CLEAR)
        menu.AppendSeparator()
        menu.Append(wx.ID_SELECTALL, messages.SELECT_ALL)

        if '__WXGTK__' in wx.PlatformInfo:
            # (see note below re: GTK)
            menu.Bind(wx.EVT_MENU, self.OnMenuChoice)
            menu.Bind(wx.EVT_UPDATE_UI, self.OnMenuUpdateUI)

        self.PopupMenu(menu)
        menu.Destroy()

        # event.Skip() intentionally not called: we don't want
        # the menu built into wx to appear!

    # GTK's popup handling seems totally broken (our menu does pop up,
    # but the enabling and actual execution don't happen). So, do our own.
    if '__WXGTK__' in wx.PlatformInfo:
        popupHandlers = {
            # (FYI: these are method names, and so should not be localized.)
            wx.ID_UNDO: 'Undo',
            wx.ID_REDO: 'Redo',
            wx.ID_CUT: 'Cut',
            wx.ID_COPY: 'Copy',
            wx.ID_PASTE: 'Paste',
            wx.ID_CLEAR: 'Clear',
            wx.ID_SELECTALL: 'SelectAll'
            }
        def OnMenuChoice(self, event):
            handlerName = DragAndDropTextCtrl.popupHandlers.get(event.GetId(), None)
            if handlerName is None:
                event.Skip()
                return
            h = getattr(self, handlerName)
            return h()
    
        def OnMenuUpdateUI(self, event):
            evtName = DragAndDropTextCtrl.popupHandlers.get(event.GetId(), None)
            if evtName is None:
                event.Skip()
                return
            handlerName = "Can%s" % evtName
            h = getattr(self, handlerName)
            enabled = h()
            event.Enable(enabled)
        
        # wx.TextCtrl.Clear is documented to remove all the text in the
        # control; only the GTK version works this way (the others do what
        # we want, which is to remove the selection). So, here, we hack
        # Clear to just remove the selection on GTK only.
        def Clear(self):
            self.Remove(*self.GetSelection())

        def CanClear(self):    
            (selStart, selEnd) = self.GetSelection()
            return self.CanCut() and selStart != selEnd
    else:
        # CanClear for all other platforms.
        def CanClear(self):
            return self.CanCut()

    def Cut(self):
        result = self.GetStringSelection()
        super(DragAndDropTextCtrl, self).Cut()
        return result

    def Copy(self):
        result = self.GetStringSelection()
        super(DragAndDropTextCtrl, self).Copy()
        return result
    
    def onCopyEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanCopy()

    def onCopyEvent(self, event):
        self.Copy()

    def onCutEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanCut()

    def onCutEvent(self, event):
        self.Cut()

    def onPasteEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanPaste()

    def onPasteEvent(self, event):
        self.Paste()

    def onClearEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanClear()
    
    def onClearEvent(self, event):
        self.Clear()
    
    def onRedoEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanRedo()

    def onRedoEvent(self, event):
        self.Redo()

    def onUndoEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanUndo()
    
    def onUndoEvent(self, event):
        self.Undo()

    def onRemoveEventUpdateUI(self, event):
        (startSelect, endSelect) = self.GetSelection()
        event.arguments ['Enable'] = startSelect < self.GetLastPosition()
    
    def onRemoveEvent(self, event):
        # I tried the following code, but apparently a SWIG bug (#3978)
        # prevents EmulateKeyPress from accepting it's argument. So
        # alternatively, I tried to duplicat the code that handles
        # delete in EmulateKeyPress, however it didn't work correctly -- DJA
        #keyEvent = wx.KeyEvent
        #keyEvent.m_keyCode = wx.WXK_DELETE
        #self.EmulateKeyPress (keyEvent)
        (startSelect, endSelect) = self.GetSelection()
        if startSelect < self.GetLastPosition():
            if startSelect == endSelect:
                endSelect += 1
            self.Remove (startSelect, endSelect)

    def onSelectAllEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.GetLastPosition() > 0

    def onSelectAllEvent(self, event):
        self.SetSelection(-1, -1)
        
class wxEditText(DragAndDropTextCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxEditText, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterPressed, id=self.GetId())
        minW, minH = arguments[-1] # assumes minimum size passed as last arg
        self.SetSizeHints(minW=minW, minH=minH)

    def OnEnterPressed(self, event):
        self.blockItem.postEventByName ('EnterPressed', {'text':self.GetValue()})
        event.Skip()

class AEStaticText(ShownSynchronizer,
                   wx.StaticText):
    """ 
    Wrap wx.StaticText to give it the same GetValue/SetValue behavior
    that other wx controls have. (This was simpler than putting lotsa special
    cases all over the StringAttributeEditor...)
    """
    GetValue = wx.StaticText.GetLabel
    SetValue = wx.StaticText.SetLabel
    
def NotifyBlockToSaveValue(widget):
    """ Notify this widget's block to save its value when we lose focus """
    # We wish there were a cleaner way to do this notification!
    try:
        # if we have a block, and it has a save method, get it
        saveMethod = widget.blockItem.saveValue
    except AttributeError:
        pass
    else:
        logger.debug("%s: saving value", getattr(widget.blockItem, 'blockName',
                                                 widget.blockItem.itsName))
        saveMethod()

class AENonTypeOverTextCtrl(DragAndDropTextCtrl):
    def __init__(self, *args, **keys):
        super(AENonTypeOverTextCtrl, self).__init__(*args, **keys)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnEditLoseFocus)

    def OnEditLoseFocus(self, event):
        NotifyBlockToSaveValue(self)
        event.Skip()

class AETypeOverTextCtrl(wxRectangularChild):
    def __init__(self, parent, id, title=u'', position=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, *args, **keys):
        super(AETypeOverTextCtrl, self).__init__(parent, id)
        staticSize = keys['staticSize']
        del keys['staticSize']
        self.hideLoc = (-100,-100)
        self.showLoc = (0,0)
        editControl = DragAndDropTextCtrl(self, -1, pos=position, size=size, 
                                          style=style, *args, **keys)
        self.editControl = editControl
        editControl.Bind(wx.EVT_KILL_FOCUS, self.OnEditLoseFocus)
        editControl.Bind(wx.EVT_SET_FOCUS, self.OnEditGainFocus)
        editControl.Bind(wx.EVT_LEFT_DOWN, self.OnEditClick)
        editControl.Bind(wx.EVT_LEFT_DCLICK, self.OnEditClick)
        editControl.Bind(wx.EVT_KEY_UP, self.OnEditKeyUp)
        staticControl = AEStaticText(self, -1, pos=position, 
                                                      size=staticSize, style=style, 
                                                      *args, **keys)
        self.staticControl = staticControl
        staticControl.Bind(wx.EVT_LEFT_DOWN, self.OnStaticClick)
        self.shownControl = staticControl
        self.otherControl = editControl
        self.shownControl.Move(self.showLoc)
        self.otherControl.Move(self.hideLoc)
        self._resize()

    def _showingSample(self):
        try:
            showingSample = self.editor.showingSample
        except AttributeError:
            showingSample = False
        return showingSample

    def OnStaticClick(self, event):
        editControl = self.editControl
        editControl.SetFocus()
        # if we're currently displaying the "sample text", select
        # the entire field, otherwise position the insertion appropriately
        # The AE should provide a SampleText api for this,
        #  or better yet, encapsulate the concept of SampleText into
        #  the control so the AE doesn't have that complication.
        if self._showingSample():
            editControl.SelectAll()
        else:
            result, row, column = editControl.HitTest(event.GetPosition())
            if result != wx.TE_HT_UNKNOWN: 
                editControl.SetInsertionPoint(editControl.XYToPosition(row, column))
        # return without calling event.Skip(), since we eat the click

    def OnEditClick(self, event):
        if self._showingSample():
            self.editControl.SelectAll() # eat the click
        else:
            event.Skip() # continue looking for a click handler
            
    def OnEditGainFocus(self, event):
        self._swapControls(self.editControl)
        event.Skip()

    def OnEditLoseFocus(self, event):
        NotifyBlockToSaveValue(self)
        self._swapControls(self.staticControl)
        event.Skip()

    def OnEditKeyUp(self, event):
        if event.m_keyCode == wx.WXK_RETURN:
            # not needed: Navigating will make us lose focus
            # NotifyBlockToSaveValue(self)
            self.Navigate()
        event.Skip()

    def _swapControls(self, controlToShow):
        if controlToShow is self.otherControl:
            hiddenControl = controlToShow
            shownControl = self.shownControl
            self.Freeze()
            hiddenValue = hiddenControl.GetValue()
            shownValue = shownControl.GetValue()
            if shownValue != hiddenValue:
                hiddenControl.SetValue(shownValue)
            shownControl.Move(self.hideLoc)
            hiddenControl.Move(self.showLoc)
            self.shownControl = hiddenControl
            self.otherControl = shownControl
            self._resize()
            self.Thaw()

    def _resize(self):
        if self.IsShown():
            # first relayout our sizer with the new shown control
            shownControl = self.shownControl
            sizer = self.GetSizer()
            if not sizer:
                sizer = wx.BoxSizer (wx.HORIZONTAL)
                self.SetSizer (sizer)
            sizer.Clear()
            stretchFactor = 1
            border = 0
            borderFlag = 0
            self.SetSize(shownControl.GetSize())
            sizer.Add (shownControl,
                       stretchFactor, 
                       borderFlag, 
                       border)
            sizer.Hide (self.otherControl)
            self.Layout()

            # need to relayout the view container - so tell the block
            try:
                sizeChangedMethod = self.blockItem.onWidgetChangedSize
            except AttributeError:
                pass
            else:
                sizeChangedMethod()

    def GetValue(self): return self.shownControl.GetValue()
    def SetValue(self, *args): return self.shownControl.SetValue(*args)
    def SetForegroundColour(self, *args): self.shownControl.SetForegroundColour(*args)
    def onCopyEventUpdateUI(self, *args): self.shownControl.onCopyEventUpdateUI(*args)
    def onCopyEvent(self, *args): self.shownControl.onCopyEvent(*args)
    def onCutEventUpdateUI(self, *args): self.shownControl.onCutEventUpdateUI(*args)
    def onCutEvent(self, *args): self.shownControl.onCutEvent(*args)
    def onPasteEventUpdateUI(self, *args): self.shownControl.onPasteEventUpdateUI(*args)
    def onPasteEvent(self, *args): self.shownControl.onPasteEvent(*args)
    def onClearEventUpdateUI(self, *args): self.shownControl.onClearEventUpdateUI(*args)
    def onClearEvent(self, *args): self.shownControl.onClearEvent(*args)
    def onSelectAllEventUpdateUI(self, *args): self.shownControl.onSelectAllEventUpdateUI(*args)
    def onSelectAllEvent(self, *args): self.shownControl.onSelectAllEvent(*args)
    def onRedoEventUpdateUI(self, *args): self.shownControl.onRedoEventUpdateUI(*args)
    def onRedoEvent(self, *args): self.shownControl.onRedoEvent(*args)
    def onUndoEventUpdateUI(self, *args): self.shownControl.onUndoEventUpdateUI(*args)
    def onUndoEvent(self, *args): self.shownControl.onUndoEvent(*args)
    def onRemoveEventUpdateUI(self, *args): self.shownControl.onRemoveEventUpdateUI(*args)
    def onRemoveEvent(self, *args): self.shownControl.onRemoveEvent(*args)

    def SetFont(self, font):
        self.editControl.SetFont(font)
        self.staticControl.SetFont(font)

    def SetSelection(self, *args):
        self._swapControls(self.editControl)
        self.editControl.SetSelection(*args)

    def SelectAll(self, *args):
        self._swapControls(self.editControl)
        self.editControl.SelectAll()

class StringAttributeEditor (BaseAttributeEditor):
    """ 
    Uses a Text Control to edit attributes in string form. 
    Supports sample text.
    """
    
    def EditInPlace(self):
        try:
            editInPlace = self.presentationStyle.editInPlace
        except AttributeError:
            editInPlace = False
        return editInPlace

    def IsFixedWidth(self, blockItem):
        """
        Return True if this control shouldn't be resized to fill its space
        """
        try:
            fixedWidth = self.blockItem.stretchFactor == 0.0
        except AttributeError:
            fixedWidth = False # yes, let our textctrl fill the space.
        return fixedWidth

    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        """
        Draw this control's value; used only by Grid when the attribute's not
        being edited.
        @@@ Currently only handles left justified single line text.
        """
        #logger.debug("StringAE.Draw: %s, %s of %s; %s in selection",
                     #self.isShared and "shared" or "dv",
                     #attributeName, item,
                     #isInSelection and "is" or "not")

        # Erase the bounding box
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)

        dc.DrawRectangleRect (rect)

        # Get the text we'll display, and note whether it's the sample text.
        theText = None # assume that we won't use the sample.
        if not self.HasValue(item, attributeName):
            # Consider using the sample text
            theText = self.GetSampleText(item, attributeName)
        if theText is None:
            # No sample text, or we have a value. Use the value.
            theText = self.GetAttributeValue(item, attributeName)
        elif len(theText) > 0:
            # theText is the sample text - switch to gray
            dc.SetTextForeground (wx.SystemSettings.GetColour (wx.SYS_COLOUR_GRAYTEXT))

        if len(theText) > 0:
            # Draw inside the lines.
            dc.SetBackgroundMode (wx.TRANSPARENT)
            rect.Inflate (-1, -1)
            dc.SetClippingRect (rect)
            
            # theText = "%s %s" % (dc.GetFont().GetFaceName(), dc.GetFont().GetPointSize())
            DrawingUtilities.DrawClippedTextWithDots (dc, theText, rect)
                
            dc.DestroyClippingRegion()
        
    def CreateControl(self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):
        # logger.debug("StringAE.CreateControl")
        
        # We'll use a DragAndDropTextCtrl, unless we're an edit-in-place 
        # control in 'edit' mode.
        useStaticText = self.EditInPlace() and not forEditing
                
        # Figure out the size we should be
        # @@@ There's a wx catch-22 here: The text ctrl on Windows will end up
        # horizonally scrolled to expose the last character of the text if this
        # size is too small for the value we put into it. If the value is too
        # large, the sizer won't ever let the control get smaller than this.
        # For now, use 200, a not-too-happy medium that doesn't eliminate either problem.
        if parentBlock is None:
            # This is the case when we're used from the grid - the grid's gonna 
            # resize us, so just use the default.
            size = wx.DefaultSize
        else:
            # This is the case when we're used from AEBlock. We still could be 
            # resized by our sizer, but if we're too small initially, the widget
            # might show up horizontally scrolled, so we try to avoid that.
            # First, base our height on our font:
            if font is not None:
                measurements = Styles.getMeasurements(font)
                height = measurements.textCtrlHeight
                staticHeight = measurements.height
            else:
                height = wx.DefaultSize.GetHeight()
                staticHeight = height
            
            # Next, do width... pick one:
            # - our block's value if it's not default
            # - our parent's width (less our own border), if we have a parent widget
            # - 200, a value that has survived numerous rewritings of this 
            #   algorigthm, and whose original meaning is lost to history.
            if parentBlock.stretchFactor == 0.0 and parentBlock.size.width != 0:
                width = parentBlock.size.width
            else:
                try:
                    width = parentWidget.GetRect().width - (parentBlock.border.left + parentBlock.border.right)
                except:
                    width = 200
            size = wx.Size(width, height)

        style = wx.TAB_TRAVERSAL
        if readOnly: style |= wx.TE_READONLY
        
        if useStaticText:
            style |= (parentWidget.GetWindowStyle() & wx.SIMPLE_BORDER)
            control = AETypeOverTextCtrl(parentWidget, id, '', wx.DefaultPosition, 
                                         size, style, 
                                         staticSize=wx.Size(width, staticHeight)
                                         )
            editControl = control.editControl
            editControl.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
            editControl.Bind(wx.EVT_TEXT, self.onTextChanged)      
            editControl.Bind(wx.EVT_SET_FOCUS, self.onGainFocus)
            editControl.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocus)
            
        else:
            style |= wx.TE_AUTO_SCROLL
            try:
                lineStyleEnum = parentBlock.presentationStyle.lineStyleEnum
            except AttributeError:
                lineStyleEnum = ""
            if lineStyleEnum == "MultiLine":
                style |= wx.TE_MULTILINE
            else:
                style |= wx.TE_PROCESS_ENTER
                
            control = AENonTypeOverTextCtrl(parentWidget, id, '', wx.DefaultPosition, 
                                            size, style)
            control.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
            control.Bind(wx.EVT_TEXT, self.onTextChanged)      
            control.Bind(wx.EVT_LEFT_DOWN, self.onClick)
            control.Bind(wx.EVT_SET_FOCUS, self.onGainFocus)
            control.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocus)
        
        return control

    def BeginControlEdit (self, item, attributeName, control):
        self.sampleText = self.GetSampleText(item, attributeName)
        self.item = item
        self.attributeName = attributeName
        self.control = control
        # logger.debug("BeginControlEdit: context for %s.%s is '%s'", item, attributeName, self.sampleText)

        # set up the value (which may be the sample!) and select all the text
        value = self.GetAttributeValue(item, attributeName)
        if self.sampleText is not None and len(value) == 0:
            self._changeTextQuietly(control, self.sampleText, True, False)
        else:
            self._changeTextQuietly(control, value, False, False)
        #logger.debug("BeginControlEdit: %s (%s) on %s", attributeName, self.showingSample, item)

    def EndControlEdit (self, item, attributeName, control):
        # update the item attribute value, from the latest control value.
        # logger.debug("EndControlEdit: '%s' on %s", attributeName, item)
        if item is not None:
            value = self.GetControlValue (control)
            self.SetAttributeValue (item, attributeName, value)

    def GetControlValue (self, control):
        # return the empty string, if we're showing the sample value.
        if self.showingSample:
            value = u""
        else:
            value = super(StringAttributeEditor, self).GetControlValue(control)
        return value
    
    def SetControlValue(self, control, value):
        if len(value) != 0 or self.sampleText is None:
            self._changeTextQuietly(control, value, False, False)
        else:
            self._changeTextQuietly(control, self.sampleText, True, False)

    def onGainFocus(self, event):
        if self.showingSample:
            self.control.SelectAll()  # (select all)
        event.Skip()
    
    def onLoseFocus(self, event):
        if self.showingSample:
            self.control.SetSelection(0,0)
        event.Skip()
    
    def onTextChanged(self, event):
        if not getattr(self, "ignoreTextChanged", False):
            control = event.GetEventObject()
            if getattr(self, 'sampleText', None) is not None:
                currentText = control.GetValue()
                #logger.debug("StringAE.onTextChanged: not ignoring; value is '%s'" % currentText)                    
                if self.showingSample:
                    if currentText != self.sampleText:
                        alreadyChanged = True
                        # workaround for bug 3085 - changed text starts with copy of sample
                        #  due to multiple calls to this method
                        if '__WXGTK__' in wx.PlatformInfo:
                            if currentText.startswith(self.sampleText):
                                currentText = currentText.replace(self.sampleText,'',1)
                                alreadyChanged = False
                        #logger.debug("onTextChanged: replacing sample with it (alreadyChanged)")
                        self._changeTextQuietly(control, currentText, False, alreadyChanged)
                elif len(currentText) == 0:
                    #logger.debug("StringAE.onTextChanged: installing sample.")
                    self._changeTextQuietly(control, self.sampleText, True, False)
                pass # logger.debug("StringAE.onTextChanged: done; new values is '%s'" % control.GetValue())
            else:
                pass # logger.debug("StringAE.onTextChanged: ignoring (no sample text)")
        else:
            pass # logger.debug("StringAE.onTextChanged: ignoring (self-changed); value is '%s'" % event.GetEventObject().GetValue())
        
    def _isFocused(self, control):
        """
        Return True if the control is in the cluster of widgets
        within a single block.
        """
        focus = wx.Window_FindFocus()
        while control != None:
            if control == focus:
                return True
            if hasattr(control, 'blockItem'):
                break
            control = control.GetParent()
        return False
        
    def _changeTextQuietly(self, control, text, isSample=False, alreadyChanged=False):
        self.ignoreTextChanged = True
        try:
            #logger.debug("_changeTextQuietly: %s, to '%s', sample=%s", 
                         #self.attributeName, text.split('\n')[0], isSample)
            # text = "%s %s" % (control.GetFont().GetFaceName(), control.GetFont().GetPointSize())
            normalTextColor = wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT)
            if isSample:
                self.showingSample = True
    
                # Calculate a gray level to use: Mimi wants 50% of the brightness
                # of the text color, but 50% of black is still black.
                backColor = control.GetBackgroundColour()
                
                def __shadeBetween(shade, color1, color2):
                    shade1 = shade(color1)
                    shade2 = shade(color2)
                    smaller = min(shade1, shade2)
                    delta = abs(shade1 - shade2)
                    return smaller + (delta / 2)
                textColor = wx.Colour(__shadeBetween(wx.Colour.Red, normalTextColor, backColor),
                                      __shadeBetween(wx.Colour.Green, normalTextColor, backColor),
                                      __shadeBetween(wx.Colour.Blue, normalTextColor, backColor))
            else:
                self.showingSample = False
                textColor = normalTextColor
            
            if not alreadyChanged:
                oldValue = control.GetValue()
                if oldValue != text:
                    control.SetValue(text)
    
            if hasattr(control, 'SetStyle'):
                # Trying to make the text in the editbox gray doesn't seem to work on Win.
                # (I'm doing it anyway, because it seems to work on Mac.)
                control.SetStyle(0, len(text), wx.TextAttr(textColor))
                
                if isSample and self._isFocused(control):
                    control.SelectAll()
            else:
                control.SetForegroundColour(textColor)
        finally:
            del self.ignoreTextChanged
 
    def onKeyDown(self, event):
        """ Note whether the sample's been replaced. """
        # If we're showing sample text and this key would only change the 
        # selection, ignore it.
        if self.showingSample and event.GetKeyCode() in \
           (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_BACK):
             # logger.debug("onKeyDown: Ignoring selection-changer %s (%s) while showing the sample text", event.GetKeyCode(), wx.WXK_LEFT)
             return # skip out without calling event.Skip()

        # logger.debug("onKeyDown: processing %s (%s)", event.GetKeyCode(), wx.WXK_LEFT)
        event.Skip()
        
    def onClick(self, event):
        """ Ignore clicks if we're showing the sample """
        control = event.GetEventObject()
        if self.showingSample:
            if self._isFocused(control):
                # logger.debug("onClick: ignoring click because we're showing the sample.")
                control.SelectAll() # Make sure the whole thing's still selected
        else:
            event.Skip()
            
    def GetSampleText(self, item, attributeName):
        """ Return this attribute's sample text, or None if there isn't any. """
        try:
            sampleText = self.presentationStyle.sampleText
        except AttributeError:
            return None

        # Yep, there's supposed to be sample text.
        if len(sampleText) == 0:
            # Empty sample text was specified: this means use the attribute's displayName,
            # or the attribute name itself if no displayName is present. Redirect if 
            # necessary first.
            sampleText = item.getAttributeAspect(attributeName, 'redirectTo');
            if sampleText is None:
                sampleText = attributeName
            if item.hasAttributeAspect (sampleText, 'displayName'):
                sampleText = item.getAttributeAspect (sampleText, 'displayName')                  
        return sampleText

    def HasValue(self, item, attributeName):
        """
        Return True if a non-default value has been set for this attribute, 
        or False if this value is the default and deserves the sample text 
        (if any) instead. (Can be overridden.) """
        try:
            v = getattr(item, attributeName)
        except AttributeError:
            return False

        return len(unicode(v)) > 0

    def GetAttributeValue(self, item, attributeName):
        """ Get the attribute's current value """
        try:
            theValue = unicode(getattr(item, attributeName))
        except AttributeError:
            valueString = u""
        else:
            try:
                cardinality = item.getAttributeAspect (attributeName, "cardinality")
            except AttributeError:
                cardinality = "single"

            if cardinality == "list":
                valueString = u", ".join([part.getItemDisplayName()
                                          for part in theValue])
            else:
                valueString = unicode(theValue)

        return valueString

    def SetAttributeValue(self, item, attributeName, valueString):
        try:
            cardinality = item.getAttributeAspect (attributeName, "cardinality")
        except AttributeError:
            cardinality = "single"
        if cardinality == "single":
            if self.GetAttributeValue(item, attributeName) != valueString:
                # The value changed
                if self.allowEmpty() or len(valueString.strip()) > 0:
                    # Either the value's not empty, or we allow empty values.
                    # Write the updated value.
                    # logger.debug("StringAE.SetAttributeValue: changed to '%s' ", valueString)
                    setattr (item, attributeName, valueString)
                    self.AttributeChanged()
                else:
                    # The user cleared out the old value, which isn't allowed. 
                    # Reread the old value from the content model.
                    self.SetControlValue(self.control, 
                                         self.GetAttributeValue(item, attributeName))

    def allowEmpty(self):
        """ 
        Return true if this field allows an empty value to be written
        to the content model. 
        """
        # Defaults to true
        return True

    def getShowingSample(self):
        return getattr(self, '_showingSample', False)
    def setShowingSample(self, value):
        self._showingSample = value
    showingSample = property(getShowingSample, setShowingSample,
                    doc="Are we currently displaying the sample text?")

class ItemNameAttributeEditor(StringAttributeEditor):
    """
    The editor used for editing collection names in the sidebar
    """
    def allowEmpty(self):
        return False
    
class StaticStringAttributeEditor(StringAttributeEditor):
    """
    To be always static, we pretend to be "edit-in-place", but never in 
    'edit' mode.
    """
    def CreateControl(self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):
        return super(StaticStringAttributeEditor, self).\
               CreateControl(False, readOnly, parentWidget, id, parentBlock, font)
    
    def EditInPlace(self):
        return True

class LobImageAttributeEditor (BaseAttributeEditor):

    def ReadOnly (self, (item, attribute)):
        return True

    def CreateControl(self, forEditing, readOnly, parentWidget, id,
                      parentBlock, font):
        return wx.StaticBitmap(parentWidget, id, wx.NullBitmap, (0, 0))

    def __getBitmapFromLob(self, attributeValue):
        input = attributeValue.getInputStream()
        data = input.read()
        input.close()
        stream = cStringIO.StringIO(data)
        image = wx.ImageFromStream(stream)
        # image = image.Scale(width, height)
        return wx.BitmapFromImage(image)

    def BeginControlEdit(self, item, attributeName, control):

        try:
            bmp = self.__getBitmapFromLob(getattr(item, attributeName))
        except Exception, e:
            logger.debug("Couldn't render image (%s)" % str(e))
            bmp = wx.NullBitmap

        control.SetBitmap(bmp)


class DatetimeFormatter(object):
    """This class works around some issues with timezone dependence of
    PyICU DateFormat objects; for details, see:

    <http://wiki.osafoundation.org/bin/view/Journal/GrantBaillie20050809>
    
    @ivar dateFormat: A C{PyICU.DateFormat} object, which we want to
      use to parse or format dates/times in a timezone-aware fashion.
    """



    def __init__(self, dateFormat):
        super(DatetimeFormatter, self).__init__()
        self.dateFormat = dateFormat
        
    def parse(self, string, referenceDate=None):
        """
        @param string: The date/time string to parse
        @type string: C{str} or C{unicode}

        @param referenceDate: Specifies what timezone to use when
            interpretting the parsed result.
        @type referenceDate: C{datetime}

        @return: C{datetime}
        
        @raises: ICUError or ValueError (The latter occurs because
            PyICU DateFormat objects sometimes claim to parse bogus
            inputs like "06/05/0506/05/05". This triggers an exception
            later when trying to create a C{datetime}).
        """

        tzinfo = None
        if referenceDate is not None:
            tzinfo = referenceDate.tzinfo
            
        if tzinfo is None:
            self.dateFormat.setTimeZone(ICUtzinfo.getDefault().timezone)
        else:
            self.dateFormat.setTimeZone(tzinfo.timezone)
        
        timestamp = self.dateFormat.parse(string)
        
        if tzinfo is None:
            # We started with a naive datetime, so return one
            return datetime.fromtimestamp(timestamp)
        else:
            # Similarly, return a naive datetime
            return datetime.fromtimestamp(timestamp, tzinfo)
        
    def format(self, datetime):
        """
        @param datetime: The C{datetime} to format. If it's naive,
            its interpreted as being in the user's default timezone.

        @return: A C{unicode}
        
        @raises: ICUError
        """
        tzinfo = datetime.tzinfo
        if tzinfo is None: tzinfo = ICUtzinfo.getDefault()
        self.dateFormat.setTimeZone(tzinfo.timezone)
        return unicode(self.dateFormat.format(datetime))

class DateTimeAttributeEditor(StringAttributeEditor):
    # Cache formatting info
    shortTimeFormat = DatetimeFormatter(
            DateFormat.createTimeInstance(DateFormat.kShort))
    shortDateFormat = DatetimeFormatter(
            DateFormat.createDateInstance(DateFormat.kShort))
    mediumDateFormat = DatetimeFormatter(
            DateFormat.createDateInstance(DateFormat.kMedium))

    
    symbols = DateFormatSymbols()
    weekdays = symbols.getWeekdays()
    
    def GetAttributeValue(self, item, attributeName):
        itemDateTime = getattr (item, attributeName, None) # getattr will work with properties
        if itemDateTime is None:
            return u''
        
        # [grant] This means we always display datetimes in the
        # user's default timezone in the summary table.
        if itemDateTime.tzinfo is not None:
            itemDateTime = itemDateTime.astimezone(ICUtzinfo.getDefault())

        itemDate = itemDateTime.date()
        today = datetime.today()
        todayDate = today.date()
        if itemDate > todayDate or itemDate < (today + timedelta(days=-5)).date():
            # Format as a date if it's after today, or in the distant past 
            # (same day last week or earlier). (We'll do day names for days
            # in the last week (below), but this excludes this day last week
            # from that, to avoid confusion.)
            value = DateTimeAttributeEditor.mediumDateFormat.format(\
                            itemDateTime)
        elif itemDate == todayDate:
            # Today? Just use the time.
            value = DateTimeAttributeEditor.shortTimeFormat.format(itemDateTime)
        elif itemDate == (today + timedelta(days=-1)).date(): 
            # Yesterday? say so.
            value = _(u'Yesterday')
        else:
            # Do day names for days in the last week. We'll need to convert 
            # python's weekday (Mon=0 .. Sun=6) to PyICU's (Sun=1 .. Sat=7).
            wkDay = ((itemDateTime.weekday() + 1) % 7) + 1
            value = DateTimeAttributeEditor.weekdays[wkDay]

        return value

    def ReadOnly (self, (item, attribute)):
        # @@@MOR Temporarily disable editing of DateTime.  This AE needs some
        # more robust parsing of the date/time info the user enters.
        return True

class DateAttributeEditor (StringAttributeEditor):
    
    def GetAttributeValue (self, item, attributeName):
        try:
            dateTimeValue = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = u''
        else:
            value = dateTimeValue is not None \
                  and DateTimeAttributeEditor.shortDateFormat.format(
                                                          dateTimeValue) \
                  or u''
        return value

    def SetAttributeValue(self, item, attributeName, valueString):
        newValueString = valueString.replace('?','').strip()

        if len(newValueString) == 0:
            return # leave the value alone if the user clears it out.

        oldValue = getattr(item, attributeName, None)

        try:
            dateValue = DateTimeAttributeEditor.shortDateFormat.parse(newValueString, referenceDate=oldValue)
        except ICUError, ValueError:
            self._changeTextQuietly(self.control, "%s ?" % newValueString)
            return
        

        # If this results in a new value, put it back.
        value = (oldValue is None) and dateValue \
              or datetime.combine(dateValue.date(), oldValue.timetz())
        if oldValue != value:
            setattr(item, attributeName, value)
            self.AttributeChanged()
            
        # Refresh the value in place
        if not item.isDeleted():
            self.SetControlValue(self.control, 
                                 self.GetAttributeValue(item, attributeName))
    
    def GetSampleText(self, item, attributeName):
        # We want to build a hint like "mm/dd/yy", but we don't know the locale-
        # specific ordering of these fields. Format a date with distinct values,
        # then replace the resulting string's pieces with text.
        if not hasattr(self, 'cachedSampleText'):
            year4 = u"yyyy"
            year2 = u"yy"
            month = u"mm"
            day   = u"dd"
            sampleText = DateTimeAttributeEditor.shortDateFormat.format(datetime(2003,10,30))
            sampleText = sampleText.replace(u"2003", year4) # Some locales use 4-digit year, some use 2.
            sampleText = sampleText.replace(u"03", year2)   # so we'll handle both.
            sampleText = sampleText.replace(u"10", month)
            sampleText = sampleText.replace(u"30", day)
            self.cachedSampleText = unicode(sampleText)
        return self.cachedSampleText
    
class TimeAttributeEditor(StringAttributeEditor):
    def GetAttributeValue(self, item, attributeName):
        try:
            dateTimeValue = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = u''
        else:
            value = \
                DateTimeAttributeEditor.shortTimeFormat.format(dateTimeValue)
        return value

    def SetAttributeValue(self, item, attributeName, valueString):
        newValueString = valueString.replace('?','').strip()
        if len(newValueString) == 0:
            return # leave the value alone if the user clears it out.
        
        # We have _something_; parse it.
        oldValue = getattr(item, attributeName, None)
        try:
            timeValue = DateTimeAttributeEditor.shortTimeFormat.parse(
                            newValueString, referenceDate=oldValue)
        except ICUError:
            self._changeTextQuietly(self.control, "%s ?" % newValueString)
            return
            

        if oldValue is not None:
            time = datetime.fromtimestamp(timeValue, oldValue.tzinfo).time()
        else:
            time = datetime.fromtimestamp(timeValue).time()

        # If we got a new value, put it back.
        value = datetime.combine(oldValue.date(), time)
        
        if item.anyTime or oldValue != value:
            # Something changed.                
            setattr (item, attributeName, value)
            self.AttributeChanged()
            
        # Refresh the value in the control
        self.SetControlValue(self.control, 
                             self.GetAttributeValue(item, attributeName))

    def GetSampleText(self, item, attributeName):
        # We want to build a hint like "hh:mm PM", but we don't know the locale-
        # specific ordering of these fields. Format a date with distinct values,
        # then replace the resulting string's pieces with text.            
        if not hasattr(self, 'cachedSampleText'):
            hour = u"hh"
            minute = u"mm"
            sampleText = DateTimeAttributeEditor.shortTimeFormat.format(\
                datetime(2003,10,30,11,45))

            sampleText = sampleText.replace("11", hour)
            sampleText = sampleText.replace("45", minute)
            self.cachedSampleText = sampleText
        return self.cachedSampleText

class RepositoryAttributeEditor (StringAttributeEditor):
    """ Uses Repository Type conversion to provide String representation. """
    def ReadOnly (self, (item, attribute)):
        return False # Force editability even if we're in the "read-only" part of the repository

    def GetAttributeValue (self, item, attributeName):
        # attempt to access as a Chandler attribute first
        try:
            attrType = item.getAttributeAspect (attributeName, "type")
        except:
            # attempt to access as a plain Python attribute
            try:
                value = getattr (item, attributeName)
            except AttributeError:
                valueString = "no value"
            else:
                valueString = str (value)
        else:
            value = item.getAttributeValue (attributeName)
            try:
                valueString = attrType.makeString (value)
            except:
                valueString = "no value (%s)" % attrType.itsName
        return valueString

    def SetAttributeValue (self, item, attributeName, valueString):
        # attempt access as a Chandler attribute first
        try:
            attrType = item.getAttributeAspect (attributeName, "type")
        except:
            # attempt access as a plain Python attribute
            try:
                value = getattr (item, attributeName)
            except AttributeError:
                # attribute currently has no value, can't figure out the type
                setattr (item, attributeName, valueString) # hope that a string will work
                self.AttributeChanged()
                return
            else:
                # ask the repository for the type associated with this value
                attrType = ItemHandler.ItemHandler.typeHandler (item.itsView, value)

        # now we can convert the string to the right type
        value = attrType.makeValue (valueString)
        setattr (item, attributeName, value)
        self.AttributeChanged()

class LocationAttributeEditor (StringAttributeEditor):
    """ Knows that the data Type is a Location. """
    def SetAttributeValue (self, item, attributeName, valueString):
        if not valueString:
            try:
                delattr(item, attributeName)
            except AttributeError:
                return # no change
        else:
            # lookup an existing item by name, if we can find it, 
            newValue = Calendar.Location.getLocation (item.itsView, valueString)
            try:
                oldValue = getattr(item, attributeName)
            except AttributeError:
                oldValue = None
            if oldValue is newValue:
                return # no change
            setattr (item, attributeName, newValue)
        
        self.AttributeChanged()

    def CreateControl (self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):
        control = super(LocationAttributeEditor, self).\
                CreateControl(forEditing, readOnly, parentWidget,
                              id, parentBlock, font)
        if forEditing and not readOnly:
            control.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        return control

    def onKeyUp(self, event):
        """
          Handle a Key pressed in the control.
        """
        # logger.debug("LocationAttrEditor: onKeyUp")
        
        control = event.GetEventObject()
        controlValue = self.GetControlValue (control)
        keysTyped = len(controlValue)
        isDelete = event.m_keyCode == wx.WXK_DELETE or event.m_keyCode == wx.WXK_BACK
        if keysTyped > 1 and not isDelete:
            # See if there's exactly one existing Location object whose 
            # displayName starts with the current string; if so, we'll complete
            # on it.
            view = wx.GetApp().UIRepositoryView
            existingLocation = None
            for aLoc in Calendar.Location.iterItems(view):
                if aLoc.displayName[0:keysTyped] == controlValue:
                    if existingLocation is None:
                        existingLocation = aLoc
                        # logger.debug("LocationAE.onKeyUp: '%s' completes!", aLoc.displayName)
                    else:
                        # We found a second candidate - we won't complete
                        # logger.debug("LocationAE.onKeyUp: ... but so does '%s'", aLoc.displayName)
                        existingLocation = None
                        break
                
            if existingLocation is not None:
                completion = existingLocation.displayName
                self.SetControlValue (control, completion)
                # logger.debug("LocationAE.onKeyUp: completing with '%s'", completion[keysTyped:])
                control.SetSelection (keysTyped, len (completion))

class TimeDeltaAttributeEditor (StringAttributeEditor):
    """ Knows that the data Type is timedelta. """

    hourMinuteFormat = SimpleDateFormat("H:mm")
    zeroHours = hourMinuteFormat.parse("0:00")
    dummyDate = datetime(2005,1,1)
    
    def GetAttributeValue (self, item, attributeName):
        # attempt to access as a plain Python attribute
        try:
            value = getattr (item, attributeName)
        except:
            valueString = "HH:MM"
        else:
            valueString = self._format (value)
        return valueString

    def SetAttributeValue (self, item, attributeName, valueString):
        # attempt access as a plain Python attribute
        try:
            value = self._parse(valueString)
        except ValueError:
            pass
        else:
            if self.GetAttributeValue(item, attributeName) != value:
                setattr (item, attributeName, value)
                self.AttributeChanged()

    def _parse(self, inputString):
        """"
          parse the durationString into a timedelta.
        """
        seconds = self.hourMinuteFormat.parse(inputString) - self.zeroHours
        theDuration = timedelta(seconds=seconds)
        return theDuration

    def _format(self, aDuration):
        # if we got a value different from the default
        durationTime = self.dummyDate + aDuration
        value = unicode(self.hourMinuteFormat.format(durationTime))
        return value

class ContactNameAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        try:
            contactName = item.getAttributeValue (attributeName)
        except AttributeError:
            value = ""
        else:
            value = contactName.firstName + ' ' + contactName.lastName
        return value

class ContactAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):

        def computeName(contact):
            return contact.contactName.firstName + ' ' + \
             contact.contactName.lastName

        try:
            contacts = item.getAttributeValue (attributeName)
        except AttributeError:
            value = ""
        else:
            cardinality = item.getAttributeAspect(attributeName, "cardinality")
            if cardinality == "list":
                value = ', '.join([computeName(contact) for contact in contacts])
            else:
                value = computeName(contacts)
        return value

class EmailAddressAttributeEditor (StringAttributeEditor):
    def GetAttributeValue(self, item, attributeName):
        attrValue = getattr(item, attributeName, None)
        if attrValue is not None:
            cardinality = item.getAttributeAspect(attributeName, "cardinality")
            if cardinality == 'list':
                # build a string of comma-separated email addresses
                value = u', '.join(map(lambda x: unicode(x), attrValue))
            else:
                # Just format one address
                value = unicode(attrValue)
        else:
            value = u''
        return value

    def SetAttributeValue(self, item, attributeName, valueString):            
        processedAddresses, validAddresses, invalidCount = \
            Mail.EmailAddress.parseEmailAddresses(item.itsView, valueString)
        if invalidCount == 0:
            # All the addresses were valid. Put them back.
            cardinality = item.getAttributeAspect (attributeName, "cardinality")
            oldValue = self.GetAttributeValue(item, attributeName)
            if oldValue != processedAddresses:
                if cardinality == 'list':
                    # List cardinality.
                    setattr(item, attributeName, validAddresses)
                    self.AttributeChanged()
                else:
                    if len(validAddresses) > 1:
                        # got more than one valid address? That's invalid!
                        processedAddresses = processedAddresses + "?"
                    else:
                        value = len(validAddresses) > 0 \
                              and validAddresses[0] or None
                        setattr(item, attributeName, value)
                        self.AttributeChanged()
                    
        if processedAddresses != valueString:
            # This processing changed the text in the control - update it.
            self._changeTextQuietly(self.control, processedAddresses)

class BasePermanentAttributeEditor (BaseAttributeEditor):
    """ Base class for editors that always need controls """
    def EditInPlace(self):
        return False
    
    def BeginControlEdit (self, item, attributeName, control):
        value = self.GetAttributeValue(item, attributeName)
        self.SetControlValue(control, value)

class AECheckBox(ShownSynchronizer, wx.CheckBox):
    pass

class CheckboxAttributeEditor (BasePermanentAttributeEditor):
    """ A checkbox control. """
    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        # We have to implement Draw, but we don't need to do anything
        # because we've always got a control to do it for us.
        pass

    def CreateControl (self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):
        
        # Figure out the size we should be
        size = wx.DefaultSize
        if font is not None and parentBlock is not None:
            measurements = Styles.getMeasurements(font)
            try:
                parentWidth = parentBlock.minimumSize.width
            except:
                parentWidth = wx.DefaultSize.width
            size = wx.Size(parentWidth,
                           measurements.checkboxCtrlHeight)

        style = wx.TAB_TRAVERSAL
        control = AECheckBox(parentWidget, id, u"", 
                             wx.DefaultPosition, size, style)
        control.Bind(wx.EVT_CHECKBOX, self.onChecked)
        if readOnly:
            control.Enable(False)
        return control
        
    def onChecked(self, event):
        #logger.debug("CheckboxAE.onChecked: new choice is %s", 
                     #self.GetControlValue(event.GetEventObject()))
        control = event.GetEventObject()
        self.SetAttributeValue(self.item, self.attributeName, \
                               self.GetControlValue(control))

    def GetControlValue (self, control):
        """ Are we checked? """
        return control.IsChecked()

    def SetControlValue (self, control, value):
        """ Set our state """
        control.SetValue(value)

class AEChoice(ShownSynchronizer, wx.Choice):
    pass

class ChoiceAttributeEditor(BasePermanentAttributeEditor):
    """ A pop-up control. The list of choices comes from presentationStyle.choices """        
    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        # We have to implement Draw, but we don't need to do anything
        # because we've always got a control to do it for us.
        pass

    def CreateControl (self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):

        # Figure out the size we should be
        size = wx.DefaultSize
        if font is not None and parentBlock is not None:
            measurements = Styles.getMeasurements(font)
            try:
                parentWidth = parentBlock.minimumSize.width
            except:
                parentWidth = wx.DefaultSize.width
            size = wx.Size(parentWidth,
                           measurements.choiceCtrlHeight)

        style = wx.TAB_TRAVERSAL
        control = AEChoice(parentWidget, id, wx.DefaultPosition, size, [], style)
        control.Bind(wx.EVT_CHOICE, self.onChoice)
        if readOnly:
            control.Enable(False)
        return control
        
    def onChoice(self, event):
        control = event.GetEventObject()
        newChoice = self.GetControlValue(control)
        # logger.debug("ChoiceAE.onChoice: new choice is %s", newChoice)
        self.SetAttributeValue(self.item, self.attributeName, \
                               newChoice)

    def GetChoices(self):
        """ Get the choices we're presenting """
        return self.presentationStyle.choices

    def GetControlValue (self, control):
        """ Get the selected choice's text """
        choiceIndex = control.GetSelection()
        if choiceIndex == -1:
            return None
        value = self.item.getAttributeAspect(self.attributeName, 'type').values[choiceIndex]
        return value

    def SetControlValue (self, control, value):
        """ Select the choice with the given text """
        # We also take this opportunity to populate the menu
        existingValue = self.GetControlValue(control)
        if existingValue is None or existingValue != value:            
            # rebuild the list of choices
            choices = self.GetChoices()
            control.Clear()
            control.AppendItems(choices)
        
            try:
                choiceIndex = self.item.getAttributeAspect(self.attributeName, 'type').values.index(value)
            except AttributeError:
                choiceIndex = 0
            control.Select(choiceIndex)

class TimeZoneAttributeEditor(ChoiceAttributeEditor):
    """ A pop-up control for the tzinfo field of a datetime. The list of
    choices comes from the calendar.TimeZone module """
    
    def SetAttributeValue(self, item, attributeName, tzinfo):
        oldValue = getattr(item, attributeName, None)

        if oldValue is not None and tzinfo != oldValue.tzinfo:
            # Something changed.                
            value = oldValue.replace(tzinfo=tzinfo)
            setattr(item, attributeName, value)
                        
            self.AttributeChanged()
            
    def GetAttributeValue(self, item, attributeName):
        value = getattr(item, attributeName, None)
        if value is not None:
            return value.tzinfo
        else:
            return None

    def GetControlValue (self, control):
        """ Get the selected choice's time zone """
        choiceIndex = control.GetSelection()
        if choiceIndex != -1:
            return control.GetClientData(choiceIndex)
        else:
            return None

    def SetControlValue(self, control, value):
        """ Select the choice with the given time zone """
        
        # We also take this opportunity to populate the menu
        existingValue = self.GetControlValue(control)
        if existingValue is None or existingValue != value:
            control.Clear()

            selectIndex = -1
            info = TimeZoneInfo.get(view=self.item.itsView)
            
            canonicalTimeZone = info.canonicalTimeZone(value)

            # rebuild the list of choices
            for name, zone in info.iterTimeZones():
            
                # [@@@] grant: Should be canonicalTimeZone == zone; PyICU bug?
                if canonicalTimeZone is not None and \
                   canonicalTimeZone.timezone == zone.timezone:
                    selectIndex = control.Append(name, clientData=value)
                else:
                    control.Append(name, clientData=zone)

            # Add an entry for "floating" (a tzinfo of None)
            index = control.Append(_(u"Floating"), clientData=None)
            if value is None:
                selectIndex = index
        
            if selectIndex is -1:
                control.Insert(unicode(value), 0, clientData=value)
                selectIndex = 0
                
            if selectIndex != -1:
                control.Select(selectIndex)



    
class IconAttributeEditor (BaseAttributeEditor):
    def ReadOnly (self, (item, attribute)):
        return True # The Icon editor doesn't support editing.

    def GetAttributeValue (self, item, attributeName):
        # simple implementation - get the value, assume it's a string
        try:
            value = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = ""
        return value

    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        dc.SetPen (wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect) # always draw the background
        imageName = self.GetAttributeValue(item, attributeName)
        if len(imageName):
            imageName += ".png"
            image = wx.GetApp().GetImage(imageName)
            if image is not None:
                x = rect.GetLeft() + (rect.GetWidth() - image.GetWidth()) / 2
                y = rect.GetTop() + (rect.GetHeight() - image.GetHeight()) / 2
                dc.DrawBitmap (image, x, y, True)

class EnumAttributeEditor (IconAttributeEditor):
    """
    An attribute editor for enumerated types to be represented as icons. 
    Uses the attribute name, an underscore, and the value name as the image filename.
    (An alternative might be to use the enum type name instead of the attribute name...)
    """
    def GetAttributeValue (self, item, attributeName):
        try:
            value = "%s_%s" % (attributeName, item.getAttributeValue(attributeName))
        except AttributeError:
            value = ''
        return value;

class StampAttributeEditor (IconAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        if isinstance(item, TaskMixin):
            return 'taskStamp'
        elif isinstance(item, Calendar.CalendarEventMixin):
            return 'eventStamp'
        else:
            return ''
