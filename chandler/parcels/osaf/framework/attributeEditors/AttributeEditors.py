__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import os
import wx
import mx.DateTime as DateTime
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.calendar.Calendar as Calendar
import repository.item.ItemHandler as ItemHandler
import repository.item.Query as ItemQuery
import repository.query.Query as Query
import osaf.framework.blocks.DrawingUtilities as DrawingUtilities
import osaf.framework.blocks.Styles as Styles
import logging
from operator import itemgetter

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
        instance = aeClass (True, typeName, item=None, attributeName=None, presentationStyle=None)
        _TypeToEditorInstances [typeName] = instance
    return instance

def getInstance (typeName, item, attributeName, presentationStyle):
    """ Get a new unshared instance of the Attribute Editor for this type (and optionally, format). """
    try:
        format = presentationStyle.format
    except AttributeError:
        format = None
    aeClass = _getAEClass(typeName, format)
    logger.debug("getAEClass(%s [%s, %s]) --> %s" % (attributeName, typeName, format, aeClass))    
    instance = aeClass (False, typeName, item=item, attributeName=attributeName, presentationStyle=presentationStyle)        
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
    def __init__(self, isShared, typeName, item=None, attributeName=None, presentationStyle=None):
        """ 
        Create a shared, or unshared instance of an Attribute Editor. 
        
        @param isShared: tells if this Attribute Editor is shared among
                  several values (e.g. Grid uses a single AE for a whole
                  column).
        @type isShared: boolean
        @param typeName: the string name of this type
        @type typeName: str
        @param presentationStyle: gives style information to the AE
        @type presentationStyle: reference to PresentationStyle item, or
                  None when isShared is True (default presentation).
        Unshared instances may store data in attributes of self, but
        that may cause trouble for shared Attribute Editors instances.
        """
        self.isShared = isShared
        
        # Note the characteristics that made us pick this editor
        self.typeName = typeName
        self.attributeName = attributeName
        self.presentationStyle = presentationStyle
        
        # And the item we're editing, if we have it
        self.item = item

    def ReadOnly (self, (item, attribute)):
        """ Return True if this Attribute Editor refuses to edit """
        # By default, everything's editable.
        return False

    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        """ Draw the value of the attribute in the specified rect of the dc """
        raise NotImplementedError
    
    def UsePermanentControl(self):
        """ 
        Does this attribute editor use a permanent control (or
        will the control be created when the user clicks)? 
        """
        return False

    def CreateControl (self, parent, id):
        """ 
        Create and return a control to use for editing the attribute value. 
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
        # @@@ BJS For now, make sure the strings we return are Unicode.
        # This'll go away when we build wx with the "unicode" flag.
        if isinstance(value, str): value = unicode(value)
        assert not isinstance(value, str)
        return value

    def SetControlValue (self, control, value):
        """ Set the value in the control. """
        # @@@BJS For now, make sure the strings we put in the controls 
        # are Unicode.
        assert not isinstance(value, str)
        control.SetValue (value)

    def GetAttributeValue (self, item, attributeName):
        """ Get the value from the specified attribute of the item. """
        value = getattr(item, attributeName, None)
        # @@@BJS For now, make sure the strings we put in the content model 
        # are Unicode. This'll go away when we build wx with the unicode flag.
        assert not isinstance(value, str)
        return value

    def SetAttributeValue (self, item, attributeName, value):
        """ Set the value of the attribute given by the value. """
        if not self.ReadOnly((item, attributeName)):
            # @@@BJS For now, make sure the strings we put in the content model 
            # are Unicode. This'll go away when we build wx with the 
            # "unicode" flag.
            # if isinstance(value, str): value = unicode(value)
            assert not isinstance(value, str)
            setattr(item, attributeName, value)

class myTextCtrl(wx.TextCtrl):
    def Destroy(self):
        # @@@BJS Hack until we switch to wx 2.5.4: don't destroy if we're already destroyed
        # (in which case we're a PyDeadObject)
        if isinstance(self, wx.TextCtrl):
            super(myTextCtrl, self).Destroy()
        else:
            pass # (give me a place to set a breakpoint)

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

    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        """
          Currently only handles left justified single line text.
        """
        
        # If we have a control, it'll do the drawing.
        if self.UsePermanentControl():
            return
        
        if False:
            logger.debug("StringAE.Draw: %s, %s of %s; %s in selection",
                         self.isShared and "shared" or "dv",
                         attributeName, item,
                         isInSelection and "is" or "not")

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
        
    def CreateControl (self, parent, id):
        # create a text control for editing the string value
        logger.debug("StringAE.CreateControl")
        
        size = wx.DefaultSize
        if False:
            try:
                isMultiline = self.presentationStyle.multiLine
            except:
                isMultiline = False
            if not isMultiline:
                font = parent.GetFont()
                try:
                    size.height = Styles.getMeasurements(font).textCtrlHeight
                except AttributeError:
                    pass
            
        control = myTextCtrl(parent, id, '', wx.DefaultPosition, 
                             size,
                             wx.TE_PROCESS_TAB | wx.TE_AUTO_SCROLL)
        control.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        control.Bind(wx.EVT_TEXT, self.onTextChanged)
        control.Bind(wx.EVT_LEFT_DOWN, self.onClick)
        
        if not self.isShared:
            # Inflate us to our parent's size
            parentRect = parent.GetRect()
            control.SetSizeHints(minW=parentRect.width, minH=parentRect.height)
            controlSize = wx.Rect(wx.DefaultPosition[0], wx.DefaultPosition[0], parentRect.width, parentRect.height)
            logger.debug("StringAE.CreateControl: created; control size is %s", controlSize)    
            control.SetRect(controlSize)

        return control

    def BeginControlEdit (self, item, attributeName, control):
        self.sampleText = self.GetSampleText(item, attributeName)
        self.item = item
        self.attributeName = attributeName
        logger.debug("BeginControlEdit: context for %s.%s is '%s'", item, attributeName, self.sampleText)

        # set up the value (which may be the sample!) and select all the text
        value = self.GetAttributeValue(item, attributeName)
        if self.sampleText is not None and len(value) == 0:
            self.__setSampleText(control, self.sampleText)
        else:
            self.showingSample = False
            self.__changeTextQuietly(control, value)
            control.SetSelection (-1,-1)
            # @@@BJS is this necessary?: control.SetInsertionPointEnd ()

        logger.debug("BeginControlEdit: %s (%s) on %s", attributeName, self.showingSample, item)

    def EndControlEdit (self, item, attributeName, control):
        # update the item attribute value, from the latest control value.
        logger.debug("EndControlEdit: '%s' on %s", attributeName, item)
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
            self.showingSample = False
            self.__changeTextQuietly(control, value)
        else:
            self.__setSampleText(control, self.sampleText)

    def onTextChanged(self, event):
        if not getattr(self, "ignoreTextChanged", False):
            control = event.GetEventObject()
            if self.sampleText is not None:
                logger.debug("StringAE.onTextChanged: not ignoring.")                    
                currentText = control.GetValue()
                if self.showingSample:
                    logger.debug("onTextChanged: removing sample")
                    if currentText != self.sampleText:
                        self.showingSample = False
                elif len(currentText) == 0:
                    self.__setSampleText(control, self.sampleText)
            else:
                logger.debug("StringAE.onTextChanged: ignoring (no sample text)")
        else:
            logger.debug("StringAE.onTextChanged: ignoring (self-changed)")

    def __changeTextQuietly(self, control, text):
        self.ignoreTextChanged = True
        logger.debug("__changeTextQuietly: to '%s'", text)
        # text = "%s %s" % (control.GetFont().GetFaceName(), control.GetFont().GetPointSize())
        control.SetValue(text)
        logger.debug("AE(%s): Got '%s' after Set '%s'" % (self.attributeName, control.GetValue(), text))
        
        del self.ignoreTextChanged
        
    def __setSampleText(self, control, sampleText):
        logger.debug("__setSampleText: installing sampletext")
        self.showingSample = True
        self.__changeTextQuietly(control, sampleText)
        control.SetSelection (-1,-1)
        control.SetStyle(0, len(sampleText), wx.TextAttr(wx.Colour(153, 153, 153)))

    def onKeyDown(self, event):
        """ Note whether the sample's been replaced. """
        # If we're showing sample text and this key would only change the 
        # selection, ignore it.
        if self.showingSample and event.GetKeyCode() in \
            (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_BACK):
             logger.debug("onKeyDown: Ignoring selection-changer %s (%s) while showing the sample text", event.GetKeyCode(), wx.WXK_LEFT)
             return # skip out without calling event.Skip()

        logger.debug("onKeyDown: processing %s (%s)", event.GetKeyCode(), wx.WXK_LEFT)
        event.Skip()
        
    def onClick(self, event):
        """ Ignore clicks if we're showing the sample """
        control = event.GetEventObject()
        if self.showingSample and control == wx.Control.FindFocus():
            logger.debug("onClick: ignoring click because we're showing the sample.")
        else:
            event.Skip()
        if self.showingSample:
            control.SetSelection(-1, -1) # Make sure the whole thing's still selected
            
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
        """ Get the attribute's current value, converted to a (unicode) string """
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
                setattr (item, attributeName, valueString)

class DateTimeAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        try:
            itemDate = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = "No date specified"
        else:
            today = DateTime.today()
            yesterday = today + DateTime.RelativeDateTime(days=-1)
            beginningOfWeek = today + DateTime.RelativeDateTime(days=-8)
            endOfWeek = today + DateTime.RelativeDateTime(days=-2)
            if today.date == itemDate.date:
                value = itemDate.Format('%I:%M %p')
            elif yesterday.date == itemDate.date:
                value = 'Yesterday'
            elif itemDate.date >= beginningOfWeek.date and itemDate.date <= endOfWeek.date:
                value = itemDate.Format('%A')
                pass
            else:
                value = itemDate.Format('%b %d, %Y')
        return value

    def ReadOnly (self, (item, attribute)):
        # @@@MOR Temporarily disable editing of DateTime.  This AE needs some
        # more robust parsing of the date/time info the user enters.
        return True

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
                return
            else:
                # ask the repository for the type associated with this value
                attrType = ItemHandler.ItemHandler.typeHandler (item.itsView, value)
        # now we can convert the string to the right type
        value = attrType.makeValue (valueString)
        setattr (item, attributeName, value)

class LocationAttributeEditor (StringAttributeEditor):
    """ Knows that the data Type is a Location. """
    def SetAttributeValue (self, item, attributeName, valueString):
        if not valueString:
            # @@@BJS There's a repository bug that makes this hasattr necessary;
            # once it's fixed, replace this with try: delattr(item, attributeName) except AttributeError: pass
            #if hasattr(item, attributeName):
            #    delattr (item, attributeName)
            try:
                delattr(item, attributeName)
            except AttributeError:
                pass
        else:
            # lookup an existing item by name, if we can find it, 
            value = Calendar.Location.getLocation (item.itsView, valueString)
            if getattr(item, attributeName, None) is not value:
                setattr (item, attributeName, value)

    def CreateControl (self, parent, id):
        control = super(LocationAttributeEditor, self).CreateControl(parent, id)
        control.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        return control

    def onKeyUp(self, event):
        """
          Handle a Key pressed in the control.
        """
        logger.debug("LocationAttrEditor: onKeyUp")
        
        control = event.GetEventObject()
        controlValue = self.GetControlValue (control)
        keysTyped = len(controlValue)
        isDelete = event.m_keyCode == wx.WXK_DELETE or event.m_keyCode == wx.WXK_BACK
        if keysTyped > 1 and not isDelete:
            # See if there's exactly one existing Location object whose 
            # displayName starts with the current string; if so, we'll complete
            # on it.
            view = wx.GetApp().UIRepositoryView
            locationKind = view.findPath(Calendar.Location.myKindPath)
            allLocations = ItemQuery.KindQuery().run([locationKind])
            existingLocation = None
            for aLoc in allLocations:
                if aLoc.displayName[0:keysTyped] == controlValue:
                    if existingLocation is None:
                        existingLocation = aLoc
                        logger.debug("LocationAE.onKeyUp: '%s' completes!", aLoc.displayName)
                    else:
                        # We found a second candidate - we won't complete
                        logger.debug("LocationAE.onKeyUp: ... but so does '%s'", aLoc.displayName)
                        existingLocation = None
                        break
                
            if existingLocation is not None:
                completion = existingLocation.displayName
                self.SetControlValue (control, completion)
                logger.debug("LocationAE.onKeyUp: completing with '%s'", completion[keysTyped:])
                control.SetSelection (keysTyped, len (completion))

