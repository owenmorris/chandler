# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyICU_iterators

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
import PyICU_locale
class ForwardCharacterIterator(PyICU_bases.UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::ForwardCharacterIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    DONE = _PyICU_iterators.ForwardCharacterIterator_DONE
    def __eq__(*args): return _PyICU_iterators.ForwardCharacterIterator___eq__(*args)
    def __ne__(*args): return _PyICU_iterators.ForwardCharacterIterator___ne__(*args)
    def hashCode(*args): return _PyICU_iterators.ForwardCharacterIterator_hashCode(*args)
    def nextPostInc(*args): return _PyICU_iterators.ForwardCharacterIterator_nextPostInc(*args)
    def hasNext(*args): return _PyICU_iterators.ForwardCharacterIterator_hasNext(*args)

class ForwardCharacterIteratorPtr(ForwardCharacterIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = ForwardCharacterIterator
_PyICU_iterators.ForwardCharacterIterator_swigregister(ForwardCharacterIteratorPtr)

class CharacterIterator(ForwardCharacterIterator):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::CharacterIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    kStart = _PyICU_iterators.CharacterIterator_kStart
    kCurrent = _PyICU_iterators.CharacterIterator_kCurrent
    kEnd = _PyICU_iterators.CharacterIterator_kEnd
    def clone(*args): return _PyICU_iterators.CharacterIterator_clone(*args)
    def first(*args): return _PyICU_iterators.CharacterIterator_first(*args)
    def firstPostInc(*args): return _PyICU_iterators.CharacterIterator_firstPostInc(*args)
    def last(*args): return _PyICU_iterators.CharacterIterator_last(*args)
    def current(*args): return _PyICU_iterators.CharacterIterator_current(*args)
    def next(*args): return _PyICU_iterators.CharacterIterator_next(*args)
    def previous(*args): return _PyICU_iterators.CharacterIterator_previous(*args)
    def setToStart(*args): return _PyICU_iterators.CharacterIterator_setToStart(*args)
    def setToEnd(*args): return _PyICU_iterators.CharacterIterator_setToEnd(*args)
    def setIndex(*args): return _PyICU_iterators.CharacterIterator_setIndex(*args)
    def hasPrevious(*args): return _PyICU_iterators.CharacterIterator_hasPrevious(*args)
    def startIndex(*args): return _PyICU_iterators.CharacterIterator_startIndex(*args)
    def endIndex(*args): return _PyICU_iterators.CharacterIterator_endIndex(*args)
    def getIndex(*args): return _PyICU_iterators.CharacterIterator_getIndex(*args)
    def getLength(*args): return _PyICU_iterators.CharacterIterator_getLength(*args)
    def move(*args): return _PyICU_iterators.CharacterIterator_move(*args)
    def getText(*args): return _PyICU_iterators.CharacterIterator_getText(*args)

class CharacterIteratorPtr(CharacterIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = CharacterIterator
_PyICU_iterators.CharacterIterator_swigregister(CharacterIteratorPtr)

class UCharCharacterIterator(CharacterIterator):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::UCharCharacterIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_iterators.new_UCharCharacterIterator(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown

class UCharCharacterIteratorPtr(UCharCharacterIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = UCharCharacterIterator
_PyICU_iterators.UCharCharacterIterator_swigregister(UCharCharacterIteratorPtr)

class StringCharacterIterator(CharacterIterator):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::StringCharacterIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_iterators.new_StringCharacterIterator(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def setText(*args): return _PyICU_iterators.StringCharacterIterator_setText(*args)

class StringCharacterIteratorPtr(StringCharacterIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = StringCharacterIterator
_PyICU_iterators.StringCharacterIterator_swigregister(StringCharacterIteratorPtr)

class BreakIterator(PyICU_bases.UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::BreakIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __eq__(*args): return _PyICU_iterators.BreakIterator___eq__(*args)
    def __ne__(*args): return _PyICU_iterators.BreakIterator___ne__(*args)
    def clone(*args): return _PyICU_iterators.BreakIterator_clone(*args)
    def adoptText(*args): return _PyICU_iterators.BreakIterator_adoptText(*args)
    def setText(*args): return _PyICU_iterators.BreakIterator_setText(*args)
    def first(*args): return _PyICU_iterators.BreakIterator_first(*args)
    def last(*args): return _PyICU_iterators.BreakIterator_last(*args)
    def previous(*args): return _PyICU_iterators.BreakIterator_previous(*args)
    def next(*args): return _PyICU_iterators.BreakIterator_next(*args)
    def current(*args): return _PyICU_iterators.BreakIterator_current(*args)
    def following(*args): return _PyICU_iterators.BreakIterator_following(*args)
    def preceding(*args): return _PyICU_iterators.BreakIterator_preceding(*args)
    def getLocale(*args): return _PyICU_iterators.BreakIterator_getLocale(*args)
    def getLocaleID(*args): return _PyICU_iterators.BreakIterator_getLocaleID(*args)
    createWordInstance = staticmethod(_PyICU_iterators.BreakIterator_createWordInstance)
    createLineInstance = staticmethod(_PyICU_iterators.BreakIterator_createLineInstance)
    createCharacterInstance = staticmethod(_PyICU_iterators.BreakIterator_createCharacterInstance)
    createSentenceInstance = staticmethod(_PyICU_iterators.BreakIterator_createSentenceInstance)
    createTitleInstance = staticmethod(_PyICU_iterators.BreakIterator_createTitleInstance)
    getAvailableLocales = staticmethod(_PyICU_iterators.BreakIterator_getAvailableLocales)
    getDisplayName = staticmethod(_PyICU_iterators.BreakIterator_getDisplayName)

class BreakIteratorPtr(BreakIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = BreakIterator
_PyICU_iterators.BreakIterator_swigregister(BreakIteratorPtr)

BreakIterator_createWordInstance = _PyICU_iterators.BreakIterator_createWordInstance

BreakIterator_createLineInstance = _PyICU_iterators.BreakIterator_createLineInstance

BreakIterator_createCharacterInstance = _PyICU_iterators.BreakIterator_createCharacterInstance

BreakIterator_createSentenceInstance = _PyICU_iterators.BreakIterator_createSentenceInstance

BreakIterator_createTitleInstance = _PyICU_iterators.BreakIterator_createTitleInstance

BreakIterator_getAvailableLocales = _PyICU_iterators.BreakIterator_getAvailableLocales

BreakIterator_getDisplayName = _PyICU_iterators.BreakIterator_getDisplayName

class RuleBasedBreakIterator(BreakIterator):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::RuleBasedBreakIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_iterators.new_RuleBasedBreakIterator(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getRules(*args): return _PyICU_iterators.RuleBasedBreakIterator_getRules(*args)
    def isBoundary(*args): return _PyICU_iterators.RuleBasedBreakIterator_isBoundary(*args)
    def getRuleStatus(*args): return _PyICU_iterators.RuleBasedBreakIterator_getRuleStatus(*args)

class RuleBasedBreakIteratorPtr(RuleBasedBreakIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = RuleBasedBreakIterator
_PyICU_iterators.RuleBasedBreakIterator_swigregister(RuleBasedBreakIteratorPtr)

class DictionaryBasedBreakIterator(RuleBasedBreakIterator):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::DictionaryBasedBreakIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_iterators.new_DictionaryBasedBreakIterator(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown

class DictionaryBasedBreakIteratorPtr(DictionaryBasedBreakIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = DictionaryBasedBreakIterator
_PyICU_iterators.DictionaryBasedBreakIterator_swigregister(DictionaryBasedBreakIteratorPtr)

class CanonicalIterator(PyICU_bases.UObject):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::CanonicalIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_iterators.new_CanonicalIterator(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getSource(*args): return _PyICU_iterators.CanonicalIterator_getSource(*args)
    def setSource(*args): return _PyICU_iterators.CanonicalIterator_setSource(*args)
    def reset(*args): return _PyICU_iterators.CanonicalIterator_reset(*args)
    def next(*args): return _PyICU_iterators.CanonicalIterator_next(*args)

class CanonicalIteratorPtr(CanonicalIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = CanonicalIterator
_PyICU_iterators.CanonicalIterator_swigregister(CanonicalIteratorPtr)

class CollationElementIterator(PyICU_bases.UObject):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::CollationElementIterator instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __eq__(*args): return _PyICU_iterators.CollationElementIterator___eq__(*args)
    def __ne__(*args): return _PyICU_iterators.CollationElementIterator___ne__(*args)
    def reset(*args): return _PyICU_iterators.CollationElementIterator_reset(*args)
    def next(*args): return _PyICU_iterators.CollationElementIterator_next(*args)
    def previous(*args): return _PyICU_iterators.CollationElementIterator_previous(*args)
    def getMaxExpansion(*args): return _PyICU_iterators.CollationElementIterator_getMaxExpansion(*args)
    def strengthOrder(*args): return _PyICU_iterators.CollationElementIterator_strengthOrder(*args)
    def setText(*args): return _PyICU_iterators.CollationElementIterator_setText(*args)
    def getOffset(*args): return _PyICU_iterators.CollationElementIterator_getOffset(*args)
    def setOffset(*args): return _PyICU_iterators.CollationElementIterator_setOffset(*args)
    primaryOrder = staticmethod(_PyICU_iterators.CollationElementIterator_primaryOrder)
    secondaryOrder = staticmethod(_PyICU_iterators.CollationElementIterator_secondaryOrder)
    tertiaryOrder = staticmethod(_PyICU_iterators.CollationElementIterator_tertiaryOrder)
    isIgnorable = staticmethod(_PyICU_iterators.CollationElementIterator_isIgnorable)

class CollationElementIteratorPtr(CollationElementIterator):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = CollationElementIterator
_PyICU_iterators.CollationElementIterator_swigregister(CollationElementIteratorPtr)

CollationElementIterator_primaryOrder = _PyICU_iterators.CollationElementIterator_primaryOrder

CollationElementIterator_secondaryOrder = _PyICU_iterators.CollationElementIterator_secondaryOrder

CollationElementIterator_tertiaryOrder = _PyICU_iterators.CollationElementIterator_tertiaryOrder

CollationElementIterator_isIgnorable = _PyICU_iterators.CollationElementIterator_isIgnorable


