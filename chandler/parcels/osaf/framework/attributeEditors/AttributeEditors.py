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


"""
Attribute Editors
"""
__parcel__ = "osaf.framework.attributeEditors"

import os, cStringIO, re
import wx
from wx.lib.scrolledpanel import ScrolledPanel
from osaf.pim.tasks import TaskStamp
import osaf.pim as pim
import osaf.pim.calendar.Calendar as Calendar
import osaf.pim.mail as Mail
from osaf.pim.calendar import TimeZoneInfo

import repository.item.ItemHandler as ItemHandler
from repository.util.Lob import Lob
from chandlerdb.util.c import Nil
from osaf.framework.blocks import DragAndDrop, DrawingUtilities, Styles
import logging
from operator import itemgetter
from datetime import datetime, time, timedelta
from PyICU import ICUError, ICUtzinfo, UnicodeString
from osaf.framework.blocks.Block import (ShownSynchronizer, 
                                         wxRectangularChild, debugName)
from osaf.pim.items import ContentItem
from application import schema, styles
from application.dialogs import RecurrenceDialog, TimeZoneList
from util.MultiStateButton import BitmapInfo, MultiStateBitmapCache

from i18n import ChandlerMessageFactory as _
from osaf import messages

import parsedatetime.parsedatetime as parsedatetime
import parsedatetime.parsedatetime_consts as ptc
from datetime import date
import PyICU
from i18n import getLocaleSet

logger = logging.getLogger(__name__)

# Should we do autocompletion? (was handy for turning it off during development)
bigAutocompletionSwitch = True

#
# The attribute editor registration mechanism:
# For each editor, there's one or more AttributeEditorMapping objects that
# map a string to the editor classname. Each one maps a different type (and
# possibly format & readonlyness). The AttributeEditorMapping's constructor
# makes sure that all the instances are referenced from the 
# AttributeEditorMappingCollection, which we use to find them at runtime.

class AttributeEditorMappingCollection(schema.Item):
    """ 
    Singleton item that hosts a collection of all L{AttributeEditorMapping}s
    in existance: L{AttributeEditorMapping}'s constructor adds each new instance
    to us to assure this.
    """
    editors = schema.Sequence(otherName="mappingCollection", initialValue=[])
    
class AttributeEditorMapping(schema.Item):
    """ 
    A mapping from a 'type name' (the name of this L{Item}) to a specific
    L{BaseAttributeEditor} subclass.

    This item's name is a type name (of an attribute) that'll cause this
    editor to be used to present or edit that attribute's value, optionally
    followed by a '+'-separated list of words that, if present, influence
    the attribute editor picking process - see L{getAEClass} for a full
    explanation of how it's used.

    @ivar className: class path (python dotted style) to this attribute editor.
    @type className: String
    """
    className = schema.One(schema.Text)
    mappingCollection = schema.One(otherName="editors")

    def __init__(self, *args, **kwds):
        """ 
        When we construct an L{AttributeEditorMapping}, we need to make sure
        it gets added to the L{AttributeEditorMappingCollection} that tracks
        them.
        """
        super(AttributeEditorMapping, self).__init__(*args, **kwds)

        aeMappings = schema.ns("osaf.framework.attributeEditors", self.itsView).aeMappings
        aeMappings.editors.append(self, alias=self.itsName)

    @classmethod
    def register(cls, parcel, aeDict, moduleName):
        for typeName, className in aeDict.items():
            if className.find('.') == -1:
                className = moduleName + '.' + className
            cls.update(parcel, typeName, className=className)

def installParcel(parcel, oldVersion=None):
    """ 
    Do initial registry of attribute editors.
    
    @param parcel: The parcel we're installing.
    @type parcel: Parcel
    @param oldVersion: @@@ Always None for now.
    @type oldVersion: NoneType
    """

    # Create our one collection of attribute editor mappings; when each gets
    # created, its __init__ will add it to this collection automagically.
    AttributeEditorMappingCollection.update(parcel, "aeMappings")
    
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
    aeDict = {
        '_default': 'RepositoryAttributeEditor',
        'Boolean': 'CheckboxAttributeEditor',
        'EventStamp': 'EventStampAttributeEditor',
        'Contact': 'ContactAttributeEditor',
        'ContactName': 'ContactNameAttributeEditor', 
        'ContentItem': 'StringAttributeEditor', 
        'DateTime': 'DateTimeAttributeEditor', 
        'DateTimeTZ': 'DateTimeAttributeEditor', 
        'DateTime+dateOnly': 'DateAttributeEditor', 
        'DateTimeTZ+dateOnly': 'DateAttributeEditor', 
        'DateTime+timeOnly': 'TimeAttributeEditor',
        'DateTimeTZ+timeOnly': 'TimeAttributeEditor',
        'DateTime+timeZoneOnly': 'TimeZoneAttributeEditor',
        'DateTimeTZ+timeZoneOnly': 'TimeZoneAttributeEditor',
        'EmailAddress': 'EmailAddressAttributeEditor',
        'Integer': 'RepositoryAttributeEditor',
        'Item': 'ItemNameAttributeEditor',
        'image/jpeg': 'LobImageAttributeEditor',
        'Location': 'LocationAttributeEditor',
        'MailStamp': 'MailStampAttributeEditor',
        'TaskStamp': 'TaskStampAttributeEditor',
        'Text': 'StringAttributeEditor',
        'Text+static': 'StaticStringAttributeEditor',
        'Timedelta': 'TimeDeltaAttributeEditor',
        'TimeTransparencyEnum': 'ChoiceAttributeEditor',
        'TriageEnum': 'TriageAttributeEditor',
        'URL': 'StaticStringAttributeEditor',
    }
    AttributeEditorMapping.register(parcel, aeDict, __name__)

_TypeToEditorInstances = {}

def getSingleton (typeName, format=None):
    """
    Get (and cache) a single shared Attribute Editor for this type.
    
    These 'singleton' attribute editor instances are used by the Table block
    and are moved about to edit different items' values as the user selects
    them. We lazily create one of each and cache it at runtime.

    @param typeName: The name of the type of the attribute to be edited
    @type typeName: String
    @param format: Optional, customization for this editor
    @type typeName: String
    @return: The attribute editor instance
    @rtype: BaseAttributeEditor
    """
    try:
        instance = _TypeToEditorInstances [(typeName, format)]
    except KeyError:
        aeClass = getAEClass (typeName, format=format)
        logger.debug("getSingleton(%s, %s) --> %s", 
                     typeName, format, aeClass)
        instance = aeClass()
        _TypeToEditorInstances [(typeName, format)] = instance
    return instance

def getInstance(typeName, cardinality, item, attributeName, readOnly, presentationStyle):
    """
    Get a new unshared instance of the Attribute Editor for this type
    (and optionally, format).

    These unshared instances are used in the detail view; we don't cache them.

    @param typeName: The name of the type of the attribute to be edited,
        optionally including "+"-separated parameters; see L{getAEClass} for
        explanation of how the mechanism works.
    @type typeName: String
    @param item: The item whose attribute is to be edited.
    @type item: Item
    @param attributeName: The attributeName of the item to be edited.
    @type attributeName: String
    @param presentationStyle: Behavior customization for this editor, or None.
    @type presentationStyle: PresentationStyle
    @return: The attribute editor instance
    @rtype: BaseAttributeEditor
    """
    try:
        format = presentationStyle.format
    except AttributeError:
        format = None
    if typeName == "Lob" and hasattr(item, attributeName):
        typeName = getattr(item, attributeName).mimetype
    aeClass = getAEClass(typeName, cardinality, readOnly, format)
    #logger.debug("getAEClass(%s [%s, %s, %s]%s) --> %s", 
                 #attributeName, typeName, cardinality, format, 
                 #readOnly and ", readOnly" or "", aeClass)
    instance = aeClass()        
    return instance

