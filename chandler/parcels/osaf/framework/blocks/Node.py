import application.Globals as Globals
from repository.item.Item import Item

class BadURL(Exception):
    pass

class Node(Item):
    """
      Used to store URL space
    """
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
    
    def GetDescendant(self, descendantParts):
        if len(descendantParts) == 0:
            return self
        childName = descendantParts.pop(0)
        for child in self.children:
            if childName == child.getItemDisplayName():
                return child.GetDescendant(descendantParts)
        raise BadURL
                
    def GetItemFromPath(theClass, path, rootURL='//parcels/OSAF/views/locations/URLRoot'):
        rootNode = Globals.repository.find(rootURL)
        while path.startswith('/'):
            path = path[1:]
        return rootNode.GetDescendant(path.split('/'))
        
    GetItemFromPath = classmethod(GetItemFromPath)