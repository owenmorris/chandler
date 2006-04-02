# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyICU_bases

def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "this"):
        if isinstance(value, class_type):
            self.__dict__[name] = value.this
            if hasattr(value,"thisown"): self.__dict__["thisown"] = value.thisown
            del value.thisown
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static) or hasattr(self,name) or (name == "thisown"):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError,name

import types
try:
    _object = types.ObjectType
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0
del types


def _swig_setattr_nondynamic_method(set):
    def set_attr(self,name,value):
        if hasattr(self,name) or (name in ("this", "thisown")):
            set(self,name,value)
        else:
            raise AttributeError("You cannot add attributes to %s" % self)
    return set_attr


U_FOLD_CASE_DEFAULT = _PyICU_bases.U_FOLD_CASE_DEFAULT
U_FOLD_CASE_EXCLUDE_SPECIAL_I = _PyICU_bases.U_FOLD_CASE_EXCLUDE_SPECIAL_I
U_COMPARE_CODE_POINT_ORDER = _PyICU_bases.U_COMPARE_CODE_POINT_ORDER
class UMemory(object):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::UMemory instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)

class UMemoryPtr(UMemory):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = UMemory
_PyICU_bases.UMemory_swigregister(UMemoryPtr)

class UObject(UMemory):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::UObject instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)

class UObjectPtr(UObject):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = UObject
_PyICU_bases.UObject_swigregister(UObjectPtr)

