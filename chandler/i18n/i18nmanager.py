# -*- coding: utf-8 -*-
#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


from egg_translations import EggTranslations, hasCountryCode, stripCountryCode

from types import ListType, StringType, UnicodeType
from PyICU import Locale
from cStringIO import StringIO
import os, locale


"""
RULES:
===========
    1. When loading files into Chandler use the
       sys.filesystemencoding.  When converting unicode
       to build filesystem paths use "utf8"

THOUGHTS:
==========
   1. Could add a change locale dialog to i18n test menu

TO DO:
===========
   1. Do performance testing (are caches needed?) (Markku)

"""

# Keep a Global reference to the PyICU Locale
# To ensure it does not get unloaded during the
# application life cycle. There can be only one
# PyICU locale per Python instance
_PYICU_LOCALE = None

try:
    import wx
    _WX_AVAILABLE = True

    # Keep a Global reference to the Wx Locale
    # To ensure that it does not get unloaded during the
    # application life cycle. There can be only one
    # Wx locale le per Python instance
    _WX_LOCALE = None


    __all__ = ["I18nManager", "setEnvironmentLocale", "getPyICULocale",
               "setPythonLocale", "convertPyICULocale",
               "isValidPyICULocale", "setPyICULocale", "I18nException",
               "setWxLocale", "getWxLocale", "findWxLocale", "wxIsAvailable"]
except:
    _WX_AVAILABLE = False
    __all__ = ["I18nManager", "setEnvironmentLocale", "getPyICULocale",
               "setPythonLocale", "convertPyICULocale",
               "isValidPyICULocale", "setPyICULocale", "I18nException", "wxIsAvailable"]

def wxIsAvailable():
    global _WX_AVAILABLE

    if _WX_AVAILABLE:
        return wx.GetApp() is not None

    return False


