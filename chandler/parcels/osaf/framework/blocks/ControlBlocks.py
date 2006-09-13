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


__parcel__ = "osaf.framework.blocks"

import os, sys
from application.Application import mixinAClass
from application import schema
from Block import ( 
    Block, RectangularChild, BlockEvent,  ShownSynchronizer, lineStyleEnumType,
    logger, debugName, WithoutSynchronizeWidget, IgnoreSynchronizeWidget
)
from ContainerBlocks import BoxContainer
import DragAndDrop
from chandlerdb.item.ItemError import NoSuchAttributeError
import wx
import wx.html
import wx.gizmos
import webbrowser # for opening external links
import PyICU
from util import MultiStateButton

import application.dialogs.ReminderDialog as ReminderDialog
import application.dialogs.RecurrenceDialog as RecurrenceDialog
import Styles
from datetime import datetime, time, timedelta
from osaf.pim.calendar import Calendar
from osaf.pim import Reminder
from repository.item.Monitors import Monitors
from i18n import ChandlerMessageFactory as _


class textAlignmentEnumType(schema.Enumeration):
    values = "Left", "Center", "Right"

class buttonKindEnumType(schema.Enumeration):
     values = "Text", "Image", "Toggle", "Stamp"

class Button(RectangularChild):

    characterStyle = schema.One(Styles.CharacterStyle)
    title = schema.One(schema.Text)
    buttonKind = schema.One(buttonKindEnumType)
    icon = schema.One(schema.Text)
    rightClicked = schema.One(BlockEvent)
    event = schema.One(BlockEvent)
    helpString = schema.One(schema.Text, initialValue = u'')

    def instantiateWidget(self):
        id = self.getWidgetID()
        parentWidget = self.parentBlock.widget
        if self.buttonKind == "Text":
            button = wx.Button (parentWidget,
                                id,
                                self.title,
                                wx.DefaultPosition,
                                (self.minimumSize.width, self.minimumSize.height))
        elif self.buttonKind == "Image":
            bitmap = wx.GetApp().GetImage (self.icon)
            button = wx.BitmapButton (parentWidget,
                                      id,
                                      bitmap,
                                      wx.DefaultPosition,
                                      (self.minimumSize.width, self.minimumSize.height))
        elif self.buttonKind == "Toggle":
            button = wx.ToggleButton (parentWidget, 
                                      id, 
                                      self.title,
                                      wx.DefaultPosition,
                                      (self.minimumSize.width, self.minimumSize.height))
        elif self.buttonKind == "Stamp":
            # for a stamp button, we use "self.icon" as the base name of all bitmaps and look for:
            #
            #   {icon}Normal, {icon}Stamped, {icon}Rollover, {icon}Pressed, {icon}Disabled
            #
            # From these we build two states suffixed "unstamped" and "stamped", which can
            # be used the toggle the appearance of the button.
            #
            assert len(self.icon) > 0

            assert len(self.icon) > 0
            normal = MultiStateButton.BitmapInfo()
            normal.normal   = "%sNormal" % self.icon
            normal.rollover = "%sRollover" % self.icon
            normal.disabled = "%sDisabled" % self.icon
            normal.selected = "%sPressed" % self.icon
            normal.stateName = "%s.Unstamped" % self.icon
            stamped = MultiStateButton.BitmapInfo()
            stamped.normal   = "%sStamped" % self.icon
            stamped.rollover = "%sStampedRollover" % self.icon
            stamped.disabled = "%sStampedDisabled" % self.icon
            stamped.selected = "%sStampedPressed" % self.icon
            stamped.stateName = "%s.Stamped" % self.icon
            button = wxChandlerMultiStateButton (parentWidget, 
                                id, 
                                wx.DefaultPosition,
                                (self.minimumSize.width, self.minimumSize.height),
                                helpString = self.helpString,
                                multibitmaps=(normal, stamped))
        elif __debug__:
            assert False, "unknown buttonKind"

        parentWidget.Bind(wx.EVT_BUTTON, self.buttonPressed, id=id)
        return button

    def isStamped(self):
        stamped = False;
        if self.buttonKind == "Stamp":
            stamped = (self.widget.currentState == "%s.Stamped" % self.icon)
        return stamped

    def buttonPressed(self, event):
        try:
            event = self.event
        except AttributeError:
            pass
        else:
            Block.post(event, {'item':self}, self)


class wxChandlerMultiStateButton(MultiStateButton.MultiStateButton):
    """
    Just like MultiStateButton, except that it uses wx.GetApp().GetImage
    as the provider of bitmaps, and the button has no border.
    
    Dispatch notifications at the end of handling the left-up event, because
    we'll destroy the button in the process of stamping, and the base-class
    implementation tries to use it again (to Refresh, etc.)
    """
    def __init__(self, parent, ID, pos, size, multibitmaps, *args, **kwds):
        super(wxChandlerMultiStateButton, self).__init__(parent,
                                                        ID,
                                                        pos,
                                                        size,
                                                        wx.BORDER_NONE,
                                                        multibitmaps = multibitmaps,
                                                        bitmapProvider = wx.GetApp().GetImage,
                                                        *args, **kwds)
    def OnLeftUp(self, event):
        if not self.IsEnabled() or not self.HasCapture():
            return
        if self.HasCapture():
            self.ReleaseMouse()
            if not self.up:    # if the button was down when the mouse was released...
                # use wx.CallAfter() in case the button is deleted
                wx.CallAfter(self.Notify)
            self.up = True
            self.Refresh()
            event.Skip()


class ContextMenu(RectangularChild):
    def displayContextMenu(self, parentWindow, position, data):
        menu = wx.Menu()
        for child in self.childrenBlocks:
            child.addItem(menu, data)
        parentWindow.PopupMenu(menu, position)
        menu.Destroy()
        

class ContextMenuItem(RectangularChild):

    event = schema.One(BlockEvent)
    title = schema.One(schema.Text)
    schema.addClouds(
        copying = schema.Cloud(byCloud=[event])
    )

    def addItem(self, wxContextMenu, data):
        id = self.getWidgetID()
        self.data = data
        wxContextMenu.Append(id, self.title)
        wxContextMenu.Bind(wx.EVT_MENU, wx.GetApp().OnCommand, id=id)


class textStyleEnumType(schema.Enumeration):
      values = "PlainText", "RichText"


