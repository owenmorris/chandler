import wx

from osaf.framework.blocks import ControlBlocks
from util.divisions import get_divisions

from osaf.framework.attributeEditors.AttributeEditors import BaseAttributeEditor, AttributeEditorMapping
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

        # a set indicating which sections are collapsed
        self.collapsedSections = set()

        # total rows in the table
        self.totalRows = 0
        
    def SynchronizeDelegate(self):
        """
        its reasonably cheap to rebuild section indexes, as
        get_divisions is really optimized for this
        """

        self.RebuildSections()

    def RebuildSections(self):
        indexName = self.blockItem.contents.indexName
        self.sectionRows = []
        self.totalRows = 0
        
        # regenerate index-based sections - each entry in
        # self.sectionIndexes is the first index in the collection
        # where we would need a section
        if indexName in (None, '__adhoc__'):
            self.sectionIndexes = []
        else:
            self.sectionIndexes = \
                get_divisions(self.blockItem.contents,
                              key=lambda x: getattr(x, indexName))

        # dont' show section headers for zero or one section
        if len(self.sectionIndexes) <= 1:
            self.totalRows = len(self.blockItem.contents)
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

        # make sure we're sane
        assert len(self.sectionRows) == len(self.sectionIndexes)
        assert sum([length+1 for (row, length) in self.sectionRows]) == \
               self.totalRows
                   

    def GetElementCount(self):
        return self.totalRows

    def GetElementType(self, row, column):
        itemIndex = self.RowToIndex(row)
        if itemIndex == -1:
            return "Section"

        return super(SectionedGridDelegate, self).GetElementType(row, column)

    def ReadOnly(self, row, column):
        itemIndex = self.RowToIndex(row)
        if itemIndex == -1:
            return True, True

        return super(SectionedGridDelegate, self).ReadOnly(row, column)
    
    def GetElementValue(self, row, column):
        
        itemIndex = self.RowToIndex(row)
        if itemIndex == -1:
            # section headers: we get the section title from the next row
            firstItemIndex = self.RowToIndex(row+1)
            firstItemInSection = self.blockItem.contents[firstItemIndex]
            
            indexAttribute = self.blockItem.contents.indexName
            return (firstItemInSection, indexAttribute, column)
        
        attributeName = self.blockItem.columnData[column]
        return (self.blockItem.contents [itemIndex], attributeName)

    def SectionRowCount(self, section):
        if section in self.collapsedSections:
            # collapsed sections are easy
            return 0
        elif section == len(self.sectionIndexes) - 1:
            # the last section needs special calculation - because its
            # the total items minux the position of the last index
            return len(self.blockItem.contents) - self.sectionIndexes[-1]
        else:
            # everybody else is easy
            return (self.sectionIndexes[section+1] -
                    self.sectionIndexes[section])

    def RowToIndex(self, row):
        for (sectionNum, (sectionRow, sectionSize)) in enumerate(self.sectionRows):
            if row == sectionRow:
                return -1
            if row < sectionRow:
                return row - sectionNum
            
        return row - len(self.sectionRows)

    def IndexToRow(self, itemIndex):
        for sectionNum, sectionIndex in enumerate(self.sectionIndexes):
            if itemIndex < sectionIndex:
                return itemIndex + sectionNum

        # the last section
        return itemIndex + len(self.sectionIndexes)


class SectionRenderer(BaseAttributeEditor):
    def __init__(self, *args, **kwds):
        super(SectionRenderer, self).__init__(*args, **kwds)
        self.brushes = DrawingUtilities.Gradients()
        
    def ReadOnly(self, *args):
        return True

    def Draw(self, dc, rect, (firstItem, attributeName, col), isInSelection=False):
        dc.SetPen(wx.TRANSPARENT_PEN)
        brush = self.brushes.GetGradientBrush(0, rect.height,
                                              (153, 204, 255), (203, 229, 255),
                                              "Vertical")
        dc.SetBrush(brush)
        dc.DrawRectangleRect(rect)

        if col == 0:
            dc.SetTextForeground(wx.BLACK)
            dc.SetBackgroundMode(wx.TRANSPARENT)
            sectionTitle = _(u"Section: %s") % getattr(firstItem, attributeName, "[None]")
            dc.DrawText(sectionTitle, 3, rect.y + 2)

def makeSections(parcel):
    """
    Attribute editor for "sections"

    the "Section" string maps
    directly to the "Section" string returned by GetElementType() in
    SectiondGridDelegate
    """
    AttributeEditorMapping.update(parcel, "Section",
                                  className=(SectionRenderer.__module__ + "." +
                                             SectionRenderer.__name__))

    