class DateTimeDeltaAttributeEditor (StringAttributeEditor):
    """ Knows that the data Type is DateTimeDelta. """
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
            setattr (item, attributeName, value)

    def _parse(self, inputString):
        """"
          parse the durationString into a DateTimeDelta.
        """
        # convert to DateTimeDelta
        theDuration = DateTime.Parser.DateTimeDeltaFromString (inputString)
        return theDuration

    durationFormatShort = '%H:%M'
    durationFormatLong = '%d:%H:%M:%S'

    def _format(self, aDuration):
        # if we got a value different from the default
        if aDuration.day == 0 and aDuration.second == 0:
            format = self.durationFormatShort
        else:
            format = self.durationFormatLong
        return aDuration.strftime (format)

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

class CheckboxAttributeEditor (BasePermanentAttributeEditor):
    """ A checkbox control. """
    def __init__(self, isShared, typeName, item=None, attributeName=None, presentationStyle=None):
        super(CheckboxAttributeEditor, self).__init__(isShared, typeName, item=item, attributeName=attributeName, presentationStyle=presentationStyle)
        
    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        # We have to implement Draw, but we don't need to do anything
        # because we've always got a control to do it for us.
        pass

    def CreateControl (self, parent, id):
        control = wx.CheckBox(parent, id)
        control.Bind(wx.EVT_CHECKBOX, self.onChecked)
        return control
        
    def DestroyControl (self, control, losingFocus=False):
        # Only destroy the control if we're not just losing focus
        if losingFocus:
            return False # we didn't destroy the control
        
        wx.CallAfter(control.Destroy)
        return True
    
    def onChecked(self, event):
        logger.debug("CheckboxAE.onChecked: new choice is %s",
                     self.GetControlValue(event.GetEventObject()))
        control = event.GetEventObject()
        self.SetAttributeValue(self.item, self.attributeName, \
                               self.GetControlValue(control))

    def GetControlValue (self, control):
        """ Are we checked? """
        return control.IsChecked()

    def SetControlValue (self, control, value):
        """ Set our state """
        control.SetValue(value)

