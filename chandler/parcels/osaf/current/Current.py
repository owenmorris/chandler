
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from osaf.contentmodel.ContentModel import CurrentPointer

CURRENT = "//parcels/osaf/current"

def get(view, pointerName):
    current = view.findPath(CURRENT)
    ptr = current.findPath(pointerName)
    if ptr is None or not hasattr(ptr, 'item'):
        return None
    return ptr.item

def set(view, pointerName, item):
    current = view.findPath(CURRENT)
    ptr = current.findPath(pointerName)
    if ptr is None:
        ptr = CurrentPointer(pointerName, current)
    ptr.item = item

def isCurrent(view, pointerName, item):
    current = view.findPath(CURRENT)
    ptr = current.findPath(pointerName)
    if ptr is not None and hasattr(ptr, 'item') and ptr.item is item:
        return True
    else:
        return False

