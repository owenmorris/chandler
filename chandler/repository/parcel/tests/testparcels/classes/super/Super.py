from repository.item.Item import Item

class Super(Item):
    def __init__(self, name, parent, kind):
        Item.__init__(self, name, parent, kind)
        self.initCalled = True
