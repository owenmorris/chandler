# -*- coding: utf-8 -*- 
__revision__  = "$Revision: 5970 $"
__date__      = "$Date: 2005-07-12 16:27:25 -0700 (Tue, 12 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

from types import ListType
from PyICU import Locale
import os, sys, locale, logging, gettext
import i18n
import wx

"""
TO DO:
1. Implement cache with thread lock
2. Create generic localeset fallback interface
3. Divide up class using plug in and interfaces to abstract the 
   PyICU and Wx specific calls. This will allow other projects to 
   leverage the code without requiring wx and PyICU
4. Rethink resource loading logic as it pertains to eggs.
5. Unit and functional tests need to setup locale before calling 
   translation service
6. When loading files into Chandler use the sys.filesystemencoding.
   When converting unicode to build filesystem paths use "utf8"
  
"""


__all__ = ["I18nManager"]
logger = logging.getLogger(__name__)

class I18nManager(object):
    DEFAULT_ROOT = "."
    RESOURCE_ROOT = "resources"
    IMAGE_PATH = "images"
    AUDIO_PATH = "audio"
    HTML_PATH = "html"
    #HELP_PATH = "help"

    __slots__ = ["_localeSet", "_defaultDomain", "_initialized", 
                 "_wxLocale", "_pyICULocale", "_cache", "_wxPath", "_rootPath"]

    def __init__(self, defaultDomain):
        super(I18nManager, self).__init__()
        assert isinstance(defaultDomain, str)

        self._cache = {"RESOURCES": {}, "TRANSLATIONS": {}}
        self._localeSet = []
        self._defaultDomain = defaultDomain
        self._initialized = False
        
        # Keep a reference to the Wx Locale and PyICU Locale
        # To ensure they do not get unloaded during the application
        # life cycle
        self._wxLocale = None
        self._pyICULocale = None

        self._wxPath = None
        self._rootPath = self.DEFAULT_ROOT

    def __repr__(self):
        return "I18nManager(%s, %s)" % (self._defaultDomain)

    def setRootPath(self, path):
        """
           Set the root path under which the I18nManager runs.
           This path is used to locale resources and 
           optionally is used as part of the wxTranslation 
           loading mechanism. If the root path is not explicitly
           set it defaults to "."

           @type path: unicode or str
           @param path: A filesystem path to the root directory that the
                        I18nManager is run under
        """
        assert(path is not None)

        if isinstance(path, unicode):
            path = path.encode("utf8")

        if not os.path.isdir(path):
            raise i18n.I18nException("Invalid root path %s" % path)

        self._rootPath = path

    def setWxPath(self, path):
        """
           Set the WxWidgets translation filesystem path.
           Under this path be the following structure:

           $LOCALE_NAME/LC_MESSAGES/wxstd.mo

           Setting the wxPath is optional. But 
           if not set the wx localizations files for 
           the "wxstd" domain will not be loaded.

           @type path: unicode or str
           @param path: A filesystem path to the directory
                        that contains the wx translations
        """
        assert(path is not None)

        if isinstance(path, unicode):
            path = path.encode("utf8")

        if not os.path.isdir(path):
            raise i18n.I18nException("Invalid wx path %s" % path)

        self._wxPath = path

    def flushCache(self):
        """
            Flushes the current resource path and translation per locale cache.
            This should be called when a locale set has been changed during runtime
            or to reload translations.
        """
        del self._cache
        self._cache = {"RESOURCES": {}, "TRANSLATIONS": {}}
        self._initialized = False

    def discoverLocaleSet(self):
        """
            Queries the Operating System for the current locale sets.
            The Operating System may return one or more locales. In the case
            where more than one locale is returned the translation fallback will
            try each locale in the set in order till a resource or translation is 
            encountered.

            For .7 only the primary locale will be used.
        """

        #     For .7 we will use wx to get the primary OS locale.
        #     PyICU does not return the correct value when calling
        #     Locale.getDefault(). For example, the Operating System is
        #     es_UY and PyICU returns en

        locale = wx.Locale(wx.LANGUAGE_DEFAULT).GetName()

        if locale is None:
            raise i18n.I18nException("Unable to retrieve default System Locale")

        self.setLocaleSet([locale])


    def setLocaleSet(self, localeSet=None):
        """
            Sets the current locale set for translation.

            @type localeSet: List
            @param localeSet: an ordered  List of locale strings
                              for example ['en_US', 'en']
        """

        assert isinstance(localeSet, ListType)
        assert len(localeSet) > 0

        #The 'test' locale is used in .7 for testing non-ascii translations
        #However in test mode, the French Canadian locale is leveraged by ICU.
        #This is done to test Chandler calendering support against 
        #a non-english locale.
        if 'test' in localeSet:
            self._localeSet = ['fr_CA', 'fr']
            self._localeSet.extend(localeSet)
        else:
            self._localeSet = localeSet

        #The primary locale from the command line or the OS
        locale = self._localeSet[0]

        if self._wxPath is not None:
            # If a wxPath was specified to the i18n manager then try and load
            # the wx localization catalog and set the wx locale

            #@bug 6017 Linux WxWidgets incorrecty 
            # reports an error setting a valid Locale :(
            # The UI does localize dialog buttons etc.
            # but those localization strings are coming
            # from the OS UI layer because the
            # I18nManager sets the LANG, LANGUAGE, 
            # LC_ALL and LC_MESSAGES environmental
            # variables.

            if os.name == 'nt' or sys.platform == 'darwin':
                self.__setWxLocale(locale)
                self.__loadWxTranslations()

        self.__setPyICULocale(locale)

        # Set the OS Environment
        os.environ['LANGUAGE'] = locale
        os.environ['LC_ALL'] = locale
        os.environ['LC_MESSAGES'] = locale
        os.environ['LANG'] = locale

        self._initialized = True

    def getLocaleSet(self):
        """
            Returns the current ordered locale set.

            @rtype: List
            @return: an ordered  List of locale strings 
                     for example ['en_US', 'en']
        """

        return self._localeSet

    def translate(self, domain, defaultText):
        """
            Performs localized translation of the defaultText key 
            based upon the locale set. The method access the 
            I18nManager cache to retrieve the translated string
            for defaultText key on the domain. The cache is 
            populated from gettext .mo translation files.
            The method employs the tradition locale set fallback mechanism
            and will search for a defaultText key for each
            locale in the ordered locale set until a match is
            found. If no match can be made the default
            english defaultText is returned.

            @type domain: ascii str
            @param domain: unique ascii domain name

            @type defaultText: unicode or ascii str
            @param defaultText: the unicode or ascii default key

            @rtype: unicode
            @return: The translated unicode string for key 
                     defaultText or defaultText itself if
                     no translation found.
        """

        assert isinstance(domain, str)
        assert isinstance(defaultText, unicode)

        #XXX This breaks hardhat commenting out
        #if not self._initialized:
        #    raise i18n.I18nException("translate called " \
        #                             "before locale set created")

        if 'test' in self._localeSet and not "Ctrl+" in defaultText \
                  and not "DELETE" == defaultText and not ":mm" in defaultText \
                  and not "yy" in defaultText and not "hh" in defaultText and not \
                  "0:00" in defaultText:
            # The 'test' locale is used return a unicode character at the
            # start of the defaultText block. However, if the text contains
            # accelerator key info or Date info return the default as 
            # changing it will cause errors.
            return u"(\u00FC): %s" % defaultText

        return defaultText


    def wxTranslate(self, defaultText):
        """
           Returns the translation for the current localeset for the
           WxWidgets "wxstd" domain.

           The WxWidgets localization path needs to be set
           prior to calling wxTranslate via the setWxPath method.
           Setting the wxPath tells the I18nManager how to 
           find the wxstd.mo translation files.

           If the wx path has not been set wxTranslate will raise a
           i18n.I18nException.

           @type defaultText: unicode
           @param defaultText: the unicode or ascii default key

            @rtype: unicode
            @return: The translated unicode string for key defaultText 
                      or defaultText itself if no translation found
        """

        #if not self._initialized:
        #    raise i18n.I18nException("wxTranslate called " \
        #                             "before locale set created")

        if self._wxPath is None:
            raise i18n.I18nException("The wx path must be set before calling " \
                                     "wxTranslate")

        wxTrans = wx.GetTranslation(defaultText)

        if 'test' in self._localeSet:
            return u"(\u00FC): %s" % wxTrans

        return wxTrans


    def getImage(self, fileName, domain=None):
        """
            Retrieves the localized image for the given domain.
            A folder structure based on the ordered locale set of the domain
            is searched for a image with the passed in fileName. When a match is
            found an open file object for the resource is returned. This path is
            then cached for future lookups. If no match is found for 
            the given locale set and no default file with the 
            fileName is found None is returned.

            @type fileName: unicode
            @param fileName: The name of the file to return

            @type domain: ASCII str
            @param domain: unique ASCII domain name

            @rtype: file or None
            @return: An open file handle to the resource or None if no file found
        """

        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, self.IMAGE_PATH, \
                                  fileName, domain)

    def getHTML(self, fileName, domain=None):
        """
            Retrieves the localized html file for the given domain.
            A folder structure based on the ordered locale set of the domain
            is searched for an html file with the passed in fileName. 
            When a match is found an open file object for the resource is
            returned. This path is then cached for future lookups. 
            If no match is found for the given locale set
            and no default file with the fileName is found None is returned.

            @type fileName: unicode
            @param fileName: The name of the file to return

            @type domain: ASCII str
            @param domain: unique ASCII domain name

            @rtype: file or None
            @return: An open file handle to the resource or None if no file found
        """

        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, self.HTML_PATH, \
                                  fileName, domain)

    def getAudio(self, fileName, domain=None):
        """
            Retrieves the localized audio file for the given domain.
            A folder structure based on the ordered locale set of the domain
            is searched for an audio file with the passed in fileName. 
            When a match is found an open file object for the 
            resource is returned. This path is then cached for 
            future lookups. If no match is found for the given locale set
            and no default file with the fileName is found None is returned.

            @type fileName: unicode
            @param fileName: The name of the file to return

            @type domain: ASCII str
            @param domain: unique ASCII domain name

            @rtype: file or None
            @return: An open file handle to the resource or None if no file found
        """

        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, self.AUDIO_PATH, \
                                fileName, domain)

    def getResource(self, relPath, fileName, domain=None):
        """
            Generic method for looking up localized resources.
            retrieves the localized file for the given domain 
            and relative file path. A folder structure based on 
            the ordered locale set of the domain is searched for 
            a resource with the passed in fileName. When a match is
            found an open file object for the resource is returned. 
            This path is then cached for future lookups. 
            If no match is found for the given locale set and 
            no default file with the fileName is found None is returned.

            @type relPath: unicode
            @param relPath: The relative file path in
                           relation to the domain file path

            @type fileName: unicode
            @param fileName: The name of the file to return

            @type domain: ASCII str
            @param domain: unique ASCII domain name

            @rtype: file or None
            @return: An open file handle to the resource or None if no file found
        """

        if domain is None:
            domain = self._defaultDomain

        return self.__getResource(self.RESOURCE_ROOT, \
                           relPath, fileName, domain)

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
            raise i18n.I18nException("Only OSAF domain supported")

        if rootPath is not None:
            root = os.sep.join([self._rootPath, rootPath,  relPath])
        else:
            root = os.sep.join([self._rootPath, relPath])

        res  = os.sep.join([root, resourceName])

        try:
            file = open(res, "rb")
        except IOError:
            return None

        return file

    def __setWxLocale(self, locale):
        lc = self.__getWxLocale(locale)

        if not lc.IsOk() and self.__hasCountryCode(locale):
            #Need to unload wx.Locale object otherwise it will
            #hold a dangling reference and not use the
            #Stripped Locale
            lc = None
            # Strip the country code and just use the language
            # For example wx does not have a translation for
            # 'es_UY' but does have one for 'es'
            lc = self.__getWxLocale(self.__stripCountryCode(locale))

        if not lc.IsOk():
            raise i18n.I18nException("Invalid wxPython Locale: '%s'" \
                                     % locale)

        self._wxLocale = lc

    def __getWxLocale(self, locale):
        # This is used to look up the wx Language integer code.
        # The code is needed to create a wx.Locale object.
        # For example the code for en_US is 58.
        # If FindLanguageInfo(locale) returns None then wx
        # does not support the requested locale or the lang / country
        # codes are invalid.

        langInfo = wx.Locale.FindLanguageInfo(locale)

        if langInfo is None:
            #The locale request is invalid or not supported by wx
            raise i18n.I18nException("Invalid wxPython Locale: '%s'" \
                                 % locale)

        #Get the wx Locale object for the ISO lang / country code
        return wx.Locale(langInfo.Language)

    def __loadWxTranslations(self):
        # The wxPython Locale.AddCatalogLookupPathPrefix method can
        # fail on non-ascii file paths. To work around this
        # the i18nManager manually changes the current directory
        # to the location of the wx translation files.

        try:
            os.chdir(self._wxPath)
            self._wxLocale.AddCatalog('wxstd')
            # Change the directory back
            os.chdir(self._rootPath)

            #self._wxLocale.AddCatalogLookupPathPrefix(self._wxPath)
        except OSError:
            raise i18n.I18nException("Unable to load wx translation files. " \
                                     "An invalid filesystem path was specified.")


    def __setPyICULocale(self, locale):

        if isinstance(locale, unicode):
            locale = locale.encode("utf8")

        locale = self.__stripEncodingCode(locale)

        lc = Locale(locale)

        if not self.__isValidPyICULocale(lc):
            raise i18n.I18nException("Invalid PyICU Locale: '%s'" \
                                     % locale)

        Locale.setDefault(lc)

    def __isValidPyICULocale(self, pyICULocale):
        for l in pyICULocale.getAvailableLocales():
            if str(l) == str(pyICULocale):
                return True

        return False

    def __convertPyICULocale(self, pyICULocale):
        if pyICULocale is None:
            return None

        langCode = pyICULocale.getLanguage()
        countryCode = pyICULocale.getCountry()

        if countryCode is not None:
            return "%s_%s" % (langCode, countryCode)

        return langCode

    def __setPythonLocale(self, locale):
        try:
            # Set the Python locale
            locale.setlocale(locale.LC_ALL, locale)
        except locale.Error:
            return False

        return True


    def __stripEncodingCode(self, locale):
        # A locale can contain additional
        # information beyond the two digit
        # language and country codes.
        # For example and encoding can be
        # specified: "en_US.UTF-8"
        # The encoding portion is not understood by
        # PyICU so we strip it.
         
        pos = locale.find(".")

        if pos != -1:
            return locale[0:pos]
       
        return locale

    def __stripCountryCode(self, locale):
        return locale.split('_')[0]

    def __hasCountryCode(self, locale):
        return len(locale) == 5 and locale[2] == '_'

