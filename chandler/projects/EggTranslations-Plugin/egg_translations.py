#!/bin/env python
# -*- coding: utf-8 -*-

#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

"""
Egg Translations Management Package

@author:    Brian Kirsch - bkirsch@osafoundation.org
@author:    Markku Mielityinen - mmmm@osafoundation.org
@copyright: Copyright (c) 2003-2006 Open Source Applications Foundation
@license:   Apache License, Version 2.0
"""

__all__ = ["DefaultTranslations", "EggTranslations", "hasCountryCode",
           "stripCountryCode", "stripEncodingCode", 
           "isValidLocaleForm", "normalizeLocale",
           "buildFallbackLocales", "logger"]

import pkg_resources
from cStringIO import StringIO
import types
import sys
from gettext import GNUTranslations
import logging

logger = logging.getLogger(__name__)

class INIParsingException(Exception):
    pass

class DefaultTranslations(GNUTranslations):
    def ugettext(self, message, *args):
        if not args:
            return GNUTranslations.ugettext(self, message)

        missing = object()
        tmsg = self._catalog.get(message, missing)

        if tmsg is missing:
            if self._fallback:
                return self._fallback.ugettext(message, args[0])
           
            # return the default value not the message value
            # as GNUTranslations does.
            return args[0]

        return tmsg

"""
NEXT:
      1. Update API documentation for exceptions, project vs. domain,
         etc.
      2. Think about log file use with an .egg zip format
      3. API takes only unicode or ascii


LATER:
      1. Overwrite of a key ie domain, name, locale
         should print a warning.

      2. Only one definition of a locale in a 
         resource file per project can't have
         [myproject::fr_CA, fr] then later [myproject::fr].
         Need to error or print warning.

      3. Clean up debug logging messages to be less
         verbose and more useful.

      4. Make sure at least one locale passed in 
         locale set.
"""

