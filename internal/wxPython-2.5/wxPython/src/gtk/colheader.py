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
wxCOLUMNHEADER_JUST_Left = _colheader.wxCOLUMNHEADER_JUST_Left
wxCOLUMNHEADER_JUST_Center = _colheader.wxCOLUMNHEADER_JUST_Center
wxCOLUMNHEADER_JUST_Right = _colheader.wxCOLUMNHEADER_JUST_Right
wxCOLUMNHEADER_FLAGATTR_Enabled = _colheader.wxCOLUMNHEADER_FLAGATTR_Enabled
wxCOLUMNHEADER_FLAGATTR_Selected = _colheader.wxCOLUMNHEADER_FLAGATTR_Selected
wxCOLUMNHEADER_FLAGATTR_SortDirection = _colheader.wxCOLUMNHEADER_FLAGATTR_SortDirection
wxCOLUMNHEADER_HITTEST_NoPart = _colheader.wxCOLUMNHEADER_HITTEST_NoPart
wxCOLUMNHEADER_HITTEST_ItemZero = _colheader.wxCOLUMNHEADER_HITTEST_ItemZero
class wxColumnHeaderEvent(_core.wxCommandEvent):
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
EVT_COLUMNHEADER_DOUBLECLICKED =  wx.PyEventBinder(wxEVT_COLUMNHEADER_DOUBLECLICKED, 1)
EVT_COLUMNHEADER_SELCHANGED =     wx.PyEventBinder(wxEVT_COLUMNHEADER_SELCHANGED, 1)

class wxColumnHeader(_core.wxControl):
    def __repr__(self):
        return "<%s.%s; proxy of C++ wxColumnHeader instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        """
        __init__(self, wxWindow parent, int id=-1, wxPoint pos=wxDefaultPosition, 
            wxSize size=wxDefaultSize, long style=0, 
            wxString name=wxColumnHeaderNameStr) -> wxColumnHeader
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
        """HitTest(self, wxPoint locationPt) -> int"""
        return _colheader.wxColumnHeader_HitTest(*args, **kwargs)

    def GetItemCount(*args, **kwargs):
        """GetItemCount(self) -> long"""
        return _colheader.wxColumnHeader_GetItemCount(*args, **kwargs)

    def AppendItem(*args, **kwargs):
        """
        AppendItem(self, wxString textBuffer, long textJust, long extentX, bool bActive, 
            bool bSortAscending)
        """
        return _colheader.wxColumnHeader_AppendItem(*args, **kwargs)

    def DeleteItem(*args, **kwargs):
        """DeleteItem(self, long itemIndex)"""
        return _colheader.wxColumnHeader_DeleteItem(*args, **kwargs)

    def GetLabelText(*args, **kwargs):
        """GetLabelText(self, long itemIndex) -> wxString"""
        return _colheader.wxColumnHeader_GetLabelText(*args, **kwargs)

    def SetLabelText(*args, **kwargs):
        """SetLabelText(self, long itemIndex, wxString textBuffer, long textJust)"""
        return _colheader.wxColumnHeader_SetLabelText(*args, **kwargs)

    def GetUIExtent(*args, **kwargs):
        """GetUIExtent(self, long itemIndex) -> wxPoint"""
        return _colheader.wxColumnHeader_GetUIExtent(*args, **kwargs)

    def SetUIExtent(*args, **kwargs):
        """SetUIExtent(self, long itemIndex, wxPoint extentPt)"""
        return _colheader.wxColumnHeader_SetUIExtent(*args, **kwargs)

    def GetFlagAttribute(*args, **kwargs):
        """GetFlagAttribute(self, long itemIndex, int flagEnum) -> bool"""
        return _colheader.wxColumnHeader_GetFlagAttribute(*args, **kwargs)

    def SetFlagAttribute(*args, **kwargs):
        """SetFlagAttribute(self, long itemIndex, int flagEnum, bool bFlagValue) -> bool"""
        return _colheader.wxColumnHeader_SetFlagAttribute(*args, **kwargs)


class wxColumnHeaderPtr(wxColumnHeader):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = wxColumnHeader
_colheader.wxColumnHeader_swigregister(wxColumnHeaderPtr)


