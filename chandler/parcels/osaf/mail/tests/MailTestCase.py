import unittest, os, sys

import repository.tests.RepositoryTestCase as RepositoryTestCase

import application
import application.Globals as Globals

class MailTestCase(RepositoryTestCase.RepositoryTestCase):

    def setUp(self):

        super(MailTestCase, self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'parcels', 'osaf',
         'contentmodel', 'mail')

        super(MailTestCase, self)._openRepository(self)

        Globals.repository = self.rep

        # Notification manager is now needed for Item Collections(?):
        from osaf.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()