class EggTranslations(object):

    __slots__ = ["_init", "_iniFileName", "_localeSet", "_fallback",
                 "_iniCache", "_gtCache", "_moCache", "_iniEncoding"]

    _NAME = "EggTranslations"

    def __init__(self):
        super(EggTranslations, self).__init__()   

        # Flag indicating whether the initialize method
        # has been called
        self._init = False

        self._iniFileName = None
        self._iniEncoding = None

        self._localeSet = None
        self._fallback = False

        # Cache for key values pairs in ini file.
        # Persists for the life of the EggTranslations 
        # instance.
        self._iniCache = {}

        # Cache for the file path to gettext .mo localizations.
        # Persists for the life of the EggTranslations 
        # instance.
        self._moCache = {}

        # Holds the EggTranslations for locale set.
        # Is flushed when the locale set changes.
        self._gtCache = {}


    def initialize(self, localeSet, iniFileName="resources.ini", 
                   encoding="UTF-8", fallback=True):
        """
        #XXX Raises LookupError
        The initialize method performs the following operations:

            1. Calls the c{pkg_resources.add_activation_listener} method 
               passing the c{EggTranslations._parseINIFiles} method
               as the callback. See the parseINIFiles method for 
               more info on loading resources and gettext translation files.


            2. Calls the EggTranslations's setLocaleSet method passing the  
               localeSet param. See the setLocaleSet method documentation for 
               more info.

            The initialize method sets the locale set and loads the 
            resource and translation caches. 

            It must be called before using the EggTranslations API.

            The initialize method can only be called once per EggTranslations
            instance.

        @param localeSet: A String or List containing locale country 
                          and language codes

        @type localeSet: c{str} or c{unicode} or c{List} containing c{str} 
                         or c{unicode} values

        @param iniFileName: The name of the resource ini file in the egg's
                             info directory.

                             This file contains the location of localized 
                             and non-localized resources
                             as well as translation files in gettext mo format. 
                             The default value for this file is "resources.ini".
 
         @type iniFileName: c{str} or c{unicode}

         @param fallback: Indicates where locale set fallback should 
                          take place. If set to True, the EggTranslations 
                          will search all locales in the locale set till a 
                          resource or gettext mo translation file is found. If
                          set to False the EggTranslations will only try to
                          locate a resource or gettext mo translation file for 
                          the current locale which is the first locale in the 
                          locale set.


          @type fallback: c{boolean} 
   
        """
        assert(self._init, False, 
              "EggTranslations already initialized")

        if type(iniFileName) == types.StringType:
            iniFileName = unicode(iniFileName,
                             sys.getfilesystemencoding())

        if type(encoding) == types.StringType:
            # If encoding is a str it should only have
            # ASCII characters
            encoding = unicode(encoding)

        assert(type(iniFileName) == types.UnicodeType)
        assert(type(encoding) == types.UnicodeType)
        assert(type(fallback) == types.BooleanType)

        self._init = True
        self._fallback = fallback


        self._iniFileName = iniFileName
        self._iniEncoding = encoding

        pkg_resources.add_activation_listener(self._parseINIFiles)
        self.setLocaleSet(localeSet, fallback)

    def hasKey(self, project, name, locale=None):
        """
        returns True if a key was specified in one or more 
        eggs resource ini files (default is "resource.ini")
        for the given project and name. 
 
        The locale is an optional argument. By default
        the locale set is searched in fallback order as well
        as the 'all' default locale (if fallback=True in the 
        initialize or setLocaleSet method) until a 
        key is found.  If no key found the method returns False.
          
        However, if a locale is specified the method will only
        search for a key in the resource ini files for the 
        given locale.
   
        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

         @type project: c{str} or c{unicode}
             
         @param name: the name of the key that must be present in one
                      or more ini files in order for the method to return
                      True
         @type name: c{str} or c{unicode}
           
         
         @param locale: Optional argument that if specified tells the method 
                        to only return True if key is present in one or more
                        ini files for the given locale.

                       #XXX can be unicode but must contain
                            only ascii characters
         @type locale: c{str} a valid language country locale string i.e. "en_US"

         @return: c{bool} True if the name is found otherwise False

        """
        assert(self._init, True)
        
        if type(project) == types.StringType:
             project = unicode(project) 

        if type(name) == types.StringType:
             name = unicode(name) 

        assert(type(project) == types.UnicodeType)
        assert(type(name) == types.UnicodeType)

        if locale is not None:
            if type(locale) == types.UnicodeType:
                locale = str(locale)

            assert(type(locale) == types.StringType)
            return (project, name, locale) in self._iniCache

        if not self._fallback:
            loc = self._localeSet[0]
            return (project, name, loc) in self._iniCache

       
        for locale in self._localeSet:
            if (project, name, locale) in self._iniCache:
                return True
                               
        return (project, name, 'all') in self._iniCache


    def getValueForKey(self, project, name, locale=None):
        """
        Returns the unicode string value that was specified 
        in one or more eggs resource ini files (default is 
        "resource.ini") for the given project and name. or 
        None if not found.
 
        The locale is an optional argument. By default
        the locale set is searched in fallback order
        (if fallback=True in the initialize or setLocale method) until a 
        key is found.
          
        However, if a locale is specified the method will only
        search for a key in the resource ini files for the 
        given locale.

        Example:
           A resource.ini file contains the following line: 
              [mypackage::fr]
               myimage = /resources/imgs/myimage.png

           >>> print eggRMInstance.getValueForKey("mypackage", 
           ...                               "myimage", "fr")
           /resource/imgs/myimage.png
           >>>

        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

         @type project: c{str} or c{unicode}
             
         @param name: the name of the key that must be present in one
                      or more ini files in order for the method to return
                      True
         @type name: c{str} or c{unicode}
           
         
         @param locale: Optional argument that if specified tells the method 
                        to only return True if key is present in one or more
                        ini files for the given locale.

         @type locale: c{str} a valid language country locale string i.e. "en_US"


         @return c{unicode} value or None if not found
        """
        res = self._getTupleForKey(project, name, locale)

        return res and res[1] or None

    def isDirectory(self, project, name, locale=None):
        """
          Returns True if:
          1.  one or more resource ini files have an entry for the key 
              contained in the name parameter.
 
          2. The entry must be a valid directory path
             in the same egg as resource ini.

        The locale is an optional argument. By default
        the locale set is searched in fallback order
        (if fallback=True in the initialize or setLocale method) until a 
        key is found. If no key found the method returns False.
          
        However, if a locale is specified the method will only
        search for a key in the resource ini files for the 
        given locale.

        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

         @type project: c{str} or c{unicode}
             
         @param name: the name of the key that must be present in one
                      or more ini files in order for the method to return
                      True
         @type name: c{str} or c{unicode}
           
         
         @param locale: Optional argument that if specified tells the method 
                        to only return True if key is present in one or more
                        ini files for the given locale.

         @type locale: c{str} a valid language country locale string i.e. "en_US"

         @return: c{bool} True if the name is found and the entry for that 
                  name is a valid directory path in the same egg
                  otherwise False
        """
        res = self._getTupleForKey(project, name, locale)
 
        if res is not None:
            dist, value = res

            return dist.metadata_isdir(
                        value.encode(self._iniEncoding))

        return False


    def listDirectory(self, project, name, locale=None):
        """
        Returns a c{List} of c{unicode} values containing the 
        names of files in the directory entry for the 
        given project and name. The listDirectory
        method will not return the names of sub directories 
        only files in the directory for the given project and 
        name.

        The locale is an optional argument. By default
        the locale set is searched in fallback order
        (if fallback=True in the initialize or setLocale method) until a 
        key is found. If no key found the method returns False.
          
        However, if a locale is specified the method will only
        search for a key in the resource ini files for the 
        given locale.

        Raises a c{NameError} if no entry is found for the 
        given project and name.

        Raises a c{OSError} if the entry for given project 
        and name is not a directory.

        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

         @type project: c{str} or c{unicode}
             
         @param name: the name of the key that must be present in one
                      or more ini files in order for the method to return
                      True
         @type name: c{str} or c{unicode}
           
         
         @param locale: Optional argument that if specified tells the method 
                        to only return True if key is present in one or more
                        ini files for the given locale.

         @type locale: c{str} a valid language country locale string i.e. "en_US"
        

        @return: c{List} of c{unicode} filenames
        """
        res = self._getTupleForKey(project, name, locale)
 
        if res is None:
           self._raiseNameError(project, name, locale)

        dist, value = res

        return dist.metadata_listdir(
                      value.encode(self._iniEncoding))

    def hasResource(self, project, name, locale=None):
        """
        Returns True if:
          1.  one or more resource ini files have an entry for the key 
              contained in the name parameter.
 
          2. The entry must be a valid path to a file 
             in the same egg as resource ini.

             Example:    
             A resource.ini file contain's the following line: 
             
                [mypackage::fr]
                myResource=/resources/myresource.png

           >>> print eggRMInstance.hasResource("mypackage", 
           ...                                 "myResource", "fr")
           True
           >>>
            
        The locale is an optional argument. By default
        the locale set is searched in fallback order
        (if fallback=True in the initialize or setLocale method) until a 
        key is found. If no key found the method returns False.
          
        However, if a locale is specified the method will only
        search for a key in the resource ini files for the 
        given locale.

        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

        @type project: c{str} or c{unicode}
             
        @param name: the name of the key to look up in the resource ini files.
        @type name: c{str} or c{unicode}
           
         
        @param locale: Optional argument that if specified tells the method 
                       to only return True if key is present in one or more
                       ini files for the given locale and that keys value points
                       to a valid file path in the same egg as resource ini.

        @type locale: c{str} a valid language country locale string i.e. "en_US"
  
        @return: c{bool} True if the name key points to at least one 
                 resource in an egg otherwise False.
        """
        res = self._getTupleForKey(project, name, locale)
 
        if res is not None:
            dist, value = res
            return dist.has_metadata(
                             value.encode(self._iniEncoding))

        return False


    def getResourceAsStream(self, project, name, locale=None):
        """
        #XXX: Update documentation for file like object
        Returns a c{cStringIO.StringIO} stream 
        handle to the resource for the given project 
        and name.

        Raises a c{NameError} if no entry is found for the 
        given project and name.

        Raises a c{IOError} if the entry for given project 
        and name is not a file resource.

        The locale is an optional argument. By default
        the locale set is searched in fallback order
        (if fallback=True in the initialize or setLocale method) until a 
        key is found. If no key found the method returns False.
          
        However, if a locale is specified the method will only
        search for a key in the resource ini files for the 
        given locale.

        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

         @type project: c{str} or c{unicode}
             
         @param name: the name of the key that must be present in one
                      or more ini files in order for the method to return
                      True
         @type name: c{str} or c{unicode}
           
         
         @param locale: Optional argument that if specified tells the method 
                        to only return True if key is present in one or more
                        ini files for the given locale.

         @type locale: c{str} a valid language country locale string i.e. "en_US"
        

        @return: c{cStringIO.StringIO} stream handle to the resource
        """
        res = self._getTupleForKey(project, name, locale)
 
        if res is None:
           self._raiseNameError(project, name, locale)

        dist, value = res

        return StringIO(dist.get_metadata(
                          value.encode(self._iniEncoding)))


    def getResourceAsLines(self, project, name, locale=None, encoding='UTF-8'):
        """
        Returns a c{generator} containing a list of non-blank 
        non-comment lines in a resource file for the given project 
        and name.

        Raises a c{NameError} if no entry is found for the 
        given project and name.

        Raises a c{IOError} if the entry for given project 
        and name is not a file resource.

        The locale is an optional argument. By default
        the locale set is searched in fallback order
        (if fallback=True in the initialize or setLocale method) until a 
        key is found. If no key found the method returns False.
          
        However, if a locale is specified the method will only
        search for a key in the resource ini files for the 
        given locale.

        
        Example:
           A resource.ini file contains the following line: 
              [mypackage::all]
              myDocument = README.txt

           >>> lines = eggRMInstance.getResourceAsLines("mypackage", 
           ...                                          "myDocument", "all")

           >>> for line in lines:
           >>>    print line
           
        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

         @type project: c{str} or c{unicode}
             
         @param name: the name of the key that must be present in one
                      or more ini files in order for the method to return
                      True
         @type name: c{str} or c{unicode}
           
         
         @param locale: Optional argument that if specified tells the method 
                        to only return True if key is present in one or more
                        ini files for the given locale.

         @type locale: c{str} a valid language country locale string i.e. "en_US"
        

        @return: c{generator} list of non-blank non-comment lines.
        #XXX Strips blank lines and comments
        """
        return pkg_resources.yield_lines(self.getResourceAsString(
                             project, name, locale, encoding))
 
  
    def getResourceAsString(self, project, name, locale=None, encoding='UTF-8'):
        """
        Returns a c{unicode} string containing the contents of 
        the resource file for the given project and name.

        Raises a c{NameError} if no entry is found for the 
        given project and name.

        Raises a c{IOError} if the entry for given project 
        and name is not a file resource.

        Raises a c{UnicodeDecodeError} if the file resource
        encoding does not match the value of the encoding 
        argument.

        Raises a c{LookupError} if an invalid or unsupported encoding
        is specified.

        The locale is an optional argument. By default
        the locale set is searched in fallback order
        (if fallback=True in the initialize or setLocale method) until a 
        key is found. If no key found the method returns False.
          
        However, if a locale is specified the method will only
        search for a key in the resource ini files for the 
        given locale.

        
        Example:
           A resource.ini file contains the following line: 
              [mypackage::all]
              myDocument = README.txt

           >>> fileContents = eggRMInstance.getResourceAsString("mypackage", 
           ...                                              "myDocument", "all")

           >>> print fileContents
           This is the text contained in the
           readme file
          
           More text in the readme file.
           >>>
           
        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

         @type project: c{str} or c{unicode}
             
         @param name: the name of the key that must be present in one
                      or more ini files in order for the method to return
                      True
         @type name: c{str} or c{unicode}
           
         
         @param locale: Optional argument that if specified tells the method 
                        to only return True if key is present in one or more
                        ini files for the given locale.

         @type locale: c{str} a valid language country locale string i.e. "en_US"
        

        @return: c{unicode} string containing contents of the resource file.
        """
        res = self._getTupleForKey(project, name, locale)
 
        if res is None:
           self._raiseNameError(project, name, locale)

        dist, value = res

        bytes = dist.get_metadata(value.encode(self._iniEncoding))
        return unicode(bytes, encoding)
   
    def getText(self, project, name, txt, *args):
        """
        Returns a c{unicode} string containing the localized value
        for key txt in the given project. The name
        parameter points to a key in a resource ini file that
        contain a value entry pointing to a gettext .mo 
        resource in the same egg.

        An optional additional argument can be specified as the 
        default value to return if no localized is found. By default
        the txt parameter will be returned by c{EggTranslations.getText}
        if no localized value found for the txt parameter. However,
        if the default value argument is passed that value will be 
        returned instead of text.

        Example where there in no localized value for 
        txt parameter "Hello World":
        
            >>> eggRMInstance.getText("myproject", "message_catalog", "Hello World")
            u'Hello World'
            >>>
            >>> eggRMInstance.getText("myproject", "message_catalog", 
            ...                             "Hello World", "Default Value")  
            u'Default Value'
            >>>

        If fallback was set to True in the c{EggTranslations.initialize} method
        or the c{EggTranslations.setLocale} method, the 
        c{EggTranslations.getText} method will search all locales in the 
        locale set till a gettext mo translation is found for the txt parameter.

        If fallback was set to False in the c{EggTranslations.initialize} method
        or the c{EggTranslations.setLocale} method, the
        c{EggTranslations.getText} method will only search the current locale
        which is the first locale in the locale set for a gettext mo translation for 
        the txt parameter.
                          
        Note that the "all" default locale can not contain any  key value pairs 
        that point to gettext .mo files.
         
        If a .mo gettext value is found in the "all" default locale, the .mo file 
        will not be loaded by the c{EggTranslations}.


        Example:
           A resource.ini file contains the following line: 
              [mypackage::fr]
              my_message_catalog = locale/fr/mypackage.mo

           The locale/fr/mypackage.mo file contains a localization of "Hello"
           to "Bonjour".

           >>> egRMInstance.initialize("fr")
           >>> eggRMInstance.getText("mypackage", "my_message_catalog", "Hello")
           u'Bonjour'                                              

           
        @param project: A project is a root namespace for which 
                       resources and localizations exist under. 

                       A project name can be any unique string 
                       and does not have to match the egg name.
 
                       An egg's info file can contain resource
                       and localizations for more than one project.

                       The project terminology comes from the 
                       gettext API architecture.

         @type project: c{str} or c{unicode}
             
         @param name: the name of the key that must be present in one
                      or more ini files in order for the method to return
                      True
         @type name: c{str} or c{unicode}
           
         
         @param txt: The default text string which is used as look up key 
                     to retrieve a localized value from a gettext .mo file.
                     The default text string is usual the English version
                     of the text. The .mo gettext files will contain 
                     localizations of the English version with the English
                     version as the key.
                     

         @type txt: c{str} or c{unicode}
        

        @return: c{unicode} the localized version of the txt parameter, the txt
                 parameter if no localized version found, or a default value passed
                 as an additional argument if no localized version of txt parameter found.
        """
        assert(self._init, True)

        if type(project) == types.StringType:
             project = unicode(project) 

        if type(name) == types.StringType:
             name = unicode(name) 

        if type(txt) == types.StringType:
             txt  = unicode(txt) 

        assert(type(project) == types.UnicodeType)
        assert(type(name) == types.UnicodeType)
        assert(type(txt) == types.UnicodeType)

        if self._fallback:
            for locale in self._localeSet:
                key = (project, name, locale)

                # The first found EggTranslation for 
                # locale set is the root for fallback
                if key in self._gtCache:
                    return self._gtCache[key].ugettext(txt, *args)

            if __debug__:
                logger.debug(u"No EggTranslations found for %s %s %s",
                             project, name, self._localeSet)
            
            return args and args[0] or txt

        key = (project, name, self._localeSet[0])

        if key in self._gtCache:
            return self._gtCache[key].ugettext(txt, *args)
  

        if __debug__:
            logger.debug(u"No EggTranslations found for %s %s %s", 
                         project, name, self._localeSet)
            
        return args and args[0] or txt

    def hasFallback(self):
        """
        Returns True if fallback was set to True in either the 
        c{EggTranslations.initialize} method or the 
        c{EggTranslations.setLocale} method.
        
        @return: c{bool} True if fallback set to True in initialize or setLocale methods
                         otherwise False.
        """
        assert(self._init, True)
        return self._fallback

    def getINIFileName(self): 
        """
        Returns the c{unicode} file name of the resource ini files. The 
        default for the resource ini file is "resource.ini".
 
        The name of the resource ini file is set in the c{EggTranslations.initialize}
        method.
 
        @return: c{unicode} the name of the resource ini file.
        """
        assert(self._init, True)
        return self._iniFileName

    def getLocaleSet(self):
        """
        Returns a c{List} of valid c{str} locale language / country codes.
        The c{List} is arrange in ascending fallback order.

        @return: c{List or c{str} locale language / country codes.
        """
        assert(self._init, True)
        return self._localeSet

    def setLocaleSet(self, localeSet, fallback=True): 
        """
        #XXX raises UnicodeEncodeError and NameError
        Resets the c{EggTranslations}'s locale set c{list}.
        Resetting the locale set includes unloading all gettext 
        .mo translations, loading the the gettext .mo translations
        for the current locale set, and setting the gettext locale
        fallback order if the fallback parameter is set to True.

        Calling this method also resets the c{EggTranslations}'s
        resource look up and localization caches as 
        the locale set has changed and thus those caches are no longer
        valid.

        When a resource or localization is retrieved for the 
        current locale set the value, localizations or resource file 
        location is cached so the next time the value or resource file 
        is request the locale set fallback order does not need to be
        searched as that value is now in the cache.  

        Note the initial locale set for the c{EggTranslations}
        must be set in the C{EggTranslations.initialize}
        method.

        Note, setting the c{EggTranslations}'s locale set 
        also adds the language code as a fallback for language /
        county code locale definitions when fallback is set to True.
        If the locale set contains 'fr_CA' this method will also add
        to the locale set 'fr' as a fallback for 'fr_CA'. 

        @param localeSet: A String or List containing locale country 
                          and language codes

        @type localeSet: c{str} or c{unicode} or c{list} containing c{str} 
                         or c{unicode} values


        @param fallback: Indicates where locale set fallback should 
                         take place. If set to True, the c{EggTranslations} 
                         will search all locales in the locale set till a 
                         resource or gettext mo translation file is found. If
                         set to False the c{EggTranslations} will only try to
                         locate a resource or gettext mo translation file for 
                         the current locale which is the first locale in the 
                         locale set.


        @type fallback: c{boolean} 
        """
        assert(self._init, True)

        self._fallback = fallback

        if type(localeSet) == types.ListType:
            tmpLocaleSet = localeSet

            for i in xrange(0, len(tmpLocaleSet)):
                if type(tmpLocaleSet[i]) == types.UnicodeType:
                    tmpLocaleSet[i] = str(tmpLocaleSet[i])

                # All entries in the locale set must be strings
                assert(type(tmpLocaleSet[i]) == types.StringType)


        elif type(localeSet) == types.StringType:
            tmpLocaleSet = localeSet.split(",") 

        elif type(localeSet) == types.UnicodeType:
            #Convert to Python str from unicode
            tmpLocaleSet = str(localeSet).split(",") 
        else:
            raise NameError("localeSet must of type str, unicode, \
                             or List")

        for i in xrange(0, len(tmpLocaleSet)):
            tmpLocaleSet[i] = normalizeLocale(tmpLocaleSet[i])

            if not isValidLocaleForm(tmpLocaleSet[i]):
                raise NameError("Invalid locale name found '%s'" %
                                tmpLocaleSet[i])
             

        #Deallocate the _gtCache and its contents
        self._gtCache = None
        self._gtCache = {}

        if self._fallback:
            self._localeSet = buildFallbackLocales(tmpLocaleSet)
        else:
            self._localeSet = tmpLocaleSet

        if __debug__:
            logger.debug(u"Setting Locale Set to: %s", 
                         self._localeSet)

        keys = self._moCache.keys()

        for key in keys:
            project, name = key

            if not self._fallback:
                # Create EggTranslation for the primary locale
                # (self._localeSet[0]) only if
                # there is an mo file declaration in the ini.

                locale = self._localeSet[0]

                if not locale in self._moCache[key]:
                    #Continue past the EggTranslation code
                    continue

                dist, mofile = self._moCache[key][locale]
 
                # The mofile variable is an str not 
                # unicode
                bytes = dist.get_metadata(mofile)
                trans = DefaultTranslations(StringIO(bytes))

                self._gtCache[(project, name, locale)] = trans 

                if __debug__:
                    logger.debug(u"%s EggTranslation %s " \
                                 "(No Fallback)", key, locale)

                
                #Continue past the fallback code
                continue

            root = None 

            for locale in self._localeSet:
                if locale not in self._moCache[key]:
                    #Continue past the EggTranslation code
                    continue

                dist, mofile = self._moCache[key][locale]
                    
                bytes = dist.get_metadata(mofile)
                trans = DefaultTranslations(StringIO(bytes))

                self._gtCache[(project, name, locale)] = trans 
                   
                if root is None:
                    root = trans

                    if __debug__:
                        logger.debug(u"%s Root EggTranslation %s", 
                                     key, locale)
                else:
                    root.add_fallback(trans)

                    if __debug__:
                        logger.debug(u"%s Adding Fallback %s", key, 
                                     locale)

    def getDebugString(self):
        """
        Returns a c{str} representation of the c{EggTranslations}'s
        egg loading values suitable for debugging using print, the logging 
        package, or a UI dialog box.

        The structure of the debug string is as follows:

         EggTranslations
         =========================
            INI FILE: ResourceFileName (Encoding)
            LOCALE SET: [localeSetValues]
            FALLBACK: True | False
                  
            EggName 
            ===============================

               ProjectName
               ---------------------
                 [LocaleName] 
                    entryKey=entryValue
                    gettextKey=getTextMoFile (LOADED | NOT_LOADED)

       
        An additional Example using real values:

         EggTranslations
         =========================
            INI FILE: 'resources.ini' (UTF-8)
            LOCALE SET: ['fr_CA', 'fr']
            FALLBACK: True

            MyProject
            ===============================

               myProjectDomain
               -------------------------
                 [all] 
                    splashScreenImage = imgs/splash.png
                    readme = README.txt
               
               myAlternateDomain
               -------------------------
                 [all]
                    splashScreenImage = alternate/imgs/splash.png
                    readme=alternate/README.txt
                  
            MyProject_FR
            ===============================

               myProjectDomain 
               ------------------------
                 [fr_CA] 
                    splashScreenImage = locale/fr/imgs/splash.png
                    readme = locale/fr/README.txt
                    catalog= locale/fr/myProjectDomain.mo (LOADED)
               
               myAlternateDomain
               ------------------------
                 [fr_CA]
                    splashScreenImage = alternate/locale/fr/imgs/splash.png
                    readme = alternate/locale/fr/README.txt
                    catalog = alternate/locale/fr/myProjectDomain.mo (LOADED)

         @return: c{str} debug string of c{EggTranslations} 
                  current configuration in the UTF-8 encoding.
        """
        tree = {}
        sBuffer = []

        keys = self._iniCache.keys()

        # Build a tree of dictionaries 
        # which can be traversed to render
        # the debug string in the correct order
        for key in keys:
            project, name, locale = key
            dist, value = self._iniCache[key]
   
            if not dist in tree:
                tree[dist] = {}

            if not project in tree[dist]:
                tree[dist][project] = {}

            if not locale in tree[dist][project]:
                tree[dist][project][locale] = {}

            tree[dist][project][locale][name] = value

         
        sBuffer.append(u"\n\n%s\n" % (self._NAME))
        sBuffer.append(u"=============================\n")
        sBuffer.append(u"  INI FILE: '%s' (%s)\n" % (
                             self._iniFileName, 
                             self._iniEncoding))

        sBuffer.append(u"  LOCALE SET: %s\n" % (self._localeSet))
        sBuffer.append(u"  FALLBACK: %s\n" % (self._fallback))
        sBuffer.append(u"\n")

        dists = tree.keys()

        for dist in dists:
            sBuffer.append(u"  %s\n" % (dist))
            sBuffer.append(u"  ================================\n\n")

            for project in tree[dist]:
                sBuffer.append(u"    %s\n" % (project))
                sBuffer.append(u"    --------------------" \
                               "---------\n")
               

                for locale in tree[dist][project]:
                    sBuffer.append(u"      [%s]\n" % (locale))

                    for name in tree[dist][project][locale]:
                        val = tree[dist][project][locale][name]
                        
                        state = ""
 
                        if val.endswith(u".mo"):
                            key = (project, name, locale)

                            if key in self._gtCache:
                                state = " (LOADED)"
                            else:
                               state = u" (NOT_LOADED)"
                           
                        sBuffer.append(u"        %s = %s%s\n" % (
                                       name, val, state))

                    sBuffer.append(u"\n")

                sBuffer.append(u"\n")

            sBuffer.append(u"\n")
                  
        return (u"".join(sBuffer)).encode("UTF-8", "replace")


    def _parseINIFiles(self, dist):
        """
        Callback method passed to c{pkg_resources.add_activation_listener} method.
      
        For each egg distribution contained in the dist parameter:
          1. Parses the resource ini file (default name is "resource.ini") for each egg
             that contains one.
          2. Builds a cache of resources based on project, locale, and name.
          3. For each .mo value for a given project, locale, and name cache 
             the file path to the .mo gettext file.

      @param dist: An egg package distribution
      @type dist: c{pkg_resources.Distribution}
        """
        if __debug__:
            logger.debug(u"EggTranslations parsing %s", dist)
   
        #Convert from unicode to byte str since the 
        # pkg_resources API only works with str's.
        iniFile = self._iniFileName.encode(self._iniEncoding)

        if dist.has_metadata(iniFile):

            if __debug__:
                logger.debug(u"Found '%s' for project %s", 
                                     self._iniFileName, dist)

            ini_unicode_data = None
           
            try:
                s = dist.get_metadata(iniFile)
                ini_unicode_data = unicode(s, self._iniEncoding)
            except Exception, e:
                s = u"unable to load ini file in %s encoding. (%s)"

                self._raiseParseError(dist, s, self._iniEncoding, e) 

            # The call to the pkg_resources.split_sections 
            # strips comments and blank lines
            ini_map = None
            try:
                data = pkg_resources.split_sections(ini_unicode_data)
                ini_map = dict(data)
            except Exception, e:
                s = u"one or more invalid ini token found: %s"
                self._raiseParseError(dist, s, e) 

            ini_keys = ini_map.keys()

            if len(ini_keys) == 1 and ini_keys[0] is None:

                # Invalid tokens found in project definition.
                # Represented in map as
                # {None: [ONE_OR_MORE_VALUES]}

                if len(ini_map[None]):
                    s = u"one or more invalid ini token found: %s"
                    self._raiseParseError(dist, s, ini_map[None]) 
                
                # If the resource ini file does not 
                # contain any project definitions 
                # i.e. [myproject::all] then return
                if __debug__:
                    logger.debug(u"%s no projects defined in '%s'",
                                  dist, self._iniFileName)
                return 

            ini_values = ini_map.values()

            for i in xrange(0, len(ini_map)):
                project, locales = (None, None)
                try:
                    project, locales = ini_keys[i].split("::")
                except:
                    s = u"invalid project format found '[%s]'. " \
                        "Should be [project_name::locale_name]"

                    self._raiseParseError(dist, s, ini_keys[i])

                #Trim leading and trailing whitespace
                project = project.strip()
                locales = locales.strip()

                if not locales or not project:
                    s = u"invalid project format found '[%s]'. " \
                        "Should be [project_name::locale_name]"

                    self._raiseParseError(dist, s, ini_keys[i])


                for locale in locales.split(","):
                    locale = locale.strip()

                    if not locale:
                        s = u"invalid project format found '[%s]'. " \
                            "Should be [project_name::locale_name]"

                        self._raiseParseError(dist, s, ini_keys[i])
                    
                    if not ini_values[i]:
                        logger.warn("%s  %s [%s] no key " \
                                    "value entries defined", dist,
                                    self._iniFileName, ini_keys[i])

                    try:
                        if locale.lower() == 'all':
                            # Normalize 'all' to lowercase
                            locale = locale.lower()
                        else:
                            #try converting the locale from unicode 
                            #to ascii str and normalize it
                            locale = normalizeLocale(str(locale))
                                   
                    except:
                        s = u"Invalid locale found. Unable to " \
                            "convert to ASCII: %s"

                        self._raiseParseError(dist, s, locale)

                    if locale != 'all' and not \
                       isValidLocaleForm(locale):
                        s = u"invalid locale format found '%s'" 

                        self._raiseParseError(dist, s, locale)

                    for line in ini_values[i]:
                        name, value = (None, None)
                        try:
                            name, value = line.split("=", 1)
                        except:
                            s = u"invalid key value pair found " \
                                "'%s' in [%s]. Should be " \
                                "key = value"

                            self._raiseParseError(dist, s, line,
                                                  ini_keys[i])

                        if value.rfind("#") != -1:
                            value, comment = value.split("#", 1)

                        #Trim leading and trailing whitespace
                        value = value.strip()
                        name = name.strip()

                        key = (project, name, locale)

                        self._iniCache[key] = (dist, value)

		        if __debug__:
		            logger.debug(u"[%s::%s] '%s = %s' " \
                                         "added to ini cache", 
                                         project, locale, name, value)

                        if value.endswith(u".mo") and not \
                           locale == 'all':
                            # Caches the file resource
                            # location of each .mo file.
                            #
                            # This cache will be used by
                            # setLocale method to 
                            # load the EggTranslations 
                            # and build the fallback order
                            # if fallback set to True
                           
                            isValidPath = False
                            bVal = value.encode(self._iniEncoding)
                            
                            try:
                                isValidPath = dist.has_metadata(bVal)
                            except:
                                pass
  
                            if not isValidPath:
                                s = u" mo file entry '%s' does not " \
                                    "point to a valid resource " \
                                    "path"
                                self._raiseParseError(dist, s, line)
                                                      
                            pKey = (project, name)
                            # Add the byte version of .mo path
                            # to moCache
                            pVal = (dist, bVal)
                            
                            if not pKey in self._moCache:
                                self._moCache[pKey] = {}

                            self._moCache[pKey][locale] = pVal
   
                            if __debug__:
                                logger.debug(u"[%s::%s] %s added " \
                                             "%s to mo cache", 
                                             project, locale, name,
                                             value)

                        elif value.endswith(u".mo"):
                            logger.warn(u"gettext .mo file " \
                                    "definition '%s' found in " \
                                    "'all' default locale. " \
                                    "This file will not be loaded.",
                                    value)
                                    

    def _getTupleForKey(self, project, name, locale=None):
        assert(self._init, True)

        if type(project) == types.StringType:
             project = unicode(project) 

        if type(name) == types.StringType:
             name = unicode(name) 


        assert(type(project) == types.UnicodeType)
        assert(type(name) == types.UnicodeType)

        if locale is None and not self._fallback:
            locale = self._localeSet[0]

        if locale is not None:
            if type(locale) == types.UnicodeType:
                locale = str(locale)

            assert(type(locale) == types.StringType)
            key = (project, name, locale)

            if key in self._iniCache:
                return self._iniCache[key]

            return None

        for locale in self._localeSet:
            key = (project, name, locale)

            if key in self._iniCache:
                return self._iniCache[key]

        key = (project, name, 'all') 
        
        if key in self._iniCache:
            return self._iniCache[key]

        return None

    def _raiseNameError(self, project, name, locale):
        s = u"No match found for [%s::%s] %s" \
            % (project, locale and locale or self._localeSet, name)

        raise NameError(s.encode("UTF-8", "replace"))

    def _raiseParseError(self, dist, errTxt, *args):
        s = u"Error Parsing '%s' for Project '%s' " \
            % (self._iniFileName, dist)

        if args:
            errTxt = errTxt % args

        s += errTxt
 
        raise INIParsingException(s.encode("UTF-8", "replace"))

