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

from osaf.framework.notifications.Notification import Notification

def MakeEvent():
    eventKind = Globals.repository.findPath('//parcels/osaf/framework/notifications/schema/Event')
    event = eventKind.newItem(None, Globals.repository)
    return event

def repositoryCallback(view, changes, notification, **kwds):
    if notification == 'History':
        eventPath = '//parcels/osaf/framework/commit_history'
    else:
        return

    event = Globals.repository.findPath(eventPath)

    from osaf.framework.notifications.Notification import Notification
    note = Notification(event)
    note.threadid = id(threading.currentThread())
    d = { 'changes' : changes , 'keywords' : kwds }
    note.SetData(d)

    #print uuid, notification, reason, kwds

    Globals.notificationManager.PostNotification(note)

import repository.tests.RepositoryTestCase as RepositoryTestCase
class NMTest(RepositoryTestCase.RepositoryTestCase):
    """ Notification Manager TestCase """

    def setUp(self):
        super(NMTest,self)._setup(self)

        self.testdir = os.path.join(self.rootdir, 'parcels',
         'osaf', 'framework', 'notifications', 'tests')

        super(NMTest,self)._openRepository(self)

        # set Globals.repository
        Globals.repository = self.rep

        # Create and start the notification manager
        from osaf.framework.notifications.NotificationManager import NotificationManager
        Globals.notificationManager = NotificationManager()

        # Load the parcels
        self.loadParcel("http://osafoundation.org/parcels/osaf/framework/notifications/schema")


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