class I18nManager(EggTranslations):
    _NAME = "I18nManager"

    __slots__ = ["_testing", "_lookupCache", "_wx_filehandler",
                 "_DEFAULT_PROJECT", "_DEFAULT_CATALOG", "_DEFAULT_IMAGE",
                 "_DEFAULT_HTML"]

    def __init__(self, DEFAULT_PROJECT, DEFAULT_CATALOG,
                 DEFAULT_IMAGE, DEFAULT_HTML):

        super(I18nManager, self).__init__()

        assert(type(DEFAULT_PROJECT) == StringType or
               type(DEFAULT_PROJECT) == UnicodeType)

        assert(type(DEFAULT_CATALOG) == StringType or
               type(DEFAULT_CATALOG) == UnicodeType)

        assert(type(DEFAULT_IMAGE) == StringType or
               type(DEFAULT_IMAGE) == UnicodeType)

        assert(type(DEFAULT_HTML) == StringType or
               type(DEFAULT_HTML) == UnicodeType)

        self._DEFAULT_PROJECT = DEFAULT_PROJECT
        self._DEFAULT_CATALOG = DEFAULT_CATALOG
        self._DEFAULT_IMAGE   = DEFAULT_IMAGE
        self._DEFAULT_HTML    = DEFAULT_HTML

        self._lookupCache = None
        self._wx_filehandler = None
        self._testing = False

    def __repr__(self):
        return "I18nManager(%s, %s, %s, %s)" % (
                                self._DEFAULT_PROJECT,
                                self._DEFAULT_CATALOG,
                                self._DEFAULT_IMAGE,
                                self._DEFAULT_HTML)


    def initialize(self, localeSet=None, iniFileName="resources.ini",
                   encoding="UTF-8", fallback=True):
        """
        The initialize method performs the following operations:

            1. Calls the c{pkg_resources.add_activation_listener}
               method passing the c{I18nManager._parseINIFiles}
               method as the callback. See the parseINIFiles method
               for more info on loading resources and
               gettext translation files.

            2. Calls the I18nManager's setLocaleSet method
               passing the localeSet param. See the setLocaleSet
               method documentation for more info.

            3. Registers the I18nManager as a wxPython
               Filesystem handler for loading images,
               html, and resources by wxPython from
               Python eggs.

            The initialize method sets the locale set and loads the
            resource and translation caches.

            It must be called before using the I18nManager API.

            The initialize method can only be called once per
            I18nManager instance.

        The initialize method can raise the following exceptions:
            1. c{INIParsingException}
            2. c{LookupError}
            3. c{UnicodeDecodeError}
            4. c{UnicodeEncodeError}

        @param localeSet: A c{unicode} or c{str}  or c{List}
                          containing locale country and language
                          codes. The value(s) must be able to
                          be converted to ASCII.

        @type localeSet: ASCII c{str} or c{unicode} or
                         c{List} containing ASCII c{str}
                         or c{unicode} values

        @param iniFileName: The name of the resource ini file
                            in the egg's info directory.

                             This file contains the location of
                             localized and non-localized resources
                             as well as translation files in gettext
                             mo format.  The default value for this
                             file is "resources.ini". If a c{str}
                             is passed it must be able to be
                             converted to c{unicode} using the
                             encoding passed to the initialize
                             method. The default encoding
                             is "UTF-8".

         @type iniFileName: ASCII c{str} or c{unicode}

         @param encoding: The character set encoding of the
                          iniFileName. This encoding will be
                          used to convert c{str} values contained
                          in the iniFileName to c{unicode}.
                          The default encoding is "UTF-8".

         @type encoding: ASCII c{str} or c{unicode}

         @param fallback: Indicates whether locale set fallback should
                          take place. If set to True, the
                          I18nManager will search all locales
                          in the locale set till a resource or
                          gettext mo translation file is found. If
                          set to False the I18nManager will
                          only try to locate a resource or
                          gettext mo translation file for the
                          current locale which is the first locale
                          in the locale set.


          @type fallback: c{boolean}
        """

        super(I18nManager, self).initialize(localeSet, iniFileName,
                                            encoding, fallback)

        if wxIsAvailable():
            self._wx_filehandler = I18nFileSystemHandler(self)
            wx.FileSystem.AddHandler(self._wx_filehandler)

    def discoverLocaleSet(self):
        """
         Queries the Operating System for the current locale sets.
         The Operating System may return one or more locales.

         In the case where more than one locale is returned
         the translation fallback will try each locale in the set
         in order till a resource or translation is encountered.

         Note: For Preview only the primary locale will be used.

         The discoverLocaleSet method can raise the following
         exceptions:
            1. c{I18nException}

         @return: c{str} The Operating System primary locale

        """

        assert(self._init, True)

        if wxIsAvailable():
            locale = I18nLocale(wx.LANGUAGE_DEFAULT, i18nMan=self).GetName()
        else:
            locale = Locale.getDefault().getName()

        if locale is None:
            raise I18nException("Unable to retrieve default " \
                                "System Locale")
        return locale

    def setLocaleSet(self, localeSet=None, fallback=True):
        """
        Resets the c{I18nManager locale set c{List}.

        Resetting the locale set includes unloading all gettext
        .mo translations, loading the the gettext .mo translations
        for the current locale set, and setting the gettext locale
        fallback order if the fallback parameter is set to True.

        Note the initial locale set for the c{I18nManager}
        must be set in the C{I18nManager.initialize}
        method.

        Note, setting the c{I18nManager} locale set
        also adds the language code as a fallback for language /
        county code locale definitions when fallback is set to True.
        If the locale set contains 'fr_CA' this method will also add
        to the locale set 'fr' as a fallback for 'fr_CA'.

        If no localeSet is passed the discoverLocaleSet
        method will be called to retrieve the
        locale set of the Operating System.

        A locale of 'test' can be passed to this method.

        The 'test' locale is a debug keyword
        which sets the locale set to ['fr_CA', 'fr']
        and enables the testing mode flag.

        In testing mode all values returned by
        the c{I18nManager.getText} method insert
        a (\u00FC): at the start of the string.
        All values returned by the c{I18nManager.wxTranslate}
        method return (WX): at the start of the
        string.

        This method sets the following:
           1. The PyICU Locale
           2. The wxPython Locale
           3. The Python Locale
           4. The Operating System Enviroment Locale

        The setLocaleSet method can raise the following exceptions:
            1. c{UnicodeEncodeError}
            2. c{NameError}
            3. c{I18nException}

        @param localeSet: A c{unicode} or c{str}  or c{List}
                          containing locale country and language
                          codes. The value(s) must be able to
                          be converted to ASCII. If None
                          is passed the setLocaleSet method
                          will call the discoverLocaleSet
                          method to retrieve the Operating
                          System locale set.

        @type localeSet: None or ASCII c{str} or c{unicode} or
                         c{List} containing ASCII
                         c{str} or c{unicode} values

         @param fallback: Indicates whether locale set fallback should
                          take place. If set to True, the
                          c{I18nManager} will search all locales
                          in the locale set till a resource or
                          gettext mo translation file is found. If
                          set to False the c{I18nManager} will
                          only try to locate a resource or
                          gettext mo translation file for the
                          current locale which is the first locale
                          in the locale set.


          @type fallback: c{boolean}
        """
        self._testing = False

        discover = localeSet is None

        if discover:
            localeSet = self.discoverLocaleSet()

        else:
            assert(type(localeSet) == ListType or
                   type(localeSet) == UnicodeType or
                   type(localeSet) == StringType)

            if 'test' in localeSet:
                localeSet = ['fr_CA', 'fr']
                self._testing = True

        super(I18nManager, self).setLocaleSet(localeSet, fallback)

        if discover:
            # The Chandler gettext strings are written in English.
            # If there is not an .mo translation file loaded for any
            # of the locales in the locale set then default to
            # English to prevent wxPython and PyICU from localizing
            # while Chandler is displaying English text.
            primaryLocale = "en_US"

            if fallback:
                for lc in self._localeSet:
                    if self.hasTranslation(self._DEFAULT_PROJECT, self._DEFAULT_CATALOG, lc):
                        primaryLocale = lc
                        break

            else:
                lc = self._localeSet[0]

                if self.hasTranslation(self._DEFAULT_PROJECT, self._DEFAULT_CATALOG, lc):
                    primaryLocale = lc

        else:
            # If one of more locales are passed
            # (command line) then set the
            # locale of PyICU, wxPython, and
            # Python regardless of whether
            # Chandler provides a localization.
            primaryLocale = self._localeSet[0]

        if wxIsAvailable():
            setWxLocale(primaryLocale, self)

        setPyICULocale(primaryLocale)
        setPythonLocale(primaryLocale)
        setEnvironmentLocale(primaryLocale)

        # Reset the resource lookup cache
        self._lookupCache = None
        self._lookupCache = {}

    def getText(self, project, name, txt, *args):
        """
        Returns a c{unicode} string containing the localized
        value for key txt in the given project. The name
        parameter points to a key in a resource ini file that
        contain a value entry pointing to a gettext .mo
        resource in the same egg.

        An optional additional argument can be specified as the
        default value to return if no localized is found.

        The txt parameter will be returned by
        c{I18nManager.getText} if no localized value found
        for the txt parameter.

        However, if the default value argument is passed,
                 that value will be returned instead of text.

        Example where there in no localized value for
        txt parameter "Hello World":

            >>> i18nInstance.getText("MyProject", "catalog",
            ...                      "Hello World")
            u'Hello World'
            >>>
            >>> i18nInstance.getText("MyProject", "catalog",
            ...                       "Hello World",
            ...                        None)
            None
            >>>

        If fallback was set to True in the
        c{I18nManager.initialize} method or the
        c{I18nManager.setLocaleSet} method, the
        c{I18nManager.getText} method will search all
        locales in the locale set till a gettext mo
        translation is found for the txt parameter.

        If fallback was set to False in the
        c{I18nManager.initialize} method
        or the c{I18nManager.setLocaleSet} method, the
        c{I18nManager.getText} method will only search
        the current locale, which is the first locale in the
        locale set for a gettext mo translation for
        the txt parameter.

        Note that the "all" default locale can not
        contain any key value pairs that point to gettext
        .mo files.

        If a .mo gettext value is found in the "all" default
        locale, the .mo file will not be loaded by
        the c{I18nManager}.


        Example:
           A resource.ini file contains the following line:
              [MyProject::fr]
              catalog = locale/fr/MyProject.mo

           The locale/fr/myproject.mo file contains a
           localization of "Hello" to "Bonjour".

           >>> i18nInstance.initialize("fr")
           >>> i18nInstance.getText("MyProject", "catalog",
           ...                      "Hello")
           u'Bonjour'

        In testing mode all values returned by the
        c{I18nManager.getText} method insert
        a (\u00FC): at the start of the string.

        The getText method can raise the following exceptions:
            1. c{UnicodeDecodeError}

        @param project: A project is a root namespace under which
                        resources and localizations exist.

                        A project name matches an egg name.
                        An egg's info file can contain resource
                        and localizations for more than one project.

                        The project name must be either an ASCII
                        c{str} or c{unicode}.

         @type project: ASCII c{str} or c{unicode}

         @param name: name is the key to lookup in
                      a resource ini file to retrieve the
                      value specifed. For example,
                      myname = this is my value.

                      The name must be either an ASCII
                      c{str} or c{unicode}.

         @type name: ASCII c{str} or c{unicode}

         @param txt: The default text string which is used
                     as look up key to retrieve a localized
                     value from a gettext .mo file.

                     The default text string is usual
                     the English version of the text. The
                     .mo gettext files will contain
                     localizations of the English version
                     with the English version as the key.

         @param txt: The default text string which is used
                     as look up key to retrieve a localized
                     value from a gettext .mo file.

                     The default text string is usual
                     the English version of the text. The
                     .mo gettext files will contain
                     localizations of the English version
                     with the English version as the key.

         @type txt: ASCII c{str} or c{unicode}

        @param args: An optional argument which if passed
                     will be returned if no localzation
                     found for txt. The type of the
                     return value in the args list 
                     has no limitations.
        @type args:  c{list}

        @return: c{unicode} localized text or
                 either the original txt argument
                 or the default value in args if no
                 localization found.
        """

        if not self._init:
            from application import Globals
            self.initialize(Globals.options.locale)

        res = super(I18nManager, self).getText(project, name, txt, *args)

        #If the additional argument passed to getText is
        #the same as res meaning no translation was found
        #then do not add u"(\u00FC):" to it.
        ignore = args and args[0] == res

        if self._testing \
           and not ignore \
           and not "Ctrl+" in res \
           and not "DELETE" == res \
           and not "Del" == res \
           and not ":mm" in res \
           and not "yy" in res \
           and not "hh" in res \
           and not "0:00" in res:
             return u"(\u00FC): %s" % res

        return res


    def wxTranslate(self, txt):
        """
        Returns the current locale set translation for the
        WxWidgets "wxstd" domain.

        @param txt: The unicode or ASCII default key to
                    translation
        @type txt: ASCII c{str} or c{unicode}

        @rtype: c{unicode}
        @return: The translated unicode string for key txt
                  or txt if no translation found
        """
        assert(self._init, True)

        if wxIsAvailable():
            res = wx.GetTranslation(txt)
        else:
            res = txt

        if self._testing:
            return u"(WX): %s" % res

        return res


    def getImage(self, file_name, project=None, img_dir_name=None):
        """
        Retrieves the localized image for the given project.
        The getImage is a convience method that differs from
        getResourceAsStream.

        With getImage no images are registered in the
        resource ini file. Instead a resource directory
        key is registered with a value pointing to
        a directory in the egg containing image resources.

        This path is then searched by the c{I18nManager}
        till an image matching file_name is found
        for the given locale set.

        if fallback was set to False in the c{I18nManager.initialize}
        or the c{I18nManager.setLocale} methods then
        only the first locale in the locale set is
        scanned for an image matching file_name.

        Example resource ini registration:

          [MyProject::all]
          imgs.resources = resource_directory/images/

          [MyProject::fr]
          imgs.resources = locale/fr/resource_directory/images/

        Retrieving the localized image "test.png":

          >>> i18nInstance.setLocaleSet("fr")
          >>> i = i18nInstance.getImage("test.png", "MyProject",
          ...                           "imgs.resources")

       The above will first scan the
       locale/fr/resource_directory/images/ in the egg
       for a file named "test.png". If found a handle to this
       file is returned. Otherwise fallback is employed
       and the 'all' resource_directory/images/ is searched
       for a file named "test.png". If the file is found
       a c{file} handle is returned otherwise None.

       Once the location of a image is found for the
       given localeSet that location is cached so
       subsequent requests for the same image do
       not result in scanning of the egg for a localized
       file name match.

       if no project argument is passed the
       c{I18nManager._DEFAULT_PROJECT is used.

       if no img_dir_name argument is passed the
       c{I18nManager._DEFAULT_IMAGE is used.

       A sub directory path can alos be past. For example,
       a valid file_name can be "my_sub_dir/test.png".
       the img_dir_name value will be combined with the file_name
       value and the "my_sub_dir" under the img_dir_name
       value will be searched for a file named "test.png"

       However, this sub directory path must only contain "/"
       separators and not Windows "\\" separators
       as the underlying egg API is platform independent
       and does not recognize "\\" as a path separator.

       The getImage method can raise the following exceptions:
         1. c{UnicodeDecodeError}
         2. c{UnicodeDecodeError}

       @param file_name: the file name of the image to
                         retrieve. This image file
                         must be in the same egg as
                         its resource ini definition.

       @type file_name: ASCII c{str} or c{unicode}

       @param project: A project is a root namespace under which
                       resources and localizations exist.

                       A project name matches an egg name.
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project name must be either an ASCII
                       c{str} or c{unicode}. If no project is
                       specified the c{I18nManager._DEFAULT_PROJECT}
                       is used.


         @type project: ASCII c{str} or c{unicode}

         @param img_dir_name: The named key in a resource ini
                              file whose value points to a
                              directory in the egg that
                              contains image resources.
                              The img_dir_name must be either
                              an ASCII c{str} or c{unicode}.
                              If no img_dir_namme is specified
                              the c{I18nManager._DEFAULT_IMAGE}
                              is used.

         @type img_dir_name: ASCII c{str} or c{unicode}


         @return: An c{file} handle to the image resource or None
        """

        assert(self._init, True)

        if project is None:
            project = self._DEFAULT_PROJECT

        if img_dir_name is None:
            img_dir_name = self._DEFAULT_IMAGE

        return self._findResource(file_name, project, img_dir_name)


    def getHTML(self, file_name, project=None, html_dir_name=None):
        """
        Retrieves the localized html for the given project.
        The getHTML is a convience method that differs from
        getResourceAsStream.

        With getHTML no html files are registered in the
        resource ini file. Instead a resource directory
        key is registered with a value pointing to
        a directory in the egg containing html resources.

        This path is then searched by the c{I18nManager}
        till an html file matching file_name is found
        for the given locale set.

        if fallback was set to False in the c{I18nManager.initialize}
        or the c{I18nManager.setLocale} methods then
        only the first locale in the locale set is
        scanned for an html file matching file_name.

        Example resource ini registration:

          [MyProject::all]
          html.resources = resource_directory/html/

          [MyProject::fr]
          html.resources = locale/fr/resource_directory/html/

        Retrieving the localized html "test.html":

          >>> i18nInstance.setLocaleSet("fr")
          >>> h = i18nInstance.getHTML("test.html", "MyProject",
          ...                           "html.resources")

       The above will first scan the
       locale/fr/resource_directory/html/ in the egg
       for a file named "test.html". If found a handle to this
       file is returned. Otherwise fallback is employed
       and the 'all' resource_directory/html/ is searched
       for a file named "test.html". If the file is found
       a c{file} handle is returned otherwise None.

       Once the location of a html file is found for the
       given localeSet that location is cached so
       subsequent requests for the same html do
       not result in scanning of the egg for a localized
       file name match.

       if no project argument is passed the
       c{I18nManager._DEFAULT_PROJECT is used.

       if no html_dir_name argument is passed the
       c{I18nManager._DEFAULT_HTML is used.

       A sub directory path can alos be past. For example,
       a valid file_name can be "my_sub_dir/test.html".
       the img_dir_name value will be combined with the file_name
       value and the 'my_sub_dir" under the html_dir_name
       value will be searched for a file named "test.html"

       However, this sub directory path must only contain "/"
       separators and not Windows "\\" separators
       as the underlying egg API is platform independent
       and does not recognize "\\" as a path separator.

       The getHTML method can raise the following exceptions:
         1. c{UnicodeDecodeError}
         2. c{UnicodeDecodeError}

       @param file_name: the file name of the html to
                         retrieve. This html file
                         must be in the same egg as
                         its resource ini definition.

       @type file_name: ASCII c{str} or c{unicode}

       @param project: A project is a root namespace under which
                       resources and localizations exist.

                       A project name matches an egg name.
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project name must be either an ASCII
                       c{str} or c{unicode}. If no project is
                       specified the c{I18nManager._DEFAULT_PROJECT}
                       is used.


         @type project: ASCII c{str} or c{unicode}

         @param html_dir_name: The named key in a resource ini
                              file whose value points to a
                              directory in the egg that
                              contains image resources.
                              The html_dir_name must be either
                              an ASCII c{str} or c{unicode}.
                              If no html_dir_namme is specified
                              the c{I18nManager._DEFAULT_HTML}
                              is used.

         @type html_dir_name: ASCII c{str} or c{unicode}


         @return: An c{file} handle to the html resource or None
        """

        assert(self._init, True)

        if project is None:
            project = self._DEFAULT_PROJECT

        if html_dir_name is None:
            html_dir_name = self._DEFAULT_HTML

        return self._findResource(file_name, project,
                                  html_dir_name)


    def _findResource(self, file_name, project, res_dir_name):
        if type(file_name) == StringType:
            file_name = unicode(file_name)

        if type(project) == StringType:
            project = unicode(project)

        if type(res_dir_name) == StringType:
            res_dir_name = unicode(res_dir_name)

        assert(type(file_name) == UnicodeType)
        # Make sure no Windows paths were passed in.
        # The pkg_resources API will normalize paths
        # for the appropriate OS.
        assert(u"\\" not in file_name)

        assert(type(project) == UnicodeType)
        assert(type(res_dir_name) == UnicodeType)

        key = (project, res_dir_name, file_name)

        if key in self._lookupCache:
            # We have either a path to a resource or
            # None cached.
            dist, res_path = self._lookupCache[key]

            if dist:
                return StringIO(dist.get_metadata(res_path))

            return None

        if not self._fallback:
            dist, res_path  = self._getResource(file_name, project,
                                             res_dir_name,
                                             self._localeSet[0])

            self._lookupCache[key] = (dist, res_path)

            if dist:
                return StringIO(dist.get_metadata(res_path))

            return None

        for locale in self._localeSet:
            dist, res_path = self._getResource(file_name, project,
                                            res_dir_name, locale)

            if dist:
                self._lookupCache[key] = (dist, res_path)
                return StringIO(dist.get_metadata(res_path))

        dist, res_path = self._getResource(file_name, project,
                                           res_dir_name, 'all')

        self._lookupCache[key] = (dist, res_path)

        if dist:
            return StringIO(dist.get_metadata(res_path))

        return None


    def _getResource(self, file_name, project, res_dir_name, locale):

        tup = self._getTupleForKey(project, res_dir_name,
                                   locale)

        if tup:
            dist, res_dir_path = tup
            res_path = res_dir_path + u"/" + file_name

            res_path = res_path.encode(self._iniEncoding)
            if dist.has_metadata(res_path):
                return (dist, res_path)

        return (None, None)