class EditText(RectangularChild):

    characterStyle = schema.One(Styles.CharacterStyle)
    lineStyleEnum = schema.One(lineStyleEnumType)
    textStyleEnum = schema.One(textStyleEnumType, initialValue = 'PlainText')
    readOnly = schema.One(schema.Boolean, initialValue = False)
    textAlignmentEnum = schema.One(
        textAlignmentEnumType, initialValue = 'Left',
    )
    schema.addClouds(
        copying = schema.Cloud(byRef=[characterStyle])
    )

    def instantiateWidget(self):
        # Remove STATIC_BORDER: it wrecks padding on WinXP; was: style = wx.STATIC_BORDER
        style = 0
        if self.textAlignmentEnum == "Left":
            style |= wx.TE_LEFT
        elif self.textAlignmentEnum == "Center":
            style |= wx.TE_CENTRE
        elif self.textAlignmentEnum == "Right":
            style |= wx.TE_RIGHT

        if self.lineStyleEnum == "MultiLine":
            style |= wx.TE_MULTILINE
        else:
            style |= wx.TE_PROCESS_ENTER

        if self.textStyleEnum == "RichText":
            style |= wx.TE_RICH2

        if self.readOnly:
            style |= wx.TE_READONLY

        editText = AttributeEditors.wxEditText (self.parentBlock.widget,
                               -1,
                               "",
                               wx.DefaultPosition,
                               (self.minimumSize.width, self.minimumSize.height),
                               style=style, name=self.itsUUID.str64())

        editText.SetFont(Styles.getFont(getattr(self, "characterStyle", None)))
        return editText

class HtmlWindowWithStatus(wx.html.HtmlWindow):
    def __init__(self, *arguments, **keywords):
        super (HtmlWindowWithStatus, self).__init__ (*arguments, **keywords)
        # The default setting is to show link URLs in the statusbar of the mainframe.
        self.showMessagesInStatusbar(wx.GetApp().mainFrame, True)
        
    def showMessagesInStatusbar(self, relatedFrame, show):
        self.SetRelatedFrame(relatedFrame, u"%s")
        if show:
            self.SetRelatedStatusBar(0)
        else:
            self.SetRelatedStatusBar(-1)
        
    def OnSetTitle(self, title):
        # This is an empty handler for setting the main frame window title.
        # It is empty because we do not want to show the current URL in main frame window title.
        pass
    
class wxHTML(HtmlWindowWithStatus):
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())


class HTML(RectangularChild):
    url = schema.One(schema.Text)

    def instantiateWidget (self):
        htmlWindow = wxHTML (self.parentBlock.widget,
                             self.getWidgetID(),
                             wx.DefaultPosition,
                             (self.minimumSize.width, self.minimumSize.height))
        if self.url:
            htmlWindow.LoadPage(self.url)
        return htmlWindow

class columnType(schema.Enumeration):
    """
    Indicates the type of the value used in the column, that
    determines the way that attributeName or kind is used

    An 'attribute' column gets the value of the item using
    attributeName as the attribute name.

    A 'kind' column gets the value of the item passing kind
    to the attribute editor.
    """
    values = 'attribute', 'kind'


class Column(schema.Item):
    
    heading = schema.One(schema.Text, defaultValue="")

    valueType = schema.One(columnType, initialValue='attribute',
                           doc="The type of value being displayed in "
                           "this column. Determines if client code "
                           "should use 'attributeName' or 'kind' "
                           "attributes of the Column object when "
                           "determining the value of the item in "
                           "this column")

    attributeName = schema.One(schema.Importable,
                               doc="The attribute used to "
                               "evaluate the column value for the "
                               "item in the row.")
    
    attributeSourceName = schema.One(schema.Importable,
                                     doc="The origin of the value used for "
                                     "this attribute in this row.")
    
    indexAttributes = schema.Sequence(schema.Importable, defaultValue=None,
                                      doc="A list of attributes to index on")
    
    icon = schema.One(schema.Text, 
                      doc="An optional name of an image to "
                      "display instead of a label")
    
    useSortArrows = schema.One(schema.Boolean, defaultValue=True,
                               doc="Show arrows when sorting by this column?")
    
    kind = schema.One(schema.Kind, 
                      doc="The Kind used "
                      "for 'kind' columns")

    width = schema.One(schema.Integer,  defaultValue = 20,
                       doc="The width of the column, "
                       "relative to other columns")

    format = schema.One(schema.Text)

    scaleColumn = schema.One(schema.Boolean, defaultValue = False)
    readOnly = schema.One(schema.Boolean, initialValue=False)
    selected = schema.One(schema.Boolean, defaultValue=False)
    
    schema.addClouds(
        copying = schema.Cloud(byRef=[kind])
    )

    def getAttributeEditorValue(self):
        if self.valueType == 'kind':
            return self.kind
        else:
            return self.attributeName
        
class ListDelegate (object):
    """
    Default delegate for Lists that use the block's contents.

    Override to customize your behavior. You must implement
    GetElementValue.
    """
    def GetColumnCount (self):
        return len (self.blockItem.columns)

    def GetElementCount (self):
        return len (self.blockItem.contents)

    def GetElementType (self, row, column):
        return "Text"

    def GetColumnHeading (self, column, item):
        return self.blockItem.columns[column].heading

    def ReadOnly (self, row, column):
        """
        Second argument should be C{True} if all cells have the first value.
        """
        return False, True

    def RowToIndex(self, tableRow):
        """
        Translates a UI row, such as row 3 in the grid, to the
        appropriate row in the collection.
        """
        return tableRow

    def IndexToRow(self, itemIndex):
        """
        Translates an item index, such as item 3 in the collection,
        into a row in the table.
        """
        return itemIndex

    def InitElementDelegate(self):
        """
        Called right after the delegate has been mixed in.
        """
        pass
    
    def SynchronizeDelegate(self):
        """
        Companion to wxSynchronizeWidget - gets called after the main
        class has synchronized itself.
        """
        pass


