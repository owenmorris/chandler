
from repository.item.Item import Item

class Query(Item):

    def __init__(self, *arguments, **keywords):
        super (Query, self).__init__ ( *arguments, **keywords)
 
