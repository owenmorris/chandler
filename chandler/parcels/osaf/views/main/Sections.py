from osaf.framework.blocks import ControlBlocks
from util.divisions import get_divisions

from i18n import OSAFMessageFactory as _

class SectionedGridDelegate(ControlBlocks.AttributeDelegate):

    indexName = None
    sectionIndexes = []
    sectionRows = []
    def SynchronizeDelegate(self):
        """
        its reasonably cheap to rebuild section indexes, as
        get_divisions is really optimized for this
        """
        indexName = self.blockItem.contents.indexName
        
        
        # regenerate index-based sections - each entry in
        # self.sectionIndexes is the first index in the collection
        # where we would need a section
        if indexName in (None, '__adhoc__'):
            self.sectionIndexes = []
        else:
            self.sectionIndexes = \
                get_divisions(self.blockItem.contents,
                              key=lambda x: getattr(x, indexName))

        # now build the row-based sections - each entry in this array
        # is the actual row that contains the section divider
        self.sectionRows = []
        for r in xrange(len(self.sectionIndexes)):
            self.sectionRows.append(self.sectionIndexes[r] + r)
            
    def GetElementCount(self):
        return len(self.blockItem.contents) + len(self.sectionRows)

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
            return _(u"[Section: %s]") % \
                   getattr(firstItemInSection, indexAttribute)
        
        attributeName = self.blockItem.columnData[column]
        return (self.blockItem.contents [itemIndex], attributeName)

    def RowToIndex(self, row):
        for sectionNum, sectionRow in enumerate(self.sectionRows):
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
