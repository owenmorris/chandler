
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


class MetaKind(object):

    def __init__(self, kindClass, attrDefs):

        super(MetaKind, self).__init__()
            
        self.AttrDefs = {}
        self.Class = kindClass
        
        for attrDef in attrDefs.iteritems():
            self.AttrDefs[attrDef[0]] = MetaKind.attr(attrDef[1])

    def getAttrDef(self, name):
        return self.AttrDefs.get(name)

    def attach(self, attribute, item):
        pass

    def detach(self, attribute, item):
        pass


    class attr(object):

        def __init__(self, attrs):

            super(MetaKind.attr, self).__init__()
            for attr in attrs.iteritems():
                setattr(self, attr[0], attr[1])

        def getAspect(self, name, default=None):

            return getattr(self, name, default)

        def hasAspect(self, name):

            return hasattr(self, name)
