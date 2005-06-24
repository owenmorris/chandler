__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import wx
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.calendar.Calendar as Calendar
import repository.item.ItemHandler as ItemHandler
import repository.item.Query as ItemQuery
import repository.query.Query as Query
from repository.util.Lob import Lob
from osaf.framework.blocks import DragAndDrop
from osaf.framework.blocks import DrawingUtilities
from osaf.framework.blocks import Styles
import logging
import colorsys
from operator import itemgetter
from datetime import datetime, time, timedelta
from PyICU import DateFormat, SimpleDateFormat, ICUError, ParsePosition
from osaf.framework.blocks.Block import ShownSynchronizer

logger = logging.getLogger('ae')
logger.setLevel(logging.INFO)

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

def getInstance (typeName, item, attributeName, presentationStyle):
    """ Get a new unshared instance of the Attribute Editor for this type (and optionally, format). """
    try:
        format = presentationStyle.format
    except AttributeError:
        format = None
    aeClass = _getAEClass(typeName, format)
    # logger.debug("getAEClass(%s [%s, %s]) --> %s", attributeName, typeName, format, aeClass)
    instance = aeClass()        
    return instance

def _getAEClass (type, format=None):
    """ Return the attribute editor class for this type """
    # Once per run, build a map of type -> class
    global _TypeToEditorClasses
    if len(_TypeToEditorClasses) == 0:
        for ae in wx.GetApp().UIRepositoryView.findPath('//parcels/osaf/framework/attributeEditors/AttributeEditors'):
            _TypeToEditorClasses[ae.itsName] = ae.className
        assert _TypeToEditorClasses['_default'] is not None, "Default attribute editor doesn't exist ('_default')"
        
    # If we have a format specified, try to find a specific 
    # editor for type+form. If we don't, just use the type, 
    # and if we don't have a type-specific one, use the "_default".
    classPath = ((format is not None) and _TypeToEditorClasses.get("%s+%s" % (type, format), None)) \
              or _TypeToEditorClasses.get(type, None)
    if classPath is None: # do this separately for now so I can set a breakpoint
        classPath = _TypeToEditorClasses.get("_default", None)

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
        # By default, everything's editable.
        return False

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
    
    def UsePermanentControl(self):
        """ 
        Does this attribute editor use a permanent control (or
        will the control be created when the user clicks)? 
        """
        return False
    
    def MustChangeControl(self, forEditing, existingControl):
        """
        Return False if this control is good enough for displaying
        (forEditing == False) or editing (forEditing == True) in this
        editor, or True if we have to render us up a new one.
        Note that existingControl may be None.
        """
        # Default to "if we have a control, it's good enough".
        return existingControl is None
    
    def CreateControl (self, forEditing, parentWidget, 
                       id, parentBlock, font):
        """ 
        Create and return a control to use for displaying (forEdit=False)
        or editing (forEdit=True) the attribute value.
        """
        raise NotImplementedError
    
    def DestroyControl (self, control, losingFocus=False):
        """ 
        Destroy the control at next idle, by default.
        Return True if we did, or False if we did nothing because we were just
        losing focus.
        """
        wx.CallAfter(control.Destroy)
        return True
 
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
        value = getattr(item, attributeName, None)
        return value

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
        try:
            callback = self.changeCallBack
        except AttributeError:
            pass
        else:
            if callback is not None:
                callback()

    
class AETextCtrl(ShownSynchronizer,
                 DragAndDrop.DraggableWidget,
                 DragAndDrop.DropReceiveWidget,
                 DragAndDrop.TextClipboardHandler,
                 wx.TextCtrl):
    def __init__(self, *arguments, **keywords):
        super (AETextCtrl, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)

    def OnMouseEvents(self, event):
        # trigger a Drag and Drop if we're a single line and all selected
        if self.IsSingleLine() and event.LeftDown():
            selStart, selEnd = self.GetSelection()
            if selStart==0 and selEnd>1 and selEnd==self.GetLastPosition():
                if event.LeftIsDown(): # still down?
                    self.DoDragAndDrop()
                    return # don't skip, eat the click.
        event.Skip()

    """ Try without this:
    def Destroy(self):
        # @@@BJS Hack until we switch to wx 2.5.4: don't destroy if we're already destroyed
        # (in which case we're a PyDeadObject)
        if isinstance(self, AETextCtrl):
            super(AETextCtrl, self).Destroy()
        else:
            pass # (give me a place to set a breakpoint)
    """
    
