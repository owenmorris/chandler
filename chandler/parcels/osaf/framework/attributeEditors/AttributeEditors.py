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
            instance = FindAndCacheEditor ("_default")
        return instance

    GetAttributeEditor = classmethod (GetAttributeEditor)

class StringAttributeEditor (AttributeEditor):
    def ReadOnly (self, (item, attribute)):
        return str (item.itsParent.itsPath) ==  '//userdata'

    def Draw (self, dc, rect, item, attributeName, isSelected):
        """
          Currently only handles left justified multiline text.
          Draw the boundary box
        """
        dc.SetBackgroundMode (wx.SOLID)
        dc.SetPen (wx.TRANSPARENT_PEN)
        dc.DrawRectangle ((rect.x, rect.y), (rect.width, rect.height))
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
            dc.DrawText (line, (x, y))
            lineWidth, lineHeight = dc.GetTextExtent (line)
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
            value = item.getAttributeValue (attributeName)
        except AttributeError:
            value = ""
        else:
            if item.getAttributeAspect (attributeName, "cardinality") == "list":
                compoundValue = value
                value = ''
                for part in compoundValue:
                    if value:
                        value += ', '
                    value += part.getItemDisplayName()
        return value


class DateTimeAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        try:
            itemDate = item.getAttributeValue (attributeName)
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


class ContactNameAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        try:
            contactName = item.getAttributeValue (attributeName)
        except AttributeError:
            value = ""
        else:
            value = contactName.firstName + ' ' + contactName.lastName
        return value


class StampAttributeEditor (StringAttributeEditor):
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
                    
                dc.Blit ((rect.x + 1, rect.y + 1),
                         (width, height), 
                         offscreenBuffer,
                         (0, 0),
                         wx.COPY,
                         True)
        else:
            super (StampAttributeEditor, self).Draw(dc, rect, item, attributeName, isSelected)
    
    def GetAttributeValue (self, item, attributeName):
        if isinstance(item, Calendar.CalendarEventMixin):
            return 'smKindFilterEvent'
        elif isinstance(item, Task.TaskMixin):
            return 'smKindFilterTask'
        else:
            return ''

        
class DefaultAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        return "%s doesn't have a renderer" % item.getAttributeAspect (attributeName, 'type').itsName
