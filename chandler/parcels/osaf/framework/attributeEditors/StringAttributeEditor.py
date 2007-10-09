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
from chandlerdb.util.c import Nil
from osaf.framework.blocks import DrawingUtilities, Styles
import logging
from application.dialogs import RecurrenceDialog
from i18n import ChandlerMessageFactory as _
from AETypeOverTextCtrl import AETypeOverTextCtrl, AENonTypeOverTextCtrl
from BaseAttributeEditor import BaseAttributeEditor

logger = logging.getLogger(__name__)

# Should we do autocompletion? (was handy for turning it off during development)
bigAutocompletionSwitch = True

class StringAttributeEditor (BaseAttributeEditor):
    """ 
    Uses a Text Control to edit attributes in string form.
    Supports sample text.
    """
    def __init__(self, staticControlDelegate=None, *args, **kwargs):
        super(StringAttributeEditor, self).__init__(*args, **kwargs)
        self.staticControlDelegate = staticControlDelegate

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

    def GetTextToDraw(self, item, attributeName):
        """
        Get a tuple: the text to be drawn as our static representation, and 
        whether it's the sample text, and a prefix if any (which is to be drawn
        in gray before the real text).
        """
        # Get the text we'll display, and note whether it's the sample text.
        isSample = False
        theText = None # assume that we won't use the sample.
        if not self.HasValue(item, attributeName):
            # Consider using the sample text
            theText = self.GetSampleText(item, attributeName)
        if theText is None:
            # No sample text, or we have a value. Use the value.
            theText = self.GetAttributeValue(item, attributeName)
        elif len(theText) > 0:
            # theText is the sample text - switch to gray
            isSample = True            
        return (None, theText, isSample)

    def Draw (self, grid, dc, rect, (item, attributeName), isInSelection=False):
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
        prefix, theText, isSample = self.GetTextToDraw(item, attributeName)

        # We'll draw the sample or prefix in gray (unless it's part of the
        # selection, in which case we'll leave it white)
        if not isInSelection and (isSample or prefix is not None):
            oldForeground = wx.Colour(dc.GetTextForeground())
            dc.SetTextForeground (wx.SystemSettings.GetColour (wx.SYS_COLOUR_GRAYTEXT))

        haveText = len(theText) > 0
        if (prefix is not None) or haveText:
            # Draw inside the lines.
            dc.SetBackgroundMode (wx.TRANSPARENT)
            rect.Inflate (-1, -1)
            dc.SetClippingRect (rect)
    
            textFont = Styles.getFont(grid.blockItem.characterStyle)
            textMeasurements = Styles.getMeasurements(textFont)
            textHeight = textMeasurements.height
            textTop = (rect.GetHeight() - textHeight) / 2
        
            if prefix is not None:
                # Match up baselines
                prefixFont = Styles.getFont(grid.blockItem.prefixCharacterStyle)
                prefixMeasurements = Styles.getMeasurements(prefixFont)
                prefixHeight = prefixMeasurements.height
                prefixTop = textTop + ((textHeight - textMeasurements.descent) -
                                       (prefixHeight - prefixMeasurements.descent))
                dc.SetFont(prefixFont)
                width = DrawingUtilities.DrawClippedTextWithDots(dc, prefix, 
                                                                 rect, 
                                                                 top=prefixTop)
                if width > 0:
                    rect.x += width
                    rect.width -= width
                if not isInSelection:
                    dc.SetTextForeground(oldForeground)
                dc.SetFont(textFont)

            if haveText:
                DrawingUtilities.DrawClippedTextWithDots (dc, theText, rect, 
                                                          top=textTop)
                
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

        style = 0
        if readOnly: style |= wx.TE_READONLY
        
        if useStaticText:
            style |= (parentWidget.GetWindowStyle() & wx.SIMPLE_BORDER)
            try:
                maxLineCount = self.presentationStyle.maxLineCount
            except AttributeError:
                maxLineCount = 1
            control = AETypeOverTextCtrl(parentWidget, id, '', wx.DefaultPosition, 
                                         size, maxLineCount, style, staticControlDelegate = self.staticControlDelegate,
                                         staticSize=wx.Size(width, staticHeight))
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
            if wx.Platform == "__WXMAC__": 
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
            currentText = control.GetValue()
            # If the text has changed, write it back in a little while.
            if control.IsModified():
                wx.GetApp().scheduleSave()
            if getattr(self, 'sampleText', None) is not None:
                currentText = control.GetValue()
                #logger.debug("StringAE.onTextChanged: not ignoring; value is '%s'" % currentText)                    
                if self.showingSample:
                    if currentText != self.sampleText:
                        alreadyChanged = True
                        # workaround for bug 3085 - changed text starts with copy of sample
                        #  due to multiple calls to this method
                        if wx.Platform == '__WXGTK__':
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
            # workaround for bug 9496 (DV start/end date/time fields text light gray instead of black)
            # from the bug comments:
            #   there is a place in wxMac where if the color being set is black
            #   then it is ignored because, according to the comment, "otherwise
            #   disabled controls won't be grayed out by the system anymore."  I've
            #   asked about this in the past but I don't remember what the response was.
            #   A simple workaround is to set a color that is almost black instead,
            #   such as wx.Colour(1,1,1).
            if normalTextColor == wx.BLACK:
                normalTextColor = wx.Colour(1, 1, 1)

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
                    
            control.DiscardEdits() # clear the 'changed' flag
            wx.GetApp().unscheduleSave()
    
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

        return sampleText or attributeName

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

    def IsValidForWriteback(self, valueString):
        """
        Return true if this value is valid and parseable.
        (Used to ignore invalid values instead of writing back when typing)
        """
        return True

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


class wxAutoCompleter(wx.ListBox):
    """
    A listbox that pops up for autocompletion.
    """
    # For now, measuring the font isn't working well;
    # use these 'adjustments'
    # @@@ ugh: ought to find a better way than this!
    if wx.Platform == '__WXMAC__':
        totalSlop = 5
        unitSlop = 4
        defaultBorderStyle = wx.STATIC_BORDER
    elif wx.Platform == '__WXGTK__':
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
