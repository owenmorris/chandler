"""
A helper class which sets up and tears down a repository and anything else
that a parcel loader unit test might need
"""
__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import unittest, os, sys

# from repository.persistence.XMLRepository import XMLRepository
import repository.tests.RepositoryTestCase as RepositoryTestCase

import application
import application.Globals as Globals

class ParcelLoaderTestCase(RepositoryTestCase.RepositoryTestCase):

    def setUp(self):

        # Globals.chandlerDirectory = os.path.join(os.environ['CHANDLERHOME'],
        #  "chandler")
        # self.parcelPath = [os.path.join(Globals.chandlerDirectory, "parcels")]

        super(ParcelLoaderTestCase, self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'chandler', 'application',
         'tests')

        super(ParcelLoaderTestCase, self)._openRepository(self)

        # repodir = os.path.join(self.testdir, '__repository__')
        # self.rep = XMLRepository(repodir)
        # self.rep.create()
        # bootstrapPack = os.path.join(Globals.chandlerDirectory,
        #  'repository', 'packs', 'schema.pack')
        # self.rep.loadPack(bootstrapPack)

        Globals.repository = self.rep

        # Notification manager is now needed for Item Collections(?):
        from osaf.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()
        # self.manager = application.Parcel.Manager.getManager(repository=self.rep,path=self.parcelPath)

    # def tearDown(self):
    #     self.rep.close()
    #     self.rep.delete()
