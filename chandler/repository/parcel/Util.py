"""
Utility functions for displaying repository contents
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import repository

def PrintItem(uri, rep, recursive=False, level=0):
    """
    Given a uri, display its info; include all descendents if recursive is
    True (default is False)

    Example:  PrintItem("//Schema", rep, recursive=True)
    """

    for i in range(level):
        print " ",
    item = rep.find(uri)
    if not item:
        print "Error: %s was not found" % uri
        return

    if item.hasAttributeValue("kind"):
        print "%s (Kind: %s)" % (uri, item.itsKind.itsPath )
    else:
        print "%s" % (uri)

    # For Kinds, display their attributes (except for the internal ones
    # like notFoundAttributes:
    if item.itsKind and "//Schema/Core/Kind" == str(item.itsKind.itsPath):
        for i in range(level+2):
            print " ",
        print "attributes for this kind:"

        displayedAttrs = { }
        for (name,attr) in item.iterAttributes():
            displayedAttrs[name] = attr

        keys = displayedAttrs.keys()
        keys.sort()
        for key in keys:
            for k in range(level+4):
                print " ",
            print "%s %s" % ( key, displayedAttrs[key].itsPath )

    displayedAttrs = { }
    for (name, value) in item.iterAttributeValues():
        displayedAttrs[name] = value

    keys = displayedAttrs.keys()
    keys.sort()
    for name in keys:
        value = displayedAttrs[name]
        t = type(value)

        if name == "attributes" or \
           name == "notFoundAttributes" or \
           name == "inheritedAttributes" or \
           name == "kind":
            pass

        elif t == list \
         or t == repository.item.PersistentCollections.PersistentList:
            for i in range(level+2):
                print " ",

            print "%s: (list)" % name
            for j in value:
                for k in range(level+4):
                    print " ",
                print j

        elif t == repository.item.PersistentCollections.PersistentDict:
            for i in range(level+2):
                print " ",

            print "%s: (dict)" % name
            for key in value.keys():
                for k in range(level+4):
                    print " ",
                print "%s:" % key, value[key]

        elif t == repository.persistence.XMLRepositoryView.XMLRefDict \
         or t == repository.item.ItemRef.TransientRefDict:
            for i in range(level+2):
                print " ",

            print "%s: (dict)" % name
            for j in value:
                for k in range(level+4):
                    print " ",
                print j.itsPath

        else:
            for i in range(level+2):
                print " ",

            print "%s:" % name,
            try:
                print value.itsPath
            except:
                print value, type(value)

    print

    if recursive and item.hasChildren():
        for child in item.iterChildren():
            childuri = str(child.itsPath)
            PrintItem(childuri, rep, recursive=True, level=level+1)