class AttributeDelegate (ListDelegate):
    """
    Overrides certain methods of wx.grid.Grid.
    """
    def GetElementType (self, row, column):
        """
        An apparent bug in wxWidgets occurs when there are no items
        in a table, the Table asks for the type of cell 0,0
        """
        typeName = "_default"
        try:
            itemIndex = self.RowToIndex(row)
            assert itemIndex != -1
            
            item = self.blockItem.contents [itemIndex]
        except IndexError:
            pass
        else:
            col = self.blockItem.columns[column]
            
            if col.valueType == 'kind':
                typeName = col.kind.itsName
                
            elif col.valueType == 'attribute':
                attributeName = col.attributeName
                if item.itsKind.hasAttribute(attributeName):
                    try:
                        typeName = item.getAttributeAspect (attributeName, 'type').itsName
                    except NoSuchAttributeError:
                        # We special-case the non-Chandler attributes we
                        # want to use (_after_ trying the Chandler
                        # attribute, to avoid a hit on Chandler-attribute
                        # performance). If we want to add other
                        # itsKind-like non-Chandler attributes, we'd add
                        # more tests here.
                        raise
                elif attributeName == 'itsKind':
                    typeName = 'Kind'
            else:
                try:
                    # to support properties, we get the value, and use its type's name.
                    value = getattr (item, attributeName)
                except AttributeError:
                    pass
                else:
                    typeName = type (value).__name__
        return typeName

    def GetElementValue (self, row, column):
        itemIndex = self.RowToIndex(row)
        assert itemIndex != -1

        blockItem = self.blockItem
        item = blockItem.contents[itemIndex]
        col = blockItem.columns[column]
        
        return (item, col.getAttributeEditorValue())
    
    def SetElementValue (self, row, column, value):
        itemIndex = self.RowToIndex(row)
        assert itemIndex != -1
        
        # just for now, you can't 'set' a kind
        assert self.blockItem.columns[column].valueType != 'kind'
        
        item = self.blockItem.contents [itemIndex]
        attributeName = self.blockItem.columns[column].attributeName
        assert item.itsKind.hasAttribute (attributeName), "You cannot set a non-Chandler attribute value of an item (like itsKind)"
        item.setAttributeValue (attributeName, value)

    def GetColumnHeading (self, column, item):
        col = self.blockItem.columns[column]
        if col.valueType == 'kind':
            return col.heading

        attributeName = col.attributeName
        actual = None
        if item is not None:
            try:
                attribute = item.itsKind.getAttribute (attributeName)
            except NoSuchAttributeError:
                # We don't need to redirect non-Chandler attributes (eg, itsKind).
                pass
            else:
                # We got an attribute. Does the column specify an attribute
                # source for this attribute? (eg, the relevantDate attribute has
                # a corresponding relevantDateSource attribute containing the
                # name of the attribute whose value is stored in the relevantDate
                # attribute.) 
                #
                # @@@ i18n This mechanism needs localization, but since the 
                # existing redirectTo usage hasn't been localized since 
                # displayName went away, I'm not worrying about it now...
                #
                attributeSourceName = getattr(col, 'attributeSourceName', None)
                if attributeSourceName is not None:
                    actual = getattr(item, attributeSourceName, None)
                else:
                    redirect = item.getAttributeAspect(attributeName, 'redirectTo')
                    if redirect is not None:
                        names = redirect.split('.')
                        for name in names [:-1]:
                            item = item.getAttributeValue (name)
                        actual = item.itsKind.getAttribute (names[-1]).getItemDisplayName()
                    else:
                        # non-redirecting attribute, use that title
                        pass # heading = attribute.getItemDisplayName()
        
        if actual and actual != col.heading:
            heading = _(u"%(heading)s (%(actual)s)") % {
                'heading': col.heading, 'actual': actual }
        else:
            # no such attribute, use the column heading
            heading = col.heading
        return heading
    

