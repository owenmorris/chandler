from util.testcase import NRVTestCase
from osaf.pim import *
from datetime import *
from repository.item.Item import Item
from PyICU import ICUtzinfo

"""
Tests for domain model support of edit/update workflows.

TODO: lastModifiedBy support
"""

class UpdateTestCase(NRVTestCase):
    def setUp(self):
        if not hasattr(type(self), 'view'):
            super(UpdateTestCase, self).setUp()
            type(self).view = self.view
            
        self.sandbox = Item("sandbox", self.view, None)
        
    def tearDown(self):
        self.sandbox.delete(recursive=True)


    def testInitial(self):
        item = ContentItem(itsParent=self.sandbox)
        
        self.failUnlessEqual(list(item.modifiedFlags), [])

    def testEdit(self):
        dt = datetime(2007, 1, 13, 8, 33, tzinfo=ICUtzinfo.default)
        item = ContentItem(
                  itsParent=self.sandbox,
                  createdOn=dt,
                  lastModification=Modification.created,
                  lastModified=dt,
               )
               
        # Now, change it to be edited ...
        dt += timedelta(seconds=30)
        item.changeEditState(Modification.edited, when=dt)
        
        # ... check that its lastModification is correct,
        self.failUnlessEqual(item.lastModification, Modification.edited)
        
        # ... that its modifiedFlags are correct
        self.failUnlessEqual(set(item.modifiedFlags),
                             set([Modification.edited]))
        # ... and that its lastModified got set correctly.
        self.failUnlessEqual(item.lastModified, dt)
        
    def testUpdate(self):
        item = ContentItem(itsParent=self.sandbox)
        #XXX Brian K: Items can be placed in an updated
        # state without first being in a sent state.
        # Users can be added or removed from a edit / update
        # workflow. Modification state is shared by
        # all users.
        #self.failUnlessRaises(ValueError, item.changeEditState,
        #                      Modification.updated)
                              
        # Mark it as sent ...
        item.changeEditState(Modification.sent)
        
        # ... and now try mark it as updated
        item.changeEditState(Modification.updated)
        
        self.failUnlessEqual(item.lastModification,
                             Modification.updated)
                             
        # Lastly, check that updating an edited item ...
        item.changeEditState(Modification.edited)
        
        # ... and then updating it ...
        item.changeEditState(Modification.updated)
        
        # ... clears the edited bit
        self.failIf(Modification.edited in item.modifiedFlags)
        self.failUnlessEqual(item.lastModification, Modification.updated)
                             
    def testModDate(self):
        start = datetime.now(ICUtzinfo.default)
        
        item = ContentItem(itsParent=self.sandbox)
        
        self.failUnless(item.createdOn >= start,
                        "Time ran backwards during creation?")
        
        start = datetime.now(ICUtzinfo.default)
        item.changeEditState(Modification.created)
        end = datetime.now(ICUtzinfo.default)
        
        self.failUnless(start <= item.lastModified <= end,
                        "lastModified not set to datetime.now()?")

        self.failUnlessEqual(item.lastModification, Modification.created)
        
    def testQueueAndSend(self):
        dt = datetime.now(ICUtzinfo.default)
        
        # Make anedited ContentItem
        item = ContentItem(
                  itsParent=self.sandbox,
                  modifiedFlags=set([Modification.edited]),
                  lastModified=dt,
               )
               
        # Now, change it to be queued ...
        dt += timedelta(seconds=5)
        item.changeEditState(Modification.queued, when=dt)
        
        # ... check that its lastModification is correct,
        self.failUnlessEqual(item.lastModification, Modification.queued)
        
        # ... that its modifiedFlags are correct, including clearing
        # the edited flag.
        self.failUnlessEqual(set(item.modifiedFlags),
                             set([Modification.queued]))
        # ... and that its lastModified got set correctly.
        self.failUnlessEqual(item.lastModified, dt)



        dt += timedelta(seconds=30)
        item.changeEditState(Modification.sent, when=dt)
        self.failUnlessEqual(set(item.modifiedFlags),
                             set([Modification.sent]))

        # Edit / Update workflows support sending of
        # the same message multiple times so
        # commenting out this code
        #self.failUnlessRaises(ValueError, item.changeEditState,
        #                      Modification.sent)

        # Now, queue again
        dt += timedelta(seconds=30)
        item.changeEditState(Modification.queued, when=dt)

        # ... check that its lastModification is correct,
        self.failUnlessEqual(item.lastModification, Modification.queued)
        self.failUnlessEqual(item.lastModified, dt)
        self.failUnlessEqual(set(item.modifiedFlags),
                             set([Modification.queued, Modification.sent]))

        # ... and make sure that marking it updated clears the queued flag
        dt += timedelta(seconds=30)
        item.changeEditState(Modification.updated, when=dt)
        self.failUnlessEqual(item.lastModification, Modification.updated)
        self.failUnlessEqual(item.lastModified, dt)
        self.failUnlessEqual(set(item.modifiedFlags),
                             set([Modification.updated, Modification.sent]))

        
    def testSend(self):
        dt = datetime.now(ICUtzinfo.default)
        
        # Make an edited ContentItem
        item = ContentItem(
                  itsParent=self.sandbox,
                  modifiedFlags=set([Modification.edited]),
                  lastModified=dt,
               )
               
        # Now, change it to be sent ...
        dt += timedelta(seconds=5)
        item.changeEditState(Modification.sent, when=dt)
        
        # ... check that its lastModification is correct,
        self.failUnlessEqual(item.lastModification, Modification.sent)
        
        # ... that its modifiedFlags are correct, including clearing
        # the edited flag.
        self.failUnlessEqual(set(item.modifiedFlags),
                             set([Modification.sent]))
        # ... and that its lastModified got set correctly.
        self.failUnlessEqual(item.lastModified, dt)

        # Edit / Update workflows support sending of
        # the same message multiple times so
        # commenting out this code
        #self.failUnlessRaises(ValueError, item.changeEditState, 
        #                      Modification.sent)

    def testByline(self):
        # @@@ [grant] should add code here to make sure the dependence
        # on en_US locale is made explicit
        
        email = EmailAddress(itsParent=self.sandbox, fullName=u'Tommy Totoro',
                             emailAddress=u'totoro@example.com')

        created = datetime(2004, 12, 11, 11, tzinfo=ICUtzinfo.default)
        item = ContentItem(itsParent=self.sandbox, createdOn=created)

        # Make sure you can't _set_ the byline
        self.failUnlessRaises(AttributeError, setattr, item, 'byline', u"Yuck!")
        
        self.failUnlessEqual(item.byline, u"created on 12/11/04 11:00 AM")
        
        
        # Explicitly set the state to created ...
        item.changeEditState(Modification.created, when=created)

        # Change the state to edited ...
        edited = datetime(2006, 12, 31, 22, 11, tzinfo=ICUtzinfo.default)
        item.changeEditState(Modification.edited, when=edited, who=email)
        self.failUnlessEqual(item.byline,
                             u"edited by Tommy Totoro on 12/31/06 10:11 PM")

        # Change the state to queued ...
        item.changeEditState(Modification.queued, when=edited, who=email)
        self.failUnlessEqual(item.byline,
                             u"queued by Tommy Totoro on 12/31/06 10:11 PM")
        
        # Now, sent ...
        sent = datetime(2036, 1, 12, 2, 15, tzinfo=ICUtzinfo.default)
        item.changeEditState(Modification.sent, when=sent, who=email)
        self.failUnlessEqual(item.byline,
                             u"sent by Tommy Totoro on 1/12/36 2:15 AM")

        # Lastly, updated ...
        updated = datetime(2007, 5, 17, 4, 22, 53, tzinfo=ICUtzinfo.default)
        item.changeEditState(Modification.updated, when=updated)
        self.failUnlessEqual(item.byline, u"updated on 5/17/07 4:22 AM")

    def testError(self):
        item = ContentItem(itsParent=self.sandbox)
        
        # Make sure we start out with no error
        self.failIf(item.hasLocalAttributeValue('error'))
        
        # ... and test its defaultValue
        self.failUnless(item.error is None)
        
        # Set the error
        errorString = u"Oh, no, a big boo-boo happened."
        item.error = errorString
        
        self.failUnlessEqual(errorString, item.error)
        
        # Now edit the item, and check that it doesn't lose its error
        item.changeEditState()
        self.failUnlessEqual(errorString, item.error)
        
        # Queue the item
        item.changeEditState(Modification.queued)
        self.failUnless(item.error is None,
                        "queuing should clear any error")
        
        # Same, for sending
        item.error = errorString
        item.changeEditState(Modification.sent)
        self.failUnless(item.error is None,
                        "sending should clear any error")
        

if __name__ == "__main__":
    import unittest
    unittest.main()
