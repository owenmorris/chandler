__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from model.item.Item import Item

"""
The Repertoire Class holds conditions and actions that aren't associated with particular instructions,
to allow the user to add new instructions
"""
class RepertoireFactory:
    def __init__(self, repository):
        self._container = repository.find("//Agents")
        self._kind = repository.find("//Schema/AgentsSchema/Repetoire")
        self.repository = repositoryr
        
    def NewItem(self):
        item = Repertoire(None, self._container, self._kind)
                              
        return item

class Repertoire(Item):

    def __init__(self, name, parent, kind, **_kwds):
        super(Repertoire, self).__init__(name, parent, kind, **_kwds)
             