class wxList (DragAndDrop.DraggableWidget, 
              DragAndDrop.ItemClipboardHandler,
              wx.ListCtrl):
    def __init__(self, *arguments, **keywords):
        super (wxList, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnWXSelectItem, id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnItemDrag)

    def OnInit (self):
        elementDelegate = self.blockItem.elementDelegate
        if not elementDelegate:
            elementDelegate = 'osaf.framework.blocks.ControlBlocks.ListDelegate'
        mixinAClass (self, elementDelegate)

    @WithoutSynchronizeWidget
    def OnSize(self, event):
        size = self.GetClientSize()
        widthMinusLastColumn = 0
        assert self.GetColumnCount() > 0, "We're assuming that there is at least one column"
        for column in xrange (self.GetColumnCount() - 1):
            widthMinusLastColumn += self.GetColumnWidth (column)
        lastColumnWidth = size.width - widthMinusLastColumn
        if lastColumnWidth > 0:
            self.SetColumnWidth (self.GetColumnCount() - 1, lastColumnWidth)
        event.Skip()

    @WithoutSynchronizeWidget
    def OnWXSelectItem(self, event):
        item = self.blockItem.contents [event.GetIndex()]
        if self.blockItem.selection != item:
            self.blockItem.selection = item
        self.blockItem.postEventByName("SelectItemsBroadcast", {'items':[item]})
        event.Skip()

    def OnItemDrag(self, event):
        self.DoDragAndDrop()

    def SelectedItems(self):
        """
        Return the list of items currently selected.
        """
        curIndex = -1
        while True:
            curIndex = self.GetNextItem(curIndex, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            yield self.blockItem.contents [curIndex]
            if curIndex is -1:
                break

    def wxSynchronizeWidget(self, useHints=False):
        self.Freeze()
        self.ClearAll()
        self.SetItemCount (self.GetElementCount())
        for columnIndex in xrange (self.GetColumnCount()):
            self.InsertColumn (columnIndex,
                               self.GetColumnHeading (columnIndex, self.blockItem.selection),
                               width = self.blockItem.columns[columnIndex].width)

        self.Thaw()

        if self.blockItem.selection:
            self.GoToItem (self.blockItem.selection)

    def OnGetItemText (self, row, column):
        """
        OnGetItemText won't be called if it's in the delegate -- wxPython
        won't call it if it's in a base class.
        """
        return self.GetElementValue (row, column)

    def OnGetItemImage (self, item):
        return -1

    def GoToItem(self, item):
        self.Select (self.blockItem.contents.index (item))


class wxStaticText(ShownSynchronizer, wx.StaticText):
    pass

class StaticText(RectangularChild):

    textAlignmentEnum = schema.One(
        textAlignmentEnumType, initialValue = 'Left',
    )
    characterStyle = schema.One(Styles.CharacterStyle)
    title = schema.One(schema.Text)

    schema.addClouds(
        copying = schema.Cloud(byRef=[characterStyle])
    )

    def instantiateWidget (self):
        if self.textAlignmentEnum == "Left":
            style = wx.ALIGN_LEFT
        elif self.textAlignmentEnum == "Center":
            style = wx.ALIGN_CENTRE
        elif self.textAlignmentEnum == "Right":
            style = wx.ALIGN_RIGHT

        if Block.showBorders:
            style |= wx.SIMPLE_BORDER

        staticText = wxStaticText (self.parentBlock.widget,
                                   -1,
                                   self.title,
                                   wx.DefaultPosition,
                                   (self.minimumSize.width, self.minimumSize.height),
                                   style)
        staticText.SetFont(Styles.getFont(getattr(self, "characterStyle", None)))
        return staticText

    
class wxStatusBar (ShownSynchronizer, wx.StatusBar):
    def __init__(self, *arguments, **keyWords):
        super (wxStatusBar, self).__init__ (*arguments, **keyWords)
        self.gauge = wx.Gauge(self, -1, 100, size=(125, 30), style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.gauge.Show(False)

    def Destroy(self):
        self.blockItem.getFrame().SetStatusBar(None)
        super (wxStatusBar, self).Destroy()
        
    def wxSynchronizeWidget(self, useHints=False):
        super (wxStatusBar, self).wxSynchronizeWidget()
        self.blockItem.getFrame().Layout()


class StatusBar(Block):
    def instantiateWidget (self):
        frame = self.getFrame()
        widget = wxStatusBar (frame, self.getWidgetID())
        frame.SetStatusBar (widget)
        return widget

    def setStatusMessage(self, statusMessage, progressPercentage=-1):
        """
        Allows you to set the message contained in the status bar.
        You can also specify values for the progress bar contained on
        the right side of the status bar.  If you specify a
        progressPercentage (as a float 0 to 1) the progress bar will appear.
        If no percentage is specified the progress bar will disappear.
        """
        if progressPercentage == -1:
            if self.widget.GetFieldsCount() != 1:
                self.widget.SetFieldsCount(1)
            self.widget.SetStatusText(statusMessage)
            self.widget.gauge.Show(False)
        else:
            if self.widget.GetFieldsCount() != 2:
                self.widget.SetFieldsCount(2)
                self.widget.SetStatusWidths([-1, 150])
            if statusMessage is not None:
                self.widget.SetStatusText(statusMessage)
            self.widget.gauge.Show(True)
            self.widget.gauge.SetValue((int)(progressPercentage*100))
            # By default widgets are added to the left side...we must reposition them
            rect = self.widget.GetFieldRect(1)
            self.widget.gauge.SetPosition((rect.x+2, rect.y+2))
                            
"""
    To use the TreeAndList you must provide a delegate to perform access
    to the data that is displayed.

    You might be able to subclass ListDelegate and implement the
    following methods::

        class TreeAndListDelegate (ListDelegate):

        def GetElementParent(self, element):

        def GetElementChildren(self, element):

        def GetElementValues(self, element):

        def ElementHasChildren(self, element):

    Optionally override GetColumnCount and GetColumnHeading.
"""


class wxTreeAndList(DragAndDrop.DraggableWidget, DragAndDrop.ItemClipboardHandler):
    def __init__(self, *arguments, **keywords):
        super (wxTreeAndList, self).__init__ (*arguments, **keywords)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpanding, id=self.GetId())
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSING, self.OnCollapsing, id=self.GetId())
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColumnDrag, id=self.GetId())
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnWXSelectItem, id=self.GetId())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnItemDrag)

    def OnInit (self):
        mixinAClass (self, self.blockItem.elementDelegate)
        
    @WithoutSynchronizeWidget
    def OnSize(self, event):
        if isinstance (self, wx.gizmos.TreeListCtrl):
            size = self.GetClientSize()
            widthMinusLastColumn = 0
            assert self.GetColumnCount() > 0, "We're assuming that there is at least one column"
            for column in xrange (self.GetColumnCount() - 1):
                widthMinusLastColumn += self.GetColumnWidth (column)
            lastColumnWidth = size.width - widthMinusLastColumn
            if lastColumnWidth > 0:
                self.SetColumnWidth (self.GetColumnCount() - 1, lastColumnWidth)
        else:
            assert isinstance (self, wx.TreeCtrl), "We're assuming the only other choice is a wx.Tree"
        event.Skip()

    @WithoutSynchronizeWidget
    def OnExpanding(self, event):
        self.LoadChildren(event.GetItem())

    def LoadChildren(self, parentId):
        """
        Load the items in the tree only when they are visible.
        """
        child, cookie = self.GetFirstChild (parentId)
        if not child.IsOk():

            parentUUID = self.GetItemData(parentId).GetData()

            if parentUUID is None:
                parent = None
            else:
                parent = wx.GetApp().UIRepositoryView [parentUUID]

            for child in self.GetElementChildren (parent):
                cellValues = self.GetElementValues (child)
                childNodeId = self.AppendItem (parentId,
                                               cellValues.pop(0),
                                               -1,
                                               -1,
                                               wx.TreeItemData (child.itsUUID))
                index = 1
                for value in cellValues:
                    self.SetItemText (childNodeId, value, index)
                    index += 1
                self.SetItemHasChildren (childNodeId, self.ElementHasChildren (child))
 
            self.blockItem.openedContainers [parentUUID] = True

    def OnCollapsing(self, event):
        id = event.GetItem()
        """
        If the data passed in has a UUID we'll keep track of the
        state of the opened tree.
        """
        del self.blockItem.openedContainers [self.GetItemData(id).GetData()]
        self.DeleteChildren (id)

    @WithoutSynchronizeWidget
    def OnColumnDrag(self, event):
        columnIndex = event.GetColumn()
        try:
            self.blockItem.columns[columnIndex].width = self.GetColumnWidth (columnIndex)
        except AttributeError:
            pass

    @WithoutSynchronizeWidget
    def OnWXSelectItem(self, event):
    
        itemUUID = self.GetItemData(self.GetSelection()).GetData()
        selection = self.blockItem.find (itemUUID)
        if self.blockItem.selection != selection:
            self.blockItem.selection = selection

            self.blockItem.postEventByName("SelectItemsBroadcast",
                                           {'items':[selection]})
        event.Skip()
        
    def SelectedItems(self):
        """
        Return the list of selected items.
        """
        try:
            idList = self.GetSelections() # multi-select API supported?
        except:
            idList = [self.GetSelection(), ] # use single-select API
        # convert from ids, which are UUIDs, to items.
        for id in idList:
            itemUUID = self.GetItemData(id).GetData()
            yield self.blockItem.findUUID(itemUUID)

    def OnItemDrag(self, event):
        self.DoDragAndDrop()
        
    def wxSynchronizeWidget(self, useHints=False):
        def ExpandContainer (self, openedContainers, id):
            try:
                expand = openedContainers [self.GetItemData(id).GetData()]
            except KeyError:
                pass
            else:
                self.LoadChildren(id)

                self.Expand(id)

                child, cookie = self.GetFirstChild (id)
                while child.IsOk():
                    ExpandContainer (self, openedContainers, child)
                    child = self.GetNextSibling (child)

        # A wx.TreeCtrl won't use columns
        columns = getattr (self.blockItem, 'columns', None);
        if columns is not None:
            for index in xrange(wx.gizmos.TreeListCtrl.GetColumnCount(self)):
                self.RemoveColumn (0)
    
            info = wx.gizmos.TreeListColumnInfo()
            for index in xrange (self.GetColumnCount()):
                info.SetText (self.GetColumnHeading (index, None))
                info.SetWidth (columns[index].width)
                self.AddColumnInfo (info)

        self.DeleteAllItems()

        root = self.blockItem.rootPath
        if root is None:
            root = self.GetElementChildren (None)[0]
        cellValues = self.GetElementValues (root)
        itemData = wx.TreeItemData (root.itsUUID)
        rootNodeId = self.AddRoot (cellValues.pop(0), -1, -1, itemData)        
        index = 1
        for value in cellValues:
            self.SetItemText (rootNodeId, value, index)
            index += 1
        self.SetItemHasChildren (rootNodeId, self.ElementHasChildren (root))
        self.LoadChildren (rootNodeId)
        ExpandContainer (self, self.blockItem.openedContainers, rootNodeId)

        selection = self.blockItem.selection
        if not selection:
            selection = root
        self.GoToItem (selection)
        
    def GoToItem(self, item):
        def ExpandTreeToItem (self, item):
            parent = self.GetElementParent (item)
            if parent:
                id = ExpandTreeToItem (self, parent)
                self.LoadChildren(id)
                if self.IsVisible(id):
                    self.Expand (id)
                itemUUID = item.itsUUID
                child, cookie = self.GetFirstChild (id)
                while child.IsOk():
                    if self.GetItemData(child).GetData() == itemUUID:
                        return child
                    child = self.GetNextSibling (child)
                assert False, "Didn't find the item in the tree"
                return None
            else:
                return self.GetRootItem()

        id = ExpandTreeToItem (self, item)
        self.SelectItem (id)
        self.ScrollTo (id)

    @classmethod
    def CalculateWXStyle(theClass, block):
        style = wx.TR_DEFAULT_STYLE|wx.NO_BORDER
        if block.hideRoot:
            style |= wx.TR_HIDE_ROOT
        if block.noLines:
            style |= wx.TR_NO_LINES
        if block.useButtons:
            style |= wx.TR_HAS_BUTTONS
        else:
            style |= wx.TR_NO_BUTTONS
        return style
        
 
