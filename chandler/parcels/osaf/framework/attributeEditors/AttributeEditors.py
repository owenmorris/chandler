__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import os
import wx
import mx.DateTime as DateTime
import osaf.contentmodel.tasks.Task as Task
import osaf.contentmodel.calendar.Calendar as Calendar
import repository.item.ItemHandler as ItemHandler

class AttributeEditor (object):

    TypeToEditorInstances = {}

    def GetAttributeEditor (theClass, type):
        def FindAndCacheEditor (theClass, type):
            try:
                instance = theClass.TypeToEditorInstances [type]
            except KeyError:
                map = Globals.repository.findPath('//parcels/osaf/framework/attributeEditors/AttributeEditors')
                try:
                    classPath = map.editorString [type]
                except KeyError:
                    instance = None
                else:
                    parts = classPath.split (".")
                    assert len(parts) >= 2, " %s isn't a module and class" % classPath
                    className = parts.pop ()
                    module = __import__ ('.'.join(parts), globals(), locals(), className)
                    assert module.__dict__.get (className), "Class %s doesn't exist" % classPath
                    theClass = module.__dict__[className]
                    instance = theClass.__new__ (theClass)
                    theClass.__init__ (instance)
                    theClass.TypeToEditorInstances [type] = instance
            return instance
                
        instance = FindAndCacheEditor (theClass, type)
        if not instance:
            instance = FindAndCacheEditor (theClass, "_default")
        return instance

    GetAttributeEditor = classmethod (GetAttributeEditor)

class StringAttributeEditor (AttributeEditor):
    def ReadOnly (self, (item, attribute)):
        return str (item.itsParent.itsPath) !=  '//userdata'

    def Draw (self, dc, rect, item, attributeName, isSelected):
        """
          Currently only handles left justified multiline text.
          Draw the boundary box
        """
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
        return wx.TextCtrl (parent, id)

    def BeginControlEdit (self, control, value):
        control.SetValue (value)
        control.SetInsertionPointEnd ()
        control.SetSelection (-1,-1)
        control.SetFocus()

    def GetControlValue (self, control):
        return control.GetValue()

    def SetControlValue (self, control, value):
        control.SetValue (value)

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
            except:
                valueString = "no value"
            else:
                valueString = str (value)
        else:
            valueString = attrType.makeString (value)
        return valueString

    def SetAttributeValue (self, item, attributeName, valueString):
        # attempt access as a Chandler attribute first
        try:
            attrType = item.getAttributeAspect (attributeName, "type")
        except:
            # attempt access as a plain Python attribute
            try:
                value = getattr (item, attributeName)
            except AttributeEditor:
                # attribute currently has no value, can't figure out the type
                setattr (item, attributeName, valueString) # hope that a string will work
            # ask the repository for the type associated with this value
            attrType = ItemHandler.ItemHandler.typeHandler (item.itsView, value)
        # now we can convert the string to the right type
        value = attrType.makeValue (valueString)
        setattr (item, attributeName, value)

class DateTimeDeltaAttributeEditor (StringAttributeEditor):
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
            valueString = self.format (value)
        return valueString

    def SetAttributeValue (self, item, attributeName, valueString):
        # attempt access as a plain Python attribute
        try:
            value = self.parse(valueString)
        except ValueError:
            pass
        else:
            setattr (item, attributeName, value)

    def parse(self, inputString):
        """"
          parse the durationString into a DateTimeDelta.
        """
        # convert to DateTimeDelta
        theDuration = DateTime.Parser.DateTimeDeltaFromString (inputString)
        return theDuration

    durationFormatShort = '%H:%M'
    durationFormatLong = '%d:%H:%M:%S'

    def format(self, aDuration):
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

class IconAttributeEditor (StringAttributeEditor):
    def Draw (self, dc, rect, item, attributeName, isSelected):
        imageName = self.GetAttributeValue(item, attributeName)
        if imageName != '':
            image = Globals.wxApplication.GetImage(imageName)
            if image:
                offscreenBuffer = wx.MemoryDC()
                offscreenBuffer.SelectObject (image)
                dc.SetBackgroundMode (wx.SOLID)
     
                dc.DrawRectangleRect(rect)
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
        else:
            super (IconAttributeEditor, self).Draw(dc, rect, item, attributeName, isSelected)

class EnumAttributeEditor (IconAttributeEditor):
    """
    An attribute editor for enumerated types to be represented as icons. 
    Uses the attribute name, an underscore, and the value name as the image filename.
    (An alternative might be to use the enum type name instead of the attribute name...)
    """
    def GetAttributeValue (self, item, attributeName):
        try:
            value = "%s_%s" % (attributeName, item.getAttributeValue(attributeName))
        except AttributeEditor:
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

class DefaultAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        return "%s doesn't have a renderer" % item.getAttributeAspect (attributeName, 'type').itsName
