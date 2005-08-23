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
1. Implement cache withthread lock
2. Create generic localeset fallback interface
"""

OSAF_DOMAIN = "osaf"

class I18nManager(object):

    DEFAULT_LOCALE_SET = ["en_US"]
    RESOURCE_ROOT = u"resources"
    IMAGE_PATH = u"images"
    AUDIO_PATH = u"audio"
    HTML_PATH = u"html"
    #HELP_PATH = u"help"

    def __init__(self):
        super(I18nManager, self).__init__()
        self._localeSet = None
        self._cache = {"RESOURCES": {}, "TRANSLATIONS": {}}
        self._localeSet = None

    def __repr__(self):
        return "I18nManager()"

    def flushCache(self):
        del self._cache
        self._cache = {"RESOURCES": {}, "TRANSLATIONS": {}}

    def discoverLocaleSet(self, domain=OSAF_DOMAIN):
        #XXX: TO DO GET LocaleSet from OS
        self.setLocaleSet(self.DEFAULT_LOCALE_SET)


    def setLocaleSet(self, localeSet=None, domain=OSAF_DOMAIN):
        self.flushCache()

        assert isinstance(localeSet, ListType)
        assert len(localeSet) > 0

        self._localeSet = localeSet

        #XXX: Need to translate the locale i.e. "en_US'" to a
        #     wx.LANGUAGE key
        #wx.Locale(wx.LANGUAGE_ENGLISH)

        """Set the PyICU Locale"""
        Locale.setDefault(Locale(self._localeSet[0]))
        try:
            """Set the Python locale"""
            locale.setlocale(locale.LC_ALL, self._localeSet[0])
        except locale.Error:
            logging.error("Unable to set Python locale to: '%s'" % self._localeSet[0])

        """Set the OS Environment"""
        os.environ['LANGUAGE'] = self._localeSet[0]
        os.environ['LANG'] = self._localeSet[0]
        os.environ['LC_MESSAGES'] = self._localeSet[0]

    def getLocaleSet(self, domain=OSAF_DOMAIN):
        return self._localeSet

    def translate(self, domain, defaultText):
        assert isinstance(domain, StringType)
        assert isinstance(defaultText, UnicodeType)

        return defaultText

    def getImage(self, fileName, domain=OSAF_DOMAIN):
        return self.__getResource(self.RESOURCE_ROOT, self.IMAGE_PATH, fileName, domain)

    def getHTML(self, fileName, domain=OSAF_DOMAIN):
        return self.__getResource(self.RESOURCE_ROOT, self.HTML_PATH, fileName, domain)

    def getAudio(self, fileName, domain=OSAF_DOMAIN):
        return self.__getResource(self.RESOURCE_ROOT, self.AUDIO_PATH, fileName, domain)

    def getResource(self, relPath, fileName, domain=OSAF_DOMAIN):
        return self.__getResource(self.RESOURCE_ROOT, relPath, fileName, domain)

    #Reserved for future use. We will need a help lookup system
    #def getHelpFile(self, fileName, domain=OSAF_DOMAIN):
    #    return self.__getResource(None, self.HELP_PATH, fileName, domain)

    def __getResource(self, rootPath, relPath, resourceName, domain=OSAF_DOMAIN):
        """Will cache the path of the found resource
           for the given locale set.

           The cache will be flushed when a change to the
           locale set occurs
        """

        #XXX: These amy throw UnicodeDecodeErrors
        relPath = unicode(relPath)
        resourceName = unicode(resourceName)

        if domain != OSAF_DOMAIN:
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
