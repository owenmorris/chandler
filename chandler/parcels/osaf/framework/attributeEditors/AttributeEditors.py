__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import os
import wx
import mx.DateTime as DateTime
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.calendar.Calendar as Calendar
import repository.item.ItemHandler as ItemHandler
import osaf.framework.blocks.Styles as Styles
import repository.query.Query as Query

class IAttributeEditor (object):
    """ CPIA Attribute Editor base class """
    _TypeToEditorInstances = {}

    def __init__(self, isShared, presentationStyle=None):
        """ 
        Create a shared, or unshared instance of an Attribute Editor. 
        
        @param isShared: tells if this Attribute Editor is shared among
                  several values (e.g. Grid uses a single AE for a whole
                  column).
        @type isShared: boolean
        @param presentationStyle: gives style information to the AE
        @type presentationStyle: reference to PresentationStyle item, or
                  None when isShared is True (default presentation).
        Unshared instances may store data in attributes of self, but
        that may cause trouble for shared Attribute Editors instances.
        """

    def ReadOnly (self, (item, attribute)):
        """ Return True if this Attribute Editor refuses to edit """
        
    def Draw (self, dc, rect, item, attributeName, isSelected):
        """ Draw the value of the attribute in the specified rect of the dc """
        
    def Create (self, parent, id):
        """ Create and return a control to use for editing the attribute value. """

    def BeginControlEdit (self, control, value):
        """ Begin editing the value """
        
    def EndControlEdit (self, item, attributeName, control):
        """ 
        End editing the value.  

        Called before destroying the control created in Create(). 
        """
        
    def GetControlValue (self, control):
        """ Get the value from the control. """

    def SetControlValue (self, control, value):
        """ Set the value in the control. """

    def GetAttributeValue (self, item, attributeName):
        """ Get the value from the specified attribute of the item. """
        
    def SetAttributeValue (self, item, attributeName, value):
        """ Set the value of the attribute given by the value. """

    """ Informal conventions """
    def onKeyPressed(self, event):
        """ Handle a Key pressed in the control. """

    """ Class Methods """
    def GetAttributeEditorSingleton (theClass, type):
        """ Get (and cache) a single shared Attribute Editor for this type. """
        try:
            instance = theClass._TypeToEditorInstances [type]
        except KeyError:
            aeClass = theClass._GetAttributeEditorClass (type)
            # init the attribute editor, letting it know it's shared
            instance = aeClass (isShared=True)
            # remember it in our cache
            theClass._TypeToEditorInstances [type] = instance
        return instance

    GetAttributeEditorSingleton = classmethod (GetAttributeEditorSingleton)

    def GetAttributeEditorInstance (theClass, type, item, attributeName, presentationStyle):
        """ Get a new unshared instance of the Attribute Editor for this type. """
        aeClass = theClass._GetAttributeEditorClass (type)
        # init the attribute editor, letting it know it's not shared (can use instance data)
        instance = aeClass (isShared=False, presentationStyle=presentationStyle)
        return instance
    GetAttributeEditorInstance = classmethod (GetAttributeEditorInstance)

    def _GetAttributeEditorClass (theClass, type):
        """ Return the attribute editor class for this type """
        map = Globals.repository.findPath('//parcels/osaf/framework/attributeEditors/AttributeEditors')
        try:
            classPath = map.editorString [type]
        except KeyError:
            assert map.editorString ["_default"], "Default attribute editor doesn't exist ('_default')"
            classPath = map.editorString ["_default"]
        parts = classPath.split (".")
        assert len(parts) >= 2, " %s isn't a module and class" % classPath
        className = parts.pop ()
        module = __import__ ('.'.join(parts), globals(), locals(), className)
        assert module.__dict__[className], "Class %s doesn't exist" % classPath
        aeClass = module.__dict__[className]
        return aeClass
    _GetAttributeEditorClass = classmethod (_GetAttributeEditorClass)

class BaseAttributeEditor (IAttributeEditor):
    """ Base class for many Attribute Editors. """
    def __init__(self, isShared, *args, **keys):
        self.isShared = isShared

    def ReadOnly (self, (item, attribute)):
        return str (item.itsParent.itsPath) !=  '//userdata'

    def Draw (self, dc, rect, item, attributeName, isSelected):
        """ You must override Draw. """
        raise NotImplementedError
    
    def Create (self, parent, id):
        """ You must override Create. """
        raise NotImplementedError

    def BeginControlEdit (self, control, value):
        """ Do nothing by default. """

    def GetControlValue (self, control):
        return control.GetValue()

    def SetControlValue (self, control, value):
        control.SetValue (value)

    def GetAttributeValue (self, item, attributeName):
        """ You must override GetAttributeValue. """
        raise NotImplementedError

