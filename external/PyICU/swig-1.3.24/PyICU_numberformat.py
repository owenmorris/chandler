# This file was created automatically by SWIG.
# Don't modify this file, modify the SWIG interface instead.

import _PyICU_numberformat

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
import PyICU_format
class DecimalFormatSymbols(PyICU_bases.UObject):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::DecimalFormatSymbols instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    kDecimalSeparatorSymbol = _PyICU_numberformat.DecimalFormatSymbols_kDecimalSeparatorSymbol
    kGroupingSeparatorSymbol = _PyICU_numberformat.DecimalFormatSymbols_kGroupingSeparatorSymbol
    kPatternSeparatorSymbol = _PyICU_numberformat.DecimalFormatSymbols_kPatternSeparatorSymbol
    kPercentSymbol = _PyICU_numberformat.DecimalFormatSymbols_kPercentSymbol
    kZeroDigitSymbol = _PyICU_numberformat.DecimalFormatSymbols_kZeroDigitSymbol
    kDigitSymbol = _PyICU_numberformat.DecimalFormatSymbols_kDigitSymbol
    kMinusSignSymbol = _PyICU_numberformat.DecimalFormatSymbols_kMinusSignSymbol
    kPlusSignSymbol = _PyICU_numberformat.DecimalFormatSymbols_kPlusSignSymbol
    kCurrencySymbol = _PyICU_numberformat.DecimalFormatSymbols_kCurrencySymbol
    kIntlCurrencySymbol = _PyICU_numberformat.DecimalFormatSymbols_kIntlCurrencySymbol
    kMonetarySeparatorSymbol = _PyICU_numberformat.DecimalFormatSymbols_kMonetarySeparatorSymbol
    kExponentialSymbol = _PyICU_numberformat.DecimalFormatSymbols_kExponentialSymbol
    kPerMillSymbol = _PyICU_numberformat.DecimalFormatSymbols_kPerMillSymbol
    kPadEscapeSymbol = _PyICU_numberformat.DecimalFormatSymbols_kPadEscapeSymbol
    kInfinitySymbol = _PyICU_numberformat.DecimalFormatSymbols_kInfinitySymbol
    kNaNSymbol = _PyICU_numberformat.DecimalFormatSymbols_kNaNSymbol
    kSignificantDigitSymbol = _PyICU_numberformat.DecimalFormatSymbols_kSignificantDigitSymbol
    def __init__(self, *args):
        newobj = _PyICU_numberformat.new_DecimalFormatSymbols(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def __eq__(*args): return _PyICU_numberformat.DecimalFormatSymbols___eq__(*args)
    def __ne__(*args): return _PyICU_numberformat.DecimalFormatSymbols___ne__(*args)
    def getSymbol(*args): return _PyICU_numberformat.DecimalFormatSymbols_getSymbol(*args)
    def setSymbol(*args): return _PyICU_numberformat.DecimalFormatSymbols_setSymbol(*args)
    def getLocale(*args): return _PyICU_numberformat.DecimalFormatSymbols_getLocale(*args)

class DecimalFormatSymbolsPtr(DecimalFormatSymbols):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = DecimalFormatSymbols
_PyICU_numberformat.DecimalFormatSymbols_swigregister(DecimalFormatSymbolsPtr)

class NumberFormat(PyICU_format.Format):
    def __init__(self): raise RuntimeError, "No constructor defined"
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::NumberFormat instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    kIntegerField = _PyICU_numberformat.NumberFormat_kIntegerField
    kFractionField = _PyICU_numberformat.NumberFormat_kFractionField
    INTEGER_FIELD = _PyICU_numberformat.NumberFormat_INTEGER_FIELD
    FRACTION_FIELD = _PyICU_numberformat.NumberFormat_FRACTION_FIELD
    def __eq__(*args): return _PyICU_numberformat.NumberFormat___eq__(*args)
    def format(*args): return _PyICU_numberformat.NumberFormat_format(*args)
    def parseCurrency(*args): return _PyICU_numberformat.NumberFormat_parseCurrency(*args)
    def isParseIntegerOnly(*args): return _PyICU_numberformat.NumberFormat_isParseIntegerOnly(*args)
    def setParseIntegerOnly(*args): return _PyICU_numberformat.NumberFormat_setParseIntegerOnly(*args)
    def isGroupingUsed(*args): return _PyICU_numberformat.NumberFormat_isGroupingUsed(*args)
    def setGroupingUsed(*args): return _PyICU_numberformat.NumberFormat_setGroupingUsed(*args)
    def getMaximumIntegerDigits(*args): return _PyICU_numberformat.NumberFormat_getMaximumIntegerDigits(*args)
    def setMaximumIntegerDigits(*args): return _PyICU_numberformat.NumberFormat_setMaximumIntegerDigits(*args)
    def getMinimumIntegerDigits(*args): return _PyICU_numberformat.NumberFormat_getMinimumIntegerDigits(*args)
    def setMinimumIntegerDigits(*args): return _PyICU_numberformat.NumberFormat_setMinimumIntegerDigits(*args)
    def getMaximumFractionDigits(*args): return _PyICU_numberformat.NumberFormat_getMaximumFractionDigits(*args)
    def setMaximumFractionDigits(*args): return _PyICU_numberformat.NumberFormat_setMaximumFractionDigits(*args)
    def getMinimumFractionDigits(*args): return _PyICU_numberformat.NumberFormat_getMinimumFractionDigits(*args)
    def setMinimumFractionDigits(*args): return _PyICU_numberformat.NumberFormat_setMinimumFractionDigits(*args)
    def setCurrency(*args): return _PyICU_numberformat.NumberFormat_setCurrency(*args)
    def getCurrency(*args): return _PyICU_numberformat.NumberFormat_getCurrency(*args)
    createInstance = staticmethod(_PyICU_numberformat.NumberFormat_createInstance)
    createCurrencyInstance = staticmethod(_PyICU_numberformat.NumberFormat_createCurrencyInstance)
    createPercentInstance = staticmethod(_PyICU_numberformat.NumberFormat_createPercentInstance)
    createScientificInstance = staticmethod(_PyICU_numberformat.NumberFormat_createScientificInstance)
    getAvailableLocales = staticmethod(_PyICU_numberformat.NumberFormat_getAvailableLocales)
    def parse(*args): return _PyICU_numberformat.NumberFormat_parse(*args)

class NumberFormatPtr(NumberFormat):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = NumberFormat
_PyICU_numberformat.NumberFormat_swigregister(NumberFormatPtr)

NumberFormat_createInstance = _PyICU_numberformat.NumberFormat_createInstance

NumberFormat_createCurrencyInstance = _PyICU_numberformat.NumberFormat_createCurrencyInstance

NumberFormat_createPercentInstance = _PyICU_numberformat.NumberFormat_createPercentInstance

NumberFormat_createScientificInstance = _PyICU_numberformat.NumberFormat_createScientificInstance

NumberFormat_getAvailableLocales = _PyICU_numberformat.NumberFormat_getAvailableLocales

class DecimalFormat(NumberFormat):
    kRoundCeiling = _PyICU_numberformat.DecimalFormat_kRoundCeiling
    kRoundFloor = _PyICU_numberformat.DecimalFormat_kRoundFloor
    kRoundDown = _PyICU_numberformat.DecimalFormat_kRoundDown
    kRoundUp = _PyICU_numberformat.DecimalFormat_kRoundUp
    kRoundHalfEven = _PyICU_numberformat.DecimalFormat_kRoundHalfEven
    kRoundHalfDown = _PyICU_numberformat.DecimalFormat_kRoundHalfDown
    kRoundHalfUp = _PyICU_numberformat.DecimalFormat_kRoundHalfUp
    kPadBeforePrefix = _PyICU_numberformat.DecimalFormat_kPadBeforePrefix
    kPadAfterPrefix = _PyICU_numberformat.DecimalFormat_kPadAfterPrefix
    kPadBeforeSuffix = _PyICU_numberformat.DecimalFormat_kPadBeforeSuffix
    kPadAfterSuffix = _PyICU_numberformat.DecimalFormat_kPadAfterSuffix
    def __init__(self, *args):
        newobj = _PyICU_numberformat.new_DecimalFormat(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getPositivePrefix(*args): return _PyICU_numberformat.DecimalFormat_getPositivePrefix(*args)
    def setPositivePrefix(*args): return _PyICU_numberformat.DecimalFormat_setPositivePrefix(*args)
    def getNegativePrefix(*args): return _PyICU_numberformat.DecimalFormat_getNegativePrefix(*args)
    def setNegativePrefix(*args): return _PyICU_numberformat.DecimalFormat_setNegativePrefix(*args)
    def getMultiplier(*args): return _PyICU_numberformat.DecimalFormat_getMultiplier(*args)
    def setMultiplier(*args): return _PyICU_numberformat.DecimalFormat_setMultiplier(*args)
    def getRoundingIncrement(*args): return _PyICU_numberformat.DecimalFormat_getRoundingIncrement(*args)
    def setRoundingIncrement(*args): return _PyICU_numberformat.DecimalFormat_setRoundingIncrement(*args)
    def getRoundingMode(*args): return _PyICU_numberformat.DecimalFormat_getRoundingMode(*args)
    def setRoundingMode(*args): return _PyICU_numberformat.DecimalFormat_setRoundingMode(*args)
    def getFormatWidth(*args): return _PyICU_numberformat.DecimalFormat_getFormatWidth(*args)
    def setFormatWidth(*args): return _PyICU_numberformat.DecimalFormat_setFormatWidth(*args)
    def getPadCharacterString(*args): return _PyICU_numberformat.DecimalFormat_getPadCharacterString(*args)
    def setPadCharacter(*args): return _PyICU_numberformat.DecimalFormat_setPadCharacter(*args)
    def getPadPosition(*args): return _PyICU_numberformat.DecimalFormat_getPadPosition(*args)
    def setPadPosition(*args): return _PyICU_numberformat.DecimalFormat_setPadPosition(*args)
    def isScientificNotation(*args): return _PyICU_numberformat.DecimalFormat_isScientificNotation(*args)
    def setScientificNotation(*args): return _PyICU_numberformat.DecimalFormat_setScientificNotation(*args)
    def getMinimumExponentDigits(*args): return _PyICU_numberformat.DecimalFormat_getMinimumExponentDigits(*args)
    def setMinimumExponentDigits(*args): return _PyICU_numberformat.DecimalFormat_setMinimumExponentDigits(*args)
    def isExponentSignAlwaysShown(*args): return _PyICU_numberformat.DecimalFormat_isExponentSignAlwaysShown(*args)
    def setExponentSignAlwaysShown(*args): return _PyICU_numberformat.DecimalFormat_setExponentSignAlwaysShown(*args)
    def isDecimalSeparatorAlwaysShown(*args): return _PyICU_numberformat.DecimalFormat_isDecimalSeparatorAlwaysShown(*args)
    def setDecimalSeparatorAlwaysShown(*args): return _PyICU_numberformat.DecimalFormat_setDecimalSeparatorAlwaysShown(*args)
    def getGroupingSize(*args): return _PyICU_numberformat.DecimalFormat_getGroupingSize(*args)
    def setGroupingSize(*args): return _PyICU_numberformat.DecimalFormat_setGroupingSize(*args)
    def getSecondaryGroupingSize(*args): return _PyICU_numberformat.DecimalFormat_getSecondaryGroupingSize(*args)
    def setSecondaryGroupingSize(*args): return _PyICU_numberformat.DecimalFormat_setSecondaryGroupingSize(*args)
    def toPattern(*args): return _PyICU_numberformat.DecimalFormat_toPattern(*args)
    def toLocalizedPattern(*args): return _PyICU_numberformat.DecimalFormat_toLocalizedPattern(*args)
    def applyPattern(*args): return _PyICU_numberformat.DecimalFormat_applyPattern(*args)
    def applyLocalizedPattern(*args): return _PyICU_numberformat.DecimalFormat_applyLocalizedPattern(*args)
    def getMaximumSignificantDigits(*args): return _PyICU_numberformat.DecimalFormat_getMaximumSignificantDigits(*args)
    def setMaximumSignificantDigits(*args): return _PyICU_numberformat.DecimalFormat_setMaximumSignificantDigits(*args)
    def getMinimumSignificantDigits(*args): return _PyICU_numberformat.DecimalFormat_getMinimumSignificantDigits(*args)
    def setMinimumSignificantDigits(*args): return _PyICU_numberformat.DecimalFormat_setMinimumSignificantDigits(*args)
    def areSignificantDigitsUsed(*args): return _PyICU_numberformat.DecimalFormat_areSignificantDigitsUsed(*args)
    def setSignificantDigitsUsed(*args): return _PyICU_numberformat.DecimalFormat_setSignificantDigitsUsed(*args)
    def __repr__(*args): return _PyICU_numberformat.DecimalFormat___repr__(*args)

class DecimalFormatPtr(DecimalFormat):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = DecimalFormat
_PyICU_numberformat.DecimalFormat_swigregister(DecimalFormatPtr)

class RuleBasedNumberFormat(NumberFormat):
    def __init__(self, *args):
        newobj = _PyICU_numberformat.new_RuleBasedNumberFormat(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def getRules(*args): return _PyICU_numberformat.RuleBasedNumberFormat_getRules(*args)
    def getNumberOfRuleSetNames(*args): return _PyICU_numberformat.RuleBasedNumberFormat_getNumberOfRuleSetNames(*args)
    def getRuleSetName(*args): return _PyICU_numberformat.RuleBasedNumberFormat_getRuleSetName(*args)
    def getNumberOfRuleSetDisplayNameLocales(*args): return _PyICU_numberformat.RuleBasedNumberFormat_getNumberOfRuleSetDisplayNameLocales(*args)
    def getRuleSetDisplayNameLocale(*args): return _PyICU_numberformat.RuleBasedNumberFormat_getRuleSetDisplayNameLocale(*args)
    def getRuleSetDisplayName(*args): return _PyICU_numberformat.RuleBasedNumberFormat_getRuleSetDisplayName(*args)
    def format(*args): return _PyICU_numberformat.RuleBasedNumberFormat_format(*args)
    def setLenient(*args): return _PyICU_numberformat.RuleBasedNumberFormat_setLenient(*args)
    def isLenient(*args): return _PyICU_numberformat.RuleBasedNumberFormat_isLenient(*args)
    def setDefaultRuleSet(*args): return _PyICU_numberformat.RuleBasedNumberFormat_setDefaultRuleSet(*args)
    def getDefaultRuleSetName(*args): return _PyICU_numberformat.RuleBasedNumberFormat_getDefaultRuleSetName(*args)
    def __repr__(*args): return _PyICU_numberformat.RuleBasedNumberFormat___repr__(*args)

class RuleBasedNumberFormatPtr(RuleBasedNumberFormat):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = RuleBasedNumberFormat
_PyICU_numberformat.RuleBasedNumberFormat_swigregister(RuleBasedNumberFormatPtr)

class ChoiceFormat(NumberFormat):
    def __repr__(self):
        return "<%s.%s; proxy of C++ icu::ChoiceFormat instance at %s>" % (self.__class__.__module__, self.__class__.__name__, self.this,)
    def __init__(self, *args):
        newobj = _PyICU_numberformat.new_ChoiceFormat(*args)
        self.this = newobj.this
        self.thisown = 1
        del newobj.thisown
    def applyPattern(*args): return _PyICU_numberformat.ChoiceFormat_applyPattern(*args)
    def toPattern(*args): return _PyICU_numberformat.ChoiceFormat_toPattern(*args)
    def setChoices(*args): return _PyICU_numberformat.ChoiceFormat_setChoices(*args)
    def getLimits(*args): return _PyICU_numberformat.ChoiceFormat_getLimits(*args)
    def getClosures(*args): return _PyICU_numberformat.ChoiceFormat_getClosures(*args)
    def getFormats(*args): return _PyICU_numberformat.ChoiceFormat_getFormats(*args)
    def format(*args): return _PyICU_numberformat.ChoiceFormat_format(*args)

class ChoiceFormatPtr(ChoiceFormat):
    def __init__(self, this):
        self.this = this
        if not hasattr(self,"thisown"): self.thisown = 0
        self.__class__ = ChoiceFormat
_PyICU_numberformat.ChoiceFormat_swigregister(ChoiceFormatPtr)


