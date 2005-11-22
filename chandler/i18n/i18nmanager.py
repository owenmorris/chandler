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
        """
        Flushes the current resource path and translation per locale cache.
        This should be called when a locale set has been changed during runtime
        or to reload translations.
        """
        del self._cache
        self._cache = {"RESOURCES": {}, "TRANSLATIONS": {}}
        self.__initialized = False

    def discoverLocaleSet(self):
        """
        Queries the Operating System for the current locale sets.
        The Operating System may return one or more locales. In the case
        where more than one locale is returned the translation fallback will
        try each locale in the set in order till a resource or translation is 
        encountered.
        """
        #XXX: TO DO GET LocaleSet from OS
        self.setLocaleSet(self._defaultLocaleSet)


    def setLocaleSet(self, localeSet=None, domain=None):
        """
        Sets the current locale set for translation. Each domain can have a
        unique locale set and locale set order. This allow great flexibility
        as individual parcel or parcel groupings may be run in separate locales.

        If no specific locale set is defined for a parcel. The default locale set
        returned from the Operating System will be used.

        @type localeSet: List
        @param localeSet: an ordered  List of locale strings for example ['en_US', 'en']

        @type domain: ASCII str
        @param domain: unique ASCII domain name
        """
        self.flushCache()

        if domain is None:
            domain = self._defaultDomain

        assert isinstance(localeSet, ListType)
        assert len(localeSet) > 0

        #The 'test' locale is used in .6 for testing non-ascii translations
        #However in test mode, the French Canadian locale is leveraged by ICU.
        #This is done to test Chandler ICU support against a non-english locale.
        if 'test' in localeSet:
            self._localeSet = ['fr_CA', 'fr']
            self._localeSet.extend(localeSet)
        else:
            self._localeSet = localeSet

        #XXX: Need to translate the locale i.e. "en_US'" to a
        #     wx.LANGUAGE key
        #wx.Locale(wx.LANGUAGE_ENGLISH)

        # Set the PyICU Locale
        Locale.setDefault(Locale(self._localeSet[0]))

        # Set the Python locale
        #XXX: [i18n] need to investigate how python uses this locale info
        #     since the setting of the locale fails quit a bit
        for locale in self._localeSet:
            if self.__setPythonLocale(locale):
                break

        # Set the OS Environment
        os.environ['LANGUAGE'] = self._localeSet[0]
        os.environ['LANG'] = self._localeSet[0]
        os.environ['LC_MESSAGES'] = self._localeSet[0]

        self.__initialized = True

    def getLocaleSet(self, domain=None):
        """
        Returns the current ordered locale set for the given domain.
        If the domain is None the default locale set retrieved from
        the Operating System is returned. Each domain may have a 
        custom ordered locale set.

        @type domain: ASCII str
        @param domain: unique ASCII domain name

        @rtype: List
        @return: an ordered  List of locale strings for example ['en_US', 'en']
        """

        if domain is None:
            domain = self._defaultDomain

        return self._localeSet

    def translate(self, domain, defaultText):
        """
        Performs localized translation of the defaultText key based upon the locale set of the
        domain. The method access the I18nManager cache to retrieve the translated string
        for defaultText key on the domain. The cache is populated from gettext .mo translation files.
        The method employs the tradition locale set fallback mechanism
        and will search for a defaultText key for each locale in the ordered locale set until a match is
        found. If no match can be made the default english defaultText is returned.

        For .6 no cache is implemented and the defaultText is always returned unless the locale set
        contains a locale "test". In this case "(ü) %s" % defaultTextis returned.
        This is useful for confirming that all displayable UI strings are in fact going through the
        Chandler translation mechanism.

        @type domain: ASCII str
        @param domain: unique ASCII domain name

        @type defaultText: unicode
        @param defaultText: the unicode default key in english

        @rtype: unicode
        @return: The translated unicode string for key defaultText or defaultText itself if
                 no translation found
        """

        assert isinstance(domain, StringType)
        assert isinstance(defaultText, UnicodeType)

        #XXX This breaks hardhat commenting out
        #if not self.__initialized:
        #raise i18n.I18nException("I18nManager.translate called before locale set created")

        if 'test' in self._localeSet and not "Ctrl+" in defaultText and not "DELETE" == defaultText:
            # If the 'test' locale is used return a surrogate pair at the 
            # start of the defaultText block. However, if the text contains
            # accelerator key info return the default as changing it will
            # break keyboard shortcuts
            return u"(ü): %s"% defaultText

        return defaultText

    def getImage(self, fileName, domain=None):
        """
        Retrieves the localized image for the given domain.
        A folder structure based on the ordered locale set of the domain
        is searched for a image with the passed in fileName. When a match is
        found an open file object for the resource is returned. This path is
        then cached for future lookups. If no match is found for the given locale set
        and no default file with the fileName is found None is returned.

        For .6 only the OSAF domain is allowed and the default resource is always returned.
        No scanning of locale directories for a fileName match is performed.

        @type fileName: unicode
        @param fileName: The name of the file to return

        @type domain: ASCII str
        @param domain: unique ASCII domain name

        @rtype: file or None
        @return: An open file handle to the resource or None if no file found
        """

        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, self.IMAGE_PATH, fileName, domain)

    def getHTML(self, fileName, domain=None):
        """
        Retrieves the localized html file for the given domain.
        A folder structure based on the ordered locale set of the domain
        is searched for an html file with the passed in fileName. When a match is
        found an open file object for the resource is returned. This path is
        then cached for future lookups. If no match is found for the given locale set
        and no default file with the fileName is found None is returned.

        For .6 only the OSAF domain is allowed and the default resource is always returned.
        No scanning of locale directories for a fileName match is performed.

        @type fileName: unicode
        @param fileName: The name of the file to return

        @type domain: ASCII str
        @param domain: unique ASCII domain name

        @rtype: file or None
        @return: An open file handle to the resource or None if no file found
        """

        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, self.HTML_PATH, fileName, domain)

    def getAudio(self, fileName, domain=None):
        """
        Retrieves the localized audio file for the given domain.
        A folder structure based on the ordered locale set of the domain
        is searched for an audio file with the passed in fileName. When a match is
        found an open file object for the resource is returned. This path is
        then cached for future lookups. If no match is found for the given locale set
        and no default file with the fileName is found None is returned.

        For .6 only the OSAF domain is allowed and the default resource is always returned.
        No scanning of locale directories for a fileName match is performed.

        @type fileName: unicode
        @param fileName: The name of the file to return

        @type domain: ASCII str
        @param domain: unique ASCII domain name

        @rtype: file or None
        @return: An open file handle to the resource or None if no file found
        """

        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, self.AUDIO_PATH, fileName, domain)

    def getResource(self, relPath, fileName, domain=None):
        """
        Generic method for looking up localized resources.
        retrieves the localized file for the given domain and relative file path.

        A folder structure based on the ordered locale set of the domain
        is searched for a resource with the passed in fileName. When a match is
        found an open file object for the resource is returned. This path is
        then cached for future lookups. If no match is found for the given locale set
        and no default file with the fileName is found None is returned.

        For .6 only the OSAF domain is allowed and the default resource is always returned.
        No scanning of locale directories for a fileName match is performed.

        @type relPath: unicode
        @param relPath: The relative file path in relation to the domain file path

        @type fileName: unicode
        @param fileName: The name of the file to return

        @type domain: ASCII str
        @param domain: unique ASCII domain name

        @rtype: file or None
        @return: An open file handle to the resource or None if no file found
        """

        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, relPath, fileName, domain)

    #Reserved for future use. We will need a help lookup system
    #def getHelpFile(self, fileName, domain=None):
    #    return self.__getResource(None, self.HELP_PATH, fileName, domain)

    def __getResource(self, rootPath, relPath, resourceName, domain=None):
        # Will cache the path of the found resource
        # for the given locale set.
        # The cache will be flushed when a change to the
        # locale set occurs

        #XXX: These may throw UnicodeDecodeErrors
        #    which is ok cause the errror will alert the developer 
        #    to the error. I.e. they did not pass in an ascii or unicode string

        if domain != self._defaultDomain:
            raise i18n.I18nException("Only OSAF domain supported in .6")

        # For .6 we just get the default resource. In .7 the LocaleSet will determine
        # what localizaed resource is returned

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
            # Set the Python locale
            locale.setlocale(locale.LC_ALL, lc)
        except locale.Error:
            if __debug__:
                # Log the error only in debug mode
                logging.error("Unable to set Python locale to: '%s'" % lc)
            return False

        return True