class AEStaticText(ShownSynchronizer,
                   wx.StaticText):
    """ 
    Wrap wx.StaticText to give it the same GetValue/SetValue behavior
    that other wx controls have. (This was simpler than putting lotsa special
    cases all over the StringAttributeEditor...)
    """
    GetValue = wx.StaticText.GetLabel
    SetValue = wx.StaticText.SetLabel
    
class StringAttributeEditor (BaseAttributeEditor):
    """ 
    Uses a Text Control to edit attributes in string form. 
    Supports sample text.
    """
    
    def UsePermanentControl(self):
        try:
            uc = self.presentationStyle.useControl
        except AttributeError:
            uc = False
        return uc

    def IsFixedWidth(self, blockItem):
        """
        Return True if this control shouldn't be resized to fill its space
        """
        try:
            fixedWidth = self.blockItem.stretchFactor == 0
        except AttributeError:
            fixedWidth = False # yes, let our textctrl fill the space.
        return fixedWidth

    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        """
          Currently only handles left justified single line text.
        """
        
        # If we have a control, it'll do the drawing.
        if self.UsePermanentControl():
            return
        
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
            # @@@ The "gray" color probably needs to be platform- (or theme-)
            # specific...
            textColor = wx.Colour(153, 153, 153)
            dc.SetTextForeground (textColor)

        if len(theText) > 0:
            # Draw inside the lines.
            dc.SetBackgroundMode (wx.TRANSPARENT)
            rect.Inflate (-1, -1)
            dc.SetClippingRect (rect)
            
            # theText = "%s %s" % (dc.GetFont().GetFaceName(), dc.GetFont().GetPointSize())
            DrawingUtilities.DrawWrappedText (dc, theText, rect)
                
            dc.DestroyClippingRegion()
        
    def MustChangeControl(self, forEditing, existingControl):
        must = existingControl is None or \
             (not self.UsePermanentControl() and \
             (forEditing != isinstance(existingControl, AETextCtrl)))
        # logger.debug("StringAE: Must change control is %s (%s, %s)", must, forEditing, existingControl)
        return must

    def CreateControl(self, forEditing, parentWidget, 
                       id, parentBlock, font):
        # logger.debug("StringAE.CreateControl")
        useTextCtrl = forEditing
        if not forEditing:
            try:
                useTextCtrl = parentBlock.presentationStyle.useControl
            except AttributeError:
                pass
                
        # Figure out the size we should be
        # @@@ There's a wx catch-22 here: The text ctrl on Windows will end up
        # horizonally scrolled to expose the last character of the text if this
        # size is too small for the value we put into it. If the value is too
        # large, the sizer won't ever let the control get smaller than this.
        # For now, use 200, a not-too-happy medium that doesn't eliminate either problem.

        if parentBlock is not None and parentBlock.stretchFactor == 0 and parentBlock.size.width != 0 and parentBlock.size.height != 0:
            size = wx.Size(parentBlock.size.width, parentBlock.size.height)
        else:
            if font is not None: # and parentWidget is not None:
                measurements = Styles.getMeasurements(font)
                size = wx.Size(200, # parentWidget.GetRect().width,
                               measurements.textCtrlHeight)
            else:
                size = wx.DefaultSize

        if useTextCtrl:
            style = wx.TAB_TRAVERSAL | wx.TE_AUTO_SCROLL | wx.STATIC_BORDER
            try:
                lineStyleEnum = parentBlock.presentationStyle.lineStyleEnum
            except AttributeError:
                lineStyleEnum = ""
            if lineStyleEnum == "MultiLine":
                style |= wx.TE_MULTILINE
            else:
                style |= wx.TE_PROCESS_ENTER
                
            control = AETextCtrl(parentWidget, id, '', wx.DefaultPosition, 
                                 size, style)
            control.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
            control.Bind(wx.EVT_TEXT, self.onTextChanged)      
            control.Bind(wx.EVT_LEFT_DOWN, self.onClick)
            control.Bind(wx.EVT_SET_FOCUS, self.onGainFocus)
            control.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocus)
            
        else:            
            border = parentWidget.GetWindowStyle() & wx.SIMPLE_BORDER
            control = AEStaticText(parentWidget, id, '', wx.DefaultPosition, 
                                   size,
                                   wx.TAB_TRAVERSAL | border)
        
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
            if isinstance(control, AETextCtrl):
                # @@@BJS I don't think either of these are needed.
                #control.SetSelection (-1,-1)
                #control.SetInsertionPointEnd ()
                pass
        logger.debug("BeginControlEdit: %s (%s) on %s", attributeName, self.showingSample, item)

    def EndControlEdit (self, item, attributeName, control):
        # update the item attribute value, from the latest control value.
        # logger.debug("EndControlEdit: '%s' on %s", attributeName, item)
        if item is not None:
            value = self.GetControlValue (control)
            logger.debug("EndControlEdit: value is '%s' ", value)
            self.SetAttributeValue (item, attributeName, value)
            logger.debug("EndControlEdit: value set.")

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
            self.control.SetSelection(-1,-1)
    
    def onLoseFocus(self, event):
        if self.showingSample:
            self.control.SetSelection(0,0)
    
    def onTextChanged(self, event):
        if not getattr(self, "ignoreTextChanged", False):
            control = event.GetEventObject()
            if getattr(self, 'sampleText', None) is not None:
                # logger.debug("StringAE.onTextChanged: not ignoring.")                    
                currentText = control.GetValue()
                if self.showingSample:
                    # logger.debug("onTextChanged: removing sample")
                    if currentText != self.sampleText:
                        self._changeTextQuietly(control, currentText, False, True)
                elif len(currentText) == 0:
                    self._changeTextQuietly(control, self.sampleText, True, False)
            else:
                pass # logger.debug("StringAE.onTextChanged: ignoring (no sample text)")
        else:
            pass # logger.debug("StringAE.onTextChanged: ignoring (self-changed)")
        
    def _changeTextQuietly(self, control, text, isSample=False, alreadyChanged=False):
        self.ignoreTextChanged = True
        try:
            logger.debug("_changeTextQuietly: %s, to '%s', sample=%s", 
                         self.attributeName, text, isSample)
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
                control.SetValue(text)
    
            if isinstance(control, AETextCtrl):
                if isSample and wx.Window.FindFocus() == control:
                    control.SetSelection (-1,-1)

                # Trying to make the text in the editbox gray doesn't seem to work on Win.
                # (I'm doing it anyway, because it seems to work on Mac.)
                control.SetStyle(0, len(text), wx.TextAttr(textColor))
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
            if control == wx.Control.FindFocus():
                # logger.debug("onClick: ignoring click because we're showing the sample.")
                control.SetSelection(-1, -1) # Make sure the whole thing's still selected
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
            valueString = unicode(getattr(item, attributeName))
        except AttributeError:
            valueString = u""
        else:
            try:
                cardinality = item.getAttributeAspect (attributeName, "cardinality")
            except AttributeError:
                pass
            else:
                if  cardinality == "list":
                    valueString = u", ".join([part.getItemDisplayName() for part in value])
        return valueString

    def SetAttributeValue(self, item, attributeName, valueString):            
        try:
            cardinality = item.getAttributeAspect (attributeName, "cardinality")
        except AttributeError:
            pass
        else:
            if cardinality == "single":
                if self.GetAttributeValue(item, attributeName) != valueString:
                    setattr (item, attributeName, valueString)
                    self.AttributeChanged()
    
    def getShowingSample(self):
        return getattr(self, '_showingSample', False)
    def setShowingSample(self, value):
        self._showingSample = value
    showingSample = property(getShowingSample, setShowingSample,
                    doc="Are we currently displaying the sample text?")
            
class LobAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        try:
            lob = getattr(item, attributeName)
        except AttributeError:
            value = ''
        else:
            # Read the unicode stream
            value = lob.getPlainTextReader().read()
        return value

    def SetAttributeValue(self, item, attributeName, value):            
        oldValue = self.GetAttributeValue(item, attributeName)
        if oldValue != value:
            try:
                lob = getattr(item, attributeName)
            except AttributeError:
                #logger.debug("LobAE.Set: Making new lob for \"%s\"" % value)
                lobType = item.getAttributeAspect (attributeName, "type")
                lob = lobType.makeValue(value)
                setattr(item, attributeName, lob)
            else:
                #logger.debug("LobAE.Set: writing new value to lob: \"%s\"" % value)
                writer = lob.getWriter()
                writer.write(value)
                writer.close()
            self.AttributeChanged()
            #logger.debug("LobAE.set: after changing, new value is \"%s\"" % self.GetAttributeValue(item, attributeName))
        
class DateTimeAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        try:
            itemDate = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = "No date specified"
        else:
            today = datetime.today()
            yesterday = today + timedelta(days=-1)
            beginningOfWeek = today + timedelta(days=-8)
            endOfWeek = today + timedelta(days=-2)
            if today.date == itemDate.date:
                value = itemDate.strftime('%I:%M %p')
            elif yesterday.date == itemDate.date:
                value = 'Yesterday'
            elif itemDate.date >= beginningOfWeek.date and itemDate.date <= endOfWeek.date:
                value = itemDate.strftime('%A')
                pass
            else:
                value = itemDate.strftime('%b %d, %Y')
        return value

    def ReadOnly (self, (item, attribute)):
        # @@@MOR Temporarily disable editing of DateTime.  This AE needs some
        # more robust parsing of the date/time info the user enters.
        return True