class StringAttributeEditor (BaseAttributeEditor):
    """ Uses a Text Control to edit attributes in string form. """
    
    def Draw (self, dc, rect, item, attributeName, isSelected):
        """
          Currently only handles left justified single line text.
        """
        # Erase the bounding box
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)

        dc.DrawRectangle (rect.x, rect.y, rect.width, rect.height)

        """
          Draw the text in the box
        """

        dc.SetBackgroundMode (wx.TRANSPARENT)
        rect.Inflate (-1, -1)
        dc.SetClippingRect (rect)

        x = rect.x + 1
        y = rect.y + 1

        string = self.GetAttributeValue (item, attributeName)
        for line in str (string).split (os.linesep):
            dc.DrawText (line, x, y)
            lineWidth, lineHeight = dc.GetTextExtent (line)
            # If the text doesn't fit within the box we want to clip it and
            # put '...' at the end.  This method may chop a character in half,
            # but is a lot faster than doing the proper calculation of where
            # to cut off the text.  Eventually we will want a solution that
            # doesn't chop chars, but that will come along with multiline 
            # wrapping and hopefully won't be done at the python level.
            if lineWidth > rect.width - 2:
                width, height = dc.GetTextExtent('...')
                x = rect.x+1 + rect.width-2 - width
                dc.DrawRectangle(x, rect.y+1, width+1, height)
                dc.DrawText('...', x, rect.y+1)
            y += lineHeight
        dc.DestroyClippingRegion()

    def Create (self, parent, id):
        # create a text control for editing the string value
        return wx.TextCtrl (parent, id)

    def BeginControlEdit (self, control, value):
        # set up the value and move the selection to the end
        control.SetValue (value)
        control.SetInsertionPointEnd ()
        control.SetSelection (-1,-1)
        control.SetFocus()

    def GetAttributeValue (self, item, attributeName):
        try:
            value = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = ""
        else:
            try:
                cardinality = item.getAttributeAspect (attributeName, "cardinality")
            except AttributeError:
                pass
            else:
                if  cardinality == "list":
                    value = ', '.join([part.getItemDisplayName() for part in value])
        return value

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

class RepositoryAttributeEditor (StringAttributeEditor):
    """ Uses Repository Type conversion to provide String representation. """
    def ReadOnly (self, (item, attribute)):
        return False # not read-only allows editing the attribute

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

