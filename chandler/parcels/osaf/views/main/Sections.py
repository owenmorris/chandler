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


import wx

from application import schema

from osaf.framework.blocks import ControlBlocks
from util.divisions import get_divisions

from osaf.framework.blocks import DrawingUtilities

from i18n import OSAFMessageFactory as _

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

        # a set indicating which sections are collapsed
        self.collapsedSections = set()

        # total rows in the table
        self.totalRows = 0

        self.RegisterDataType("Section", SectionRenderer(),
                              SectionEditor())

        self.previousIndex = self.blockItem.contents.indexName
        
    def SynchronizeDelegate(self):
        """
        its reasonably cheap to rebuild section indexes, as
        get_divisions is really optimized for this
        """
        if self.previousIndex != self.blockItem.contents.indexName:
            self.collapsedSections = set()
            self.previousIndex = self.blockItem.contents.indexName
            
        self.RebuildSections()

    def RebuildSections(self):
        """
        rebuild the sections - this is relatively cheap as long as
        there aren't a lot of sections
        """
        self.sectionRows = []
        self.sectionLabels = []
        self.sectionIndexes = []
        self.totalRows = 0
        
        dashboardPrefs = schema.ns('osaf.views.main',
                                   self.blockItem.itsView).dashboardPrefs
        if not dashboardPrefs.showSections:
            return
        
        # regenerate index-based sections - each entry in
        # self.sectionIndexes is the first index in the collection
        # where we would need a section
        indexName = self.blockItem.contents.indexName
        if indexName not in (None, '__adhoc__'):
            self.sectionIndexes = \
                get_divisions(self.blockItem.contents,
                              key=lambda x: getattr(x, indexName))

        # dont' show section headers for zero or one section
        if len(self.sectionIndexes) <= 1:
            return
            
        # now build the row-based sections - each entry in this array
        # is the actual row that contains the section divider
        nextSectionRow = 0
        for section in range(0, len(self.sectionIndexes)):
            sectionRow = nextSectionRow
            if section in self.collapsedSections:
                sectionLength = 0
                # previous section collapsed, so we're just one past
                # the last one
            else:
                if section == len(self.sectionIndexes)-1:
                    # last section - need to use blockItem.contents
                    # to determine the length
                    sectionLength = (len(self.blockItem.contents) -
                                     self.sectionIndexes[-1])
                else:
                    # not collapsed, so determine the length of this
                    # section from the next section in self.sectionIndexes
                    sectionLength = (self.sectionIndexes[section+1] -
                                     self.sectionIndexes[section])

            # might as well recall this for the next iteration through
            # the loop. the +1 is for the section header itself.
            nextSectionRow = sectionRow + sectionLength + 1
            
            self.sectionRows.append((sectionRow, sectionLength))
            self.totalRows += sectionLength + 1
            label = _(u"Section: %s") % \
                    getattr(self.blockItem.contents[self.sectionIndexes[section]], indexName, _(u"<unknown>"))
            self.sectionLabels.append(label)

        # make sure we're sane
        assert len(self.sectionRows) == len(self.sectionIndexes)
        assert sum([length+1 for (row, length) in self.sectionRows]) == \
               self.totalRows
                   

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

    def ReadOnly(self, row, column):
        itemIndex = self.RowToIndex(row)
        if itemIndex == -1:
            return False, True

        return super(SectionedGridDelegate, self).ReadOnly(row, column)
    
    def GetElementValue(self, row, column):
        
        itemIndex = self.RowToIndex(row)
        if itemIndex == -1:
            # this is just a hack because this value is getting passed
            # to the default attribute editor
            return object(), None

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
        for (reversedSection, (sectionRow, sectionSize)) in enumerate(reversed(self.sectionRows)):
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
            
            if itemIndex >= sectionIndex:
                if section in self.collapsedSections:
                    # section is collapsed! That's not good. Perhaps
                    # we should assert? Or maybe this is a valid case?
                    return -1
                else:
                    # Expanded sxection. Find the relative position
                    # +1 accounts for header row
                    indexOffset = itemIndex - sectionIndex
                    sectionRow = self.sectionRows[section][0]
                    row = (sectionRow + 1) + indexOffset
                    assert row < self.totalRows
                    
                    return row

                #assert False, "Couldn't find row for index %s" % itemIndex
        return -1

    def ToggleRow(self, row):
        for (section, (sectionRow, length)) in enumerate(self.sectionRows):
            if row == sectionRow:
                if section in self.collapsedSections:
                    self.ExpandSection(section)
                else:
                    self.CollapseSection(section)
                self.blockItem.synchronizeWidget()
                return

    def CollapseSection(self, section):
        """
        Collapse a given section - i.e. make it zero-length
        """
        assert section not in self.collapsedSections

        # subtract the oldLength
        (oldPosition, oldLength) = self.sectionRows[section]

        self.AdjustSectionPosition(section, -oldLength)
        self.totalRows -= oldLength
        self.collapsedSections.add(section)
            
    def ExpandSection(self, section):
        """
        Expand the given section to be the same as the original data
        """
        assert section in self.collapsedSections

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
        self.collapsedSections.remove(section)

    def AdjustSectionPosition(self, startSection, delta):
        """
        Adjust a section's position by delta - may be positive or
        negative. Since section positions are somewhat interdependent,
        we have to adjust the given section as well as all sections
        following it.
        """
        for section, (sectionPosition, sectionLength) \
            in enumerate(self.sectionRows):
            if section >= startSection:
                self.sectionRows[section] = (sectionPosition + delta,
                                             sectionLength)
        