class DateAttributeEditor (StringAttributeEditor):
    _format = DateFormat.createDateInstance(DateFormat.kShort)
    
    def GetAttributeValue (self, item, attributeName):
        try:
            dateTimeValue = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = u''
        else:
            value = unicode(DateAttributeEditor._format.format(dateTimeValue))
        return value

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
                dateValue = DateAttributeEditor._format.parse(newValueString)
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

class TimeAttributeEditor (StringAttributeEditor):
    _format = DateFormat.createTimeInstance(DateFormat.kShort)

    def GetAttributeValue (self, item, attributeName):
        noTime = getattr(item, 'allDay', False) \
               or getattr(item, 'anyTime', False)
        if noTime:
            return u''

        try:
            dateTimeValue = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = u''
        else:
            value = unicode(TimeAttributeEditor._format.format(dateTimeValue))
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
            timeValue = TimeAttributeEditor._format.parse(newValueString)
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

    def CreateControl (self, forEditing, parentWidget, 
                       id, parentBlock, font):
        control = super(LocationAttributeEditor, self).\
                CreateControl(forEditing, parentWidget,
                              id, parentBlock, font)
        if forEditing:
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
    def GetAttributeValue (self, item, attributeName):
        try:
            addresses = item.getAttributeValue (attributeName)
        except AttributeError:
            value = ""
        else:
            cardinality = item.getAttributeAspect(attributeName, "cardinality")
            if cardinality == "list":
                # build a string of comma-separated email addresses
                value = ', '.join(map(lambda x: x.emailAddress, addresses))
            else:
                value = addresses.emailAddress
        return value

class BasePermanentAttributeEditor (BaseAttributeEditor):
    """ Base class for editors that always need controls """
    def UsePermanentControl(self):
        return True
    
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

    def CreateControl (self, forEditing, parentWidget, 
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
        return control
        
    def DestroyControl (self, control, losingFocus=False):
        # @@@ still needed?
        # Only destroy the control if we're not just losing focus
        if losingFocus:
            return False # we didn't destroy the control
        
        wx.CallAfter(control.Destroy)
        return True
    
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

class ChoiceAttributeEditor (BasePermanentAttributeEditor):
    """ A pop-up control. The list of choices comes from presentationStyle.choices """        
    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        # We have to implement Draw, but we don't need to do anything
        # because we've always got a control to do it for us.
        pass

    def CreateControl (self, forEditing, parentWidget, 
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
        
    def DestroyControl (self, control, losingFocus=False):
        # Only destroy the control if we're not just losing focus
        if losingFocus:
            return False # we didn't destroy the control
        
        wx.CallAfter(control.Destroy)
        return True
    
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
        if existingValue != value:            
            # rebuild the list of choices
            choices = self.GetChoices()
            control.Clear()
            control.AppendItems(choices)
        
            try:
                choiceIndex = self.item.getAttributeAspect(self.attributeName, 'type').values.index(value)
            except AttributeError:
                choiceIndex = 0
            control.Select(choiceIndex)

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
        if isinstance(item, Task.TaskMixin):
            return 'taskStamp'
        elif isinstance(item, Calendar.CalendarEventMixin):
            return 'eventStamp'
        else:
            return ''
