
from repository.item.Item import Item

class Block(Item):

    def __init__(self, *arguments, **keywords):
        super (Block, self).__init__ (*arguments, **keywords)
        self.childrenBlocks = []
        self.styles = []
 
    def Render(self, data):
        self.RenderOneBlock (data)
        for child in self.childrenBlocks:
            child.RenderOneBlock(data)