class LabeledAttributeEditor (StringAttributeEditor):
    """ Attribute Editor that shows a Label for the attribute in addition to the value. """
    def __init__(self, isShared, presentationStyle=None):
        super (LabeledAttributeEditor, self).__init__(isShared,
                                                         presentationStyle)

        """ set up internal state for this item/attribute combination """
        try:
            labelStyle = presentationStyle.label
            self.presentationStyle = presentationStyle
        except AttributeError:
            labelStyle = 'None'
        # attributes that share an Attribute Editor will all use the same label style
        self.labelStyle = labelStyle

    def _IsAttributeLabel (self, item, attributeName):
        """ return True if this value is the "default" value
        for the attribute """
        return not hasattr (item, attributeName)

    def _GetAttributeLabel (self, item, attributeName):
        try:
            return item.getAttributeAspect (attributeName, 'displayName')
        except:
            try:
                return self.presentationStyle.labelDisplayName
            except AttributeError:
                pass
            
        raise NotImplementedError, "Can't display name of property '%s' for item of type %s" \
                           %  (attributeName, item.itsKind.displayName)

    def _SetLabelStyle (self, item, attributeName, dc):
        if self.labelStyle == 'OnLeft':
            """ 
              For Label-On-Left collect label layout information:
            self.editOffset - offset of the edit area
            self.labelOffset - offset of the label area
            """
            assert not self.isShared, "Label on Left presentationStyle not allowed for shared Attribute Editors"
            try:
                editOffset = self.editOffset # cached value?
            except AttributeError:
                label = self._GetAttributeLabel (item, attributeName)
                lineWidth, lineHeight = dc.GetTextExtent (label)
                # editOffset - where to put the edit text
                try:
                    editOffset = self.presentationStyle.labelWidth
                except AttributeError:
                    # not supplied: use the width of the label for the offset
                    editOffset = lineWidth
                try:
                    # border is extra space next to label
                    border = self.presentationStyle.labelBorder
                except AttributeError:
                    border = 0
                try:
                    # label alignment: Left, Center, or Right
                    alignment = self.presentationStyle.labelTextAlignmentEnum
                except AttributeError:
                    alignment = "Right"
                self.editOffset = editOffset
                self.border = border
                self.alignment = alignment
                self.label = label

                # figure out the label offset
                if self.alignment == "Left":
                    labelOffset = self.border
                else:
                    if self.alignment == "Right":
                        scaleFactor = 1
                    elif self.alignment == "Center":
                        scaleFactor = 2
                    else:
                        assert False, "invalid labelTextAlignmentEnum detected"
                    labelOffset = editOffset - (lineWidth + self.border) / scaleFactor
                self.labelOffset = labelOffset

        elif self.labelStyle == 'InPlace':
            drawItalic = self._IsAttributeLabel (item, attributeName)
            if drawItalic:
                style = wx.ITALIC
                textColor = wx.SYS_COLOUR_HIGHLIGHTTEXT # SYS_COLOUR_GREYTEXT is too light on Mac
            else:
                style = wx.NORMAL
                textColor = wx.SYS_COLOUR_BTNTEXT
            dc.SetTextForeground (wx.SystemSettings.GetColour(textColor))
            font = dc.GetFont ()
            font.SetStyle (style)
            dc.SetFont (font)

    def Draw (self, dc, rect, item, attributeName, isSelected):
        # always setup for drawing
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)

        dc.DrawRectangle (rect.x, rect.y, rect.width, rect.height)

        """
          Draw the text in the box
        """

        dc.SetBackgroundMode (wx.TRANSPARENT)
        rect.Inflate (-1, -1)
        dc.SetClippingRect (rect)

        x = rect.x + 1
        y = rect.y + 1

        # set up our label style information
        self._SetLabelStyle (item, attributeName, dc)

        # Label OnLeft?  
        if self.labelStyle == 'OnLeft':
            # Draw label first, then move to the right.
            label = self._GetAttributeLabel (item, attributeName)
            dc.DrawText (label, x + self.labelOffset, y)
            x += self.editOffset
            rect.width -= self.editOffset
            
            # draw an area that looks editable on the right
            dc.SetBackgroundMode (wx.SOLID)
            oldBrush = dc.GetBrush()
            dc.SetBrush (wx.WHITE_BRUSH)
            dc.DrawRectangle (x-1, y-1, rect.width, rect.height)
            dc.SetPen (wx.LIGHT_GREY_PEN)
            dc.DrawLine (x-1, y-1, x-1, y+rect.height)
            dc.DrawLine (x-1, y-1, x+rect.width, y-1)
            dc.SetBrush (oldBrush)
            
        # if not selected there's no edit control, so we need to draw the value text.
        if not isSelected:
            string = self.GetAttributeValue (item, attributeName)
            for line in str (string).split (os.linesep):
                dc.DrawText (line, x, y)
                lineWidth, lineHeight = dc.GetTextExtent (line)
                # If the text doesn't fit within the box we want to clip it and
                # put '...' at the end.  This method may chop a character in half,
                # but is a lot faster than doing the proper calculation of where
                # to cut off the text.  Eventually we will want a solution that
                # doesn't chop chars, but that will come along with multiline 
                # wrapping and hopefully won't be done at the python level.
                if lineWidth > rect.width - 2:
                    width, height = dc.GetTextExtent('...')
                    x = rect.x+1 + rect.width-2 - width
                    dc.DrawRectangle(x, rect.y+1, width+1, height)
                    dc.DrawText('...', x, rect.y+1)
                y += lineHeight
            dc.DestroyClippingRegion()
    
    def Create (self, parent, id):
        parentRect = parent.GetRect()
        controlPosition = wx.DefaultPosition
        controlSize = [parentRect.width, parentRect.height]
        
        # if the label belongs on the left, the control needs to be on the right.
        if self.labelStyle == "OnLeft":
            controlPosition = (self.editOffset, -1)
            
        # create the edit control
        control = wx.TextCtrl (parent, id, '', controlPosition)
        
        # get size hints based on the parent
        control.SetSizeHints(minW=controlSize[0], minH=controlSize[1])
        controlRect = wx.Rect(controlPosition[0], controlPosition[1], controlSize[0], controlSize[1])
        control.SetRect(controlRect)
        
        # bind to a key handler, if it exits, to process keystrokes e.g. completion
        try:
            keyHandler = self.onKeyPressed
        except AttributeError:
            pass
        else:
            control.Bind (wx.EVT_KEY_UP, keyHandler)
        return control
        
    def EndControlEdit (self, item, attributeName, control):
        # update the item attribute value, from the latest control value.
        controlValue = self.GetControlValue (control)
        if item is not None:
            self.SetAttributeValue (item, attributeName, controlValue)

