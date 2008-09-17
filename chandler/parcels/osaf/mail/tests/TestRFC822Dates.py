import unittest
from PyICU import ICUtzinfo
from datetime import datetime
from osaf.mail.utils import RFC2822DateToDatetime, datetimeToRFC2822Date

class ParseTestCase(unittest.TestCase):
    def failUnlessDatetimesMatch(self, dt1, dt2, *args):
        self.failUnlessEqual(
            dt1.replace(tzinfo=None),
            dt2.replace(tzinfo=None)
        )
        
        self.failUnlessEqual(dt1.tzinfo, dt2.tzinfo)

    def testNoTZ(self):
        """If we pass in a tz of None, returned value should be in UTC"""
        self.failUnlessDatetimesMatch(
            RFC2822DateToDatetime("Fri, 8 Feb 2008 14:53:16 -0800"),
            datetime(2008, 2, 8, 22, 53, 16)
        )

    def test(self):
        tz = ICUtzinfo.getInstance("America/Los_Angeles")
        self.failUnlessDatetimesMatch(
            RFC2822DateToDatetime("Thu, 07 Feb 2008 08:59:39 -0600", tz),
            datetime(2008, 2, 7, 6, 59, 39, tzinfo=tz)
        ) # America/Los_Angeles is 2 hours behind -0600 in Feb


    def testWayInFuture(self):
        self.failUnlessDatetimesMatch(
            RFC2822DateToDatetime("Mon, 10 Oct 2044 11:03:00"),
            datetime(2044, 10, 10, 11, 3)
        )

    def testWayInPast(self):
        self.failUnlessDatetimesMatch(
            RFC2822DateToDatetime("Thu, 17 Jan 1822 23:22:16"),
            datetime(1822, 1, 17, 23, 22, 16)
        )

class UnparseTestCase(unittest.TestCase):

    def testWayInFuture(self):
        self.failUnlessEqual(
            datetimeToRFC2822Date(datetime(2171, 11, 3, 2, 45, 3)),
            "Sun, 03 Nov 2171 02:45:03"
        )

    def testWayInPast(self):
        self.failUnlessEqual(
            datetimeToRFC2822Date(datetime(1811, 1, 2, 23, 15, 37)),
            "Wed, 02 Jan 1811 23:15:37"
        )

    def testTZ(self):
        tz = ICUtzinfo.getInstance("Africa/Johannesburg")
        self.failUnlessEqual(
            datetimeToRFC2822Date(datetime(2004, 4, 13, 13, 13, 0, tzinfo=tz)),
            "Tue, 13 Apr 2004 13:13:00 +0200"
        )

    def testNoTZ(self):
        self.failUnlessEqual(
            datetimeToRFC2822Date(datetime(2013, 10, 26, 1, 0, 33)),
            "Sat, 26 Oct 2013 01:00:33"
        )
        

if __name__ == "__main__":
    unittest.main()
