
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from model.item.Item import Item


class Namespace(Item):

    def getDomain(self):

        return self.getItemParent().getDomain()

    def resolve(self, name):

        child = self.getItemChild(name)
        if child:
            return child.getUUID()

        return None


class Domain(Namespace):

    def getDomain(self):
        return self

    def getNamespace(self, name):
        return self.getItemChild(name)