class LocationAttributeEditor (LabeledAttributeEditor):
    """ Knows that the data Type is a Location. """
    def ReadOnly (self, (item, attribute)):
        return False

    def GetAttributeValue (self, item, attributeName):
        # get the value, and if it doesn't exist, use the label
        try:
            value = getattr (item, attributeName)
        except:
            valueString = self._GetAttributeLabel (item, attributeName)
            self.isLabelValue = True
        else:
            valueString = str (value)
        self.showingTheLabel = self._IsAttributeLabel (item, attributeName) # remember if we're showing the label value
        return valueString

    import osaf.contentmodel.calendar.Calendar as Calendar

    def SetAttributeValue (self, item, attributeName, valueString):
        # if the value has changed, create a location for it.
        if not valueString or self.showingTheLabel: # no value, or still showing the label
            try:
                delattr (item, attributeName)
            except AttributeError:
                pass
        else:
            # lookup an existing item by name, if we can find it, 
            value = Calendar.Location.getLocation (valueString)
            setattr (item, attributeName, value)

    def Create (self, parent, id):
        control = super (LocationAttributeEditor, self).Create (parent, id)
        control.Bind (wx.EVT_TEXT, self.onTextChanged) # any time the text changes
        return control

    def onTextChanged(self, event):
        """
          Text changed, for any reason.
        """
        event.Skip()
        self.showingTheLabel = False # remember we've edited the value

    def onKeyPressed(self, event):
        """
          Handle a Key pressed in the control.
        """
        event.Skip()
        self.showingTheLabel = False # remember we've edited the value
        control = event.GetEventObject()
        controlValue = self.GetControlValue (control)
        keysTyped = len(controlValue)
        isDelete = event.m_keyCode == wx.WXK_DELETE or event.m_keyCode == wx.WXK_BACK
        if keysTyped > 1 and not isDelete:
            # get all Location objects whose displayName contains the current string
            # @@@DLD is there a way to get values whose displayName *starts* with the string?
            queryString = u'for i in "//parcels/osaf/contentmodel/calendar/Location" \
                          where contains(i.displayName, $0)'
            locQuery = Query.Query (Globals.repository, queryString)
            locQuery.args = [ controlValue ]
            locQuery.execute ()
    
            # build a list of matches here
            candidates = []
            for aLoc in locQuery:
                if aLoc.displayName[0:keysTyped] == controlValue:
                    candidates.append (aLoc)

            # for now, we perform competion only when exactly one match was found.
            if len (candidates) == 1:
                completion = candidates[0].displayName
                self.SetControlValue (control, completion)
                control.SetSelection (keysTyped, len (completion))


class DateTimeDeltaAttributeEditor (LabeledAttributeEditor):
    """ Knows that the data Type is DateTimeDelta. """
    def ReadOnly (self, (item, attribute)):
        return False

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

class IconAttributeEditor (BaseAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        # simple implementation - get the value, assume it's a string
        try:
            value = getattr (item, attributeName) # getattr will work with properties
        except AttributeError:
            value = ""
        return value
    
    def Draw (self, dc, rect, item, attributeName, isSelected):
        dc.DrawRectangleRect(rect) # always draw the background
        imageName = self.GetAttributeValue(item, attributeName)
        if imageName != '':
            image = Globals.wxApplication.GetImage(imageName)
            if image:
                offscreenBuffer = wx.MemoryDC()
                offscreenBuffer.SelectObject (image)
                dc.SetBackgroundMode (wx.SOLID)
     
                width, height = image.GetWidth(), image.GetHeight()
                if width > rect.width - 2:
                    width = rect.width - 2
                if height > rect.height - 2:
                    height = rect.height - 2
                    
                dc.Blit (rect.x + 1, rect.y + 1,
                         width, height, 
                         offscreenBuffer,
                         0, 0,
                         wx.COPY,
                         True)

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