def getPyICULocale():
    """
      Returns the current PyICU
      Locale object of None

      @return: a c{PyICU.Locale} object or None
    """
    global _PYICU_LOCALE
    return _PYICU_LOCALE

def setPyICULocale(locale):
    """
      Sets the c{PyICU.Locale} to the value passed in
      c{str} locale argument.

      If the locale passed in not a valid / supported
      PyICU locale a c{I18nException} is raised.

      @param locale: a c{str} locale
      @type locale: ASCII c{str}

    """
    lc = Locale(locale)

    if not isValidPyICULocale(lc):
        raise I18nException("Invalid PyICU Locale: '%s'" \
                                 % locale)

    Locale.setDefault(lc)

    # Store a reference to the PyICU Locale instance
    global _PYICU_LOCALE
    _PYICU_LOCALE = lc

def isValidPyICULocale(locale):
    """
      Returns True if the locale string passed
      is in the list of available PyICU locales
      otherwise false.

      @param locale: a c{str} locale
      @type locale: ASCII c{str}

      @return: c{boolean} True if a valid PyICU locale
               otherwise False
    """

    for l in locale.getAvailableLocales():
        if str(l) == str(locale):
            return True

    return False

def convertPyICULocale(iculocale):
    """
      Converts a c{PyICU.Locale} to a
      ISO c{str} representation of the locale.

      @param iculocale: A PyICU locale instance
      @type iculocale: c{PyICU.Locale}

      @return: c{str} ISO locale code
    """
    assert(isinstance(iculocale, Locale))

    langCode = iculocale.getLanguage()
    countryCode = iculocale.getCountry()

    if countryCode is not None:
        return "%s_%s" % (langCode, countryCode)

    return langCode

