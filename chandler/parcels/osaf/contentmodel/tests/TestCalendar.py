"""
Basic Unit tests for calendar
"""

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os

import repository.persistence.XMLRepository as XMLRepository
import repository.parcel.LoadParcels as LoadParcels
import OSAF.contentmodel.calendar.Calendar as Calendar
import application.Globals as Globals

class CalendarTest(unittest.TestCase):

    def setUp(self):
        self.rootdir = os.environ['CHANDLERHOME']
        self.testdir = os.path.join(self.rootdir, 'Chandler', 'repository',
                                    'tests')

        # Create an empty repository
        self.rep = XMLRepository.XMLRepository(os.path.join(self.testdir,
                                                            '__repository__'))
        self.rep.create()

        # Load the schema of schemas
        schemaPack = os.path.join(self.rootdir, 'Chandler', 'repository',
                                  'packs', 'schema.pack')
        self.rep.loadPack(schemaPack)
        self.rep.commit()

        # Load the parcels
        Globals.repository = self.rep
        self.parceldir = os.path.join(self.rootdir, 'Chandler', 'parcels')
        LoadParcels.LoadParcels(self.parceldir, self.rep)

    def testCalendar(self):
        # Check that the globals got created by the parcel
        self.assert_(Calendar.CalendarKind)
        self.assert_(Calendar.CalendarEventKind)
        self.assert_(Calendar.LocationKind)
        self.assert_(Calendar.RecurrencePatternKind)
        self.assert_(Calendar.ReminderKind)

        # Construct a sample item
        calendarItem = Calendar.Calendar("calendarItem")
        calendarEventItem = Calendar.CalendarEvent("calendarEventItem")
        locationItem = Calendar.Location("locationItem")
        recurrenceItem = Calendar.RecurrencePattern("recurrenceItem")
        reminderItem = Calendar.Reminder("reminderItem")

        # Check that each item was created
        self.assert_(calendarItem)
        self.assert_(calendarEventItem)
        self.assert_(locationItem)
        self.assert_(recurrenceItem)
        self.assert_(reminderItem)

    def tearDown(self):
        self.rep.close()
        self.rep.delete()

    def _reopenRepository(self):
        self.rep.commit()
        self.rep.close()
        self.rep.open()

if __name__ == "__main__":
    unittest.main()
