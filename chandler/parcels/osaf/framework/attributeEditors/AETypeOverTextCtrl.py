#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

import wx
from osaf.framework.blocks.Block import BaseWidget, wxRectangularChild
from DragAndDropTextCtrl import DragAndDropTextCtrl
from BaseAttributeEditor import NotifyBlockToSaveValue
import logging
logger = logging.getLogger(__name__)

class AEStaticText(BaseWidget,
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


class AENonTypeOverTextCtrl(DragAndDropTextCtrl):
    def __init__(self, *args, **keys):
        super(AENonTypeOverTextCtrl, self).__init__(*args, **keys)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnEditLoseFocus)

    def OnEditLoseFocus(self, event):
        NotifyBlockToSaveValue(self)
        event.Skip()


class AETypeOverTextCtrl(wxRectangularChild):
    def __init__(self, parent, id, title=u'', position=wx.DefaultPosition,
                 size=wx.DefaultSize, maxLineCount=1, style=0, staticControlDelegate=None, *args, **keys):
        super(AETypeOverTextCtrl, self).__init__(parent, id)
        staticSize = keys['staticSize']
        del keys['staticSize']
        self.hideLoc = (-100,-100)
        self.showLoc = (0,0)
        self.modelData = title
        self.staticControlDelegate = staticControlDelegate

        assert maxLineCount > 0
        size.height *= maxLineCount
        editStyle = style | wx.WANTS_CHARS
        if maxLineCount > 1:
            editStyle |= wx.TE_MULTILINE|wx.TE_AUTO_SCROLL

        editControl = DragAndDropTextCtrl(self, -1, pos=position, size=size, 
                                          style=editStyle, *args, **keys)
        self.editControl = editControl
        editControl.Bind(wx.EVT_KILL_FOCUS, self.OnEditLoseFocus)
        editControl.Bind(wx.EVT_SET_FOCUS, self.OnEditGainFocus)
        editControl.Bind(wx.EVT_LEFT_DOWN, self.OnEditClick)
        editControl.Bind(wx.EVT_LEFT_DCLICK, self.OnEditClick)
        editControl.Bind(wx.EVT_KEY_UP, self.OnEditKeyUp)

        # don't automatically resize the static control to snugly fit the text,
        # since any manipulation by the staticControlDelegate could cause it to
        # shrink down to nothing
        style |= wx.ST_NO_AUTORESIZE
        staticControl = AEStaticText(self, -1, pos=position, size=staticSize,
                                     style=style, *args, **keys)
        self.staticControl = staticControl
        staticControl.Bind(wx.EVT_LEFT_UP, self.OnStaticClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnStaticClick)
        staticControl.Bind(wx.EVT_SIZE, self.OnSize)

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
        "Switch from the static control to the edit-text control."        
        # If we're static, we don't switch. (If we're readonly, we'll still 
        # switch to the edit control, but it'll be read-only, so that the user 
        # can still select and copy text out.)
        try:
            staticMethod = self.editor.isStatic
            item = self.editor.item
            attributeName = self.editor.attributeName
        except AttributeError:
            pass
        else:
            # If we're static, we want to ignore the click and not turn 
            # editable. (Also, note: no Skip())
            if staticMethod((item, attributeName)):
                return

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
        # don't access the widget if it's not safe (quitting)
        if self.IsBeingDeleted() or self.GetParent().IsBeingDeleted():
            return
        self._swapControls(self.staticControl)
        event.Skip()

    def OnEditKeyUp(self, event):
        if event.m_keyCode == wx.WXK_RETURN and \
           not getattr(event.GetEventObject(), 'ateLastKey', False):
            # not needed: Navigating will make us lose focus
            # NotifyBlockToSaveValue(self)
            self.Navigate()
        event.Skip()

    def OnSize(self, event):
        """
        if the control is resized, allow the staticControlDelegate to adjust
        accordingly
        """
        if self.staticControlDelegate is not None:
            self.staticControlDelegate.SetStaticControl(self.staticControl, self.modelData)
        event.Skip()

    def _swapControls(self, controlToShow):
        if controlToShow is self.otherControl:
            hiddenControl = controlToShow
            shownControl = self.shownControl
            self.Freeze()
            swappingToStatic = False
            if shownControl is self.editControl:
                self.modelData = shownControl.GetValue()
                swappingToStatic = True
            if self.staticControlDelegate is not None and swappingToStatic:
                self.staticControlDelegate.SetStaticControl(self.staticControl, self.modelData)
            else:
                hiddenValue = hiddenControl.GetValue()
                shownValue = shownControl.GetValue()
                if shownValue != hiddenValue:
                    # self.swapDelegate(shownValue)
                    hiddenControl.SetValue(self.modelData)

            shownControl.Move(self.hideLoc)
            hiddenControl.Move(self.showLoc)
            self.shownControl = hiddenControl
            self.otherControl = shownControl
            self._updateStaticToolTip(self.modelData)
            self._resize()
            self.Thaw()
            if wx.Platform == '__WXGTK__':
                self.GetGrandParent().Refresh()

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
    
    def _updateStaticToolTip(self, tooltipText):
        if self.shownControl is self.staticControl:
            dc = wx.ClientDC(self.editControl)
            assert (dc is not None)
            (renderedStringWidth, ignoredHeight) = dc.GetTextExtent(tooltipText)
            if self.editControl.GetClientSize().width > renderedStringWidth:
                tooltipText = u''
            self.staticControl.SetToolTipString(tooltipText)

    def GetValue(self):
        if self.shownControl is self.editControl:
            return self.shownControl.GetValue()
        else:
            return self.modelData

    def SetValue(self, *args):
        value = args[0]
        assert isinstance(value, basestring)
        self.modelData = value
        # ensure that static control delegate gets a chance to modify the display of the new model data
        if self.staticControlDelegate is not None and self.shownControl is self.staticControl:
            self.staticControlDelegate.SetStaticControl(self.staticControl, value)
        else:
            # We're editing the value, so no need to call the staticControlDelegate
            self.shownControl.SetValue(value)
        self._updateStaticToolTip(value)

    def GetInsertionPoint(self): return self.shownControl.GetInsertionPoint()
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

    def SetStaticControlDelegate(self, staticDelegate):
        self.staticControlDelegate = staticDelegate

    def GetStaticControlDelegate(self):
        return self.staticControlDelegate

