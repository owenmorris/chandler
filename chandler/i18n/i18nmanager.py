# -*- coding: utf-8 -*-

__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from types import ListType, UnicodeType, StringType
from PyICU import Locale
import os, locale, logging, gettext
from application import  Globals
import i18n


"""
Notes:
1. Translation files take from java to look like

if domain == osaf
  i18n/messages/osaf_en.po
  i18n/messages/osaf_en_US.po
  i18n/messages/osaf_jp.po

Should be a way to register a translation file for the osaf domain for
a specific language as well

or could be domain/messages/
en.po
jp.po 


TO DO:
1. Implement cache with thread lock
2. Create generic localeset fallback interface
"""

__all__ = ["I18nManager"]


class I18nManager(object):

    RESOURCE_ROOT = "resources"
    IMAGE_PATH = "images"
    AUDIO_PATH = "audio"
    HTML_PATH = "html"
    #HELP_PATH = u"help"

    __slots__ = ['_localeSet', '_cache', "_defaultDomain", "_defaultLocaleSet", "__initialized"]

    def __init__(self, defaultDomain, defaultLocaleSet):
        super(I18nManager, self).__init__()
        assert isinstance(defaultDomain, StringType)
        assert isinstance(defaultLocaleSet, ListType)

        self._cache = {"RESOURCES": {}, "TRANSLATIONS": {}}
        self._localeSet = []
        self._defaultDomain = defaultDomain
        self._defaultLocaleSet = defaultLocaleSet
        self.__initialized = False

    def __repr__(self):
        return "I18nManager(%s, %s)" % (self._defaultDomain, self._defaultLocaleSet)

    def flushCache(self):
        del self._cache
        self._cache = {"RESOURCES": {}, "TRANSLATIONS": {}}
        self.__initialized = False

    def discoverLocaleSet(self):
        #XXX: TO DO GET LocaleSet from OS
        self.setLocaleSet(self._defaultLocaleSet)


    def setLocaleSet(self, localeSet=None, domain=None):
        self.flushCache()

        if domain is None:
            domain = self._defaultDomain

        assert isinstance(localeSet, ListType)
        assert len(localeSet) > 0

        #The 'test' locale is used in .6 for testing non-ascii translations
        #The defaultLocale set is still used so that ICU can be leveraged
        #since 'test' is a made up locale and ICU does not know how to display its dates.
        if localeSet[0] == 'test':
            self._localeSet = self._defaultLocaleSet
            self._localeSet.extend(localeSet)
        else:
            self._localeSet = localeSet

        #XXX: Need to translate the locale i.e. "en_US'" to a
        #     wx.LANGUAGE key
        #wx.Locale(wx.LANGUAGE_ENGLISH)

        """Set the PyICU Locale"""
        Locale.setDefault(Locale(self._localeSet[0]))

        """Set the Python locale"""
        #XXX: [i18n] need to investigate how python uses this locale info
        #     since the setting of the locale fails quit a bit
        for locale in self._localeSet:
            if self.__setPythonLocale(locale):
                break

        """Set the OS Environment"""
        os.environ['LANGUAGE'] = self._localeSet[0]
        os.environ['LANG'] = self._localeSet[0]
        os.environ['LC_MESSAGES'] = self._localeSet[0]

        self.__initialized = True

    def getLocaleSet(self, domain=None):
        if domain is None:
            domain = self._defaultDomain

        return self._localeSet

    def translate(self, domain, defaultText):
        assert isinstance(domain, StringType)
        assert isinstance(defaultText, UnicodeType)

        #XXX This breaks hardhat commenting out
        #if not self.__initialized:
        #raise i18n.I18nException("I18nManager.translate called before locale set created")

        if 'test' in self._localeSet and not "Ctrl+" in defaultText:
            """If the 'test' locale is used return a surrogate pair at the 
               start of the defaultText block. However, if the text contains
               accelerator key info return the default as changing it will
               break keyboard shortcuts"""
            return u"(ü): %s"% defaultText

        return defaultText

    def getImage(self, fileName, domain=None):
        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, self.IMAGE_PATH, fileName, domain)

    def getHTML(self, fileName, domain=None):
        if domain is None:
            domain = self._defaultDomain
        return self.__getResource(self.RESOURCE_ROOT, self.HTML_PATH, fileName, domain)

    def getAudio(self, fileName, domain=None):
        if domain is None:
            domain = self._defaultDomain
        return self.__getResource(self.RESOURCE_ROOT, self.AUDIO_PATH, fileName, domain)

    def getResource(self, relPath, fileName, domain=None):
        return self.__getResource(self.RESOURCE_ROOT, relPath, fileName, domain)

    #Reserved for future use. We will need a help lookup system
    #def getHelpFile(self, fileName, domain=None):
    #    return self.__getResource(None, self.HELP_PATH, fileName, domain)

    def __getResource(self, rootPath, relPath, resourceName, domain=None):
        """Will cache the path of the found resource
           for the given locale set.

           The cache will be flushed when a change to the
           locale set occurs
        """

        #XXX: These may throw UnicodeDecodeErrors
        #    which is ok cause the errror will alert the developer 
        #    to the error. I.e. they did not pass in an ascii or unicode string

        if domain != self._defaultDomain:
            raise i18n.I18nException("Only OSAF domain supported in .6")

        """For .6 we just get the default resource. In .7 the LocaleSet will determine
           what localizaed resource is returned"""
        if rootPath is not None:
            root = os.sep.join([Globals.chandlerDirectory, rootPath,  relPath])
        else:
            root = os.sep.join([Globals.chandlerDirectory, relPath])

        res  = os.sep.join([root, resourceName])

        try:
            file = open(res, "rb")
        except IOError:
            return None

        return file

    def __setPythonLocale(self, lc):
        try:
            """Set the Python locale"""
            locale.setlocale(locale.LC_ALL, lc)
        except locale.Error:
            if __debug__:
                """Log the error only in debug mode"""
                logging.error("Unable to set Python locale to: '%s'" % lc)
            return False

        return True
