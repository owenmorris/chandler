
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Parcel

class Current(application.Parcel.Parcel):

    CURRENT = "//parcels/osaf/current"
    POINTER_KIND_PATH = "//parcels/osaf/contentmodel/CurrentPointer"

    def get(cls, view, pointerName):
        current = view.findPath(cls.CURRENT)
        ptr = current.findPath(pointerName)
        if ptr is None:
            return None
        return ptr.item

    get = classmethod(get)

    def set(cls, view, pointerName, item):
        current = view.findPath(cls.CURRENT)
        ptr = current.findPath(pointerName)
        if ptr is None:
            kind = view.findPath(cls.POINTER_KIND_PATH)
            ptr = kind.newItem(pointerName, current)
        ptr.item = item

    set = classmethod(set)

    def isCurrent(cls, view, pointerName, item):
        current = view.findPath(cls.CURRENT)
        ptr = current.findPath(pointerName)
        if ptr is not None and ptr.item is item:
            return True
        else:
            return False

    isCurrent = classmethod(isCurrent)