class SectionRenderer(wx.grid.PyGridCellRenderer):
    def __init__(self, *args, **kwds):
        super(SectionRenderer, self).__init__(*args, **kwds)
        self.brushes = DrawingUtilities.Gradients()
        
    def ReadOnly(self, *args):
        # print "Who is calling RO?"
        return False, False

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        dc.SetPen(wx.TRANSPARENT_PEN)
        brush = self.brushes.GetGradientBrush(0, rect.height,
                                              (153, 204, 255), (203, 229, 255),
                                              "Vertical")
        dc.SetBrush(brush)
        dc.DrawRectangleRect(rect)

        if col == 0:
            dc.SetFont(attr.GetFont())
            dc.SetTextForeground(wx.BLACK)
            dc.SetBackgroundMode(wx.TRANSPARENT)
            # look up row in section list
            for section, (sectionRow, length) in enumerate(grid.sectionRows):
                if row == sectionRow:
                    sectionTitle = grid.sectionLabels[section]
                    break
            dc.DrawText(sectionTitle, 3, rect.y + 2)


class SectionEditor(wx.grid.PyGridCellEditor):
    def __init__(self, *args, **kwds):
        super(SectionEditor, self).__init__(*args, **kwds)

    def StartingClick(self):
        #print "StartingClick()"
        (grid, row) = self.collapseInfo
        grid.ToggleRow(row)

    def StartingKey(self, event):
        #print "StartingKey()"
        pass

    def Create(self, parent, id, evtHandler):
        """
        Create a dummy control to make wx happy - the key here is SetControl()
        """
        self.control = wx.Control(parent, id)
        self.SetControl(self.control)
        if evtHandler:
            self.control.PushEventHandler(evtHandler)
        #print "Create(%s, %s, %s)" % (parent, id, evtHandler)

    def BeginEdit(self, row, col, grid):
        """
        Don't 
        """
        self.control.Hide()
        self.collapseInfo = (grid, row)
        #print "BeginEdit(%s, %s)" % (row,col)

    def EndEdit(self, row, col, grid):
        del self.collapseInfo
        #print "EndEdit(%s, %s)" % (row,col)
        return False
        