def getAEClass(typeName, cardinality='single', readOnly=False, format=None):
    """ 
    Decide which attribute editor class to use for this type.
    
    We'll try several ways to find an appropriate editor, considering
    cardinality, readonlyness, and format, if any are provided, before
    falling back to not considering them. As a last resort, we'll use the
    '_default' one.

    @param typeName: The type name (or MIME type) of the type we'll be editing.
    @type typeName: String
    @param cardinality: The cardinality of the attribute: 'single', 'list', or 'set'.
    @type cardinality: String
    @param readOnly: True if this attribute is readOnly.
    @type readOnly: Boolean
    @param format: Format customization string, if any.
    @return: the attribute editor class to use.
    @rtype: class
    """
    def generateEditorTags():
        # Generate all permutations, most-complex first.
        formatList = format is not None and ('+%s' % format, '',) or ('',)
        readOnlyList = readOnly and ('+readOnly', '',) or ('',)
        cardinalityList = cardinality != 'single' \
                        and ('+%s' % cardinality, '',) or ('',)
        for c in cardinalityList:
            for f in formatList:
                for r in readOnlyList:
                    yield "%s%s%s%s" % (typeName, c, f, r)
        logger.warn("AttributeEditors.getAEClass: using _default for %s/%s",
                    typeName, format)
        yield "_default"

    uiView = wx.GetApp().UIRepositoryView
    aeMappings = schema.ns("osaf.framework.attributeEditors", uiView).aeMappings
    classPath = None
    for key in generateEditorTags():
        key = aeMappings.editors.resolveAlias(key) # either a UUID or None
        if key is not None:
            classPath = aeMappings.editors[key].className
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
    """
    Base class for Attribute Editors.
    """
        
    def ReadOnly (self, (item, attribute)):
        """ 
        Should the user be allowed to edit this attribute of this item?

        By default, everything's editable if the item says it is.
        Can be overridden to provide more-complex behavior.

        @param item: the item we'll test.
        @type item: Item
        @param attribute: the name of the attribute we'll test.
        @type attribute: String
        @return: True if this Attribute Editor shouldn't edit, else False.
        @rtype: Boolean
        """
        try:
            isAttrModifiable = item.isAttributeModifiable
        except AttributeError:
            return False
        else:
            return not isAttrModifiable(attribute)

    def Draw (self, dc, rect, (item, attributeName), isInSelection=False):
        """ 
        Draw the value of the this item attribute.
        
        Used only for shared attribute editors (used by the Summary Table),
        not for AEs in the detail view.
        
        @param dc: The device context in which we'll draw
        @type dc: DC
        @param rect: the rectangle in which to draw
        @type rect: Rect
        @param item: the item whose attribute we'll be drawing
        @type item: Item
        @param isInSelection: True if this row is selected
        @type isInSelection: Boolean
        """
        raise NotImplementedError

    def IsFixedWidth(self):
        """
        Should this item keep its size, or be expanded to fill its space?

        Most classes that don't use a TextCtrl will be fixed width, so we
        default to "keep its size".

        @return: True if this control is of fixed size, and shouldn't be 
        expanded to fill its space.
        @rtype: Boolean
        """
        return True

    def EditInPlace(self):
        """
        Will this attribute editor change controls when the user clicks on it?

        @return: True if this editor will change controls
        @rtype: Boolean
        """
        return False

    def CreateControl (self, forEditing, readOnly, parentWidget,
                       id, parentBlock, font):
        """ 
        Create and return a widget to use for displaying (forEdit=False)
        or editing (forEdit=True) the attribute value.
        
        @param forEditing: True if for editing, False if just displaying.
        @type forEditing: Boolean
        @param readOnly: True if we want to tell the control not to let the user
        edit the value.
        @type readOnly: Boolean
        @param parentWidget: The new widget will be a child of this widget.
        @type wx.Widget
        @param id: The wx ID to use for the new widget
        @type id: Integer
        @param parentBlock: The Block associated with this widget.
        @type parentBlock: Block
        @param font: The font to draw in
        @type font: wx.Font
        @returns: The new widget
        @rtype: wx.Widget
        """
        raise NotImplementedError
    
    def BeginControlEdit (self, item, attributeName, control):
        """
        Load this attribute's value into the editing control.

        Note that the name is a bit of a misnomer; this routine will be
        called whenever we think the value in the domain model needs to
        be loaded (or re-loaded) into the control - such as when it's
        changed externally.

        Don't assume balanced BeginControlEdit/L{EndControlEdit} calls!

        @param item: The Item from which we'll get the attribute value
        @type item: Item
        @param attributeName: the name of the attribute in the item to edit
        @type attributeName: String
        @param control: the control we'd previously created for this editor
        @type control: wx.Widget
        """
        pass # do nothing by default

    def EndControlEdit (self, item, attributeName, control):
        """ 
        Save the control's value into this attribute. Called whenever we think
        it's time to commit the user's edits.

        @param item: The Item where we'll store the attribute value
        @type item: Item
        @param attributeName: the name of the attribute in the item
        @type attributeName: String
        @param control: the control we'd previously created for this editor
        @type control: wx.Widget
        """
        # Do nothing by default.
        pass        
    
    def GetControlValue (self, control):
        """
        Get the value from the control.

        L{GetControlValue}/L{SetControlValue} and L{GetAttributeValue}/
        L{SetAttributeValue} all work together.

        The choice of value type is up to the developer; it just needs to be as
        precise as the value being stored (so that a round-trip is a no-op). See
        various subclass' implementations to help you decide; these are
        interesting:
         - L{ChoiceAttributeEditor} uses the label string, to avoid relying on
         list indexes that might change if the choices might change
         - L{DateAttributeEditor} uses the formatted date string
         - L{CheckboxAttributeEditor} uses Boolean

        @param control: The widget
        @type control: wx.Widget
        @returns: The value, in an appropriate type
        """
        value = control.GetValue()
        return value

    def SetControlValue (self, control, value):
        """ 
        Set the value in the control.

        See L{GetControlValue} for background.

        @param control: The widget
        @type control: wx.Widget
        @param value: The value to set, in an appropriate type.
        """
        control.SetValue (value)

    def GetAttributeValue (self, item, attributeName):
        """
        Get the value from the specified attribute of the item.

        See L{GetControlValue} for background.

        @param item: The item to get the value from
        @type item: Item
        @param attributeName: The name of the attribute whose value we're
        operating on
        @type attributeName: String
        @returns: the value in an appropriate type
        """
        return getattr(item, attributeName, None)

    def SetAttributeValue (self, item, attributeName, value):
        """
        Set the value of the attribute given by the value.

        See L{GetControlValue} for background.

        @param item: The item to store the value in
        @type item: Item
        @param attributeName: The name of the attribute whose value we're
        operating on
        @type attributeName: String
        @param value: The value to store, in an appropriate type
        """
        if not self.ReadOnly((item, attributeName)):
            setattr(item, attributeName, value)
    
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
        """
        Build and display our context menu
        """
        self.SetFocus()
        
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
            NotifyBlockToSaveValue(self)

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
        NotifyBlockToSaveValue(self)

    def onPasteEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanPaste()

    def onPasteEvent(self, event):
        self.Paste()
        NotifyBlockToSaveValue(self)

    def onClearEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanClear()
    
    def onClearEvent(self, event):
        self.Clear()
        NotifyBlockToSaveValue(self)
    
    def onRedoEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanRedo()

    def onRedoEvent(self, event):
        self.Redo()
        NotifyBlockToSaveValue(self)

    def onUndoEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.CanUndo()
    
    def onUndoEvent(self, event):
        self.Undo()
        NotifyBlockToSaveValue(self)

    def onRemoveEventUpdateUI(self, event):
        (startSelect, endSelect) = self.GetSelection()
        event.arguments ['Enable'] = startSelect < self.GetLastPosition()

    def onDeleteEventUpdateUI(self, event):
        """
        Bug 5717, OnDelete shouldn't be active in a text ctrl on Mac.
        """
        event.arguments['Enable'] = '__WXMAC__' not in wx.PlatformInfo

    def onRemoveEvent(self, event):
        # I tried the following code, but it didn't work. Perhaps it's
        # related to bug (#3978). So I rolled my own. -- DJA
        #keyEvent = wx.KeyEvent()
        #keyEvent.m_keyCode = wx.WXK_DELETE
        #self.EmulateKeyPress (keyEvent)
        (startSelect, endSelect) = self.GetSelection()
        if startSelect < self.GetLastPosition():
            if startSelect == endSelect:
                endSelect += 1
            self.Remove (startSelect, endSelect)

    onDeleteEvent = onRemoveEvent

    def onSelectAllEventUpdateUI(self, event):
        event.arguments ['Enable'] = self.GetLastPosition() > 0

    def onSelectAllEvent(self, event):
        self.SetSelection(-1, -1)

    def ActivateInPlace(self):
        self.SelectAll()
        
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
    For some reason, wx.StaticText uses GetLabel/SetLabel instead of
    GetValue/SetValue; also, its Label functions don't display single
    ampersands 'cuz they might be menu accelerators.

    To solve both these problems, I've added implementations of
    GetValue/SetValue that double any embedded ampersands.
    """
    def GetValue(self):
        """
        Get the label, un-doubling any embedded ampersands
        """
        return self.GetLabel().replace(u'&&', u'&')
    
    def SetValue(self, newValue):
        """
        Set the label, doubling any embedded ampersands
        """
        self.SetLabel(newValue.replace(u'&', u'&&'))
    
def NotifyBlockToSaveValue(widget):
    """
    Notify this widget's block to save its value when we lose focus
    """
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
        # We used to reflect read-onlyness in type-over-text fields
        # by not switching to edit mode. Now, we switch to edit mode, 
        # but the control makes itself readonly -- this is more consistent,
        # and "copy" works.
        #try:
            #readOnlyMethod = self.editor.ReadOnly
            #item = self.editor.item
            #attributeName = self.editor.attributeName
        #except AttributeError:
            #pass
        #else:
            ## If we're read-only, we want to ignore the click and not turn 
            ## editable. (Also, note: no Skip())
            #if readOnlyMethod((item, attributeName)):
                #return 
            
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
        if event.m_keyCode == wx.WXK_RETURN and \
           not getattr(event.GetEventObject(), 'ateLastKey', False):
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

    def GetInsertionPoint(self): return self.shownControl.GetInsertionPoint()
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

    def IsEditable(self):
        return self.editControl.IsEditable()
    
    def SetEditable(self, editable):
        self.editControl.SetEditable(editable)

class wxAutoCompleter(wx.ListBox):
    """
    A listbox that pops up for autocompletion.
    """
    # For now, measuring the font isn't working well;
    # use these 'adjustments'
    # @@@ ugh: ought to find a better way than this!
    if '__WXMAC__' in wx.PlatformInfo:
        totalSlop = 5
        unitSlop = 4
        defaultBorderStyle = wx.STATIC_BORDER
    elif '__WXGTK__' in wx.PlatformInfo:
        totalSlop = 2
        unitSlop = 4        
        defaultBorderStyle = wx.SIMPLE_BORDER
    else:
        totalSlop = 0
        unitSlop = 0
        defaultBorderStyle = wx.SIMPLE_BORDER

    def __init__(self, parent, adjacentControl, completionCallback, 
                 style=wx.LB_NEEDED_SB | wx.LB_SINGLE | defaultBorderStyle):
        self.choices = []
        self.completionCallback = completionCallback
        self.adjacentControl = adjacentControl
        
        super(wxAutoCompleter, self).__init__(parent, id=wx.ID_ANY,
                                              choices=[u""],
                                              size=wx.Size(0,0),
                                              style=style)
        self.reposition()
        theFont = adjacentControl.GetFont()
        self.lineHeight = Styles.getMeasurements(theFont).height
                
        # self.SetFont(theFont)
        self.Bind(wx.EVT_LEFT_DOWN, self.onListClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.onListClick)
        eatEvent = lambda event: None
        self.Bind(wx.EVT_RIGHT_DOWN, eatEvent)
        self.Bind(wx.EVT_RIGHT_DCLICK, eatEvent)

        self.Raise() # make us appear on top

    def reposition(self):
        """
        Put us in the proper spot, relative to the control we're supposed
        to be adjacent to.
        """
        # Convert the position of the control in its own coordinate system
        # to global coordinates, then back to the coordinate system of the 
        # our parent window... offset by the height of the original control,
        # so we'll appear below it.
        adjacentControl = self.adjacentControl
        adjControlBounds = adjacentControl.GetRect()
        pos = self.GetParent().ScreenToClient(\
            adjacentControl.GetParent().ClientToScreen(adjControlBounds.GetPosition()))
        pos.y += adjControlBounds.height
        self.SetPosition(pos)

    def resize(self):
        """
        Make us the proper size, given our current list of choices.
        """
        size = self.GetAdjustedBestSize()
        size.height = ((self.lineHeight + self.unitSlop) * len(self.choices)) \
            + self.totalSlop
        self.SetClientSize(size)

    def onListClick(self, event):
        """ 
        Intercept clicks: by handling them 'raw', we prevent the popup
        from stealing focus.
        """
        # Figure out which entry got hit
        index = event.GetPosition().y / (self.lineHeight + self.unitSlop)
        if index < len(self.choices):            
            self.SetSelection(index)
            self.completionCallback(self.GetStringSelection())
        # Eat the event - don't skip.

    def processKey(self, keyCode):
        """
        If this key is useful in autocompletion, process it and
        return True. Otherwise, return False.
        """
        if keyCode == wx.WXK_ESCAPE:
            self.completionCallback(None)
            return True

        selectionIndex = self.GetSelection() 
        if keyCode == wx.WXK_DOWN:
            selectionIndex += 1
            if selectionIndex < len(self.choices):
                self.SetSelection(selectionIndex)
            return True

        if keyCode == wx.WXK_UP:
            selectionIndex -= 1
            if selectionIndex >= 0:
                self.SetSelection(selectionIndex)
            return True
        
        if keyCode == wx.WXK_RETURN:
            # Finish autocompleting, if we have a selection
            if selectionIndex != wx.NOT_FOUND:
                self.completionCallback(self.GetStringSelection())
                return True
            
        if keyCode == wx.WXK_TAB:
            # Finish autocompleting, if we have a selection
            if selectionIndex != wx.NOT_FOUND:
                self.completionCallback(self.GetStringSelection())

        return False
            
    def updateChoices(self, choices):
        choices = sorted(set(unicode(c) for c in choices))
        if self.choices != choices:
            self.choices = choices
            self.Set(choices)
            self.resize()
            self.SetSelection(0)   #selects the first choice in the list

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
        Return True if this control shouldn't be resized to fill its space.
        """
        try:
            fixedWidth = self.blockItem.stretchFactor == 0.0
        except AttributeError:
            fixedWidth = False # yes, let our textctrl fill the space.
        return fixedWidth

    def Draw (self, dc, rect, (item, attributeName), isInSelection=False):
        """
        Draw this control's value; used only by Grid when the attribute's not
        being edited.

        Note: @@@ Currently only handles left justified single line text.
        """
        item = RecurrenceDialog.getProxy(u'ui', item, createNew=False)
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
                
        # We'll do autocompletion if someone implements the get-matches method
        doAutoCompletion = bigAutocompletionSwitch \
                         and getattr(type(self), 'generateCompletionMatches',  
                                     None) is not None

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
            bindToControl = control.editControl
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
            bindToControl = control
            bindToControl.Bind(wx.EVT_LEFT_DOWN, self.onClick)

            # hack to work around bug 5669 until the underlying wx bug is fixed.
            if '__WXMAC__' in wx.PlatformInfo: 
                def showhide(ctrl):
                    if ctrl and ctrl.IsShown():
                        ctrl.Hide()
                        ctrl.Show()
                wx.CallAfter(showhide, control)

        bindToControl.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        if doAutoCompletion: # We only need these if we're autocompleting:
            bindToControl.Bind(wx.EVT_KEY_UP, self.onKeyUp)
            bindToControl.Bind(wx.EVT_SIZE, self.onResize)
            bindToControl.Bind(wx.EVT_MOVE, self.onMove)
        bindToControl.Bind(wx.EVT_TEXT, self.onTextChanged)
        bindToControl.Bind(wx.EVT_SET_FOCUS, self.onGainFocus)
        bindToControl.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocus)

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
        self.manageCompletionList() # get rid of the popup, if we have one.        
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
    
            control.SetEditable(not self.ReadOnly((self.item, self.attributeName)))
            
            control.SetForegroundColour(textColor)
            if hasattr(control, 'SetStyle'):
                # Trying to make the text in the editbox gray doesn't seem to work on Win.
                # (I'm doing it anyway, because it seems to work on Mac.)
                control.SetStyle(0, len(text), wx.TextAttr(textColor))
                
                if isSample and self._isFocused(control):
                    control.SelectAll()
        finally:
            del self.ignoreTextChanged

    def onMove(self, event):
        """
        Reposition any autocompletion popup when we're moved.
        """
        # we seem to be getting extra Size events on Linux... ignore them.
        autocompleter = getattr(self, 'autocompleter', None)
        if autocompleter is not None:
            autocompleter.resize()
        event.Skip()

    def onResize(self, event):
        """
        Reposition any autocompletion popup when we're moved.
        """
        autocompleter = getattr(self, 'autocompleter', None)
        if autocompleter is not None:
            autocompleter.reposition()
        event.Skip()
        
    def _findAutocompletionParent(self):
        """
        Find a widget to hang the autocompletion popup from, and return it.
        Return None if no suitable widget found.
        """
        # We need to hang the completion popup off a window up the tree from 
        # where we are, since it wants to overlap our neighboring controls.
        # 
        # We used to hang ourselves off the top-level window, but a fix
        # for a toolbar redrawing bug involved turning on WS_EX_BUFFERED_DRAW
        # on various widgets - and for some unknown reason, buffered drawing prevents
        # this popup from appearing (bug 6190). So, we'll walk up our widget 
        # tree until we find our event boundary (that is, our view), and hang 
        # the popup off of that; this has the side benefit that if our view gets 
        # unrendered, this widget will be destroyed automatically.
        topLevelWindow = wx.GetTopLevelParent(self.control)
        parentWindow = None
        p = self.control
        while p is not topLevelWindow:
            # We'd better not hit a widget w/buffering before we find the view!
            assert (p.GetExtraStyle() & wx.WS_EX_BUFFERED_DRAW == 0)

            block = getattr(p, 'blockItem', None)
            if block is not None and block.eventBoundary:
                return p
            p = p.GetParent()
            
        # Oops - didn't find a view!
        return None

    def manageCompletionList(self, matches=None):
        """
        Update the autocompletion popup if necessary.
        If no matches are provided, any popup will be taken down.
        """
        autocompleter = getattr(self, 'autocompleter', None)
        if matches is not None and len(matches) > 0:
            if autocompleter is None:
                acParent = self._findAutocompletionParent()
                if acParent is None:
                    return
                autocompleter = wxAutoCompleter(acParent, self.control,
                                                self.finishCompletion)
                self.autocompleter = autocompleter
                #logger.debug("Presenting completion list on %s", debugName(self))
            #else:
                #logger.debug("Updating completion list on %s", debugName(self))
            autocompleter.updateChoices(matches)
        elif autocompleter is not None:
            #logger.debug("Destroying completion list on %s", debugName(self))
            autocompleter.Destroy()
            del self.autocompleter

    def findCompletionRange(self, value, insertionPoint):
        """
        Find the range of characters that autocompletion should replace, given
        the control's current value and the insertion point.

        Returns a tuple containing the index of the first character
        and one past the last character to be replaced.
        """
        # By default, we'll replace the whole string.
        start = 0
        end = len(value)
        
        # but if this is a 'list', we'll use separators
        try:
            cardinality = self.item.getAttributeAspect(self.attributeName, "cardinality")
        except AttributeError:
            pass
        else:
            if cardinality == 'list':
                for c in _(u',;'):
                    prevSep = value.rfind(c, 0, insertionPoint) + 1
                    if prevSep > start: 
                        start = prevSep
                    nextSep = value.find(c, insertionPoint)
                    if nextSep != -1 and nextSep < end:
                        end = nextSep

        return (start, end)
    
    # code used to test the above in a previous incarnation...
    #def testCompletionReplacement():
        #for v in ('ab, cd;ef, gh;', 'b', 'ab', ',foo,'):
            #for sep in ('', ';', ',', ',;'):
                #print "'%s' x '%s':" % (v, sep)
                #for i in range(0,len(v) + 1):
                    #(start, end) = findCompletionRange(v, i, sep)
                    #z = v[:start] + (start and ' ' or '') + 'xy' + v[end:]
                    #print "  %d: (%d, %d, '%s' -> '%s')" % (i, start, end, v[start:end], z)
            
    def finishCompletion(self, completionString):
        if completionString is not None: # it's not 'ESCAPE'
            control = self.control
            controlValue = self.GetControlValue(control)
            insertionPoint = control.GetInsertionPoint()
            (start, end) = self.findCompletionRange(controlValue, 
                                                    insertionPoint)
            # Prepend a space if we're completing partway in (like
            # the second thing in a list
            if start:
                completionString = ' ' + completionString
            newValue = (controlValue[:start] +
                        completionString + 
                        controlValue[end:])
            self.SetControlValue(self.control, newValue)
            newInsertionPoint = start + len(completionString)
            self.control.SetSelection(newInsertionPoint, newInsertionPoint)
        self.manageCompletionList() # get rid of the popup
                    
    def onKeyDown(self, event):
        """
        Handle a key pressed in the control, part one: at 'key-down',
        we'll note whether we'll be replacing the sample, and if
        we're doing autocompletion, we'll look for keys that we
        might want to prevent from being processed by the control
        (the ones that we want to handle in the completion popup).
        """
        # If we're doing completion, give the autocomplete menu a chance
        # at the keystroke - if it takes it, we won't event.Skip().
        control = event.GetEventObject()
        autocompleter = getattr(self, 'autocompleter', None)
        if autocompleter is not None:
            if autocompleter.processKey(event.m_keyCode):
                control.ateLastKey = True
                return # no event.Skip() - we'll eat the keyDown.

        # If we're showing sample text and this key would only change the 
        # selection, ignore it.
        if self.showingSample and event.GetKeyCode() in \
           (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_BACK):
             # logger.debug("onKeyDown: Ignoring selection-changer %s (%s) while showing the sample text", event.GetKeyCode(), wx.WXK_LEFT)
             control.ateLastKey = True
             return # skip out without calling event.Skip()
        # logger.debug("onKeyDown: processing %s (%s)", event.GetKeyCode(), wx.WXK_LEFT)
        control.ateLastKey = False
        event.Skip()

    def onKeyUp(self, event):
        """
        Handle a Key pressed in the control, part two: at 'key-up',
        the key's already been processed into the control; we can react
        to it, maybe by doing autocompletion.
        """
        if bigAutocompletionSwitch:
            control = event.GetEventObject()
            ateLastKey = getattr(control, 'ateLastKey', False)
            if not ateLastKey:
                matchGenerator = getattr(type(self), 'generateCompletionMatches', None)
                if matchGenerator is not None:
                    controlValue = self.GetControlValue(control)
                    insertionPoint = control.GetInsertionPoint()
                    (start, end) = self.findCompletionRange(controlValue,
                                                            insertionPoint)
                    target = controlValue[:end].rstrip()
                    targetEnd = len(target)
                    target = target[start:].lstrip()
                    matches = []
                    if len(target) > 0 and targetEnd <= insertionPoint and \
                       event.GetKeyCode() != wx.WXK_RETURN:
                        # We have at least two characters, none after the 
                        # insertion point, and this isn't a return. Find matches,
                        # but not too many.
                        count = 0
                        for m in matchGenerator(self, target):
                            count += 1
                            if count > 15:
                                # Don't show any if we find too many
                                matches = []
                                break
                            matches.append(m)
                    self.manageCompletionList(matches)
        event.Skip()

    def onClick(self, event):
        """
        Ignore clicks if we're showing the sample
        """
        control = event.GetEventObject()
        if self.showingSample:
            if self._isFocused(control):
                # logger.debug("onClick: ignoring click because we're showing the sample.")
                control.SelectAll() # Make sure the whole thing's still selected
        else:
            event.Skip()

    def GetSampleText(self, item, attributeName):
        """
        Return this attribute's sample text, or None if there isn't any.
        """
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
        return sampleText

    def HasValue(self, item, attributeName):
        """
        Return True if a non-default value has been set for this attribute,
        or False if this value is the default and deserves the sample text
        (if any) instead. (Can be overridden.)
        """
        try:
            v = getattr(item, attributeName)
        except AttributeError:
            return False

        return len(unicode(v)) > 0

    def GetAttributeValue(self, item, attributeName):
        """
        Get the attribute's current value
        """
        theValue = getattr(item, attributeName, Nil)
        if theValue is Nil:
            valueString = u""
        else:
            cardinality = item.getAttributeAspect(attributeName, 'cardinality',
                                                  True, None, 'single')
            if cardinality == "single":
                if theValue is None:
                    valueString = u""
                else:
                    valueString = unicode(theValue)
            elif cardinality in ("list", "set"):
                valueString = _(u", ").join([unicode(part) for part in theValue])

        return valueString

    def SetAttributeValue(self, item, attributeName, valueString):
        if self.GetAttributeValue(item, attributeName) == valueString:
            return # no change.

        # The value changed
        # logger.debug("StringAE.SetAttributeValue: changed to '%s' ", valueString)
        if self.allowEmpty() or len(valueString.strip()) > 0:
            # Either the value's not empty, or we allow empty values.
            # Write the updated value.
            try:
                cardinality = item.getAttributeAspect (attributeName, "cardinality")
            except AttributeError:
                cardinality = "single"
            if cardinality == "single":
                value = valueString
            elif cardinality == "list" or cardinality == "set":
                value = map(unicode.strip, valueString.split(_(u",")))
            setattr(item, attributeName, value)
        else:
            # The user cleared out the old value, which isn't allowed. 
            # Reread the old value from the domain model.
            self.SetControlValue(self.control, 
                                 self.GetAttributeValue(item, attributeName))            

    def allowEmpty(self):
        """ 
        Return true if this field allows an empty value to be written
        to the domain model.
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
    The editor used for editing collection names in the sidebar.
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
               CreateControl(False, True, parentWidget, id, parentBlock, font)
    
    def EditInPlace(self):
        return True

    def ReadOnly (self, (item, attribute)):
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

class DateTimeAttributeEditor(StringAttributeEditor):
    def GetAttributeValue(self, item, attributeName):
        # Never used anymore, since we're drawing ourselves below and we're read-only.
        return u''

    def ReadOnly (self, (item, attribute)):
        # @@@MOR Temporarily disable editing of DateTime.  This AE needs some
        # more robust parsing of the date/time info the user enters.
        return True

    def Draw (self, dc, rect, (item, attributeName), isInSelection=False):
        """
        Draw the date & time, somewhat in the style that Apple Mail does:
        Date left justified, time right justified.
        """
        item = RecurrenceDialog.getProxy(u'ui', item, createNew=False)

        # Erase the bounding box
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect (rect)

        # Figure out what to draw.
        itemDateTime = getattr (item, attributeName, None) # getattr will work with properties
        if itemDateTime is None:
            return # don't draw anything.
        
        # [grant] This means we always display datetimes in the
        # user's default timezone in the summary table.
        if itemDateTime.tzinfo is not None:
            itemDateTime = itemDateTime.astimezone(ICUtzinfo.default)

        itemDate = itemDateTime.date()
        today = datetime.today()
        todayDate = today.date()
        dateString = None
        timeString = None
        preferDate = True
        if itemDate > todayDate or itemDate < (today + timedelta(days=-5)).date():
            # Format as a date if it's after today, or in the distant past 
            # (same day last week or earlier). (We'll do day names for days
            # in the last week (below), but this excludes this day last week
            # from that, to avoid confusion.)
            pass
        elif itemDate == todayDate:
            # Today? say so, and show the time if we only have room for one value
            preferDate = False
            dateString = _(u'Today')
        elif itemDate == (today + timedelta(days=-1)).date(): 
            # Yesterday? say so.
            dateString = _(u'Yesterday')
        else:
            # Do day names for days in the last week.
            dateString = pim.weekdayName(itemDateTime)

        if dateString is None:
            dateString = pim.mediumDateFormat.format(itemDateTime)
        if timeString is None:
            timeString = pim.shortTimeFormat.format(itemDateTime)

        # Draw inside the lines.
        dc.SetBackgroundMode (wx.TRANSPARENT)
        rect.Inflate (-1, -1)
        dc.SetClippingRect (rect)
        
        dateWidth, ignored = dc.GetTextExtent(dateString)
        timeWidth, ignored = dc.GetTextExtent(timeString)
        spaceWidth, ignored = dc.GetTextExtent('  ')

        # If we don't have room for both values, draw one, clipped if necessary.
        if (dateWidth + timeWidth + spaceWidth) > rect.width:
            if preferDate:
                DrawingUtilities.DrawClippedTextWithDots(dc, dateString, rect)
            else:
                DrawingUtilities.DrawClippedTextWithDots(dc, timeString, rect,
                                                         alignRight=True)
        else:
            # Enough room to draw both            
            dc.DrawText(dateString, rect.x + 1, rect.y + 1)
            dc.DrawText(timeString, rect.x + rect.width - (timeWidth + 2), rect.y + 1)
        
        dc.DestroyClippingRegion()
            
class DateAttributeEditor (StringAttributeEditor):
    
    # natural language strings for date
    dateStr = [(u'Today',_(u'Today')), (u'Tomorrow',_(u'Tomorrow')),
                     ( u'Yesterday',_(u'Yesterday')), (u'EOW',_(u'End of week'))]
    
    # Add weekdays of the current locale
    us_weekDays = PyICU.DateFormatSymbols(PyICU.Locale.getUS()).getWeekdays()
    current_weekDays = PyICU.DateFormatSymbols().getWeekdays()
    dateStr.extend(zip(us_weekDays,current_weekDays))
    
    # Add month names of the current locale
    us_months = PyICU.DateFormatSymbols(PyICU.Locale.getUS()).getMonths()
    current_months = PyICU.DateFormatSymbols().getMonths()
    dateStr.extend(zip(us_months,current_months))
    
    textMatches = dict(dateStr)

    
    @classmethod
    def parseDate(cls, target):
        """Parses Natural Language date strings using parsedatetime library."""
        target = target.lower()
        for matchKey in cls.textMatches:
            #natural language string for date found
            if ((cls.textMatches[matchKey]).lower()).startswith(target):
                cal = parsedatetime.Calendar()
                (dateVar, invalidFlag) = cal.parse(matchKey)
                #invalidFlag is True if the string cannot be parsed successfully
                if dateVar is not None and invalidFlag is False:
                    dateStr = pim.shortDateFormat.format(datetime(*dateVar[:3]))
                    matchKey = cls.textMatches[matchKey]+ " : %s" % dateStr
                    yield matchKey
            else:
                cal = parsedatetime.Calendar(ptc.Constants(str(getLocaleSet()[0])))
                (dateVar, invalidFlag) = cal.parse(target)
                if dateVar is not None and invalidFlag is False:
                    # temporary fix: parsedatetime sometimes returns day == 0
                    if not filter(lambda x: not x, dateVar[:3]):
                        match = pim.shortDateFormat.format(datetime(*dateVar[:3]))
                        if unicode(match).lower() != target:
                            yield match
                        break
                

    def GetAttributeValue (self, item, attributeName):
        dateTimeValue = getattr(item, attributeName, None)
        value = dateTimeValue and \
                pim.shortDateFormat.format(dateTimeValue) or u''
        return value

    def SetAttributeValue(self, item, attributeName, valueString):
        newValueString = valueString.replace('?','').strip()

        if len(newValueString) == 0:
            return # leave the value alone if the user clears it out.

        oldValue = getattr(item, attributeName, None)
        if oldValue is None:
            oldValue = datetime.now(ICUtzinfo.default).\
                       replace(hour=0, minute=0, second=0, microsecond=0)

        try:
            dateValue = pim.shortDateFormat.parse(newValueString, 
                                                  referenceDate=oldValue)
        except (ICUError, ValueError):
            self._changeTextQuietly(self.control, "%s ?" % newValueString)
            return
        

        # If this results in a new value, put it back.
        if oldValue is not None:
            value = datetime.combine(dateValue.date(), oldValue.timetz())
        elif dateValue:
            value = dateValue.replace(tzinfo=ICUtzinfo.floating)
        else:
            value = None
        if oldValue != value:
            setattr(item, attributeName, value)
            
        # Refresh the value in place
        if not item.isDeleted():
            self.SetControlValue(self.control, 
                                 self.GetAttributeValue(item, attributeName))
    
    def GetSampleText(self, item, attributeName):
        return pim.sampleDate # get a hint like "mm/dd/yy"
        
    def generateCompletionMatches(self, target):
        return self.parseDate(target)
        
    def finishCompletion(self, completionString):
        if completionString is not None:
            dashIndex = completionString.find(' : ')
            if dashIndex != -1: # could be 'tomorrow - 08/02/2006'
                completionString = completionString[dashIndex + 3:]
        return super(DateAttributeEditor, self).finishCompletion(completionString)

    
class TimeAttributeEditor(StringAttributeEditor):

    #natural language strings for time
    textMatches = {'Lunch':_(u'Lunch'),'Evening':_(u'Evening'),'Noon':_(u'Noon'),
                   'Midnight':_(u'Midnight'),'Breakfast':_(u'Breakfast'),'Now':_(u'Now'),
                   'Morning':_(u'Morning'),'Dinner':_(u'Dinner'),'Tonight':_(u'Tonight'),
                   'Night':_(u'Night'),u'EOD':_(u'End of day')}
    
    @classmethod
    def parseTime(cls, target):
        """Parses Natural Language time strings using parsedatetime library."""
        target = target.lower()
        for matchKey in cls.textMatches:
            #natural language time string found
            if ((cls.textMatches[matchKey]).lower()).startswith(target):
                cal = parsedatetime.Calendar() 
                (timeVar, invalidFlag) = cal.parse(matchKey)
                #invalidFlag is True if the string cannot be parsed successfully
                if timeVar is not None and invalidFlag is False:
                    timeVar = pim.shortTimeFormat.format(datetime(*timeVar[:5]))
                    matchKey = cls.textMatches[matchKey]+ " - %s" %timeVar
                    yield matchKey
            else:
                cal = parsedatetime.Calendar() 
                (timeVar, invalidFlag) = cal.parse(target)
                if timeVar != None and invalidFlag is False:
                    match = pim.shortTimeFormat.format(datetime(*timeVar[:5]))
                    if unicode(match).lower() !=target:
                        yield match
                    break

    def GetAttributeValue(self, item, attributeName):
        dateTimeValue = getattr(item, attributeName, None)
        value = dateTimeValue and \
                pim.shortTimeFormat.format(dateTimeValue) or u''
        return value

    def SetAttributeValue(self, item, attributeName, valueString):
        newValueString = valueString.replace('?','').strip()
        if len(newValueString) == 0:
            return # leave the value alone if the user clears it out.
        
        # We have _something_; parse it.
        oldValue = getattr(item, attributeName, None)
        if oldValue is None:
            oldValue = datetime.now(ICUtzinfo.default)
        try:
            timeValue = pim.shortTimeFormat.parse(newValueString, 
                                                  referenceDate=oldValue)
        except ICUError:
            self._changeTextQuietly(self.control, "%s ?" % newValueString)
            return
            
        # If we got a new value, put it back.
        value = datetime.combine(oldValue.date(), timeValue.timetz())
        # Preserve the time zone!
        value = value.replace(tzinfo=oldValue.tzinfo)
        
        if value != oldValue:
            setattr(item, attributeName, value)
            
        # Refresh the value in the control
        self.SetControlValue(self.control, 
                             self.GetAttributeValue(item, attributeName))

    def generateCompletionMatches(self, target):
        """
        A really simple autocompletion example: if the only entry would
        be a valid hour, provide completion of AM & PM versions of it.

        Note: @@@ This may not be right for the product, but I'm leaving it in for now.
        """

        try:
            hour = int(target)
        except ValueError:
            for matchKey in self.parseTime(target):
                yield matchKey
        else:
            if hour < 24:
                if hour == 12:
                    yield pim.shortTimeFormat.format(datetime(2003,10,30,0,00))
                yield pim.shortTimeFormat.format(datetime(2003,10,30,hour,00))
                if hour < 12:
                    yield pim.shortTimeFormat.format(
                        datetime(2003,10,30,hour + 12,00))

    def finishCompletion(self, completionString):
        if completionString is not None:
            dashIndex = completionString.find(' - ')
            if dashIndex != -1: # could be 'noon - 12:00 PM'
                completionString = completionString[dashIndex + 3:]
        return super(TimeAttributeEditor, self).finishCompletion(completionString) 
        
    def GetSampleText(self, item, attributeName):
        return pim.sampleTime # Get a hint like "hh:mm PM"

class RepositoryAttributeEditor (StringAttributeEditor):
    """
    Uses Repository Type conversion to provide String representation.
    """
    def ReadOnly (self, (item, attribute)):
        return False # Force editability even if we're in the "read-only" part of the repository

    def GetAttributeValue (self, item, attributeName):
        # attempt to access as a Chandler attribute first
        attrType = item.getAttributeAspect(attributeName, 'type', True)
        value = getattr(item, attributeName, Nil)
        if value is Nil:
            if attrType is None:
                valueString = "no value"
            else:
                valueString = "no value (%s)" % attrType.itsName
        elif attrType is None:
            valueString = str(value)
        else:
            valueString = attrType.makeString(value)

        return valueString

    def SetAttributeValue (self, item, attributeName, valueString):
        # attempt access as a Chandler attribute first
        attrType = item.getAttributeAspect(attributeName, "type", True)
        if attrType is None:
            attrType = ItemHandler.ItemHandler.typeHandler(item.itsView,
                                                           valueString)

        # now we can convert the string to the right type
        value = attrType.makeValue (valueString)
        setattr (item, attributeName, value)

class LocationAttributeEditor (StringAttributeEditor):
    """
    Knows that the data Type is a Location.
    """
    def SetAttributeValue (self, item, attributeName, valueString):
        if not valueString:
            if getattr(item, attributeName, None) is None:
                return # no change
            setattr(item, attributeName, None)
        else:
            # lookup an existing item by name, if we can find it, 
            newValue = Calendar.Location.getLocation (item.itsView, valueString)
            oldValue = getattr(item, attributeName, None)
            if oldValue is newValue:
                return # no change
            setattr (item, attributeName, newValue)
        
    def CreateControl (self, forEditing, readOnly, parentWidget, 
                       id, parentBlock, font):
        control = super(LocationAttributeEditor, self).\
                CreateControl(forEditing, readOnly, parentWidget,
                              id, parentBlock, font)
        if not readOnly:
            editControl = forEditing and control or control.editControl
            editControl.Bind(wx.EVT_KEY_UP, self.onKeyUp)
            editControl.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        return control

    def generateCompletionMatches(self, target):
        view = wx.GetApp().UIRepositoryView
        target = UnicodeString(target).toLower()
        targetLength = len(target)
        for aLoc in Calendar.Location.iterItems(view):
            dispName = UnicodeString(aLoc.displayName).toLower()
            if (dispName[:targetLength] == target
                and dispName != target):
                yield aLoc

class TimeDeltaAttributeEditor (StringAttributeEditor):
    """
    Knows that the data Type is timedelta.
    """

    zeroHours = pim.durationFormat.parse("0:00")
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

    def _parse(self, inputString):
        """
        Parse the durationString into a timedelta.
        """
        seconds = pim.durationFormat.parse(inputString) - self.zeroHours
        theDuration = timedelta(seconds=seconds)
        return theDuration

    def _format(self, aDuration):
        # if we got a value different from the default
        durationTime = self.dummyDate + aDuration
        value = unicode(pim.durationFormat.format(durationTime))
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
                else:
                    if len(validAddresses) > 1:
                        # got more than one valid address? That's invalid!
                        processedAddresses = processedAddresses + "?"
                    else:
                        value = len(validAddresses) > 0 \
                              and validAddresses[0] or None
                        setattr(item, attributeName, value)
                    
        if processedAddresses != valueString:
            # This processing changed the text in the control - update it.
            self._changeTextQuietly(self.control, processedAddresses)

    def generateCompletionMatches(self, target):
        view = wx.GetApp().UIRepositoryView
        return Mail.EmailAddress.generateMatchingEmailAddresses(view, target)

class BasePermanentAttributeEditor (BaseAttributeEditor):
    """
    Base class for editors that always need controls.
    """
    def EditInPlace(self):
        return False
    
    def BeginControlEdit (self, item, attributeName, control):
        value = self.GetAttributeValue(item, attributeName)
        self.SetControlValue(control, value)
        control.Enable(not self.ReadOnly((item, attributeName)))

    def EndControlEdit(self, item, attributeName, control):
        # update the item attribute value, from the latest control value.
        # logger.debug("EndControlEdit: '%s' on %s", attributeName, item)
        if item is not None:
            value = self.GetControlValue (control)
            self.SetAttributeValue (item, attributeName, value)

class AECheckBox(ShownSynchronizer, wx.CheckBox):
    pass

class CheckboxAttributeEditor (BasePermanentAttributeEditor):
    """
    A checkbox control.
    """
    def Draw (self, dc, rect, (item, attributeName), isInSelection=False):
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
        """
        Are we checked?
        """
        return control.IsChecked()

    def SetControlValue (self, control, value):
        """
        Set our state.
        """
        control.SetValue(value)

class AEChoice(ShownSynchronizer, wx.Choice):
    def ActivateInPlace(self):
        """
        Force the pop-up to pop up so the user can select an item.
        """
#       # this is a total hack that doesn't work right now.. 
#       from osaf.framework import scripting
#       scripting.User.emulate_click(self.control, 2, 2)
        pass

    def GetValue(self):
        return self.GetStringSelection()

class ChoiceAttributeEditor(BasePermanentAttributeEditor):
    """
    A pop-up control. The list of choices comes from presentationStyle.choices.
    """
    def Draw (self, dc, rect, (item, attributeName), isInSelection=False):
        """
        Assumes that the attribute is an enum, and uses that to draw
        the locale-sensitive string returned from GetChoices().
        """
        item = RecurrenceDialog.getProxy(u'ui', item, createNew=False)
        # Erase the bounding box
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)

        dc.DrawRectangleRect (rect)
        
        # get the index of the value, and use that to find the
        # locale-specific value from GetValues()
        value = self.GetAttributeValue(item, attributeName)
        attrType = item.getAttributeAspect(attributeName, 'type')
        choiceIndex = attrType.values.index(value)
        theText = self.GetChoices()[choiceIndex]
        
        rect.Inflate (-1, -1)
        
        dc.SetClippingRect (rect)

        DrawingUtilities.DrawClippedTextWithDots (dc, theText, rect)

        dc.DestroyClippingRegion()

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
        return control
        
    def onChoice(self, event):
        control = event.GetEventObject()
        newChoice = self.GetControlValue(control)
        # logger.debug("ChoiceAE.onChoice: new choice is %s", newChoice)
        self.SetAttributeValue(self.item, self.attributeName, \
                               newChoice)

    def GetChoices(self):
        """
        Get the choices we're presenting
        """
        return self.presentationStyle.choices

    def GetControlValue (self, control):
        """
        Get the selected choice's text
        """
        choiceIndex = control.GetSelection()
        if choiceIndex == -1:
            return None
        value = self.item.getAttributeAspect(self.attributeName, 'type').values[choiceIndex]
        return value

    def SetControlValue (self, control, value):
        """
        Select the choice with the given text
        """
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
            
    def BeginControlEdit(self, item, attributeName, control):
        self.item = item
        self.attributeName = attributeName
        self.control = control
        super(ChoiceAttributeEditor, self).BeginControlEdit(item, attributeName, control)

class TimeZoneAttributeEditor(ChoiceAttributeEditor):
    """
    A pop-up control for the tzinfo field of a datetime. The list of
    choices comes from the calendar.TimeZone module.
    """

    def __init__(self, *args, **kwargs):
        super(TimeZoneAttributeEditor, self).__init__(*args, **kwargs)
        self._ignoreChanges = False

    def SetAttributeValue(self, item, attributeName, tzinfo):
        if not self._ignoreChanges:
            oldValue = getattr(item, attributeName, None)

            if oldValue is not None and tzinfo != oldValue.tzinfo:
                # Something changed.                
                value = oldValue.replace(tzinfo=tzinfo)
                setattr(item, attributeName, value)

    def GetAttributeValue(self, item, attributeName):
        value = getattr(item, attributeName, None)
        if value is not None:
            return value.tzinfo
        else:
            return None

    def GetControlValue (self, control):
        """
        Get the selected choice's time zone
        """
        choiceIndex = control.GetSelection()
        if choiceIndex != -1:
            value = control.GetClientData(choiceIndex)
            
            # handle the "Other..." option
            if not self._ignoreChanges and \
               value == TimeZoneList.TIMEZONE_OTHER_FLAG:
                # Opening the pickTimeZone dialog will trigger lose focus, don't
                # process changes to this AE while the dialog is up
                self._ignoreChanges = True
                newTimeZone = TimeZoneList.pickTimeZone(self.item.itsView)
                self._ignoreChanges = False
                # no timezone returned, set the choice back to the item's tzinfo
                if newTimeZone is None:
                    dt = getattr(self.item, self.attributeName, None)
                    if dt is not None:
                        newTimeZone = dt.tzinfo
                TimeZoneList.buildTZChoiceList(self.item.itsView, control,
                                               newTimeZone)
                return newTimeZone
            else:
                return value
        else:
            return None

    def SetControlValue(self, control, value):
        """
        Select the choice with the given time zone
        """

        if value is None:
            value = ICUtzinfo.floating

        # We also take this opportunity to populate the menu
        # @@@ for now, we always do it, since we can't tell whether we were
        # called because the prefs changed. This might adversely affect
        # performance, however, which is why I've added this comment.
        #existingValue = self.GetControlValue(control)
        if True: # existingValue is None or existingValue != value:
            # logger.debug("Rebuilding DV timezone popup again") # see how often this happens.
            TimeZoneList.buildTZChoiceList(self.item.itsView, control, value)

class TriageAttributeEditor(BaseAttributeEditor):
    def Draw (self, dc, rect, (item, attributeName), isInSelection=False):
        # Get the value we'll draw, and its label
        item = RecurrenceDialog.getProxy(u'ui', item, createNew=False)
        value = getattr(item, attributeName, '')
        label = value and pim.getTriageStatusName(value) or u''

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
        (labelWidth, labelHeight, labelDescent, ignored) = dc.GetFullTextExtent(label)
        labelTop = rect.y + ((rect.height - labelHeight) / 2)
        labelLeft = rect.x + ((rect.width - labelWidth) / 2)
        dc.DrawText(label, labelLeft, labelTop)

    def OnMouseChange(self, event, cell, isIn, isDown, (item, attributeName)):
        """
        Handle live changes of mouse state related to our cell.
        """
        # Note down-ness changes; eat the event if the downness changed, and
        # trigger an advance if appropriate.
        if isDown != getattr(self, 'wasDown', False):
            if isIn and not isDown:
                oldValue = self.GetAttributeValue(item, attributeName)
                newValue = pim.getNextTriageStatus(oldValue)
                self.SetAttributeValue(item, attributeName, newValue)                
            if isDown:
                self.wasDown = True
            else:
                del self.wasDown
        else:
            event.Skip()

class IconAttributeEditor (BaseAttributeEditor):
    """
    Base class for an icon-based attribute editor; subclass and provide
    management of state & variations on the icons.
    """
    bitmapCache = MultiStateBitmapCache()

    # A mapping from the various variation inputs (is the mouse down? is
    # the mouse over us? are we in a selected row? is this item readonly?)
    # to the variation name we should use
    rolledOverBit = 1
    selectedBit = 2
    mouseDownBit = 4
    readOnlyBit = 8
    variationMap = {
        0 : 'normal',
        rolledOverBit: 'rollover',
        selectedBit: 'selected',
        selectedBit | rolledOverBit: 'rolloverselected',
        mouseDownBit: 'normal', # note, this is the not-rollover case: mouse out
        mouseDownBit | rolledOverBit: 'mousedown', # mouse in
        mouseDownBit | selectedBit: 'selected',
        mouseDownBit | selectedBit | rolledOverBit: 'rolloverselected',
        # @@@ Change these if we need special read/only icons
        readOnlyBit: "normal",
        readOnlyBit | rolledOverBit: "normal",
        readOnlyBit | selectedBit: "selected",
        readOnlyBit | selectedBit | rolledOverBit: 'selected',
        readOnlyBit | mouseDownBit: 'normal', 
        readOnlyBit | mouseDownBit | rolledOverBit: 'normal',
        readOnlyBit | mouseDownBit | selectedBit: 'selected',
        readOnlyBit | mouseDownBit | selectedBit | rolledOverBit: 'selected',
    }

    def __init__(self, *args, **kwds):
        super(IconAttributeEditor, self).__init__(*args, **kwds)
        IconAttributeEditor.bitmapCache.AddStates(\
            multibitmaps=self.makeStates(),
            bitmapProvider=wx.GetApp().GetImage)

    def GetAttributeValue (self, item, attributeName):
        """ 
        Get the current state name. Simple implementation assumes that the 
        configured attribute holds it, and if no attribute value is present,
        no icon should be shown.
        """
        return getattr(item, attributeName, '')
    
    def getImageVariation(self, item, attributeName, isDown, isSelected, isOver):
        """ Pick the right variation """
        readOnly = self.ReadOnly((item, attributeName)) \
                 and IconAttributeEditor.readOnlyBit or 0
        selected = isSelected and IconAttributeEditor.selectedBit or 0
        mouseDown = isDown and IconAttributeEditor.mouseDownBit or 0
        rolledOver = isOver and IconAttributeEditor.rolledOverBit or 0
        return IconAttributeEditor.variationMap[readOnly | selected |
                                                mouseDown | rolledOver]

    def Draw (self, dc, rect, (item, attributeName), isInSelection=False):
        """
        Draw the appropriate variation from the set of icons for this state.
        """
        proxyItem = RecurrenceDialog.getProxy(u'ui', item, createNew=False)
        dc.SetPen (wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect) # always draw the background
        state = self.GetAttributeValue(proxyItem, attributeName)
        imageSet = self.bitmapCache.get(state)
        if imageSet is None:
            return # no images for this state (or we didn't get a state value)
        
        isDown = getattr(self, 'wasDown', False)
        isOver = getattr(self, 'rolledOverItem', None) is item

        imageVariation = self.getImageVariation(item, attributeName, 
                                                isDown, isInSelection, isOver)
        
        image = getattr(imageSet, imageVariation, None)
        if image is not None:
            x = rect.GetLeft() + (rect.GetWidth() - image.GetWidth()) / 2
            y = rect.GetTop() + (rect.GetHeight() - image.GetHeight()) / 2
            dc.DrawBitmap(image, x, y, True)

    def OnMouseChange(self, event, cell, isIn, isDown, (item, attributeName)):
        """
        Handle live changes of mouse state related to our cell.
        """
        # Note whether the in-ness changed
        wasIn = getattr(self, 'rolledOverItem', None)
        if (not isIn) or (wasIn is not item):
            if isIn:
                self.rolledOverItem = item
            else:
                del self.rolledOverItem
            #logger.debug("Rolled over: %s" % getattr(self, 'rolledOverItem', None))

        # Note down-ness changes; eat the event if the downness changed, and
        # trigger an advance if appropriate.
        downChanged = isDown != getattr(self, 'wasDown', False)
        advanceStateMethod = getattr(self, 'advanceState', None)
        if downChanged and advanceStateMethod is not None:
            if isIn and not isDown:
                advanceStateMethod(item, attributeName)
            if isDown:
                self.wasDown = True
            else:
                del self.wasDown
            #logger.debug("Downness now %s" % getattr(self, 'wasDown', False))
            #logger.debug("AE NOT calling event.Skip")
        else:
            #logger.debug("AE Calling event.Skip")
            event.Skip()
    
class StampAttributeEditor(IconAttributeEditor):
    """
    Base class for attribute editors used for the stamping 
    columns in the summary. Subclasses need to define a 
    "stampClass" attribute that points at the stamp class to be used.
    """
    
    noImage = "pixel" # filename of a one-pixel transparent png

    def _getStateName(self, isStamped):
        return "%s.%s" % (self.iconPrefix,
                         isStamped and "Stamped" or "Unstamped")
        
    def makeStates(self):
        prefix = self.iconPrefix
        states = []
        for (state, normal, selected) in ((False, StampAttributeEditor.noImage,
                                                  StampAttributeEditor.noImage),
                                          (True, "%sStamped" % prefix,
                                                 "%sStamped-Reversed" % prefix)):
            bmInfo = BitmapInfo()
            bmInfo.stateName = self._getStateName(state)
            bmInfo.normal = normal
            bmInfo.selected = selected
            bmInfo.rollover = "%sRollover" % prefix
            bmInfo.rolloverselected = "%sRollover-Reversed" % prefix
            bmInfo.mousedown = "%sPressed" % prefix
            states.append(bmInfo)

        return states

    def ReadOnly(self, (item, attributeName)):
        # Our "attributeName" is a Stamp; substitute a real attribute.
        readOnly = super(StampAttributeEditor, self).ReadOnly((item, 'body'))

        # @@@BJS: added Morgan's temporary disabling of stamping of shared
        # items, as in Detail.py's DetailStampButton._isStampable()
        readOnly = readOnly or (item.getSharedState() != ContentItem.UNSHARED)
        
        return readOnly
    
    def GetAttributeValue(self, item, attributeName):
        isStamped = pim.has_stamp(item, self.stampClass)
        return self._getStateName(isStamped)
    
    def SetAttributeValue(self, item, attributeName, value):
        isStamped = pim.has_stamp(item, self.stampClass)
        if isStamped != (value == self._getStateName(True)):
            # Stamp or unstamp the item
            stampedObject = self.stampClass(item)
            if isStamped:
                stampedObject.remove()
            else:
                stampedObject.add()

    def advanceState(self, item, attributeName):
        isStamped = pim.has_stamp(item, self.stampClass)
        newValue = self._getStateName(not isStamped)
        self.SetAttributeValue(item, attributeName, newValue)        

class EventStampAttributeEditor(StampAttributeEditor):
    stampClass = Calendar.EventStamp
    iconPrefix = "SumEvent"
    
    def makeStates(self):
        states = [
            BitmapInfo(stateName="%s.Unstamped" % self.iconPrefix,
                       normal=StampAttributeEditor.noImage,
                       selected=StampAttributeEditor.noImage,
                       rollover="EventTicklerRollover",
                       rolloverselected="EventTicklerRolloverSelected",
                       mousedown="EventTicklerMousedown"),
            BitmapInfo(stateName="%s.Stamped" % self.iconPrefix,
                       normal="SumEventStamped",
                       selected="SumEventStamped-Reversed",
                       rollover="EventTicklerRollover",
                       rolloverselected="EventTicklerRolloverSelected",
                       mousedown="EventTicklerMousedown"),
            BitmapInfo(stateName="%s.Tickled" % self.iconPrefix,
                       normal="EventTickled",
                       selected="EventTickledSelected",
                       rollover="EventTicklerRollover",
                       rolloverselected="EventTicklerRolloverSelected",
                       mousedown="EventTicklerMousedown"),
        ]
        return states
    
    def GetAttributeValue(self, item, attributeName):
        return pim.Remindable(item).getUserReminder(expiredToo=False) \
            and ("%s.Tickled" % self.iconPrefix) \
            or super(EventStampAttributeEditor, self).\
                     GetAttributeValue(item, attributeName)

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
        now = datetime.now(tz=ICUtzinfo.default)
        if now.hour < 17:
            # Today at 5PM
            reminderTime = now.replace(hour=17, minute=0, 
                                       second=0, microsecond=0)
        else:
            # Tomorrow at 8AM
            reminderTime = now.replace(hour=8, minute=0,
                                       second=0, microsecond=0) + \
                           timedelta(days=1)
        remindable.userReminderTime = reminderTime
        
class TaskStampAttributeEditor(StampAttributeEditor):
    stampClass = TaskStamp
    iconPrefix = "SumTask"

class MailStampAttributeEditor(StampAttributeEditor):
    stampClass = Mail.MailStamp
    iconPrefix = "SumMail"
    
