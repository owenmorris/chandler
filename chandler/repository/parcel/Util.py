"""
Utility functions for displaying repository contents
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository

def PrintItem(uri, rep, level=0):
    """ 
    Given a uri, display its info along with all its children recursively

    Example:  PrintItem("//Schema", rep)

    """
    for i in range(level):
        print " ",
    item = rep.find(uri)
    print uri

    for (name, value) in item.iterAttributes():

        t = type(value)

        if name == "attributes":
            for i in range(level+2):
                print " ",

            print "%s:" % name
            for (attr,source) in GetAttributes(item):
                for k in range(level+4):
                    print " ",
                if source is item:
                    print attr.getItemPath()
                else:
                    print attr.getItemPath(), "(from %s)" % source.getItemPath()

        elif name == "notFoundAttributes" or name == "inheritedAttributes":
            pass

        elif t == list \
         or t == repository.item.PersistentCollections.PersistentList:
            for i in range(level+2):
                print " ",

            print "%s:" % name
            for j in value:
                for k in range(level+4):
                    print " ",
                print j

        elif t == repository.item.PersistentCollections.PersistentDict:
            for i in range(level+2):
                print " ",

            print "%s:" % name
            for key in value.keys():
                for k in range(level+4):
                    print " ",
                print "%s:" % key, value[key]

        elif t == repository.persistence.XMLRepositoryView.XMLRefDict \
         or t == repository.item.ItemRef.TransientRefDict:
            for i in range(level+2):
                print " ",

            print "%s:" % name
            for j in value:
                for k in range(level+4):
                    print " ",
                print j.getItemPath()

        else:
            for i in range(level+2):
                print " ",

            print "%s:" % name,
            try:
                print value.getItemPath()
            except:
                print value, type(value)

    print

    for child in item:
        childuri = child.getItemPath()
        PrintItem(childuri, rep, level+1)

def GetAttributes(kind):
    """ Build the list of attributes this kind has, including inherited
    """

    for attr in kind.attributes:
        yield (attr, kind)

    try:
        for superKind in kind.superKinds:
            for tuple in GetAttributes(superKind):
                yield tuple
    except:
        pass
