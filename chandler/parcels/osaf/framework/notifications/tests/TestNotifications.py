""" Notification Manager unit tests """

__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import logging
import unittest, os
#import repository.persistence.XMLRepository as XMLRepository

import application.Globals as Globals
import repository.item.Item as Item

from OSAF.framework.notifications.Notification import Notification

def MakeEvent():
    eventKind = Globals.repository.find('//parcels/OSAF/framework/notifications/schema/Event')
    event = eventKind.newItem(None, Globals.repository)
    return event

import repository.tests.RepositoryTestCase as RepositoryTestCase
class NMTest(RepositoryTestCase.RepositoryTestCase):
    def _loadParcel(self, relPath):
        """ load only the parcel we need (and it's dependencies) """
        import repository.parcel.LoadParcels as LoadParcels

        self.parceldir = os.path.join(self.rootdir, 'Chandler', 'parcels')

        uri = "//parcels/%s" % relPath
        uri = uri.replace(os.path.sep, "/")
        parcelDir = os.path.join(self.rootdir, 'Chandler', 'parcels', relPath)
        LoadParcels.LoadParcel(parcelDir, uri, self.parceldir, self.rep)
        self.assert_(self.rep.find(uri))

    def setUp(self):
        RepositoryTestCase.RepositoryTestCase.setUp(self)

        # set Globals.repository
        Globals.repository = self.rep

        # Load the parcels
        #
        #self.parceldir = os.path.join(self.rootdir, 'Chandler', 'parcels')
        #import repository.parcel.LoadParcels as LoadParcels
        #LoadParcels.LoadParcels(self.parceldir, self.rep)
        self._loadParcel("OSAF/framework/notifications/schema")
        self._loadParcel("OSAF/framework/utils/indexer")

        # Create and start the notification manager
        from OSAF.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()



    def test_FindNotifications(self):
        """ tests FindNotifications() """
        """
        nm = Globals.notificationManager

        e1 = MakeEvent('dumb/event')
        e2 = MakeEvent('dumbevent')

        # need to call this after all events are made or else they don't currently get picked up
        nm.PrepareSubscribers()

        events = nm.FindEvents('.*')
        self.assert_(e1 in events)
        self.assert_(e2 in events)

        events = nm.FindEvents('dumb.*')
        self.assert_(e1 in events)
        self.assert_(e2 in events)
        
        events = nm.FindEvents('dumb/.*')
        self.assert_(e1 in events)
        self.assert_(e2 not in events)

        events = nm.FindEvents('dumbevent')
        self.assert_(e1 not in events)
        self.assert_(e2 in events)
        """


    def test_Subscribe(self):
        """ tests Subscribe() """
        nm = Globals.notificationManager

        event = MakeEvent()

        # need to call this after all events are made or else they don't currently get picked up
        nm.PrepareSubscribers()

        # test a callback
        self.callbackCalled = False
        def dummyCallback(notification):
            self.callbackCalled = True

        nm.Subscribe(event, 'thisShouldBeAnUUID', dummyCallback)

        notification = Notification(event, None, None)
        nm.PostNotification(notification)

        # this will break when notifications are done async
        self.assert_(self.callbackCalled)
        del self.callbackCalled

        # test duplicate subscription
        try:
            nm.Subscribe(event, 'thisShouldBeAnUUID', dummyCallback)
        except:
            pass
        else:
            self.assert_(False)



    #def test_Unsubscribe(self):
    #    """ tests Unsubscribe() """
    #    print 'Testing Unsubscribe()'

    #def test_PostNotification(self):
    #    """ tests PostNotification() """
    #    print 'Testing PostNotification()'

if __name__ == "__main__":
    # set logging
    handler = logging.FileHandler('test.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)

    unittest.main()