class wxTree(wxTreeAndList, wx.TreeCtrl):
    pass
    

class wxTreeList(wxTreeAndList, wx.gizmos.TreeListCtrl):
    pass


class Tree(RectangularChild):

    columns = schema.Sequence(Column)

    # We currently use Tree to display the repository in the
    # RepositoryViewer. Since Items in the repository may not
    # have Kinds and we want to store them in the selection,
    # we can't specify a kind for the selection. To be consistent
    # we'll treat rootPath the same way.
    elementDelegate = schema.One(schema.Text, initialValue = '')
    selection = schema.One(initialValue = None)
    hideRoot = schema.One(schema.Boolean, initialValue = True)
    noLines = schema.One(schema.Boolean, initialValue = True)
    useButtons = schema.One(schema.Boolean, initialValue = True)
    openedContainers = schema.Mapping(schema.Boolean, initialValue = {})
    rootPath = schema.One(initialValue = None)

    schema.addClouds(
        copying = schema.Cloud(byCloud=[selection, columns])
    )

    def instantiateWidget(self):
        try:
            self.columns
        except AttributeError:
            tree = wxTree (self.parentBlock.widget, self.getWidgetID(), 
                           style=wxTreeAndList.CalculateWXStyle(self))
        else:
            tree = wxTreeList (self.parentBlock.widget, self.getWidgetID(), 
                               style=wxTreeAndList.CalculateWXStyle(self))
        return tree

    def onSelectItemsEvent (self, event):
        items = event.arguments['items']
        if len(items)>0:
            self.widget.GoToItem (event.arguments['items'][0])


class wxItemDetail(HtmlWindowWithStatus):
    def OnLinkClicked(self, wx_linkinfo):
        """
        Clicking on an item changes the selection (post event).
        Clicking on a URL loads the page in a separate browser.
        """
        itemURL = wx_linkinfo.GetHref()
        item = self.blockItem.findPath(itemURL)
        if not item:
            webbrowser.open(itemURL)
        else:
            self.blockItem.postEventByName("SelectItemsBroadcast",
                                           {'items':[item]})

    def wxSynchronizeWidget(self, useHints=False):
        if self.blockItem.selection is not None:
            self.SetPage (self.blockItem.getHTMLText (self.blockItem.selection))
        else:
            self.SetPage('<html><body></body></html>')


class ItemDetail(RectangularChild):

    # We currently use ItemDetail to display the repository in the
    # RepositoryViewer. Since Items in the repository may not
    # have Kinds and we want to store them in the selection,
    selection = schema.One(initialValue = None)
    schema.addClouds(
        copying = schema.Cloud(byRef=[selection])
    )

    def __init__(self, *arguments, **keywords):
        super (ItemDetail, self).__init__ (*arguments, **keywords)
        self.selection = None

    def instantiateWidget (self):
        return wxItemDetail (self.parentBlock.widget,
                             self.getWidgetID(),
                             wx.DefaultPosition,
                             (self.size.width,
                              self.size.height))

    def getHTMLText(self, item):
        return u'<body><html><h1>%s</h1></body></html>' % item.getDisplayName()

    def onSelectItemsEvent (self, event):
        """
        Display the item in the wxWidget.
        """
        items = event.arguments['items']
        if len(items)>0:
            self.selection = items[0]
        else:
            self.selection = None
        self.synchronizeWidget ()


class ContentItemDetail(BoxContainer):
    """
    Any container block in the Content Item's Detail View hierarchy.

    Not to be confused with ItemDetail (above) which uses an HTML-based widget.
    Keeps track of the current selected item supports Color Style.
    """
    colorStyle = schema.One(Styles.ColorStyle)

class wxPyTimer(wx.Timer):
    """ 
    A wx.PyTimer that has an IsShown() method, like all the other widgets
    that blocks deal with; it also generates its own event from Notify.
    """              
    def IsShown(self):
        return True

    def Notify(self):
        event = wx.PyEvent()
        event.SetEventType(wx.wxEVT_TIMER)
        event.SetId(self.GetId())
        wx.GetApp().OnCommand(event)

    def Destroy(self):
       Block.wxOnDestroyWidget (self)

