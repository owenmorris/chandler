# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyICU_collator

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
UCOL_LESS = _PyICU_collator.UCOL_LESS
UCOL_EQUAL = _PyICU_collator.UCOL_EQUAL
UCOL_GREATER = _PyICU_collator.UCOL_GREATER
class CollationKey(PyICU_bases.UObject):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::CollationKey instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_collator.new_CollationKey(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __eq__(*args): return _PyICU_collator.CollationKey___eq__(*args)
    def __ne__(*args): return _PyICU_collator.CollationKey___ne__(*args)
    def isBogus(*args): return _PyICU_collator.CollationKey_isBogus(*args)
    def compareTo(*args): return _PyICU_collator.CollationKey_compareTo(*args)
    def getByteArray(*args): return _PyICU_collator.CollationKey_getByteArray(*args)

class CollationKeyPtr(CollationKey):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = CollationKey
_PyICU_collator.CollationKey_swigregister(CollationKeyPtr)

class Collator(PyICU_bases.UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::Collator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    PRIMARY = _PyICU_collator.Collator_PRIMARY
    SECONDARY = _PyICU_collator.Collator_SECONDARY
    TERTIARY = _PyICU_collator.Collator_TERTIARY
    QUATERNARY = _PyICU_collator.Collator_QUATERNARY
    IDENTICAL = _PyICU_collator.Collator_IDENTICAL
    def __eq__(*args): return _PyICU_collator.Collator___eq__(*args)
    def __ne__(*args): return _PyICU_collator.Collator___ne__(*args)
    def compare(*args): return _PyICU_collator.Collator_compare(*args)
    def getCollationKey(*args): return _PyICU_collator.Collator_getCollationKey(*args)
    def greater(*args): return _PyICU_collator.Collator_greater(*args)
    def greaterOrEqual(*args): return _PyICU_collator.Collator_greaterOrEqual(*args)
    def equals(*args): return _PyICU_collator.Collator_equals(*args)
    def getStrength(*args): return _PyICU_collator.Collator_getStrength(*args)
    def setStrength(*args): return _PyICU_collator.Collator_setStrength(*args)
    createInstance = staticmethod(_PyICU_collator.Collator_createInstance)
    getAvailableLocales = staticmethod(_PyICU_collator.Collator_getAvailableLocales)
    getKeywords = staticmethod(_PyICU_collator.Collator_getKeywords)
    getKeywordValues = staticmethod(_PyICU_collator.Collator_getKeywordValues)
    def getLocale(*args): return _PyICU_collator.Collator_getLocale(*args)
    getFunctionalEquivalent = staticmethod(_PyICU_collator.Collator_getFunctionalEquivalent)

class CollatorPtr(Collator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Collator
_PyICU_collator.Collator_swigregister(CollatorPtr)

Collator_createInstance = _PyICU_collator.Collator_createInstance

Collator_getAvailableLocales = _PyICU_collator.Collator_getAvailableLocales

Collator_getKeywords = _PyICU_collator.Collator_getKeywords

Collator_getKeywordValues = _PyICU_collator.Collator_getKeywordValues

Collator_getFunctionalEquivalent = _PyICU_collator.Collator_getFunctionalEquivalent

class RuleBasedCollator(Collator):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::RuleBasedCollator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_collator.new_RuleBasedCollator(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getRules(*args): return _PyICU_collator.RuleBasedCollator_getRules(*args)

class RuleBasedCollatorPtr(RuleBasedCollator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = RuleBasedCollator
_PyICU_collator.RuleBasedCollator_swigregister(RuleBasedCollatorPtr)


