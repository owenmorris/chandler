
from repository.item.Item import Item

class Block(Item):

    def __init__(self, *arguments, **keywords):
        super (Block, self).__init__ ( *arguments, **keywords)
 
    #def RenderwxWindows(self):
        #childrenIterator = self.iterChildren()
        #for childItem in childrenIterator:
            #childItem.Render(parent, sizer)