def setPythonLocale(lc):
    """
      Sets the Python locale object to
      the value in lc.

      @param locale: a c{str} locale
      @type locale: ASCII c{str}
    """
    try:
        # Set the Python locale
        locale.setlocale(locale.LC_ALL, lc)
    except locale.Error:
       pass

def setEnvironmentLocale(locale):
    """
      Sets the Operating System environmental
      variables LANG, LC_ALL, LC_MESSAGES, and
      LANGUAGE to the value contained in
      locale

      @param locale: a c{str} locale
      @type locale: ASCII c{str}
    """
    os.environ['LANGUAGE'] = locale
    os.environ['LC_ALL'] = locale
    os.environ['LC_MESSAGES'] = locale
    os.environ['LANG'] = locale


class I18nException(Exception):
    pass

if _WX_AVAILABLE:
    def getWxLocale():
        """
          Returns the current wxPython
          Locale object or None

          @return: a c{wx.Locale} object or None
        """

        global _WX_LOCALE
        return _WX_LOCALE

    def setWxLocale(locale, i18nMan):
        """
          Sets the c{wx.Locale} to the value passed in
          c{str} locale argument.

          If the locale passed is not a valid wx locale and
          and that locale consists of a lang and country code,
          the country code is stripped and the lang code
          is set as the c{wx.Locale}.

          This logic is employed in the cases such as "es_UY"
          where wxPython does not have a translation for
          'es_UY' but does have one for 'es'.

          If the locale is still not valid after attempting to
          use just the lang code a c{I18nException} is raised.

          @param locale: a c{str} locale
          @type locale: ASCII c{str}
        """

        # Need to unload wx.Locale object otherwise it will
        # hold a dangling reference and not use the new Locale
        global _WX_LOCALE
        _WX_LOCALE = None

        lc = findWxLocale(locale, i18nMan)

        if not lc.IsOk() and hasCountryCode(locale):
            # Need to unload wx.Locale object otherwise it will
            # hold a dangling reference and not use the
            # Stripped Locale

            lc = None

            # Strip the country code and just use the language
            # For example wx does not have a translation for
            # 'es_UY' but does have one for 'es'

            lc = findWxLocale(stripCountryCode(locale), i18nMan)

        if not lc.IsOk():
            raise I18nException("Invalid wxPython Locale: " \
                                     "'%s'" % locale)

        # Keep a Global reference to the Wx Locale
        # To ensure it does not get unloaded during the
        # application life cycle. There can be only one
        # wx locale per Python instance
        _WX_LOCALE = lc

    def findWxLocale(locale, i18nMan):
        """
          Looks up the wx Language integer code.
          The code is needed to create a c{wx.Locale} object.

          For example the code for "en_US" is 58.

          If c{wx.FindLanguageInfo(locale)} returns None then wx
          does not support the requested locale or the lang / country
          codes are invalid.

          the findWxLocale method can raise the following exceptions:
                1. c{I18nException}

          @param locale: a c{str} locale
          @type locale: c{str}

          @return: a c{wx.Locale} object
        """

        assert(isinstance(i18nMan, I18nManager))

        langInfo = I18nLocale.FindLanguageInfo(locale)

        if langInfo is None:
            #The locale request is invalid or not supported by wx
            raise I18nException("Invalid wxPython Locale: " \
                                     "'%s'" % locale)

        #Get the wx Locale object for the ISO lang / country code
        return I18nLocale(langInfo.Language, i18nMan=i18nMan)


    class I18nFileSystemHandler(wx.FileSystemHandler):
        def __init__(self, i18nMan):
            assert(isinstance(i18nMan, I18nManager))

            super(I18nFileSystemHandler, self).__init__()
            self.i18nMan = i18nMan

        def CanOpen(self, location):
            """
              Called by wxPython to determine if
              the c{I18nFileSystemHandler} can open a given
              file type.

              If the protocol passed in the location
              is either "image", "html", or "resource"
              and the name passed in the location points
              to a valid resource, image, or html in an
              egg then return True otherwise False.

              The location syntax is:
              project#type:name

              project is name of the egg project.
              If no project is passed i.e. "type:name"
              then the I18nManager._DEFAULT_PROJECT is
              used.

              type is the type of the resource.

              if type == image the c{I18nManager.getImage}
              method is used.

              if type == html the c{I18nManager.getHTML}
              method is used.

              if type == resource the c{I18nManager.getResourceAsStream}
              method is used.

              @param location: the project#type:name c{str}
              @type location: c{str}

              @return: c{boolean} True if the I18nManager can open
                      the file type otherwise False.
            """

            assert(self.i18nMan._init, True)

            project = self.GetLeftLocation(location)
            name = self.GetRightLocation(location)
            protocol = self.GetProtocol(location).lower(
                                                 ).strip()

            if protocol == "image":
                img = self.i18nMan.getImage(name, project and project or None)
                return img is not None

            if protocol == "html":
                html = self.i18nMan.getHTML(name, project and project or None)
                return html is not None

            if protocol == "resource":
                project = project and project or self.i18nMan._DEFAULT_PROJECT
                return self.i18nMan.hasResource(project, name)

            return False

        def OpenFile(self, fs, location):
            """
              Returns a c{file} handle to
              an "image", "html", or "resource"
              contained in an egg.

              @param fs: wx FileSystem object
              @type fs: c{wx._core.FileSystem}

              @param location: the project#type:name c{str{
              @type location: c{str}

              @return: c{file} handle
            """

            assert(self.i18nMan._init, True)

            protocol = self.GetProtocol(location).lower(
                                                 ).strip()

            # If blank use the _DEFAULT_PROJECT
            project = self.GetLeftLocation(location)
            name = self.GetRightLocation(location)
            mime = self.GetMimeTypeFromExt(location)

            if protocol == "image":
                return wx.FSFile(self.i18nMan.getImage(name,
                                 project and project or None),
                                 location, mime, "", wx.DateTime.Now())

            if protocol == "html":
                return wx.FSFile(self.i18nMan.getHTML(name,
                                 project and project or None),
                                 location, mime, "", wx.DateTime.Now())

            if protocol == "resource":
                project = project and project or self.i18nMan._DEFAULT_PROJECT
                return wx.FSFile(self.i18nMan.getResourceAsStream(project, name),
                                 location, mime, "", wx.DateTime.Now())

            return None

    class I18nLocale(wx.PyLocale):
        def __init__(self, language=-1, flags=wx.LOCALE_LOAD_DEFAULT|wx.LOCALE_CONV_ENCODING,
                     i18nMan=None):
            wx.PyLocale.__init__(self, language, flags)
            assert(isinstance(i18nMan, I18nManager))
            self.i18nMan = i18nMan

        def GetSingularString(self, txt, project=None):
            if txt is None or len(txt.strip()) == 0:
                return u""

            msg = missing = object()

            if project is None or len(project.strip()) == 0:
                project = self.i18nMan._DEFAULT_PROJECT

            msg = self.i18nMan.getText(project, self.i18nMan._DEFAULT_CATALOG,
                                       txt, missing)

            if msg is missing:
                msg = wx.GetTranslation(txt)

            return msg

    #    # this handler captures all plural translation requests
    #    def GetPluralString(self, txt, txt2, n, project=None):
    #        pass
