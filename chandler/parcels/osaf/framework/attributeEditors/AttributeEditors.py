__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import os
import wx

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
            value = "Unnamed"
        else:
            if item.getAttributeAspect (attributeName, "cardinality") == "list":
                compoundValue = value
                value = ""
                for part in compoundValue:
                    if value:
                        value = value + ", "
                    value = value + part.getItemDisplayName()
        return value


class DefaultAttributeEditor (StringAttributeEditor):
    def GetAttributeValue (self, item, attributeName):
        return "%s doesn't have a renderer" % item.getAttributeAspect (attributeName, 'type').itsName
