# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyICU_format

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


import PyICU_bases
import PyICU_iterators
import PyICU_locale
class FieldPosition(PyICU_bases.UObject):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::FieldPosition instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    DONT_CARE = _PyICU_format.FieldPosition_DONT_CARE
    def __init__(self, *args):
        newobj = _PyICU_format.new_FieldPosition(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __eq__(*args): return _PyICU_format.FieldPosition___eq__(*args)
    def __ne__(*args): return _PyICU_format.FieldPosition___ne__(*args)
    def getField(*args): return _PyICU_format.FieldPosition_getField(*args)
    def getBeginIndex(*args): return _PyICU_format.FieldPosition_getBeginIndex(*args)
    def getEndIndex(*args): return _PyICU_format.FieldPosition_getEndIndex(*args)
    def setField(*args): return _PyICU_format.FieldPosition_setField(*args)
    def setBeginIndex(*args): return _PyICU_format.FieldPosition_setBeginIndex(*args)
    def setEndIndex(*args): return _PyICU_format.FieldPosition_setEndIndex(*args)

class FieldPositionPtr(FieldPosition):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = FieldPosition
_PyICU_format.FieldPosition_swigregister(FieldPositionPtr)

class ParsePosition(PyICU_bases.UObject):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::ParsePosition instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_format.new_ParsePosition(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __eq__(*args): return _PyICU_format.ParsePosition___eq__(*args)
    def __ne__(*args): return _PyICU_format.ParsePosition___ne__(*args)
    def getIndex(*args): return _PyICU_format.ParsePosition_getIndex(*args)
    def setIndex(*args): return _PyICU_format.ParsePosition_setIndex(*args)
    def setErrorIndex(*args): return _PyICU_format.ParsePosition_setErrorIndex(*args)
    def getErrorIndex(*args): return _PyICU_format.ParsePosition_getErrorIndex(*args)

class ParsePositionPtr(ParsePosition):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = ParsePosition
_PyICU_format.ParsePosition_swigregister(ParsePositionPtr)

class Format(PyICU_bases.UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::Format instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __eq__(*args): return _PyICU_format.Format___eq__(*args)
    def __ne__(*args): return _PyICU_format.Format___ne__(*args)
    def format(*args): return _PyICU_format.Format_format(*args)
    def parseObject(*args): return _PyICU_format.Format_parseObject(*args)
    def getLocale(*args): return _PyICU_format.Format_getLocale(*args)
    def getLocaleID(*args): return _PyICU_format.Format_getLocaleID(*args)

class FormatPtr(Format):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Format
_PyICU_format.Format_swigregister(FormatPtr)

class MeasureFormat(Format):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::MeasureFormat instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    createCurrencyFormat = staticmethod(_PyICU_format.MeasureFormat_createCurrencyFormat)

class MeasureFormatPtr(MeasureFormat):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = MeasureFormat
_PyICU_format.MeasureFormat_swigregister(MeasureFormatPtr)

MeasureFormat_createCurrencyFormat = _PyICU_format.MeasureFormat_createCurrencyFormat

class MessageFormat(Format):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::MessageFormat instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_format.new_MessageFormat(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def setLocale(*args): return _PyICU_format.MessageFormat_setLocale(*args)
    def getLocale(*args): return _PyICU_format.MessageFormat_getLocale(*args)
    def applyPattern(*args): return _PyICU_format.MessageFormat_applyPattern(*args)
    def toPattern(*args): return _PyICU_format.MessageFormat_toPattern(*args)
    def setFormats(*args): return _PyICU_format.MessageFormat_setFormats(*args)
    def getFormats(*args): return _PyICU_format.MessageFormat_getFormats(*args)
    def setFormat(*args): return _PyICU_format.MessageFormat_setFormat(*args)
    def format(*args): return _PyICU_format.MessageFormat_format(*args)
    def parse(*args): return _PyICU_format.MessageFormat_parse(*args)
    formatMessage = staticmethod(_PyICU_format.MessageFormat_formatMessage)

class MessageFormatPtr(MessageFormat):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = MessageFormat
_PyICU_format.MessageFormat_swigregister(MessageFormatPtr)

MessageFormat_formatMessage = _PyICU_format.MessageFormat_formatMessage