import PyICU_iterators
import PyICU_locale
class Replaceable(UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::Replaceable instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def length(*args): return _PyICU_bases.Replaceable_length(*args)
    def charAt(*args): return _PyICU_bases.Replaceable_charAt(*args)
    def hasMetaData(*args): return _PyICU_bases.Replaceable_hasMetaData(*args)

class ReplaceablePtr(Replaceable):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Replaceable
_PyICU_bases.Replaceable_swigregister(ReplaceablePtr)

class UnicodeString(Replaceable):
    def __eq__(*args): return _PyICU_bases.UnicodeString___eq__(*args)
    def __ne__(*args): return _PyICU_bases.UnicodeString___ne__(*args)
    def __gt__(*args): return _PyICU_bases.UnicodeString___gt__(*args)
    def __lt__(*args): return _PyICU_bases.UnicodeString___lt__(*args)
    def __ge__(*args): return _PyICU_bases.UnicodeString___ge__(*args)
    def __le__(*args): return _PyICU_bases.UnicodeString___le__(*args)
    def __iadd__(*args): return _PyICU_bases.UnicodeString___iadd__(*args)
    def append(*args): return _PyICU_bases.UnicodeString_append(*args)
    def compare(*args): return _PyICU_bases.UnicodeString_compare(*args)
    def compareBetween(*args): return _PyICU_bases.UnicodeString_compareBetween(*args)
    def compareCodePointOrder(*args): return _PyICU_bases.UnicodeString_compareCodePointOrder(*args)
    def compareCodePointOrderBetween(*args): return _PyICU_bases.UnicodeString_compareCodePointOrderBetween(*args)
    def caseCompare(*args): return _PyICU_bases.UnicodeString_caseCompare(*args)
    def caseCompareBetween(*args): return _PyICU_bases.UnicodeString_caseCompareBetween(*args)
    def startsWith(*args): return _PyICU_bases.UnicodeString_startsWith(*args)
    def endsWith(*args): return _PyICU_bases.UnicodeString_endsWith(*args)
    def indexOf(*args): return _PyICU_bases.UnicodeString_indexOf(*args)
    def lastIndexOf(*args): return _PyICU_bases.UnicodeString_lastIndexOf(*args)
    def trim(*args): return _PyICU_bases.UnicodeString_trim(*args)
    def reverse(*args): return _PyICU_bases.UnicodeString_reverse(*args)
    def toUpper(*args): return _PyICU_bases.UnicodeString_toUpper(*args)
    def toLower(*args): return _PyICU_bases.UnicodeString_toLower(*args)
    def toTitle(*args): return _PyICU_bases.UnicodeString_toTitle(*args)
    def foldCase(*args): return _PyICU_bases.UnicodeString_foldCase(*args)
    def __getitem__(*args): return _PyICU_bases.UnicodeString___getitem__(*args)
    def __len__(*args): return _PyICU_bases.UnicodeString___len__(*args)
    def __setitem__(*args): return _PyICU_bases.UnicodeString___setitem__(*args)
    def __getslice__(*args): return _PyICU_bases.UnicodeString___getslice__(*args)
    def __setslice__(*args): return _PyICU_bases.UnicodeString___setslice__(*args)
    def __repr__(*args): return _PyICU_bases.UnicodeString___repr__(*args)
    def __str__(*args): return _PyICU_bases.UnicodeString___str__(*args)
    def __unicode__(*args): return _PyICU_bases.UnicodeString___unicode__(*args)
    def __cmp__(*args): return _PyICU_bases.UnicodeString___cmp__(*args)
    def __init__(self, *args):
        newobj = _PyICU_bases.new_UnicodeString(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    getAvailableStandards = staticmethod(_PyICU_bases.UnicodeString_getAvailableStandards)
    getAvailableEncodings = staticmethod(_PyICU_bases.UnicodeString_getAvailableEncodings)
    getStandardEncoding = staticmethod(_PyICU_bases.UnicodeString_getStandardEncoding)

class UnicodeStringPtr(UnicodeString):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = UnicodeString
_PyICU_bases.UnicodeString_swigregister(UnicodeStringPtr)

UnicodeString_getAvailableStandards = _PyICU_bases.UnicodeString_getAvailableStandards

UnicodeString_getAvailableEncodings = _PyICU_bases.UnicodeString_getAvailableEncodings

UnicodeString_getStandardEncoding = _PyICU_bases.UnicodeString_getStandardEncoding

class Formattable(UObject):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::Formattable instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    kIsDate = _PyICU_bases.Formattable_kIsDate
    kDate = _PyICU_bases.Formattable_kDate
    kDouble = _PyICU_bases.Formattable_kDouble
    kLong = _PyICU_bases.Formattable_kLong
    kString = _PyICU_bases.Formattable_kString
    kArray = _PyICU_bases.Formattable_kArray
    kInt64 = _PyICU_bases.Formattable_kInt64
    kObject = _PyICU_bases.Formattable_kObject
    def __init__(self, *args):
        newobj = _PyICU_bases.new_Formattable(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __eq__(*args): return _PyICU_bases.Formattable___eq__(*args)
    def __ne__(*args): return _PyICU_bases.Formattable___ne__(*args)
    def getType(*args): return _PyICU_bases.Formattable_getType(*args)
    def isNumeric(*args): return _PyICU_bases.Formattable_isNumeric(*args)
    def getDouble(*args): return _PyICU_bases.Formattable_getDouble(*args)
    def getLong(*args): return _PyICU_bases.Formattable_getLong(*args)
    def getInt64(*args): return _PyICU_bases.Formattable_getInt64(*args)
    def getDate(*args): return _PyICU_bases.Formattable_getDate(*args)
    def getString(*args): return _PyICU_bases.Formattable_getString(*args)
    def setDouble(*args): return _PyICU_bases.Formattable_setDouble(*args)
    def setLong(*args): return _PyICU_bases.Formattable_setLong(*args)
    def setInt64(*args): return _PyICU_bases.Formattable_setInt64(*args)
    def setDate(*args): return _PyICU_bases.Formattable_setDate(*args)
    def setString(*args): return _PyICU_bases.Formattable_setString(*args)

class FormattablePtr(Formattable):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Formattable
_PyICU_bases.Formattable_swigregister(FormattablePtr)

class MeasureUnit(UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::MeasureUnit instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __eq__(*args): return _PyICU_bases.MeasureUnit___eq__(*args)

class MeasureUnitPtr(MeasureUnit):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = MeasureUnit
_PyICU_bases.MeasureUnit_swigregister(MeasureUnitPtr)

class Measure(UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::Measure instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __eq__(*args): return _PyICU_bases.Measure___eq__(*args)
    def getNumber(*args): return _PyICU_bases.Measure_getNumber(*args)

class MeasurePtr(Measure):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Measure
_PyICU_bases.Measure_swigregister(MeasurePtr)

class CurrencyUnit(MeasureUnit):
    def __init__(self, *args):
        newobj = _PyICU_bases.new_CurrencyUnit(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getISOCurrency(*args): return _PyICU_bases.CurrencyUnit_getISOCurrency(*args)
    def __repr__(*args): return _PyICU_bases.CurrencyUnit___repr__(*args)

class CurrencyUnitPtr(CurrencyUnit):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = CurrencyUnit
_PyICU_bases.CurrencyUnit_swigregister(CurrencyUnitPtr)

class CurrencyAmount(Measure):
    def __init__(self, *args):
        newobj = _PyICU_bases.new_CurrencyAmount(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getCurrency(*args): return _PyICU_bases.CurrencyAmount_getCurrency(*args)
    def getISOCurrency(*args): return _PyICU_bases.CurrencyAmount_getISOCurrency(*args)
    def __repr__(*args): return _PyICU_bases.CurrencyAmount___repr__(*args)

class CurrencyAmountPtr(CurrencyAmount):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = CurrencyAmount
_PyICU_bases.CurrencyAmount_swigregister(CurrencyAmountPtr)

class StringEnumeration(UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::StringEnumeration instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def count(*args): return _PyICU_bases.StringEnumeration_count(*args)
    def reset(*args): return _PyICU_bases.StringEnumeration_reset(*args)
    def next(*args): return _PyICU_bases.StringEnumeration_next(*args)
    def unext(*args): return _PyICU_bases.StringEnumeration_unext(*args)
    def snext(*args): return _PyICU_bases.StringEnumeration_snext(*args)
    def __iter__(*args): return _PyICU_bases.StringEnumeration___iter__(*args)

class StringEnumerationPtr(StringEnumeration):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = StringEnumeration
_PyICU_bases.StringEnumeration_swigregister(StringEnumerationPtr)