def stripCountryCode(locale):
    assert(type(locale) == types.StringType)

    return (locale.split('_')[0]).lower()

def hasCountryCode(locale):
    assert(type(locale) == types.StringType)

    return len(locale) == 5 and locale[2] == '_'

def isValidLocaleForm(locale):
    assert(type(locale) == types.StringType)

    size = len(locale)
    
    if size == 2:
        return True

    if size == 5 and locale[2] == '_':
        return True

    return False


def normalizeLocale(locale):
    assert(type(locale) == types.StringType)

    l = len(locale)

    if l == 2:
        return locale.lower()

    if l == 5 and locale[2] == "_":
        lang, cntry = locale.split("_")
        return "%s_%s" % (lang.lower(), cntry.upper())

    return locale

def buildFallbackLocales(localeSet):
    assert(type(localeSet) == types.ListType)

    rLocaleSet = []

    for locale in localeSet:
            rLocaleSet.append(locale)
            if (hasCountryCode(locale)):
                langCode = stripCountryCode(locale)
                if not langCode in localeSet:
                    rLocaleSet.append(langCode)

    return rLocaleSet


def stripEncodingCode(locale):
    # A locale can contain additional
    # information beyond the two digit
    # language and country codes.
    # For example and encoding can be
    # specified: "en_US.UTF-8"
    # The encoding portion is not understood by
    # PyICU so we strip it.
  
    assert(type(locale) == types.StringType)

    pos = locale.find(".")

    if pos != -1:
        return locale[0:pos]
       
    return locale
