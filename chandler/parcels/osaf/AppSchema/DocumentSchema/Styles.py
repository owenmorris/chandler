
from repository.item.Item import Item

class Style(Item):

    def __init__(self, *arguments, **keywords):
        super (Style, self).__init__ ( *arguments, **keywords)


class CharacterStyle(Style):

    def __init__(self, *arguments, **keywords):
        super (CharacterStyle, self).__init__ ( *arguments, **keywords)
 