class ChoiceAttributeEditor (BasePermanentAttributeEditor):
    """ A pop-up control. The list of choices comes from presentationStyle.choices """
    def __init__(self, isShared, typeName, item=None, attributeName=None, presentationStyle=None):
        super(ChoiceAttributeEditor, self).__init__(isShared, typeName, item=item, attributeName=attributeName, presentationStyle=presentationStyle)
        
    def Draw (self, dc, rect, item, attributeName, isInSelection=False):
        # We have to implement Draw, but we don't need to do anything
        # because we've always got a control to do it for us.
        pass

    def CreateControl (self, parent, id):
        control = wx.Choice(parent, id)
        control.SetFont(parent.GetFont())
        control.Bind(wx.EVT_CHOICE, self.onChoice)
        return control
        
    def DestroyControl (self, control, losingFocus=False):
        # Only destroy the control if we're not just losing focus
        if losingFocus:
            return False # we didn't destroy the control
        
        wx.CallAfter(control.Destroy)
        return True
    
    def onChoice(self, event):
        logger.debug("ChoiceAE.onChoice: new choice is %s",
                     self.GetControlValue(event.GetEventObject()))
        control = event.GetEventObject()
        self.SetAttributeValue(self.item, self.attributeName, \
                               self.GetControlValue(control))

    def GetChoices(self):
        """ Get the choices we're presenting """
        return self.presentationStyle.choices

    def GetControlValue (self, control):
        """ Get the selected choice's text """
        choiceIndex = control.GetSelection()
        if choiceIndex == -1:
            return None
        value = self.item.getAttributeAspect(self.attributeName, 'type').values[choiceIndex]
        if isinstance(value, str): value = unicode(value) # @@@BJS Make sure we return unicode!
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
        value = control.GetStringSelection()
        try:
            minuteCount = int(value.split(u" ")[0])
        except ValueError:
            # "None"
            value = Calendar.CalendarEventMixin.NoReminderDelta
        else:
            value = DateTime.DateTimeDeltaFrom(minutes=-minuteCount)
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

            if value == Calendar.CalendarEventMixin.NoReminderDelta:
                choiceIndex = 0 # the "None" choice
            else:
                reminderChoice = (value.minutes == 1) and _("1 minute") or (_("%i minutes") % value.minutes)
                choiceIndex = control.FindString(reminderChoice)
                # If we can't find the choice, just show "None" - this'll happen if this event's reminder has been "snoozed"
                if choiceIndex == -1:
                    choiceIndex = 0 # the "None" choice
            control.Select(choiceIndex)
        
    def SetAttributeValue (self, item, attributeName, value):
        if value is None and hasattr(item, attributeName):
            delattr(item, attributeName)
        else:
            super(ReminderDeltaAttributeEditor, \
                  self).SetAttributeValue(item, attributeName, value)

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
        dc.DrawRectangleRect(rect) # always draw the background
        imageName = self.GetAttributeValue(item, attributeName) + ".png"
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
