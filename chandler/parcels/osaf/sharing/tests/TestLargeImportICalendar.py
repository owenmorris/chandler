import unittest, os
from repository.tests.RepositoryTestCase import RepositoryTestCase
import osaf.sharing.Sharing as Sharing
import osaf.sharing.ICalendar as ICalendar

class TestLargeImport(RepositoryTestCase):

    def testImport(self):
        if os.environ.get('CHANDLER_PERFORMANCE_TEST'):
            self.loadParcel("parcel:osaf.contentmodel.calendar")
            path = os.path.join(os.getenv('CHANDLERHOME') or '.',
                                'parcels', 'osaf', 'sharing', 'tests')

            conduit = Sharing.FileSystemConduit(name="conduit",
                                                sharePath=path,
                                                shareName="3kevents.ics",
                                                view=self.rep.view)
            format = ICalendar.ICalendarFormat(name="format", view=self.rep.view)
            share = Sharing.Share(name="share", conduit=conduit, format=format,
                                  view=self.rep.view)
            share.get()


if __name__ == "__main__":
    unittest.main()
