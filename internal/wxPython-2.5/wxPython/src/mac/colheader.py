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
COLUMNHEADER_JUST_Left = _colheader.COLUMNHEADER_JUST_Left
COLUMNHEADER_JUST_Center = _colheader.COLUMNHEADER_JUST_Center
COLUMNHEADER_JUST_Right = _colheader.COLUMNHEADER_JUST_Right
COLUMNHEADER_FLAGATTR_Enabled = _colheader.COLUMNHEADER_FLAGATTR_Enabled
COLUMNHEADER_FLAGATTR_Selected = _colheader.COLUMNHEADER_FLAGATTR_Selected
COLUMNHEADER_FLAGATTR_SortDirection = _colheader.COLUMNHEADER_FLAGATTR_SortDirection
COLUMNHEADER_HITTEST_NoPart = _colheader.COLUMNHEADER_HITTEST_NoPart
COLUMNHEADER_HITTEST_ItemZero = _colheader.COLUMNHEADER_HITTEST_ItemZero
class ColumnHeaderEvent(_core.CommandEvent):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxColumnHeaderEvent instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args, **kwargs):
        """__init__(self, ColumnHeader col, wxEventType type) -> ColumnHeaderEvent"""
        newobj = _colheader.new_ColumnHeaderEvent(*args, **kwargs)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown

class ColumnHeaderEventPtr(ColumnHeaderEvent):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = ColumnHeaderEvent
_colheader.ColumnHeaderEvent_swigregister(ColumnHeaderEventPtr)

wxEVT_COLUMNHEADER_DOUBLECLICKED = _colheader.wxEVT_COLUMNHEADER_DOUBLECLICKED
wxEVT_COLUMNHEADER_SELCHANGED = _colheader.wxEVT_COLUMNHEADER_SELCHANGED
EVT_COLUMNHEADER_DOUBLECLICKED =  wx.PyEventBinder(wxEVT_COLUMNHEADER_DOUBLECLICKED, 1)
EVT_COLUMNHEADER_SELCHANGED =     wx.PyEventBinder(wxEVT_COLUMNHEADER_SELCHANGED, 1)

class ColumnHeader(_core.Control):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxColumnHeader instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        """
        __init__(self, Window parent, int id=-1, Point pos=DefaultPosition, 
            Size size=DefaultSize, long style=0, String name=wxColumnHeaderNameStr) -> ColumnHeader
        __init__(self) -> ColumnHeader
        """
        newobj = _colheader.new_ColumnHeader(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def SetUnicodeFlag(*args, **kwargs):
        """SetUnicodeFlag(self, bool bSetFlag)"""
        return _colheader.ColumnHeader_SetUnicodeFlag(*args, **kwargs)

    def GetSelectedItemIndex(*args, **kwargs):
        """GetSelectedItemIndex(self) -> long"""
        return _colheader.ColumnHeader_GetSelectedItemIndex(*args, **kwargs)

    def SetSelectedItemIndex(*args, **kwargs):
        """SetSelectedItemIndex(self, long itemIndex)"""
        return _colheader.ColumnHeader_SetSelectedItemIndex(*args, **kwargs)

    def HitTest(*args, **kwargs):
        """HitTest(self, Point locationPt) -> int"""
        return _colheader.ColumnHeader_HitTest(*args, **kwargs)

    def GetItemCount(*args, **kwargs):
        """GetItemCount(self) -> long"""
        return _colheader.ColumnHeader_GetItemCount(*args, **kwargs)

    def AppendItem(*args, **kwargs):
        """
        AppendItem(self, String textBuffer, long textJust, long extentX, bool bActive, 
            bool bSortAscending)
        """
        return _colheader.ColumnHeader_AppendItem(*args, **kwargs)

    def DeleteItem(*args, **kwargs):
        """DeleteItem(self, long itemIndex)"""
        return _colheader.ColumnHeader_DeleteItem(*args, **kwargs)

    def GetLabelText(*args, **kwargs):
        """GetLabelText(self, long itemIndex) -> String"""
        return _colheader.ColumnHeader_GetLabelText(*args, **kwargs)

    def SetLabelText(*args, **kwargs):
        """SetLabelText(self, long itemIndex, String textBuffer, long textJust)"""
        return _colheader.ColumnHeader_SetLabelText(*args, **kwargs)

    def GetUIExtent(*args, **kwargs):
        """GetUIExtent(self, long itemIndex) -> Point"""
        return _colheader.ColumnHeader_GetUIExtent(*args, **kwargs)

    def SetUIExtent(*args, **kwargs):
        """SetUIExtent(self, long itemIndex, Point extentPt)"""
        return _colheader.ColumnHeader_SetUIExtent(*args, **kwargs)

    def GetFlagAttribute(*args, **kwargs):
        """GetFlagAttribute(self, long itemIndex, int flagEnum) -> bool"""
        return _colheader.ColumnHeader_GetFlagAttribute(*args, **kwargs)

    def SetFlagAttribute(*args, **kwargs):
        """SetFlagAttribute(self, long itemIndex, int flagEnum, bool bFlagValue) -> bool"""
        return _colheader.ColumnHeader_SetFlagAttribute(*args, **kwargs)


class ColumnHeaderPtr(ColumnHeader):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = ColumnHeader
_colheader.ColumnHeader_swigregister(ColumnHeaderPtr)


