
from Block import Block

class ContainerChild(Block):

    def __init__(self, *arguments, **keywords):
        super (ContainerChild, self).__init__ ( *arguments, **keywords)
 
class BoxContainer(ContainerChild):

    def __init__(self, *arguments, **keywords):
        super (BoxContainer, self).__init__ (*arguments, **keywords)
 