class Timer(Block):
    """
    A Timer block. Fires (sending a BlockEvent) at a particular time.
    A passed time will fire "shortly".
    """

    event = schema.One(
        BlockEvent,
        doc = "The event we'll send when we go off",
    )

    schema.addClouds(
        copying = schema.Cloud(byCloud=[event])
    )

    def instantiateWidget (self):
        timer = wxPyTimer(self.parentBlock.widget, self.getWidgetID())
        return timer

    def onDestroyWidget(self):
        self.widget.Stop()
        super(Timer, self).onDestroyWidget()

    def setFiringTime(self, when):
        """ 
        Set the timer. 
        "when" can be a timedelta (relative to now) or a datetime (absolute).
        """
        # First turn off the old timer
        timer = self.widget
        timer.Stop()

        # Set the new time, if we have one. If it's in the past, fire "really soon". If it's way in the future,
        # don't bother firing.
        if when is not None:
            if isinstance(when, timedelta):
                td = when
                if __debug__:
                    when = datetime.now(PyICU.ICUtzinfo.default) + when
            else:
                td = (when - datetime.now(PyICU.ICUtzinfo.default))
            millisecondsUntilFiring = ((td.days * 86400) + td.seconds) * 1000L
            if millisecondsUntilFiring < 100:
                millisecondsUntilFiring = 100
            elif millisecondsUntilFiring > sys.maxint:
                millisecondsUntilFiring = sys.maxint

            logger.debug("*** setFiringTime: will fire at %s in %s minutes" 
                         % (when, millisecondsUntilFiring / 60000))
            timer.Start(millisecondsUntilFiring, True)
        else:
            logger.debug("*** setFiringTime: No new time.")
            pass

class ReminderTimer(Timer):
    """
    Watches for reminders & drives the reminder dialog.
    """
    
    def synchronizeWidget (self, *args, **kwds):
        logger.debug("*** Synchronizing ReminderTimer widget!")
        super(ReminderTimer, self).synchronizeWidget(*args, **kwds)
        if not wx.GetApp().ignoreSynchronizeWidget:
            self.primeReminderTimer()
    
    def getPendingReminders (self):
        """
        Return a list of all reminder tuples with fire times in the past, 
        sorted by reminderTime.

        Each tuple contains (reminderTime, remindable, reminder).
        """

        view = self.itsView
        # nextReminderTime always adds a timezone, so add one to now 
        now = datetime.now(PyICU.ICUtzinfo.default)

        def matches(key):
            if view[key].nextReminderTime <= now:
                return 0
            return -1

        itemsWithReminders = schema.ns('osaf.pim', view).itemsWithReminders
        lastPastKey = itemsWithReminders.findInIndex('reminderTime', 'last', matches)

        if lastPastKey is not None:
            return [item.getNextReminderTuple()
                    for item in (view[key] for key in
                     itemsWithReminders.iterindexkeys('reminderTime', None, lastPastKey))]

        return []
    
    def onReminderTimeEvent(self, event):
        # Run the reminders dialog and re-queue our timer if necessary
        logger.debug("*** Got reminders time event!")
        self.primeReminderTimer()

    def primeReminderTimer(self):
        """
        Prime the reminder timer and maybe show or hide the dialog
        """
        # Ignore prime calls while we're priming
        if getattr(self, '_inPrimeReminderTimer', False):
            logger.debug("(** skipping recursive call to primeReminderTimer")
            return
        
        self._inPrimeReminderTimer = True
        try:
            mainFrame = wx.GetApp().mainFrame
            if not mainFrame.IsShown():
                # The main window isn't up yet; try again shortly.
                (nextReminderTime, closeIt) = (datetime.now(
                    PyICU.ICUtzinfo.default) + timedelta(seconds=1), False)
            else:
                # Update triagestatus on each pending reminder. Dismiss any
                # internal reminders that exist only to trigger on startTime.
                pending = self.getPendingReminders()
                if pending:
                    def processReminder((reminderTime, remindable, reminder)):
                        logger.debug("*** now-ing %s due to %s", remindable, 
                                     reminder)
                        remindable.triageStatus = 'now'
                        remindable.setTriageStatusChanged(when=reminderTime)
                        if reminder.isDeleted():
                            logger.critical("Found deleted reminder on %r %s at %s",
                                            remindable, remindable,
                                            remindable.startTime)
                        assert not reminder.isDeleted()
                        if reminder.userCreated:
                            return True # this should appear in the list.
                        # This is a non-user reminder, which served only to let us
                        # bump the triageStatus. Discard it.
                        remindable.dismissReminder(reminder)
                        return False
                    pending = filter(processReminder, pending)

                # Get the dialog if we have it; we'll create it 
                # if it doesn't exist.
                if pending:
                    reminderDialog = self.getReminderDialog(True)

                    # The dialog is displayed; get the list of pending reminders and 
                    # let it update itself. It'll tell us when it wants us to fire next, 
                    # or whether we should close it now.
                                        
                    (nextReminderTime, closeIt) = reminderDialog.UpdateList(pending)
                else:
                    # Or not.
                    (nextReminderTime, closeIt) = (None, True)
            if nextReminderTime is None:
                # The dialog didn't give us a time to fire; we'll fire at the
                # next non-pending reminder's time.
                itemsWithReminders = schema.ns('osaf.pim', self.itsView).itemsWithReminders
                firstReminder = itemsWithReminders.firstInIndex('reminderTime')
                if firstReminder is not None:
                    nextReminderTime = firstReminder.nextReminderTime
    
            if closeIt:
                self.closeReminderDialog()
            self.setFiringTime(nextReminderTime)

        finally:
            del self._inPrimeReminderTimer                


    def getReminderDialog(self, createIt):
        try:
            reminderDialog = self.widget.reminderDialog
        except AttributeError:
            if createIt:
                reminderDialog = ReminderDialog.ReminderDialog(wx.GetApp().mainFrame, -1)
                self.widget.reminderDialog = reminderDialog
                reminderDialog.dismissCallback = self.markDirty
            else:
                reminderDialog = None
        return reminderDialog

    def closeReminderDialog(self):
        try:
            reminderDialog = self.widget.reminderDialog
        except AttributeError:
            pass
        else:
            del self.widget.reminderDialog
            reminderDialog.Destroy()

    def setFiringTime(self, when):
        logger.debug("*** next reminder due %s", when)
        super(ReminderTimer, self).setFiringTime(when)

