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
 Test Cases:
*** RUN THESE TESTS ON ALL THREE PLATFORMS
"""

import unittest
import logging
import sys
import os
import types
from egg_translations import logger as rmLogger
from egg_translations import EggTranslations
from egg_translations import INIParsingException

class EggTestCase(unittest.TestCase):
    PROJECT = "ResourceManager-EggPlugin"
    INI_FILE = "test_directory/resources.ini"
    ENCODING = sys.getfilesystemencoding()
    FALLBACK = True

    # Using en_US tests the fallback logic.
    # The EggTranslations adds the lang code
    # as a fallback for lang country.
    # There is no definition for the 'en_US' locale
    # but there is one for 'en'
    #
    # Without the EggTranslations internally adding
    # 'en' as a fallback 'en_US' requests would fail.

    LOCALE_SET = [u'fr_CA', 'en_US']

    def setUp(self):
        self.initLoggers()

        self.eggTranslations = EggTranslations()

        self.eggTranslations.initialize(self.LOCALE_SET,
                      self.INI_FILE, self.ENCODING,
                      self.FALLBACK)

    def initLoggers(self):
        f = os.path.join("tests", "debug_test.log")
        logging.basicConfig(filename=f)

        rmLogger.setLevel(logging.DEBUG)
        self.logger = logging.getLogger(f)
        self.logger.setLevel(logging.DEBUG)

class TestEggTranslations(EggTestCase):

    def testGetDebugString(self):
        s = self.eggTranslations.getDebugString()
        self.assertEquals(type(s), types.StringType)

    def testHasKey(self):
        # This tests fallback. A value for 'img_resource'
        # is only present in the 'all' default locale
        hasKey = self.eggTranslations.hasKey(self.PROJECT,
                                         "img_resource")
        self.assertEquals(hasKey, True)

        hasKey = self.eggTranslations.hasKey(self.PROJECT,
                                         "txt_resource")
        self.assertEquals(hasKey, True)


        hasKey = self.eggTranslations.hasKey(self.PROJECT,
                                         "txt_resource", "fr_CA")
        self.assertEquals(hasKey, False)

        hasKey = self.eggTranslations.hasKey(self.PROJECT,
                                         "txt_resource", "fr")
        self.assertEquals(hasKey, True)


    def testGetValueForKey(self):
        value = self.eggTranslations.getValueForKey(self.PROJECT,
                                               "txt_message")

        self.assertEquals(value, "This is a String value in 'French'")

        value = self.eggTranslations.getValueForKey(self.PROJECT,
                                               "txt_message", "en_US")
        self.assertEquals(value, None)

        value = self.eggTranslations.getValueForKey(self.PROJECT,
                                               "txt_message", "BOGUS")
        self.assertEquals(value, None)


        expect = "test_directory/locale/fr_CA/catalog.mo"

        value = self.eggTranslations.getValueForKey(self.PROJECT,
                                               "catalog")
        self.assertEquals(value, expect)

        expect = "test_directory/locale/en/catalog.mo"

        value = self.eggTranslations.getValueForKey(self.PROJECT,
                                               "catalog", "en")
        self.assertEquals(value, expect)

        value = self.eggTranslations.getValueForKey(self.PROJECT,
                                               "BOGUS", "en")
        self.assertEquals(value, None)

        value = self.eggTranslations.getValueForKey("BOGUS",
                                               "catalog")
        self.assertEquals(value, None)


    def testIsDirectory(self):
        isDir = self.eggTranslations.isDirectory(self.PROJECT,
                                           "dir_resource")

        self.assertEquals(isDir, True)

        isDir = self.eggTranslations.isDirectory(self.PROJECT,
                                           "dir_resource", "fr_CA")
        self.assertEquals(isDir, False)

        isDir = self.eggTranslations.isDirectory(self.PROJECT,
                                           "bogus_resource")
        self.assertEquals(isDir, False)

        isDir = self.eggTranslations.isDirectory("BOGUS",
                                           "dir_resource")

        self.assertEquals(isDir, False)

    def testListDirectory(self):
        d = self.eggTranslations.listDirectory(self.PROJECT,
                                         "dir_resource")

        self.assert_('img_resource.jpg' in d)
        self.assert_('txt_resource.txt' in d)

        # The dir path for "dir_bogus" in the 'fr' locale is
        # bogus

        self.assertRaises(OSError, self.eggTranslations.listDirectory,
                             self.PROJECT,"dir_bogus", "fr")

        self.assertRaises(OSError, self.eggTranslations.listDirectory,
                             self.PROJECT,"dir_bogus")

        self.assertRaises(NameError, self.eggTranslations.listDirectory,
                          self.PROJECT,"dir_resource", "fr_CA")

    def test_GetTupleForKey(self):
        self.eggTranslations.setLocaleSet(["en_US", "fr_CA"])

        # The getTupleForKey method is used by
        # the majority or the high level
        # EggTranslations API's such getResourceAsString.
        #
        # Testing this method is essential
        # since it is where fallback and locale set
        # calculations take place.

        getTuple = self.eggTranslations._getTupleForKey

        # Returns English over French now that the
        # Locale set changed
        self.assertEquals(getTuple(self.PROJECT,
                               "txt_message")[1],
                          u"This is a String value in 'English'")

        self.assertEquals(getTuple(self.PROJECT,
                               "txt_message", 'fr')[1],
                          u"This is a String value in 'French'")

        # Returns fallback values from 'all'
        self.assertEquals(getTuple(self.PROJECT,
                               "dir_resource")[1],
                          u"test_directory/resources")

        self.assertEquals(getTuple(self.PROJECT,
                          "txt_resource")[1],
                          u"test_directory/locale/fr/txt_resource.txt")

        # Disable fallback support
        self.eggTranslations.setLocaleSet(["en_US", "fr_CA"], False)

        self.assertEquals(getTuple(self.PROJECT,
                          "txt_resource"), None)

        self.assertEquals(getTuple(self.PROJECT,
                               "dir_resource"), None)

        self.assertEquals(getTuple(self.PROJECT,
                               "txt_message", 'fr')[1],
                          u"This is a String value in 'French'")

        # Restore the default locale set / fallback order
        self.eggTranslations.setLocaleSet(self.LOCALE_SET, self.FALLBACK)


    def testHasResource(self):
        self.assertEquals(
              self.eggTranslations.hasResource(self.PROJECT,
                                         "BOGUS"), False)

        self.assertEquals(
              self.eggTranslations.hasResource(self.PROJECT,
                                         "txt_resource"), True)

        self.assertEquals(
              self.eggTranslations.hasResource(self.PROJECT,
                                         "txt_resource", "BOGUS"),
                                         False)

        self.assertEquals(
              self.eggTranslations.hasResource(self.PROJECT,
                                         "txt_resource", "fr_CA"),
                                         False)

        self.assertEquals(
              self.eggTranslations.hasResource(self.PROJECT,
                                         "txt_resource", "all"),
                                         True)

        self.assertEquals(
              self.eggTranslations.hasResource(self.PROJECT,
                                         "txt_message"),
                                         False)


    def testResourceAsString(self):
        self.assertEquals(
               self.eggTranslations.getResourceAsString(self.PROJECT,
                                "txt_resource"),
                                u"This is the 'French' resource\n")

        self.assertEquals(
               self.eggTranslations.getResourceAsString(self.PROJECT,
                                "txt_resource", 'all'),
                                u"This is the default 'all' resource\n")

        self.assertRaises(NameError,
               self.eggTranslations.getResourceAsString,
               "BOGUS", "txt_resource")

        self.assertRaises(NameError,
               self.eggTranslations.getResourceAsString,
               self.PROJECT, "txt_resource", 'fr_CA')


        self.assertRaises(IOError,
               self.eggTranslations.getResourceAsString,
               self.PROJECT, "txt_message")

    def testResourceAsLines(self):
        lines = self.eggTranslations.getResourceAsLines(self.PROJECT,
                                     "txt_resource")

        for line in lines:
            self.assertEquals(line, u"This is the 'French' resource")
            break

        lines = self.eggTranslations.getResourceAsLines(self.PROJECT,
                                     "txt_resource", 'all')

        for line in lines:
            self.assertEquals(line,
                  u"This is the default 'all' resource")
            break

        self.assertRaises(NameError,
               self.eggTranslations.getResourceAsLines,
               self.PROJECT, "txt_resource", 'fr_CA')

        self.assertRaises(IOError,
               self.eggTranslations.getResourceAsLines,
               self.PROJECT, "txt_message")

    def testResourceAsStream(self):
        fh = self.eggTranslations.getResourceAsStream(self.PROJECT,
                                     "txt_resource")
        for line in fh:
            self.assertEquals(line, u"This is the 'French' resource\n")
            break

        fh = self.eggTranslations.getResourceAsStream(self.PROJECT,
                                     "txt_resource", 'all')

        for line in fh:
            self.assertEquals(line,
                      u"This is the default 'all' resource\n")
            break

        self.assertRaises(NameError,
               self.eggTranslations.getResourceAsStream,
               self.PROJECT, "txt_resource", 'fr_CA')

        self.assertRaises(IOError,
               self.eggTranslations.getResourceAsStream,
               self.PROJECT, "txt_message")

    def testGetText(self):
        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "Hello")

        self.assertEquals(value, "Bonjour From Montreal")

        value = self.eggTranslations.getText(self.PROJECT, "catalog_alt",
                                       "Hello")

        self.assertEquals(value, "Bonjour From Montreal Alt")

        value = self.eggTranslations.getText("BOGUS", "catalog_alt",
                                       "Hello", "Default")

        self.assertEquals(value, "Default")

        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "fallback 2")

        expect = "I correctly handled fallback 2 in French catalog.mo"
        self.assertEquals(value, expect)

        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "fallback 1")

        expect = "I correctly handled fallback 1 in English catalog.mo"
        self.assertEquals(value, expect)

        # Change the locale order
        self.eggTranslations.setLocaleSet(["en_US", "fr_CA"])


        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "fallback 2")

        # This values comes from the catalog localization for 'fr'
        expect = "I correctly handled fallback 2 in French catalog.mo"

        self.assertEquals(value, expect)

        # Remove fallback support
        self.eggTranslations.setLocaleSet(["en_US", "fr_CA"], False)


        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "fallback 2")

        # With fallback diabled only the default locale en_US will be
        # tried. There is no catalog for "en_US" so the default
        # value passed 'fallback 2' is returned
        self.assertEquals(value, "fallback 2")

        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "fallback 1", "NOT_FOUND")

        self.assertEquals(value, "NOT_FOUND")

        # Restore the default locale set / fallback order
        self.eggTranslations.setLocaleSet(self.LOCALE_SET, self.FALLBACK)


    def testHasFallback(self):
        self.assertEquals(self.eggTranslations.hasFallback(),
                          True)

    def testGetINIFileName(self):
        self.assertEquals(self.eggTranslations.getINIFileName(),
                          self.INI_FILE)

    def testGetLocaleSet(self):
        # The fr and en are added by EggTranslations
        # as fallbacks
        self.assertEquals(self.eggTranslations.getLocaleSet(),
                          ['fr_CA', 'fr', 'en_US', 'en'])

    def testSetLocaleSet(self):
        eRM = EggTranslations()

        # The EggTranslations will normalize locales
        # so FR_CA will be converted to fr_CA
        eRM.initialize(["FR_CA"])

        self.assert_("fr_CA" in eRM.getLocaleSet())

        # The fr lang code is added by EggTranslations
        # when fallback == True
        self.assert_("fr" in eRM.getLocaleSet())

        # The EggTranslations will normalize locales
        # so FR_CA will be converted to fr_CA
        eRM.setLocaleSet(["FR_CA", "en_US", "de"], fallback=False)

        # The fr lang code will not beadded by EggTranslations
        # when fallback == False
        self.assert_(not "fr" in eRM.getLocaleSet())

        self.assertRaises(NameError, eRM.setLocaleSet, None)
        self.assertRaises(NameError, eRM.setLocaleSet, "BOGUS")

        # All is not a valid locale
        self.assertRaises(NameError, eRM.setLocaleSet, 'all')

        # Pass a unicode value for locale that can not be
        # converted to ASCII
        self.assertRaises(UnicodeEncodeError, eRM.setLocaleSet,
                          u'\u00FC')

    def testMultipleProjects(self):
        r = "test_directory/ini_files/resources_multi.ini"

        erm = EggTranslations()
        erm.initialize(self.LOCALE_SET, r)

        self.assertEquals(erm.getValueForKey("PROJECT_ONE",
                                             "txt_message"),
                          u"This is a String value in 'French'")

        self.assertEquals(erm.getValueForKey("PROJECT_ONE",
                                             "txt_message", 'all'),
                          u"This is a String value in 'all'")

        self.assertEquals(erm.getValueForKey("PROJECT_ONE",
                                             "txt_message", 'en'),
                          None)

        self.assertEquals(erm.hasResource("PROJECT_ONE",
                                          "img_resource"), True)

        self.assertEquals(erm.hasResource("PROJECT_ONE",
                                          "img_resource", "fr_CA"),
                          False)

        self.assertEquals(erm.hasResource("PROJECT_ONE",
                                          "txt_resource", "fr"),
                          True)

        self.assertEquals(erm.getText("PROJECT_ONE", "catalog",
                                      "fallback 1"),
             u"I correctly handled fallback 1 in English catalog.mo")


        self.assertEquals(erm.getValueForKey("PROJECT_TWO",
                                             "txt_message"),
                          u"This is a Project 2 in 'French'")

        self.assertEquals(erm.getValueForKey("PROJECT_TWO",
                                             "txt_message", 'en'),
                          u"This is Project 2 in 'English'")

        self.assertEquals(erm.getText("PROJECT_TWO", "catalog",
                                      "fallback 1"),
          u"I correctly handled fallback 1 in English catalog_alt.mo")

        self.assertEquals(erm.getValueForKey("PROJECT_THREE",
                                             "txt_message"),
                          u"This is a Project 3 in 'French'")

        self.assertEquals(erm.getValueForKey("PROJECT_THREE",
                                             "txt_message", "all"),
                          None)

        self.assertEquals(erm.getValueForKey("PROJECT_THREE",
                                             "txt_message", "en"),
                          u"This is Project 3 in 'English'")


    def testINIParsing(self):
        root = "test_directory/ini_files/"

        ini_list = ["resources_empty_header.ini",
                    "resources_bad_header.ini",
                    "resources_invalid_header.ini",
                    "resources_bogus_locale.ini",
                    "resources_bad_key.ini",
                    "resources_bad_mo_path.ini"]

        for ini in ini_list:
            erm = EggTranslations()
            r = "%s%s" % (root, ini)
            self.assertRaises(INIParsingException,
                              erm.initialize, self.LOCALE_SET, r)

    def testINIEncodings(self):
        erm = EggTranslations()
        r = u"test_directory/ini_files/resources_shift_jis.ini"

        self.assertRaises(INIParsingException,
                          erm.initialize, "ja_JP", r)

        erm = EggTranslations()
        self.assertRaises(LookupError,
                          erm.initialize, "ja_JP", r,
                          "BOGUS_ENCODING")

        erm = EggTranslations()
        erm.initialize("ja_JP", r, "shift-jis")

        t = erm.getValueForKey(self.PROJECT, "txt_message")
        self.assertEquals(t, u'\u7a76\u6975\u306e\u8cc7\u7523\u9632\u885b\u30ce\u30a6\u30cf\u30a6\u3084\u300c\u6295\u8cc7\u306e\u9769\u547d\u300d\u3068\u306f\u306a\u306b\u304b\u3001\u9280\u884c\u9810\u91d1\u3088\u308a\u5b89\u5168\u306a')


        t = erm.getValueForKey(self.PROJECT, u'\u7a76\u6975\u306e\u8cc7\u7523\u9632\u885b\u30ce\u30a6\u30cf\u30a6\u3084\u300c\u6295\u8cc7\u306e\u9769\u547d\u300d\u3068\u306f\u306a\u306b\u304b\u3001\u9280\u884c\u9810\u91d1\u3088\u308a\u5b89\u5168\u306a')

        self.assertEquals(t, u"Test message key")

        t = erm.getValueForKey(self.PROJECT, "txt_message", 'all')
        self.assertEquals(t, u"This is a String value in 'all'")

        t = erm.getText(self.PROJECT, "catalog", u"\u66f8")

        self.assertEquals(t, u"Hello")

        t = erm.getText(self.PROJECT, "catalog", "Hello")
        self.assertEquals(t, u"\u66f8")

    def testResourceEncodings(self):
        self.assertRaises(UnicodeDecodeError,
              self.eggTranslations.getResourceAsString,
              self.PROJECT, "ja_resource", 'ja_JP')

        self.assertRaises(LookupError,
              self.eggTranslations.getResourceAsString,
              self.PROJECT, "ja_resource", 'ja_JP',
              "BOGUS_ENCODING")

        uTxt = self.eggTranslations.getResourceAsString(self.PROJECT,
                             "ja_resource", 'ja_JP', 'shift-jis')

        self.assertEquals(uTxt, u'\u7a76\u6975\u306e\u8cc7\u7523\u9632\u885b\u30ce\u30a6\u30cf\u30a6\u3084\u300c\u6295\u8cc7\u306e\u9769\u547d\u300d\u3068\u306f\u306a\u306b\u304b\u3001\u9280\u884c\u9810\u91d1\u3088\u308a\u5b89\u5168\u306a\n')



    def testNoMOFiles(self):
        erm = EggTranslations()
        r = "test_directory/ini_files/resources_no_mofiles.ini"
        erm.initialize(self.LOCALE_SET, r)

        self.assertEquals(erm.getText(self.PROJECT, "catalog",
                                      "fallback 1", "NOT_FOUND"),
                                      "NOT_FOUND")


    def testNoResources(self):
        erm = EggTranslations()
        r = "test_directory/ini_files/resources_no_resources.ini"
        erm.initialize(self.LOCALE_SET, r)

        self.assertRaises(NameError, erm.getResourceAsStream,
                          self.PROJECT, "txt_resource")

        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "Hello")

        self.assertEquals(value, "Bonjour From Montreal")


class TestI18nValuesAndPathing(EggTestCase):
    """
       The TestCase class ensures that non-ascii
       pathing and values can be correctly processed
       by the EggTranslations API
    """
    PROJECT = u"ResourceManager-EggPlugin\u00FC"
    INI_FILE = u"i18n/resources.ini"
    ENCODING = "UTF-8"

    def testI18nValues(self):
        self.assertEquals(self.eggTranslations.hasKey(self.PROJECT,
                                       u"i18n_key\u00FC"),
                                       True)

        self.assertEquals(self.eggTranslations.hasResource(self.PROJECT,
                                       u"txt_resource"), True)

        self.assertEquals(self.eggTranslations.hasResource(self.PROJECT,
                                       u"catalog", 'en'), True)



        self.assertEquals(self.eggTranslations.getValueForKey(self.PROJECT,
                                          u"i18n_key\u00FC"),
                                          u"\u00FC i18n Value")

        self.assertEquals(self.eggTranslations.getValueForKey(self.PROJECT,
                          u"txt_message"),
                          u"\u00FCThis is a String value in 'French'")

        self.assertEquals(self.eggTranslations.getValueForKey(self.PROJECT,
                             u"txt_message", 'all'),
                             u"\u00FCThis is a String value in 'all'")

        self.assertEquals(self.eggTranslations.getValueForKey(self.PROJECT,
                              u"bogus_message", 'fr_CA'), None)

        self.assertEquals(self.eggTranslations.getValueForKey(self.PROJECT,
                          u"catalog", 'fr'),
                          u"i18n/test_dir/locale/fr/catalog.mo")


    def testI18nPathing(self):
        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "Hello")

        self.assertEquals(value, "Bonjour From Montreal")

        value = self.eggTranslations.getText("BOGUS", "catalog_alt",
                                       "Hello", "Default")

        self.assertEquals(value, "Default")


        value = self.eggTranslations.getText(self.PROJECT, "catalog",
                                       "fallback 1")

        expect = "I correctly handled fallback 1 in English catalog.mo"
        self.assertEquals(value, expect)

        self.assertEquals(
               self.eggTranslations.getResourceAsString(self.PROJECT,
                                "txt_resource"),
                                u"This is the 'French' resource\n")

        self.assertEquals(
               self.eggTranslations.getResourceAsString(self.PROJECT,
                                "txt_resource", 'all'),
                                u"This is the default 'all' resource\n")

if __name__ == "__main__":
    unittest.main()
