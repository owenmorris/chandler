"""
A helper class which sets up and tears down dual RamDB repositories
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

#XXX@BK getext is required for mail code
#   it must be imported before Sharing
#   which imports the mail code
import gettext, os
# set up the gettext locale, so we have a definition of _()
os.environ['LANGUAGE'] = 'en'
gettext.install('chandler', 'locale')

import unittest, sys, logging
import repository.persistence.DBRepository as DBRepository
import repository.item.Item as Item
import application.Parcel as Parcel
import osaf.framework.sharing.Sharing as Sharing
import osaf.framework.sharing.ICalendar as ICalendar
import osaf.contentmodel.ItemCollection as ItemCollection
import osaf.contentmodel.calendar.Calendar as Calendar
import repository.query.Query as Query


class ICalendarTestCase(unittest.TestCase):

    def runTest(self):
        self._setup()
        self.Import(self.repo.view)
        self._teardown()

    def _setup(self):

        rootdir = os.environ['CHANDLERHOME']
        packs = (
         os.path.join(rootdir, 'repository', 'packs', 'schema.pack'),
         os.path.join(rootdir, 'repository', 'packs', 'chandler.pack'),
        )
        parcelpath = [os.path.join(rootdir, 'parcels')]

        handler = logging.FileHandler(os.path.join(rootdir,'chandler.log'))
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)

        namespaces = [
         'http://osafoundation.org/parcels/osaf/framework/sharing',
         'http://osafoundation.org/parcels/osaf/contentmodel/calendar',
        ]

        self.repo = self._initRamDB(packs)
        self.manager = Parcel.Manager.get(self.repo.view,
                                          path=parcelpath)
        self.manager.loadParcels(namespaces)
        # create a sandbox root
        Item.Item("sandbox", self.repo, None)
        self.repo.commit()

    def _teardown(self):
        pass

    def _initRamDB(self, packs):
        repo = DBRepository.DBRepository(None)
        repo.create(ramdb=True, stderr=False, refcounted=True)
        for pack in packs:
            repo.loadPack(pack)
        repo.commit()
        return repo

    def Import(self, view):

        path = os.path.join(os.getenv('CHANDLERHOME') or '.',
                            'parcels', 'osaf', 'framework', 'sharing', 'tests')

        sandbox = self.repo.findPath("//sandbox")

        conduit = Sharing.FileSystemConduit(name="conduit", parent=sandbox,
         sharePath=path, shareName="Chandler.ics", view=view)
        format = ICalendar.ICalendarFormat(name="format", parent=sandbox)
        self.share = Sharing.Share(name="share", parent=sandbox,
         conduit=conduit, format=format)
        self.share.get()

        # @@@ Put some checking of the imported items here
        
        event=format.findUID('BED962E5-6042-11D9-BE74-000A95BB2738')
        self.assert_(event.displayName == u'3 hour event',
         "SUMMARY of first VEVENT not imported correctly, displayName is %s"
         % event.displayName)
        
        # Also, put in a test of updating from a modified ics file.


if __name__ == "__main__":
    unittest.main()
