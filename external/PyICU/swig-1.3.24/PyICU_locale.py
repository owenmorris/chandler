# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyICU_locale

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
ULOC_ACTUAL_LOCALE = _PyICU_locale.ULOC_ACTUAL_LOCALE
ULOC_VALID_LOCALE = _PyICU_locale.ULOC_VALID_LOCALE
URES_NONE = _PyICU_locale.URES_NONE
URES_STRING = _PyICU_locale.URES_STRING
URES_BINARY = _PyICU_locale.URES_BINARY
URES_TABLE = _PyICU_locale.URES_TABLE
URES_ALIAS = _PyICU_locale.URES_ALIAS
URES_TABLE32 = _PyICU_locale.URES_TABLE32
URES_INT = _PyICU_locale.URES_INT
URES_ARRAY = _PyICU_locale.URES_ARRAY
URES_INT_VECTOR = _PyICU_locale.URES_INT_VECTOR
RES_RESERVED = _PyICU_locale.RES_RESERVED
class Locale(PyICU_bases.UObject):
    def __init__(self, *args):
        newobj = _PyICU_locale.new_Locale(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getLanguage(*args): return _PyICU_locale.Locale_getLanguage(*args)
    def getScript(*args): return _PyICU_locale.Locale_getScript(*args)
    def getCountry(*args): return _PyICU_locale.Locale_getCountry(*args)
    def getVariant(*args): return _PyICU_locale.Locale_getVariant(*args)
    def getName(*args): return _PyICU_locale.Locale_getName(*args)
    def getBaseName(*args): return _PyICU_locale.Locale_getBaseName(*args)
    def getISO3Language(*args): return _PyICU_locale.Locale_getISO3Language(*args)
    def getISO3Country(*args): return _PyICU_locale.Locale_getISO3Country(*args)
    def getLCID(*args): return _PyICU_locale.Locale_getLCID(*args)
    def getDisplayLanguage(*args): return _PyICU_locale.Locale_getDisplayLanguage(*args)
    def getDisplayScript(*args): return _PyICU_locale.Locale_getDisplayScript(*args)
    def getDisplayCountry(*args): return _PyICU_locale.Locale_getDisplayCountry(*args)
    def getDisplayVariant(*args): return _PyICU_locale.Locale_getDisplayVariant(*args)
    def getDisplayName(*args): return _PyICU_locale.Locale_getDisplayName(*args)
    def createKeywords(*args): return _PyICU_locale.Locale_createKeywords(*args)
    getEnglish = staticmethod(_PyICU_locale.Locale_getEnglish)
    getFrench = staticmethod(_PyICU_locale.Locale_getFrench)
    getGerman = staticmethod(_PyICU_locale.Locale_getGerman)
    getItalian = staticmethod(_PyICU_locale.Locale_getItalian)
    getJapanese = staticmethod(_PyICU_locale.Locale_getJapanese)
    getKorean = staticmethod(_PyICU_locale.Locale_getKorean)
    getChinese = staticmethod(_PyICU_locale.Locale_getChinese)
    getSimplifiedChinese = staticmethod(_PyICU_locale.Locale_getSimplifiedChinese)
    getTraditionalChinese = staticmethod(_PyICU_locale.Locale_getTraditionalChinese)
    getFrance = staticmethod(_PyICU_locale.Locale_getFrance)
    getGermany = staticmethod(_PyICU_locale.Locale_getGermany)
    getItaly = staticmethod(_PyICU_locale.Locale_getItaly)
    getJapan = staticmethod(_PyICU_locale.Locale_getJapan)
    getKorea = staticmethod(_PyICU_locale.Locale_getKorea)
    getChina = staticmethod(_PyICU_locale.Locale_getChina)
    getPRC = staticmethod(_PyICU_locale.Locale_getPRC)
    getTaiwan = staticmethod(_PyICU_locale.Locale_getTaiwan)
    getUK = staticmethod(_PyICU_locale.Locale_getUK)
    getUS = staticmethod(_PyICU_locale.Locale_getUS)
    getCanada = staticmethod(_PyICU_locale.Locale_getCanada)
    getCanadaFrench = staticmethod(_PyICU_locale.Locale_getCanadaFrench)
    getDefault = staticmethod(_PyICU_locale.Locale_getDefault)
    setDefault = staticmethod(_PyICU_locale.Locale_setDefault)
    createFromName = staticmethod(_PyICU_locale.Locale_createFromName)
    createCanonical = staticmethod(_PyICU_locale.Locale_createCanonical)
    getAvailableLocales = staticmethod(_PyICU_locale.Locale_getAvailableLocales)
    def __repr__(*args): return _PyICU_locale.Locale___repr__(*args)
    def getKeywordValue(*args): return _PyICU_locale.Locale_getKeywordValue(*args)
    getISOCountries = staticmethod(_PyICU_locale.Locale_getISOCountries)
    getISOLanguages = staticmethod(_PyICU_locale.Locale_getISOLanguages)

class LocalePtr(Locale):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = Locale
_PyICU_locale.Locale_swigregister(LocalePtr)

Locale_getEnglish = _PyICU_locale.Locale_getEnglish

Locale_getFrench = _PyICU_locale.Locale_getFrench

Locale_getGerman = _PyICU_locale.Locale_getGerman

Locale_getItalian = _PyICU_locale.Locale_getItalian

Locale_getJapanese = _PyICU_locale.Locale_getJapanese

Locale_getKorean = _PyICU_locale.Locale_getKorean

Locale_getChinese = _PyICU_locale.Locale_getChinese

Locale_getSimplifiedChinese = _PyICU_locale.Locale_getSimplifiedChinese

Locale_getTraditionalChinese = _PyICU_locale.Locale_getTraditionalChinese

Locale_getFrance = _PyICU_locale.Locale_getFrance

Locale_getGermany = _PyICU_locale.Locale_getGermany

Locale_getItaly = _PyICU_locale.Locale_getItaly

Locale_getJapan = _PyICU_locale.Locale_getJapan

Locale_getKorea = _PyICU_locale.Locale_getKorea

Locale_getChina = _PyICU_locale.Locale_getChina

Locale_getPRC = _PyICU_locale.Locale_getPRC

Locale_getTaiwan = _PyICU_locale.Locale_getTaiwan

Locale_getUK = _PyICU_locale.Locale_getUK

Locale_getUS = _PyICU_locale.Locale_getUS

Locale_getCanada = _PyICU_locale.Locale_getCanada

Locale_getCanadaFrench = _PyICU_locale.Locale_getCanadaFrench

Locale_getDefault = _PyICU_locale.Locale_getDefault

Locale_setDefault = _PyICU_locale.Locale_setDefault

Locale_createFromName = _PyICU_locale.Locale_createFromName

Locale_createCanonical = _PyICU_locale.Locale_createCanonical

Locale_getAvailableLocales = _PyICU_locale.Locale_getAvailableLocales

Locale_getISOCountries = _PyICU_locale.Locale_getISOCountries

Locale_getISOLanguages = _PyICU_locale.Locale_getISOLanguages

class ResourceBundle(PyICU_bases.UObject):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::ResourceBundle instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_locale.new_ResourceBundle(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getSize(*args): return _PyICU_locale.ResourceBundle_getSize(*args)
    def getString(*args): return _PyICU_locale.ResourceBundle_getString(*args)
    def getUInt(*args): return _PyICU_locale.ResourceBundle_getUInt(*args)
    def getInt(*args): return _PyICU_locale.ResourceBundle_getInt(*args)
    def getKey(*args): return _PyICU_locale.ResourceBundle_getKey(*args)
    def getName(*args): return _PyICU_locale.ResourceBundle_getName(*args)
    def getType(*args): return _PyICU_locale.ResourceBundle_getType(*args)
    def hasNext(*args): return _PyICU_locale.ResourceBundle_hasNext(*args)
    def resetIterator(*args): return _PyICU_locale.ResourceBundle_resetIterator(*args)
    def getNext(*args): return _PyICU_locale.ResourceBundle_getNext(*args)
    def getNextString(*args): return _PyICU_locale.ResourceBundle_getNextString(*args)
    def get(*args): return _PyICU_locale.ResourceBundle_get(*args)
    def getWithFallback(*args): return _PyICU_locale.ResourceBundle_getWithFallback(*args)
    def getStringEx(*args): return _PyICU_locale.ResourceBundle_getStringEx(*args)
    def getVersionNumber(*args): return _PyICU_locale.ResourceBundle_getVersionNumber(*args)
    def getBinary(*args): return _PyICU_locale.ResourceBundle_getBinary(*args)
    def getIntVector(*args): return _PyICU_locale.ResourceBundle_getIntVector(*args)
    def getLocale(*args): return _PyICU_locale.ResourceBundle_getLocale(*args)

class ResourceBundlePtr(ResourceBundle):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = ResourceBundle
_PyICU_locale.ResourceBundle_swigregister(ResourceBundlePtr)