class PresentationStyle(schema.Item):
    """ 
    Information that customizes picking or presentation of an attribute
    editor in an L{AEBlock}.

    L{format} is used to influence the picking process; see
    L{osaf.framework.attributeEditors.AttributeEditors.getAEClass} for
    information on how it's used.

    The other settings are used by various attribute editors to customize
    their presentation or behavior.
    """

    sampleText = schema.One(
        schema.Text,
        doc = 'Localized in-place sample text (optional); if "", will use the attr\'s displayName.',
    )
    format = schema.One(
        schema.Text,
        doc = 'customization of presentation format',
    )
    choices = schema.Sequence(
        schema.Text,
        doc = 'options for multiple-choice values',
    )
    editInPlace = schema.One(
        schema.Boolean,
        doc = 'For text controls, True if we should wait for a click to become editable',
    )
    lineStyleEnum = schema.One(
        lineStyleEnumType,
        doc = 'SingleLine vs MultiLine for textbox-based editors',
    )
    schema.addClouds(
        copying = schema.Cloud(
            byValue=[sampleText,format,choices,editInPlace,lineStyleEnum]
        )
    )

class AEBlock(BoxContainer):
    """
    Attribute Editor Block: instantiates an Attribute Editor appropriate for
    the value of the specified attribute; the Attribute Editor then creates
    the widget. Issues:
     - Finalization.  We're relying on EVT_KILL_FOCUS to know when to end
       editing.  We know the Detail View doesn't always operate in ways that
       cause this to be reliable, but I think these problems can be fixed there.
    """
    schema.kindInfo(
        description="Block that instantiates an appropriate Attribute Editor."
    )

    characterStyle = schema.One(Styles.CharacterStyle, 
        doc="""an optional CharacterStyle in which this editor should draw""")
    readOnly = schema.One(schema.Boolean, initialValue = False,
        doc="""If True, this editor should never allow editing of its value""")
    presentationStyle = schema.One(PresentationStyle,
        doc="""an optional PresentationStyle to customize
               this editor's selection or behavior""")

    schema.addClouds(
        copying = schema.Cloud(byRef=[characterStyle, presentationStyle])
    )

    def setItem(self, value): 
        assert not value.isDeleted()
        self.contents = value
    item = property(Block.getProxiedContents, setItem, 
                    doc="Safely access the selected item (or None)")

    def getAttributeName(self): return getattr(self, 'viewAttribute', None)
    def setAttributeName(self, value): self.viewAttribute = value
    attributeName = property(getAttributeName, setAttributeName, doc=\
                             "Safely access the configured attribute name (or None)")

    def instantiateWidget(self):
        """
        Ask our attribute editor to create a widget for us.

        @return: the widget
        @rtype: wx.Widget
        """
        existingWidget = getattr(self, 'widget', None) 
        if existingWidget is not None:
            return existingWidget

        forEditing = getattr(self, 'forEditing', False)

        # Tell the control what font we expect it to use
        try:
            charStyle = self.characterStyle
        except AttributeError:
            charStyle = None
        font = Styles.getFont(charStyle)

        editor = self.lookupEditor()
        if editor is None:
            assert False
            widget = wx.Panel(self.parentBlock.widget, self.getWidgetID())
            return widget

        widget = editor.CreateControl(forEditing, editor.readOnly,
                                      self.parentBlock.widget,
                                      self.getWidgetID(), self, font)
        widget.SetFont(font)
        # logger.debug("Instantiated a %s, forEditing = %s" % (widget, forEditing))

        # Cache a little information in the widget.
        widget.editor = editor

        widget.Bind(wx.EVT_KILL_FOCUS, self.onLoseFocusFromWidget)
        widget.Bind(wx.EVT_KEY_UP, self.onKeyUpFromWidget)
        widget.Bind(wx.EVT_LEFT_DOWN, self.onClickFromWidget)

        return widget

    def synchronizeWidget (self, useHints=False):
        """
        Override to call the editor to do the synchronization.

        @param useHints: Ignored here for now
        """
        def BeginEdit():
            editor = self.lookupEditor()
            if editor is not None:
                editor.BeginControlEdit(editor.item, editor.attributeName, self.widget)

        if not wx.GetApp().ignoreSynchronizeWidget:
            IgnoreSynchronizeWidget(True, BeginEdit)


    def onWidgetChangedSize(self):
        """
        Called by our widget when it changes size.
        Presumes that there's an event boundary at the point where
        we need to resynchronize, so it will work with the Detail View.
        """
        evtBoundaryWidget = self.widget
        while evtBoundaryWidget is not None:
            if evtBoundaryWidget.blockItem.eventBoundary:
                break
            evtBoundaryWidget = evtBoundaryWidget.GetParent()
        if evtBoundaryWidget:
            evtBoundaryWidget.blockItem.synchronizeWidget()

    def lookupEditor(self):
        """
        Make sure we've got the right attribute editor for this type.

        @return: The editor to use for the configured item/attributeName, or None
        @rtype: BaseAttributeEditor
        """
        item = self.item
        if item is None:
            return None
        
        # Get the parameters we'll use to pick an editor
        (typeName, cardinality) = self.getItemAttributeTypeInfo()
        attributeName = self.attributeName
        readOnly = self.isReadOnly(item, attributeName)
        try:
            presentationStyle = self.presentationStyle
        except AttributeError:
            presentationStyle = None
        
        # If we have an editor already, and it's the right one, return it.
        try:
            oldEditor = self.widget.editor
        except AttributeError:
            pass
        else:
            if (oldEditor is not None):
                if (oldEditor.typeName == typeName
                   and oldEditor.cardinality == cardinality
                   and oldEditor.attributeName == attributeName
                   # see bug 4553 note below: was "and oldEditor.readOnly == readOnly"
                   and oldEditor.presentationStyle is presentationStyle):
                    # Yep, it's good enough - use it.
                    oldEditor.item = item # note that the item may have changed.
                    return oldEditor

                # It's not good enough, so we'll be changing editors.
                # unRender(), then re-render(); lookupEditor will get called
                # from within render() and will install the right editor; once
                # it returns, we can just return that.
                # @@@ Note:
                # - I don't know of a case where this can happen now (it would
                #   require a contentitem kind containing an attribute whose
                #   value could have different types, and whose different types
                #   have different attribute editors registered for them), 
                #   so this hasn't been tested.
                # - If this does happen in a situation where this code is called
                #   from within a wx event handler on this item's widget, a
                #   crash would result (because wx won't be happy if we return
                #   through it after that widget has been destroyed).
                # Additional note from work on bug 4553:
                # - Prior to bug 4553, we included read-onlyness in the test 
                #   above for whether the existing editor was still suitable 
                #   for editing this attribute. Unfortunately, that bug
                #   presented a case where this (a need to change widgets, which 
                #   the code below wants to do, but which doesn't work right)
                #   happened. Since this case only happens in 0.6 when readonly-
                #   ness is the issue on text ctrls, I'm fixing the problem by 
                #   making BeginControlEdit on those ctrls call wx.SetEditable
                #   (or not) when appropriate.
                assert False, "Please let Bryan know you've found a case where this happens!"
                logger.debug("AEBlock.lookupEditor %s: Rerendering", 
                             getattr(self, 'blockName', '?'))
                self.unRender()
                self.render()
                self.onWidgetChangedSize(item)
                return getattr(self.widget, 'editor', None)

        # We need a new editor - create one.
        #logger.debug("Creating new AE for %s (%s.%s), ro=%s", 
                     #typeName, item, attributeName, readOnly)
        selectedEditor = AttributeEditors.getInstance\
                       (typeName, cardinality, item, attributeName, readOnly, presentationStyle)

        # Note the characteristics that made us pick this editor
        selectedEditor.typeName = typeName
        selectedEditor.cardinality = cardinality
        selectedEditor.item = item
        selectedEditor.attributeName = attributeName
        selectedEditor.readOnly = readOnly
        selectedEditor.presentationStyle = presentationStyle
        selectedEditor.parentBlock = self

        return selectedEditor

    def isReadOnly(self, item, attributeName):
        """
        Are we not supposed to allow editing?

        @param item: The item we're operating on
        @type item: Item
        @param attributeName: the name of the attribute from the item
        @type attributeName: String
        @returns: True if we're configured to be readonly, or if the content
        model says we shouldn't let the user edit this; else False.
        @rtype: Boolean
        """
        if self.readOnly: 
            return True

        # Return true if the domain model says this attribute should be R/O
        # (we might not be editing an item, so we check the method presence)
        try:
            isAttrModifiable = item.isAttributeModifiable
        except AttributeError:
            result = False
        else:
            result = not isAttrModifiable(attributeName)

        #logger.debug("AEBlock: %s %s readonly", attributeName,
                     #result and "is" or "is not")
        return result

    def onSetContentsEvent (self, event):
        self.setContentsOnBlock(event.arguments['item'],
                                event.arguments['collection'])
        assert not hasattr(self, 'widget')

    def getItemAttributeTypeInfo(self):
        """
        Get the type & cardinality of the current attribute.
        
        @returns: A tuple containing the name of the type and the cardinality
        of the item/attribute we're operating on
        @rtype: String
        """
        item = self.item
        if item is None:
            return (None, 'single')

        # Ask the schema for the attribute's type first
        cardinality = 'single'
        theType = item.getAttributeAspect(self.attributeName, 'type', True)
        if theType is not None:
            # The repository knows about it.
            typeName = theType.itsName
            cardinality = item.getAttributeAspect(self.attributeName, 'cardinality')
        else:
            # If the repository doesn't know about it (it might be a property),
            # see if it's one of our type-friendly Calculated properties
            try:
                theType = schema.itemFor(getattr(item.__class__, 
                                                 self.attributeName).type, 
                                         item.itsView)
            except:
                # get its value and use its type
                try:
                    attrValue = getattr(item, self.attributeName)
                except:
                    typeName = "_default"
                else:
                    typeName = type(attrValue).__name__
            else:
                # Got the computed property's type - get its name
                typeName = theType.itsName
        
        return (typeName, cardinality)

    def onClickFromWidget(self, event):
        """
        The widget got clicked on - make sure we're in edit mode.

        @param event: The wx event representing the click
        @type event: wx.Event
        """
        #logger.debug("AEBlock: %s widget got clicked on", self.attributeName)

        # If the widget didn't get focus as a result of the click,
        # grab focus now.
        # @@@ This was an attempt to fix bug 2878 on Mac, which doesn't focus
        # on popups when you click on them (or tab to them!)
        oldFocus = self.getFocusBlock()
        if oldFocus is not self:
            Block.finishEdits(oldFocus) # finish any edits in progress

            #logger.debug("Grabbing focus.")
            wx.Window.SetFocus(self.widget)

        event.Skip()

    def onLoseFocusFromWidget(self, event):
        """
        The widget lost focus - we're finishing editing.

        @param event: The wx event representing the lose-focus event
        @type event: wx.Event
        """
        #logger.debug("AEBlock: %s, widget losing focus" % self.blockName)
        
        if event is not None:
            event.Skip()
        
        # Workaround for wx Mac crash bug, 2857: ignore the event if we're being deleted
        widget = getattr(self, 'widget', None)
        if widget is None or widget.IsBeingDeleted() or widget.GetParent().IsBeingDeleted():
            #logger.debug("AEBlock: skipping onLoseFocus because the widget is being deleted.")
            return

        # Make sure the value is written back to the item. 
        self.saveValue()

    def saveValue(self, validate=False):
        """
        Make sure the value is written back to the item.

        @param validate: (Ignored here)
        """
        widget = getattr(self, 'widget', None)
        if widget is not None:
            editor = self.widget.editor
            if editor is not None:
                editor.EndControlEdit(self.item, self.attributeName, widget)

    def unRender(self):
        # Last-chance write-back.
        if getattr(self, 'forEditing', False):
            self.saveValue()
        super(AEBlock, self).unRender()
            
    def onKeyUpFromWidget(self, event):
        if event.m_keyCode == wx.WXK_RETURN \
           and not getattr(event.GetEventObject(), 'ateLastKey', False):
            # Do the tab thing if we're not a multiline thing.
            # stearns says: I think this is wrong (it doesn't mix well when one 
            # of the fields you'd "enter" through is multiline - it clears the 
            # content!) but Mimi wants it to work like iCal.
            try:
                isMultiLine = self.presentationStyle.lineStyleEnum == "MultiLine"
            except AttributeError:
                isMultiLine = False
            if not isMultiLine:
                self.widget.Navigate()
        event.Skip()

# Ewww, yuk.  Blocks and attribute editors are mutually interdependent
import osaf.framework.attributeEditors
AttributeEditors = sys.modules['osaf.framework.attributeEditors']

