"""
Notification Manager unit tests

@copyright: Copyright (c) 2004 Open Source Applications Foundation
@license: U{http://osafoundation.org/Chandler_0.1_license_terms.htm}
"""

import logging, threading
import unittest, os
#import repository.persistence.XMLRepository as XMLRepository

import application.Globals as Globals
import repository.item.Item as Item

from OSAF.framework.notifications.Notification import Notification

def MakeEvent():
    eventKind = Globals.repository.find('//parcels/OSAF/framework/notifications/schema/Event')
    event = eventKind.newItem(None, Globals.repository)
    return event

def repositoryCallback(uuid, notification, reason, **kwds):
    if notification == 'History':
        eventPath = '//parcels/OSAF/framework/item_' + reason
    else:
        return

    event = Globals.repository.find(eventPath)

    from OSAF.framework.notifications.Notification import Notification
    note = Notification(event)
    note.threadid = id(threading.currentThread())
    d = { 'uuid' : uuid, 'keywords' : kwds }
    note.SetData(d)

    #print uuid, notification, reason, kwds

    Globals.notificationManager.PostNotification(note)

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
        self._loadParcel("OSAF/framework")

        # Create and start the notification manager
        from OSAF.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()

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

        nm.Subscribe([event], 'thisShouldBeAnUUID', dummyCallback)

        event.Post(None)

        # this will break when notifications are done async
        self.assert_(self.callbackCalled)
        del self.callbackCalled

        # test duplicate subscription
        try:
            nm.Subscribe([event], 'thisShouldBeAnUUID', dummyCallback)
        except:
            pass
        else:
            self.assert_(False)



    def test_RepositoryNotifications(self):
        """ tests Unsubscribe() """
        nm = Globals.notificationManager
        rep = Globals.repository

        # initialization code
        nm.PrepareSubscribers()
        rep.commit()
        rep.addNotificationCallback(repositoryCallback)

        def onItemChanged(note):
            uuid = note.GetData()['uuid']
            print 'Changed:', Globals.repository[uuid].getItemPath()
        def onItemAdded(note):
            uuid = note.GetData()['uuid']
            print 'Added:', Globals.repository[uuid].getItemPath()
        def onItemDeleted(note):
            uuid = note.GetData()['uuid']
            print 'Deleted:', uuid

        # subscribe to changed, added, deleted events
        e = rep.find('//parcels/OSAF/framework/item_changed')
        nm.Subscribe([e], 1, onItemChanged)
        e = rep.find('//parcels/OSAF/framework/item_added')
        nm.Subscribe([e], 2, onItemAdded)
        e = rep.find('//parcels/OSAF/framework/item_deleted')
        nm.Subscribe([e], 3, onItemDeleted)

        print 'adding event'
        e = MakeEvent()
        Globals.repository.commit()

        print '\n'
        print 'deleting event'
        e.delete()
        Globals.repository.commit()





if __name__ == "__main__":
    # set logging
    handler = logging.FileHandler('test.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)

    unittest.main()

