# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

"""
Classes for a column header control with a native appearance.
"""

import _colheader

import _misc
import _core
wx = _core 
__docfilter__ = wx.__DocFilter(globals()) 
wxCOLUMNHEADER_JustLeft = _colheader.wxCOLUMNHEADER_JustLeft
wxCOLUMNHEADER_JustCenter = _colheader.wxCOLUMNHEADER_JustCenter
wxCOLUMNHEADER_JustRight = _colheader.wxCOLUMNHEADER_JustRight
wxCOLUMNHEADER_HITTEST_NOWHERE = _colheader.wxCOLUMNHEADER_HITTEST_NOWHERE
wxCOLUMNHEADER_HITTEST_ITEM_ZERO = _colheader.wxCOLUMNHEADER_HITTEST_ITEM_ZERO
class wxColumnHeaderEvent(_core.CommandEvent):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxColumnHeaderEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args, **kwargs):
        """__init__(self, wxColumnHeader col, wxEventType type) -> wxColumnHeaderEvent"""
        newobj = _colheader.new_wxColumnHeaderEvent(*args, **kwargs)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown

class wxColumnHeaderEventPtr(wxColumnHeaderEvent):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = wxColumnHeaderEvent
_colheader.wxColumnHeaderEvent_swigregister(wxColumnHeaderEventPtr)

wxEVT_COLUMNHEADER_DOUBLECLICKED = _colheader.wxEVT_COLUMNHEADER_DOUBLECLICKED
wxEVT_COLUMNHEADER_SELCHANGED = _colheader.wxEVT_COLUMNHEADER_SELCHANGED
EVT_COLUMNHEADER_DOUBLECLICKED =  wx.PyEventBinder( wxEVT_COLUMNHEADER_DOUBLECLICKED, 1)
EVT_COLUMNHEADER_SELCHANGED =     wx.PyEventBinder( wxEVT_COLUMNHEADER_SELCHANGED, 1)

class wxColumnHeader(_core.Control):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxColumnHeader instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        """
        __init__(self, Window parent, int id=-1, Point pos=DefaultPosition, 
            Size size=DefaultSize, long style=0, String name=wxColumnHeaderNameStr) -> wxColumnHeader
        __init__(self) -> wxColumnHeader
        """
        newobj = _colheader.new_wxColumnHeader(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def SetUnicodeFlag(*args, **kwargs):
        """SetUnicodeFlag(self, bool bSetFlag)"""
        return _colheader.wxColumnHeader_SetUnicodeFlag(*args, **kwargs)

    def GetSelectedItemIndex(*args, **kwargs):
        """GetSelectedItemIndex(self) -> long"""
        return _colheader.wxColumnHeader_GetSelectedItemIndex(*args, **kwargs)

    def SetSelectedItemIndex(*args, **kwargs):
        """SetSelectedItemIndex(self, long itemIndex)"""
        return _colheader.wxColumnHeader_SetSelectedItemIndex(*args, **kwargs)

    def HitTest(*args, **kwargs):
        """HitTest(self, Point locationPt) -> int"""
        return _colheader.wxColumnHeader_HitTest(*args, **kwargs)

    def GetItemCount(*args, **kwargs):
        """GetItemCount(self) -> long"""
        return _colheader.wxColumnHeader_GetItemCount(*args, **kwargs)

    def AppendItem(*args, **kwargs):
        """
        AppendItem(self, String textBuffer, long textJust, long extentX, bool bActive, 
            bool bSortAscending)
        """
        return _colheader.wxColumnHeader_AppendItem(*args, **kwargs)

    def DeleteItem(*args, **kwargs):
        """DeleteItem(self, long itemIndex)"""
        return _colheader.wxColumnHeader_DeleteItem(*args, **kwargs)

    def GetLabelText(*args, **kwargs):
        """GetLabelText(self, long itemIndex, String textBuffer, long textJust) -> bool"""
        return _colheader.wxColumnHeader_GetLabelText(*args, **kwargs)

    def SetLabelText(*args, **kwargs):
        """SetLabelText(self, long itemIndex, String textBuffer, long textJust) -> bool"""
        return _colheader.wxColumnHeader_SetLabelText(*args, **kwargs)

    def GetUIExtent(*args, **kwargs):
        """GetUIExtent(self, long itemIndex, long originX, long extentX) -> bool"""
        return _colheader.wxColumnHeader_GetUIExtent(*args, **kwargs)

    def SetUIExtent(*args, **kwargs):
        """SetUIExtent(self, long itemIndex, long originX, long extentX) -> bool"""
        return _colheader.wxColumnHeader_SetUIExtent(*args, **kwargs)

    def GetFlags(*args, **kwargs):
        """GetFlags(self, long itemIndex, bool bActive, bool bEnabled, bool bSortAscending) -> bool"""
        return _colheader.wxColumnHeader_GetFlags(*args, **kwargs)

    def SetFlags(*args, **kwargs):
        """SetFlags(self, long itemIndex, bool bActive, bool bEnabled, bool bSortAscending) -> bool"""
        return _colheader.wxColumnHeader_SetFlags(*args, **kwargs)


class wxColumnHeaderPtr(wxColumnHeader):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = wxColumnHeader
_colheader.wxColumnHeader_swigregister(wxColumnHeaderPtr)


