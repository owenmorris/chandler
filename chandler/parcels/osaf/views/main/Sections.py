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


import wx
from application import schema, styles
from i18n import ChandlerMessageFactory as _
from osaf.framework.blocks import (ControlBlocks, DrawingUtilities, 
                                   Styles)
from osaf.framework.attributeEditors import BaseAttributeEditor
from osaf.pim import getTriageStatusName
from util.divisions import get_divisions

import logging
logger = logging.getLogger(__name__)

# Drawing geometry
margin = 10
swatchWidth = 25
swatchHeight = '__WXMAC__' in wx.PlatformInfo and 8 or 10

class SectionedGridDelegate(ControlBlocks.AttributeDelegate):

    def InitElementDelegate(self):
        # indexes of item in blockItem.contents that designate the
        # start of a new section
        self.sectionIndexes = []

        # an array of (row, length) where row is the row that has a
        # section header, and length is the number of rows following
        # that section header. Note that length+1 is the number of
        # rows including the section header
        self.sectionRows = []

        self.sectionLabels = []

        # total rows in the table
        self.totalRows = 0

        # The attribute we're sectioning on
        self.attributeName = None

        self.previousIndex = self.blockItem.contents.indexName
        self.currentColumn = self.findCurrentColumn()
        
    def SynchronizeDelegate(self):
        """
        its reasonably cheap to rebuild section indexes, as
        get_divisions is really optimized for this
        """
        if self.previousIndex != self.blockItem.contents.indexName:
            self.currentColumn = self.findCurrentColumn()
            self.previousIndex = self.blockItem.contents.indexName
            
        self.RebuildSections()

    def RebuildSections(self):
        """
        rebuild the sections - this is relatively cheap as long as
        there aren't a lot of sections
        """
        super(SectionedGridDelegate, self).RebuildSections()
        self.sectionRows = []
        self.sectionLabels = []
        self.sectionIndexes = []
        self.sectionColors = []
        self.totalRows = len(self.blockItem.contents)
        self.attributeName = None
        
        dashboardPrefs = schema.ns('osaf.views.main',
                                   self.blockItem.itsView).dashboardPrefs
        if not dashboardPrefs.showSections:
            return
        
        indexName = self.blockItem.contents.indexName        
        # @@@ For now, we only section on triage status
        if indexName != 'osaf.views.main.summaryblocks.triage': 
            return
        self.attributeName = self.currentColumn.attributeName
        
        # Get the divisions
        self.sectionIndexes = get_divisions(self.blockItem.contents,
            key=lambda x: getattr(x, self.attributeName))

        # don't show section headers unless we have at least one section
        if len(self.sectionIndexes) == 0:
            return
            
        # now build the row-based sections - each entry in this array
        # is the actual row that contains the section divider
        self.totalRows = 0
        nextSectionRow = 0
        for section in range(0, len(self.sectionIndexes)):
            sectionRow = nextSectionRow
            if section == len(self.sectionIndexes)-1:
                # last section - need to use blockItem.contents
                # to determine the length
                sectionTotal = (len(self.blockItem.contents) -
                                self.sectionIndexes[-1])
            else:
                # not collapsed, so determine the length of this
                # section from the next section in self.sectionIndexes
                sectionTotal = (self.sectionIndexes[section+1] -
                                self.sectionIndexes[section])

            sectionValue = self.findSectionValue(section)
            sectionVisible = ((not self.currentColumn.isSectionCollapsed(sectionValue))
                              and sectionTotal or 0)

            # might as well recall this for the next iteration through
            # the loop. the +1 is for the section header itself.
            nextSectionRow = sectionRow + sectionVisible + 1
            
            self.sectionRows.append((sectionRow, sectionVisible, sectionTotal))
            self.totalRows += sectionVisible + 1

            # Get the color name we'll use for this section
            # For now, it's just the attribute value.
            self.sectionColors.append(sectionValue)
            
            # Get the label we'll use for this section
            # By default, it's the value (which we just grabbed as the color 
            # name), unless this is an Enumeration whose `values` is a 
            # dictionary that maps to a string label
            label = getTriageStatusName(sectionValue)
            self.sectionLabels.append(label)
            
        # make sure we're sane
        assert len(self.sectionRows) == len(self.sectionIndexes)
        assert sum([visible+1 for (row, visible, total) in self.sectionRows]) \
               == self.totalRows
                   
    def findCurrentColumn(self):
        # Find the column we're currently sorting by
        currentIndexName = self.blockItem.contents.indexName
        for c in self.blockItem.columns:
            if c.indexName == currentIndexName:
                return c
        return None

    def findSectionValue(self, section):
        # Get the value associated with this section index.
        return getattr(self.blockItem.contents[self.sectionIndexes[section]], 
                       self.attributeName, None)

    def GetElementCount(self):

        # ack. temporary fix for Functional test suite - bug 5150. in
        # general if an item is dragged to the trash, the sections
        # probably need to be recalculated (or at least readjusted!) -
        # but the sections code doesn't get any notification (yet)
        # that this has happened.

        # temporary fix: when there are no sections (which is the
        # condition under which the functional tests are running) then
        # use the original collection for row length
        if len(self.sectionRows) == 0:
            return len(self.blockItem.contents)
        else:
            return self.totalRows

    def GetElementType(self, row, column):
        itemIndex = self.RowToIndex(row)
        if itemIndex == -1:
            return "Section"

        return super(SectionedGridDelegate, self).GetElementType(row, column)
    
    def GetElementValue(self, row, column):
        itemIndex = self.RowToIndex(row)
        if itemIndex == -1:
            # This is a section row. Return a tuple containing:
            # - the attribute we're sectioned on,
            # - the label for this section
            # - the number of items in this section
            # - the color name for this section (which may be None)
            # - whether this section is expanded (True) or not (False)
            # - whether this is the last (triage status) column
            #
            # Note that this tuple matches the one passed into 
            # SectionAttributeEditor.Draw, below.
            for (section, (sectionRow, visible, itemCount)) in enumerate(self.sectionRows):
                if row == sectionRow:
                    return (self.attributeName,
                            self.sectionLabels[section],
                            itemCount,
                            self.sectionColors[section],
                            not self.currentColumn.isSectionCollapsed(self.findSectionValue(section)),
                            column == len(self.blockItem.columns) - 1)
            
            assert False
            return (None, u'', 0, None, False, False)
        
        return super(SectionedGridDelegate, self).GetElementValue(row, column)

    def RowToIndex(self, row):
        """
        Map Row->Index taking into account collapsed sections.

        Right now this is a linear search of sections - if we need to
        worry about performance then we probably need to switch to a
        binary search. Generally, there aren't many sections so we
        won't optimize this.
        """

        if len(self.sectionRows) == 0:
            return row

        sectionAdjust = len(self.sectionRows) - 1
        # search backwards so we can jump right to the section number
        for (reversedSection, (sectionRow, visible, total)) in enumerate(reversed(self.sectionRows)):
            section = sectionAdjust - reversedSection
            
            if row == sectionRow:
                # this row is a section header, there is no valid data
                # row here
                return -1
            
            if row > sectionRow:
                # We are in an expanded section. We need to find the
                # relative position of this row within the section,
                # and then go look up that relative position in
                # self.sectionIndexes (+1 accounts for the header row)
                
                rowOffset = row - (sectionRow + 1)
                itemIndex = self.sectionIndexes[section] + rowOffset
                
                assert itemIndex < len(self.blockItem.contents)
                return itemIndex

        #assert False, "Couldn't find index for row %s in %s" % (row, [x[0] for x in reversed(self.sectionRows)])
        return -1

    def IndexToRow(self, itemIndex):
        """
        Find the row for the corresponding item. This is done with a
        linear search through the sections. Generally there aren't a
        lot of sections though so this should be reasonably fast.
        """
        if len(self.sectionIndexes) == 0:
            return itemIndex

        sectionAdjust = len(self.sectionIndexes) - 1
        for reversedSection, sectionIndex in enumerate(reversed(self.sectionIndexes)):
            section = sectionAdjust - reversedSection
            sectionValue = self.findSectionValue(section)
            
            if itemIndex >= sectionIndex:
                if self.currentColumn.isSectionCollapsed(sectionValue):
                    # section is collapsed! That's not good. Perhaps
                    # we should assert? Or maybe this is a valid case?
                    return -1
                else:
                    # Expanded section. Find the relative position
                    # +1 accounts for header row
                    indexOffset = itemIndex - sectionIndex
                    sectionRow = self.sectionRows[section][0]
                    row = (sectionRow + 1) + indexOffset
                    assert row < self.totalRows
                    
                    return row

                #assert False, "Couldn't find row for index %s" % itemIndex
        return -1

    def RangeToIndex(self, startRow, endRow):
        """
        Translate these rows to collection indexes; make sure the ends point at 
        actual rows (or return (-1,-1) if there aren't any actual rows in this range)
        """
        startIndex = self.RowToIndex(startRow)
        while startIndex == -1:
            startRow += 1
            if startRow >= self.totalRows:
                return -1, -1
            startIndex = self.RowToIndex(startRow)
        
        endIndex = self.RowToIndex(endRow)
        while endIndex == -1:
            endRow -= 1
            if endRow < startRow:
                return -1, -1
            endIndex = self.RowToIndex(endRow)
            
        return startIndex, endIndex

    def ToggleRow(self, row):
        for (section, (sectionRow, visible, total)) in enumerate(self.sectionRows):
            if row == sectionRow:
                sectionValue = self.findSectionValue(section)
                if self.currentColumn.isSectionCollapsed(sectionValue):
                    self.ExpandSection(section)
                else:
                    self.CollapseSection(section)
                self.blockItem.synchronizeWidget()
                return

    def CollapseSection(self, section):
        """
        Collapse a given section - i.e. make it zero-length
        """
        sectionValue = self.findSectionValue(section) 
        assert not self.currentColumn.isSectionCollapsed(sectionValue)

        # subtract the oldVisibleCount
        (oldPosition, oldVisibleCount, oldTotalCount) = self.sectionRows[section]

        self.AdjustSectionPosition(section, -oldVisibleCount)
        self.totalRows -= oldVisibleCount
        self.currentColumn.setSectionState(sectionValue, True)
            
    def ExpandSection(self, section):
        """
        Expand the given section to be the same as the original data
        """
        sectionValue = self.findSectionValue(section) 
        assert self.currentColumn.isSectionCollapsed(sectionValue)

        # we look back in the original data to find the section length
        if section == len(self.sectionIndexes) - 1:
            # last section, need to look this up
            newLength = (len(self.blockItem.contents) - 
                         self.sectionIndexes[section])
        else:
            newLength = (self.sectionIndexes[section+1] -
                         self.sectionIndexes[section])

        self.AdjustSectionPosition(section, newLength)
        self.totalRows += newLength
        self.currentColumn.setSectionState(sectionValue, False)

    def AdjustSectionPosition(self, startSection, delta):
        """
        Adjust a section's position by delta - may be positive or
        negative. Since section positions are somewhat interdependent,
        we have to adjust the given section as well as all sections
        following it.
        """
        for section, (sectionPosition, sectionVisibleCount, sectionTotalCount) \
            in enumerate(self.sectionRows):
            if section >= startSection:
                self.sectionRows[section] = (sectionPosition + delta,
                                             sectionVisibleCount,
                                             sectionTotalCount)
        
