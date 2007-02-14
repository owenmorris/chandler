#   Copyright (c) 2007 Open Source Applications Foundation
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
BaseAttributeEditor - a general base class from which all attribute editors
are derived. Includes methods:
    ReadOnly(), Draw(), IsFixedWidth(), EditInPlace(),
    CreateControl(), Begin/EndControlEdit(),
    Get/SetControlValue(), and Get/SetAttributeValue().

Also defines global function NotifyBlockToSaveValue()
"""

import logging
logger = logging.getLogger(__name__)

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
        isAttrModifiableMethod = getattr(item, 'isAttributeModifiable', None)
        if isAttrModifiableMethod is None:
            return False
        # In case this editor is keyed off a stamp class instead of an attribute,
        # map to an actual attribute name.
        if not isinstance(attribute, basestring):
            attribute = 'body'
        return not isAttrModifiableMethod(attribute)

    def Draw (self, grid, dc, rect, (item, attributeName), isInSelection=False):
        """ 
        Draw the value of the this item attribute.
        
        Used only for shared attribute editors (used by the Summary Table),
        not for AEs in the detail view.
        
        @param grid: The wxGrid in which we're drawing
        @type grid: wxGrid
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

