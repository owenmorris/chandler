
from repository.item.Item import Item

class Node(Item):

    def __init__(self, *arguments, **keywords):
        super (Node, self).__init__ (*arguments, **keywords)
        self.children = []
        self.parent = None
        self.item = None

    def GetPath(self):
        node = self
        path = ''
        while node:
            path = '/' + node.getItemDisplayName() + path
            node = node.parent
        return path
 