class SectionAttributeEditor(BaseAttributeEditor):    
    def __init__(self, *args, **kwds):
        super(SectionAttributeEditor, self).__init__(*args, **kwds)
        self.brushes = DrawingUtilities.Gradients()
    
    def ReadOnly(self, *args):
        """ 
        Sections are never editable. 
        (Contract/expand toggling is handled separately.)
        """
        return True

    def _getTriangle(self, expanded=False):
        """ Cache the triangle symbols and their measurements """
        triSuffix = expanded and 'Open' or 'Closed'
        cacheAttribute = '_tri%s' % triSuffix
        triBitmapInfo = getattr(self, cacheAttribute, None)
        if triBitmapInfo is not None:
            return triBitmapInfo

        triBitmap = wx.GetApp().GetImage("SectionCaret%s.png" % triSuffix)
        triWidth = triBitmap.GetWidth()
        triHeight = triBitmap.GetHeight()
        triBitmapInfo = (triBitmap, triWidth, triHeight)
        setattr(self, cacheAttribute, triBitmapInfo)
        return triBitmapInfo
                     
    def Draw(self, grid, dc, rect, 
             (attributeName, label, count, colorName, expanded, last), 
             isInSelection=False):
        dc.SetPen(wx.TRANSPARENT_PEN)

        sectionBackgroundColor = styles.cfg.get('summary', 'SectionBackground')
        sectionLabelColor = styles.cfg.get('summary', 'SectionLabel')
        sectionCountColor = styles.cfg.get('summary', 'SectionCount')
        sectionSampleColor = colorName and styles.cfg.get('summary', 
                                'SectionSample_%s_%s' % (attributeName, colorName)) or None

        # We want a little space below the section bar, so it looks nice when 
        # they're contracted together... so erase a one-pixel-high rectangle at
        # the bottom of our rect, then make ours a little smaller, 
        dc.SetBrush(wx.WHITE_BRUSH)
        rect.height -= 1
        dc.DrawRectangleRect((rect.x, rect.y + rect.height, rect.width, 1))
        
        # Draw the background
        brush = wx.Brush(sectionBackgroundColor, wx.SOLID)
        dc.SetBrush(brush)
        dc.DrawRectangleRect(rect)
        dc.SetTextBackground(sectionBackgroundColor)

        # We'll center the 12-point text on the row, not counting descenders.
        labelFont = Styles.getFont(grid.blockItem.sectionLabelCharacterStyle)
        dc.SetFont(labelFont)
        (labelWidth, labelHeight, labelDescent, ignored) = dc.GetFullTextExtent(label)
        labelTop = rect.y + ((rect.height - labelHeight) / 2)
                
        # Draw the expando triangle
        (triBitmap, triWidth, triHeight) = self._getTriangle(expanded)
        triTop = rect.y + ((rect.height - triHeight) / 2)
        dc.DrawBitmap(triBitmap, margin, triTop, True)
            
        # Draw the text label, if it overlaps the rect to be updated
        labelPosition = margin + triWidth
        dc.SetTextForeground(wx.BLACK)
        dc.DrawText(label, labelPosition, labelTop)
        
        # Draw the item count, if it overlaps the rect to be updated
        countPosition = labelPosition + labelWidth
        if count == 1:
            itemCount = _(u" 1 item   ") % {'count': count }
        else:
            itemCount = _(u" %(count)d items   ") % {'count': count }
        countFont = Styles.getFont(grid.blockItem.sectionCountCharacterStyle)
        dc.SetFont(countFont)
        labelMeasurements = Styles.getMeasurements(labelFont)
        countMeasurements = Styles.getMeasurements(countFont)
        countTop = labelTop + ((labelHeight - labelMeasurements.descent) -
                               (countMeasurements.height - countMeasurements.descent))
        dc.SetTextForeground(sectionCountColor)
        dc.DrawText(itemCount, countPosition, countTop)
                
        # If we're sectioned on triage status, draw the swatch
        if colorName and last:
            dc.SetPen(wx.WHITE_PEN)
            brush = wx.Brush(sectionSampleColor, wx.SOLID)
            dc.SetBrush(brush)
            swatchX = rect.x + ((rect.width - swatchWidth) / 2)
            swatchY = rect.y + ((rect.height - swatchHeight) / 2)
            dc.DrawRectangleRect((swatchX, swatchY, swatchWidth, swatchHeight))

    def OnMouseChange(self, event):
        # Handle clicks on our triangle
        if event.GetEventType() == wx.wxEVT_LEFT_DOWN:
            (triBitmap, triWidth, triHeight) = self._getTriangle()
            if (event.m_x - margin) < triWidth:
                grid = event.GetEventObject().GetParent()
                grid.ToggleRow(event.cell[1])
                event.Skip(False) # Eat the event
        return False # don't capture the mouse for us
