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


import unittest
from datetime import datetime, time
from PyICU import *
from osaf.pim.calendar import DateTimeUtil
from repository.tests.RepositoryTestCase import RepositoryTestCase

class AbstractTestCase(RepositoryTestCase):
    """
    An abstract class that sets global PyICU locale and timezone
    settings at setUp time, and then restores the defaults in
    test tearDown. This makes for more reproducible
    parsing/formatting unit tests.
    
    @ivar locale: Override to run your test class with a different
                  locale.
    @type locale: PyICU.Locale

    @ivar tzinfo:
    @type tzinfo: PyICU.ICUtzinfo
    """

    locale = Locale.getUS()

    def setUp(self):
        super(AbstractTestCase, self).setUp()
        self.tzinfo = self.view.tzinfo.getInstance("US/Pacific")
        self.__savedLocale = Locale.getDefault()
        self.__savedTzinfo = self.view.tzinfo.default

        Locale.setDefault(self.locale)
        self.view.tzinfo.setDefault(self.tzinfo)

    def tearDown(self):
        super(AbstractTestCase, self).tearDown()
        self.view.tzinfo.setDefault(self.__savedTzinfo)
        Locale.setDefault(self.__savedLocale)



class ShortDateParse(AbstractTestCase):

    def testSimple(self):
        parsed = DateTimeUtil.shortDateFormat.parse(self.view, "12/11/2004")

        self.failUnlessEqual(parsed, datetime(2004,12,11))

    def testFullYear(self):
        parsed = DateTimeUtil.shortDateFormat.parse(self.view, "3/7/2005")

        self.failUnlessEqual(parsed, datetime(2005,3,7))

    def testOutOfRangeYear(self):
        # Whoa, dude, that's a crazy year. But it triggers
        # bug 5650 on all platforms (e.g. 1904 works on
        # Unixes).
        parsed = DateTimeUtil.shortDateFormat.parse(self.view, "4/18/102")

        self.failUnlessEqual(parsed, datetime(102,4,18))

    def testSimpleWithReference(self):
        tzinfo = self.view.tzinfo.getInstance("US/Eastern")
        parsed = DateTimeUtil.shortDateFormat.parse(self.view, 
                    "12/11/2004",
                    datetime(2006, 1, 1,tzinfo=tzinfo))

        self.failUnlessEqual(parsed, datetime(2004,12,11, tzinfo=tzinfo))

    def testFullYearWithReference(self):
        tzinfo = self.view.tzinfo.getInstance("Asia/Shanghai")
        parsed = DateTimeUtil.shortDateFormat.parse(self.view, 
                    "3/7/2005",
                    datetime(2002, 1, 9,tzinfo=tzinfo))

        self.failUnlessEqual(parsed, datetime(2005,3,7, tzinfo=tzinfo))

    def testOutOfRangeYearWithReference(self):
        tzinfo = self.view.tzinfo.getInstance("Europe/Rome")
        parsed = DateTimeUtil.shortDateFormat.parse(self.view, 
                    "4/18/102",
                    datetime(1999,9,9,tzinfo=tzinfo))

        self.failUnlessEqual(parsed, datetime(102,4,18, tzinfo=tzinfo))


class ShortTimeParse(AbstractTestCase):

    def testPM(self):
        parsed = DateTimeUtil.shortTimeFormat.parse(self.view, "12:03 PM")

        self.failUnlessEqual(parsed.timetz(), time(12, 3))

    def testAM(self):
        parsed = DateTimeUtil.shortTimeFormat.parse(self.view, "12:52 AM")

        self.failUnlessEqual(parsed.timetz(), time(0, 52))


"""
Tests to write:

- Other formatters in DateTimeUtil.py
- Output tests
- Other locales/timezones

"""

if __name__ == "__main__":
    unittest.main()
