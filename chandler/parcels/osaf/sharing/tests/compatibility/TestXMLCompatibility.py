import os
import sys
import unittest
import pkg_resources
from elementtree import ElementTree

from PyICU import ICUtzinfo
import datetime

from application import schema
from osaf import sharing, pim
from util import testcase
from osaf.mail.message import messageTextToKind
from chandlerdb.util.c import UUID

CLASS_MAP = {
    'CalendarEvent': (pim, 'EventStamp'),
    'MailMessage': (pim.mail, 'MailStamp'),
    'Task': (pim, 'TaskStamp'),
}



class SharingTestCase(testcase.SingleRepositoryTestCase):
    """
    This is the base class for the other tests in this module, which tests
    backward compatibility of Cloud XML import/export. It was written for
    the stamping-as-annotation implementation, which would otherwise have
    changed the Cloud XML format completely.
    
    The idea is that you have:
    
      - C{filename}: A file containing Cloud XML data, generated from
      
      - C{attributes}: A dictionary of attributes that you expect
                       to be set when importing from C{filename}
                       
   To test Cloud XML import (the C{testImport} method in all subclasses
   that follow), you import the object from C{filename}, and check that
   its attributes match.
   
   To test Cloud XML export (the C{testExport} method in the subclasses),
   you create the object using the _createObject() method, and pass it
   to runExportTest(). That creates a Cloud XML blob for the object, and
   compares that with what's in filename.
   
   If your attributes depend on having a repository view set up (i.e. you
   want to include Items as values), you should override C{setUp}, call
   C{super} to get the view created, make a copy of C{self.attributes}, and
   then update it as necessary.
   
   It's also possible to generate the file in question, by setting
   GENERATE_OUTPUT in the environment, and running this .py as your main().
   The way it's currently written, this will change the UUIDs of the
   generated objects, though.
   """


    GENERATE_OUTPUT = os.getenv("GENERATE_OUTPUT")
    attributes = {} # override this in a subclass
    
    def setUp(self):
        super(SharingTestCase, self).setUp()
        
        repoView = self.view
        
        collection = pim.ListCollection(itsView=self.view, displayName=u"Woo!")
        collection.subscribers = [] # woo!
        self.share = sharing.Share(itsView=self.view, contents=collection)

        # Create our format
        self.share.format = sharing.CloudXMLFormat(itsParent=self.share)
        self.share.filterAttributes = sharing.CALDAVFILTER
        
    def _createObject(self, typeOrName, attributes):
        # Create the given object, usually so that we can go ahead
        # and export it.
        if isinstance(typeOrName, type):
            itemClass = typeOrName
        else:
            module, className = CLASS_MAP[typeOrName]
            itemClass = getattr(module, className, None)
            if itemClass is None:
                itemClass = getattr(module, typeOrName)

        if issubclass(itemClass, schema.Annotation):
            annotationClasses = [itemClass]
            itemClass = itemClass.targetType()
        else:
            annotationClasses = []

        objectAttrs = dict(attributes)
        try:
            del objectAttrs['itsUUID']
        except KeyError:
            pass
        else:
            # if no KeyError, then we know it exists
            uuid = attributes['itsUUID']
            
        # A cheesy hack for our only computed attribute
        try:
            del objectAttrs['stamp_types']
        except KeyError:
            pass
        else:
            for cls in attributes['stamp_types']:
                if not cls in annotationClasses:
                    annotationClasses.append(cls)
            del attributes['stamp_types']

        # A cheesy hack for our only computed attribute
        try:
            triageStatusChanged = attributes['triageStatusChanged']
        except KeyError:
            triageStatusChanged = None
        else:
            del objectAttrs['triageStatusChanged']

        if annotationClasses:
            # Translate the "unqualified" attribute names to fully-qualified
            # ones ... for the given stamp class
            for attr, value in attributes.iteritems():
                for cls in annotationClasses:
                    schemaAttribute = getattr(cls, attr, None)
                    if schemaAttribute is not None:
                        del objectAttrs[attr]
                        objectAttrs[schemaAttribute.name] = value
                        break
            

        if self.GENERATE_OUTPUT: # Note: for pre-stamping-as-annotation code!
            result = itemClass(itsParent=self.share, **objectAttrs)
        else:
            kind = itemClass.getKind(self.view)
            result = kind.instantiateItem(None, self.share, uuid, withInitialValues=True)
                                            
            for key, value in objectAttrs.iteritems():
                setattr(result, key, value)
               
                
            if annotationClasses:
                 for cls in annotationClasses:
                    if issubclass(cls, pim.Stamp): 
                        cls(result).add()

        if triageStatusChanged is not None:
            result.triageStatusChanged = triageStatusChanged
        
        return result
    
    @staticmethod
    def _canonicalizeXml(xml):
        # A very rough attempt at canonicalization, so that we'll
        # still be able to compare xml output even if the order of
        # attributes changes.
        tree = ElementTree.XML(xml) # If this raises, the test fails
        
        items = []
        remaining = [tree]
        for thisElt in remaining:
            children = thisElt.getchildren()
            if children:
                # Remove surrounding whitespace if this element
                # has sub-elements
                thisElt.text = thisElt.tail = None

                # Sorting as is done below is not good enough, as the order
                # in which attributes are shared also determines when a
                # given item reference is shared by value. Such shared by
                # value item references need to be pulled out of the tree,
                # appended and sorted as well so as to compare these trees
                # predictably.
                canonicalChildren = []
                for child in children:
                    child.tail = '\n'
                    if child.get('uuid') and child.getchildren():
                        items.append(child)
                        remaining.append(child)
                        child = ElementTree.Element(child.tag,
                                                    uuid=child.get('uuid'))
                        child.tail = '\n'
                    canonicalChildren.append(child)

                # Strictly speaking, we should only reorder attributes
                # of items, not, say, the children of a 'list' cardinality
                # attribute. However, for our purposes, it's probably OK to
                # assume that switching to stamping-as-annotation won't have
                # re-ordered 'list' attributes.
                sortedChildren = sorted(canonicalChildren,
                                        key = lambda x: x.tag)

                # Now replace all children with the sorted version.
                # Yay for elementtree's slice replacement!
                thisElt[:] = sortedChildren
                remaining.extend(sortedChildren)

        for item in sorted(items, key = lambda x: x.get('uuid')):
            tree.append(item)

        return ElementTree.tostring(tree, 'UTF-8')
                    
        
    def createObject(self, typeName):
        return self._createObject(typeName, self.attributes)

    def runExportTest(self, item):
        # Create the xml for the given item ...
        result = self.share.format.exportProcess(item)

        if self.GENERATE_OUTPUT:
            # Write out to self.filename if GENERATE_OUTPUT is True ...
            expected = result
            path = pkg_resources.resource_filename(__name__, self.filename)
            out = open(path, "wb")
            out.write(result)
            out.close()
            sys.stderr.write("\nWrote %d bytes to %s\n" % (len(result), path))
        else:
            # Otherwise, just read it from self.filename; this is the value
            # we expect
            expected = pkg_resources.resource_string(__name__, self.filename)
        
        self.failUnless(len(expected) > 0, "Unable to read %s" % (self.filename,))
        result = self._canonicalizeXml(result)
        expected = self._canonicalizeXml(expected)
        try:
            self.failUnlessEqual(result, expected)
        except:
            sys.stderr.write("\n----------------\nFailed ... Expected:\n")
            sys.stderr.write("\n%s\n ... Actual:%s\n----------------\n" % (expected, result))
            raise
            
    def importObject(self):
        # Use our share format to import the given object from
        # self.filename
        text = pkg_resources.resource_string(__name__, self.filename)
        result = self.share.format.importProcess(self.view, text)
        
        self.failIfEqual(result, None)
        
        return result
        
    def checkImportedAttributes(self, object, expected=None):
        # Helper to do the work of checking that the values of
        # object's attributes matches what's in the dict 'expected'.
        if expected is None:
            expected = self.attributes

        for attr, value in expected.iteritems():
            objectValue = getattr(object, attr)
            if isinstance(value, list):
                try:
                    i = iter(objectValue)
                except TypeError:
                    pass
                else:
                    objectValue = list(i)

            if attr == 'triageStatusChanged':
                self.assertTrue(objectValue <= value,
                                "Value for attribute %s of imported object %r didn't match" %(attr, object))
            else:
                self.failUnlessEqual(objectValue, value,
                                     "Value for attribute %s of imported object %r didn't match" %(attr, object))


class EventTestCase(SharingTestCase):

    filename = "Event.xml"
        
    attributes = {
        'itsUUID': UUID('5502c952-410a-11db-f9a1-0016cbca6aed'),
        'displayName': u'This is my \u2022ed event',
        'allDay': False,
        'anyTime': False,
        'icalUID': '9d7813fe-4100-11db-9645-0016cbca6aed',
        'createdOn':
            datetime.datetime(2006, 8, 24, 10, 4, 23,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'startTime':
            datetime.datetime(2006, 9, 10, 16, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'duration': datetime.timedelta(minutes=30),
        'body': u'This is the contents\nof the event',
        'triageStatusChanged': -1157944145.0,
    }

    def testExport(self):
        event = self.createObject('CalendarEvent')
        
        # @@@ [grant] Hack for working against both 2006/09/10 trunk
        # and stamping-as-annotation branch
        item = getattr(event, 'itsItem', event)
        self.runExportTest(item)
        
    def testImport(self):
        
        eventItem = self.importObject()
        
        # Check the base item (i.e. the notes)
        self.failUnless(isinstance(eventItem, pim.Note))
        expected = dict((key, self.attributes.get(key)) for key in
                            ('itsUUID', 'displayName', 'createdOn', 'body',
                             'triageStatusChanged'))
        self.checkImportedAttributes(eventItem, expected=expected)
        
        # Make sure we ended up with the right stamps
        self.failUnlessEqual(list(pim.Stamp(eventItem).stamp_types),
                             [pim.EventStamp])

        # ... and now check various stamped attributes. (Many of the event
        # ones will be missing because we applied the CALDAVFILTER).
        event = pim.EventStamp(eventItem)
        expected = dict((key, self.attributes.get(key)) for key in
                            ('icalUID',))
        self.checkImportedAttributes(event, expected=expected)
        
        # Make sure importing an Event didn't delete attributes
        # on MailStamp.
        mailMsg = pim.mail.MailStamp(eventItem)
        self.failUnlessEqual(mailMsg.mimeContainer, None)
        self.failUnlessEqual(list(mailMsg.mimeParts), [])
        self.failUnlessEqual(list(mailMsg.toAddress), [])
        self.failUnlessEqual(mailMsg.fromAddress, None)
        self.failUnlessEqual(mailMsg.replyToAddress, None)


class TaskTestCase(SharingTestCase):

    filename = "Task.xml"
        
    attributes = {
        'itsUUID': UUID('ee0dc68e-41ea-11db-ca3a-0016cbca6aed'),
        'displayName': u'A vewwy vewwy important task',
        'createdOn':
            datetime.datetime(2006, 8, 27, 12, 1, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'dueDate':
            datetime.datetime(2006, 9, 12, 13, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'body': u'Here are some fascinating task notes',
        'triageStatus': pim.TriageEnum.later,
        'triageStatusChanged': -1159945337.0
    }

    def testExport(self):
        task = self.createObject('Task')
        
        # @@@ [grant] Hack for working against both 2006/09/10 trunk
        # and stamping-as-annotation branch
        item = getattr(task, 'itsItem', task)
        self.runExportTest(item)
        
    def testImport(self):
        
        taskItem = self.importObject()
        
        # Check the base item (i.e. the notes)
        self.failUnless(isinstance(taskItem, pim.Note))
        expected = dict((key, self.attributes.get(key)) for key in
                            ('itsUUID', 'displayName', 'createdOn', 'body',
                             'triageStatus', 'triageStatusChanged'))
        self.checkImportedAttributes(taskItem, expected=expected)
        
        # Make sure we ended up with the right stamps
        self.failUnlessEqual(list(pim.Stamp(taskItem).stamp_types),
                             [pim.TaskStamp])

        # Note: dueDate isn't part of the sharing cloud, so we don't
        # need to check it.
        
        # Check that pim.TaskStamp() works on the imported Item.
        task = pim.TaskStamp(taskItem)

class MailTestCase(SharingTestCase):

    filename = "Mail.xml"
        
    attributes = {
        'itsUUID': UUID('5b44e42a-420a-11db-b64e-0016cbca6aed'),
        'subject': u'This is the subject',
        'createdOn':
            datetime.datetime(2006, 8, 27, 12, 1, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'body': u'This is a highly\npoignant email message\n',
        'mimeType': 'message/rfc822',
        'triageStatus': pim.TriageEnum.later,
        'triageStatusChanged': -1159945337.0
    }
    
    def setUp(self):
        super(MailTestCase, self).setUp()
        
        self.fromAddress = self._createObject(pim.mail.EmailAddress, dict(
               itsUUID=UUID('5b446b8a-420a-11db-b64e-0016cbca6aed'),
                emailAddress="someone@somewhere.example.com",
                fullName="Sum Won",
                createdOn = datetime.datetime(2006, 9, 10, 17, 3, 11,
                                    tzinfo=ICUtzinfo.getInstance("US/Pacific")),
                triageStatus = pim.TriageEnum.done,
                triageStatusChanged = -1158958218.0))
        
        self.toAddress = self._createObject(pim.mail.EmailAddress, dict(
               itsUUID=UUID('5b44b9aa-420a-11db-b64e-0016cbca6aed'),
               emailAddress="someone-else@example.com",
               fullName="Sum Wonelse",
               createdOn=datetime.datetime(2006, 9, 10, 17, 3, 9,
                    tzinfo=ICUtzinfo.getInstance("US/Pacific")),
               triageStatus=pim.TriageEnum.done,
               triageStatusChanged=-1158958391.0))

        self.attributes = dict(self.attributes)
        self.attributes.update(toAddress=[self.toAddress], 
                               fromAddress=self.fromAddress)

    def testExport(self):
        message = self.createObject('MailMessage')
        
        # @@@ [grant] Hack for working against both 2006/09/10 trunk
        # and stamping-as-annotation branch
        message = getattr(message, 'itsItem', message)
        self.runExportTest(message)
        
    def testImport(self):
        
        mailItem = self.importObject()
        
        # Check the base item (i.e. the notes)
        self.failUnless(isinstance(mailItem, pim.Note))
        expected = dict((key, self.attributes.get(key)) for key in
                            ('itsUUID', 'createdOn', 'body',
                             'triageStatus', 'triageStatusChanged'))
        self.checkImportedAttributes(mailItem, expected=expected)
        
        # Make sure we ended up with the right stamps
        self.failUnlessEqual(list(pim.Stamp(mailItem).stamp_types),
                             [pim.mail.MailStamp])

        # Check that pim.MailStamp() works on the imported Item.
        mailObject = pim.mail.MailStamp(mailItem)
        # ... and check the mail-specific attributes
        expected = dict((key, self.attributes.get(key)) for key in
                            ('subject', 'fromAddress', 'toAddress'))
        self.checkImportedAttributes(mailObject, expected=expected)

class ComplexMailTestCase(SharingTestCase):
    filename = "ComplexMail.xml"
        
    attributes = {
        'itsUUID': UUID('09da180e-442a-11db-bd6e-0016cbca6aed'),
        'subject': u'ALTERNATIVE MIMETYPE TEST',
        'createdOn':
            datetime.datetime(2006, 8, 27, 12, 1, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'mimeType': 'message/rfc822',
        'body': '\n'.join(("This should be in the body of the email", "",
                "--", "Anthony Baxter     &lt;anthony@interlink.com.au&gt;",
                "It's never too late to have a happy childhood.", "")),
        'triageStatus': pim.TriageEnum.now,
        'triageStatusChanged': -1158292128.0
    }
    
    def setUp(self):
        super(ComplexMailTestCase, self).setUp()

        address = self._createObject(pim.mail.EmailAddress, dict(
               itsUUID=UUID('09dd5f96-442a-11db-bd6e-0016cbca6aed'),
                emailAddress="anthony@interlink.com.au",
                fullName="Anthony Baxter",
                createdOn = datetime.datetime(2006, 9, 14, 12, 48, 48,
                                    tzinfo=ICUtzinfo.getInstance("US/Pacific")),
                triageStatus = pim.TriageEnum.now,
                triageStatusChanged = -1158288128.0))
                
        mimeBinary = self._createObject(pim.mail.MIMEBinary, dict(
            itsUUID=UUID('09dbbb82-442a-11db-bd6e-0016cbca6aed'),
            filename=u"Attachment-1.obj",
            filesize=775,
            mimeType=u"application/octet-stream",
            body=u"",
            createdOn=datetime.datetime(2006, 9, 14, 12, 48, 48, 228990,
                                    tzinfo=ICUtzinfo.getInstance("US/Pacific")),
            triageStatus=pim.TriageEnum.now,
            triageStatusChanged=-1158288128.0))
            
        mimeText = self._createObject(pim.mail.MIMEText, dict(
              itsUUID=UUID('09dc66d6-442a-11db-bd6e-0016cbca6aed'),
              filename=u"Attachment-2.html",
              filesize=19,
              mimeType="text/html",
              body=u"&lt;br&gt; Test Two&lt;/br&gt;\n",
              createdOn=datetime.datetime(2006, 9, 14, 12, 48, 48, 232830,
                                    tzinfo=ICUtzinfo.getInstance("US/Pacific")),
              triageStatus=pim.TriageEnum.now,
              triageStatusChanged=-1158292128.0))

        
        self.attributes = dict(self.attributes)
        self.attributes.update(toAddress=[address], 
                               fromAddress=address,
                               replyToAddress=address,
                               mimeParts=[mimeBinary, mimeText])
    
    def testExport(self):

        if self.GENERATE_OUTPUT:
            mimeDir = pkg_resources.resource_filename("osaf.mail.tests",
                                                       "mime_tests")
            f = open(os.path.join(mimeDir, "test_alternative"), "rb")
            mimeText = f.read()
            f.close()
            message = messageTextToKind(self.view, mimeText)
            
        else:
            message = self.createObject('MailMessage')
        
        # @@@ [grant] Hack for working against both 2006/09/10 trunk
        # and stamping-as-annotation branch
        message = getattr(message, 'itsItem', message)
        self.runExportTest(message)
            
    def testImport(self):
        mailItem = self.importObject()
        
        # Check the base item (i.e. the notes)
        self.failUnless(isinstance(mailItem, pim.Note))
        expected = dict((key, self.attributes.get(key)) for key in
                            ('itsUUID', 'createdOn', 'body',
                             'triageStatus', 'triageStatusChanged'))
        self.checkImportedAttributes(mailItem, expected=expected)
        
        # Make sure we ended up with the right stamps
        self.failUnlessEqual(list(pim.Stamp(mailItem).stamp_types),
                             [pim.mail.MailStamp])

        # Check that pim.MailStamp() works on the imported Item.
        mailObject = pim.mail.MailStamp(mailItem)
        # ... and check the mail-specific attributes
        expected = dict((key, self.attributes.get(key)) for key in
                            ('subject', 'fromAddress', 'toAddress'))
        self.checkImportedAttributes(mailObject, expected=expected)

class EmptyMailTestCase(SharingTestCase):

    filename = "EmptyMail.xml"
        
    attributes = {
        'itsUUID': UUID('7b3b015e-6f57-11db-ed86-0016cbca6aed'),
        'subject': u'Untitled',
        'createdOn':
            datetime.datetime(2006, 10, 31, 12, 19, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'body': u'',
        'mimeType': 'message/rfc822',
        'toAddress': [],
        'triageStatus': pim.TriageEnum.now,
        'triageStatusChanged': -1156502242.0
    }


    def testExport(self):
        message = self.createObject('MailMessage')
        
        # @@@ [grant] Hack for working against both 2006/09/10 trunk
        # and stamping-as-annotation branch
        message = getattr(message, 'itsItem', message)
        self.runExportTest(message)
        
    def testImport(self):
        
        mailItem = self.importObject()
        
        # Check the base item (i.e. the notes)
        self.failUnless(isinstance(mailItem, pim.Note))
        expected = dict((key, self.attributes.get(key)) for key in
                            ('itsUUID', 'createdOn', 'body',
                             'triageStatus', 'triageStatusChanged'))
        self.checkImportedAttributes(mailItem, expected=expected)
        
        # Make sure we ended up with the right stamps
        self.failUnlessEqual(list(pim.Stamp(mailItem).stamp_types),
                             [pim.mail.MailStamp])

        # Check that pim.MailStamp() works on the imported Item.
        mailObject = pim.mail.MailStamp(mailItem)
        # ... and check the mail-specific attributes
        expected = dict((key, self.attributes.get(key)) for key in
                            ('subject', 'fromAddress', 'toAddress'))
        self.checkImportedAttributes(mailObject, expected=expected)
        
    def testSync(self):
        self.importObject() # create the object
        self.testImport()

class EventTaskTestCase(SharingTestCase):

    filename = "EventTask.xml"
        
    attributes = {
        'itsUUID': UUID('711cc574-4cff-11db-af32-c2da3320d5d3'),
        'displayName': u'Hi',
        'allDay': False,
        'anyTime': False,
        'icalUID': '711cc574-4cff-11db-af32-c2da3320d5d3',
        'createdOn':
            datetime.datetime(2006, 9, 25, 18, 36, 33,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'startTime':
            datetime.datetime(2006, 9, 10, 16, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'duration': datetime.timedelta(minutes=60),
        'triageStatus': pim.TriageEnum.now,
        'triageStatusChanged': -1159263393.0,
        'stamp_types': [pim.TaskStamp],
    }
    
    def setUp(self):
        super(EventTaskTestCase, self).setUp()
        
        contactName = self._createObject(pim.ContactName, dict(
            itsUUID=UUID('9b65343e-49b1-11db-e5fa-f7316ff1be10'),
            firstName=u'Chandler',
            lastName=u'User',
            createdOn=datetime.datetime(2006, 9, 21, 13, 41, 50, 272075,
                                    tzinfo=ICUtzinfo.getInstance("US/Pacific")),
            triageStatus=pim.TriageEnum.now,
            triageStatusChanged=-1158900110.0))
          
        contact = self._createObject(pim.Contact, dict(
            itsUUID=UUID('9b839032-49b1-11db-e5fa-f7316ff1be10'),
            contactName=contactName,
            displayName=u'Me',
            createdOn=datetime.datetime(2006, 9, 21, 13, 41, 50, 470953,
                                    tzinfo=ICUtzinfo.getInstance("US/Pacific")),
            triageStatus=pim.TriageEnum.now,
            triageStatusChanged=-1158900110.0))
            
        
        self.attributes = dict(self.attributes)
        
        

    def testExport(self):
        event = self.createObject('CalendarEvent')
        
        # @@@ [grant] Hack for working against both 2006/09/10 trunk
        # and stamping-as-annotation branch
        item = getattr(event, 'itsItem', event)
        self.runExportTest(item)
        
    def testImport(self):
        
        eventItem = self.importObject()
        
        # Check the base item (i.e. the notes)
        self.failUnless(isinstance(eventItem, pim.Note))
        expected = dict((key, self.attributes.get(key)) for key in
                            ('itsUUID', 'displayName', 'createdOn',
                             'triageStatusChanged', 'triageStatus'))
        self.checkImportedAttributes(eventItem, expected=expected)
        
        # Make sure we ended up with the right stamps
        self.failUnlessEqual(set(pim.Stamp(eventItem).stamp_types),
                             set([pim.EventStamp, pim.TaskStamp]))

        # ... and now check various stamped attributes. (Many of the event
        # ones will be missing because we applied the CALDAVFILTER).
        event = pim.EventStamp(eventItem)
        expected = dict((key, self.attributes.get(key)) for key in
                            ('icalUID',))
        self.checkImportedAttributes(event, expected=expected)


class MailedEventTaskTestCase(SharingTestCase):

    filename = "MailedEventTask.xml"
        
    attributes = {
        'itsUUID': UUID('711cc574-4cff-11db-af32-c2da3320d5d3'),
        'displayName': 'Here we go.....',
        'allDay': False,
        'anyTime': False,
        'icalUID': '711cc574-4cff-11db-af32-c2da3320d5d3',
        'createdOn':
            datetime.datetime(2006, 9, 25, 18, 36, 33, 571631,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'startTime':
            datetime.datetime(2006, 9, 10, 16, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'duration': datetime.timedelta(minutes=60),
        'mimeType': 'message/rfc822',
        'triageStatus': pim.TriageEnum.later,
        'triageStatusChanged': -1158900317.0,
        'stamp_types': [pim.TaskStamp, pim.mail.MailStamp],
    }

    def testExport(self):
        event = self.createObject('CalendarEvent')
        
        # @@@ [grant] Hack for working against both 2006/09/10 trunk
        # and stamping-as-annotation branch
        item = getattr(event, 'itsItem', event)
        self.runExportTest(item)
        
    def testImport(self):
        
        eventItem = self.importObject()
        
        # Check the base item (i.e. the notes)
        self.failUnless(isinstance(eventItem, pim.Note))

        # Make sure we ended up with the right stamps
        self.failUnlessEqual(set(pim.Stamp(eventItem).stamp_types),
                             set([pim.EventStamp, pim.TaskStamp,
                                  pim.mail.MailStamp]))

        expected = dict((key, self.attributes.get(key)) for key in
                            ('itsUUID', 'displayName', 'createdOn',
                             'triageStatusChanged', 'triageStatus'))
        self.checkImportedAttributes(eventItem, expected=expected)
        
        # ... and now check various stamped attributes. (Many of the event
        # ones will be missing because we applied the CALDAVFILTER).
        event = pim.EventStamp(eventItem)
        expected = dict((key, self.attributes.get(key)) for key in
                            ('icalUID',))
        self.checkImportedAttributes(event, expected=expected)
        
class ShareTestCase(SharingTestCase):

    filename = "Share.xml"
        
    attributes = {
        'itsUUID': UUID('d1514632-47ea-11db-a812-0016cbca6aed'),
        'displayName': u'Shared Collection',
        'filterAttributes': list(iter(sharing.CALDAVFILTER)),
        'createdOn':
            datetime.datetime(2006, 8, 27, 12, 1, 0,
                              tzinfo=ICUtzinfo.getInstance("US/Pacific")),
        'triageStatusChanged': -1158704779.0,
    }
    
    def setUp(self):
        super(ShareTestCase, self).setUp()

        collection = self._createObject(pim.ListCollection, dict(
               itsUUID=UUID('d1511b12-47ea-11db-a812-0016cbca6aed'),
               displayName=u'A new collection',
               createdOn = datetime.datetime(2005, 4, 11, 8, 12, 33,
                                    tzinfo=ICUtzinfo.getInstance("US/Pacific")),
               triageStatus = pim.TriageEnum.now,
               triageStatusChanged = -1158191886.0))
               
        try:
            pim.EventStamp
        except AttributeError:
            # "old" (pre-stamping-as-annotation) classes
            classNames = [
                "osaf.pim.calendar.Calendar.CalendarEventMixin",
                "osaf.pim.tasks.TaskMixin",
                "osaf.pim.mail.MailMessageMixin",
            ]
        else:
            classNames = ["%s.%s" % (cls.__module__, cls.__name__)
                 for cls in (pim.EventStamp, pim.TaskStamp, pim.mail.MailStamp)]
            
                
        self.attributes = dict(self.attributes)
        self.attributes.update(contents=collection)
    
    def testExport(self):
        share = self.createObject(sharing.Share)
        self.runExportTest(share)

    def testImport(self):
        shareItem = self.importObject()
        
        # Check the base item
        self.failUnless(isinstance(shareItem, sharing.Share))
        self.checkImportedAttributes(shareItem)
        
if __name__ == "__main__":
    if SharingTestCase.GENERATE_OUTPUT:
        existingArguments = sys.argv[1:]
        sys.argv[1:] = ()
        tests = []
        for arg in existingArguments:
            if arg.startswith("-"):
                sys.argv.append(arg)
            else:
                tryAttr = "%sTestCase" % (arg,)
                if tryAttr in globals():
                    tests.append("%s.testExport" % (tryAttr,))
            
        if not tests:
            tests = ["%s.testExport" % (k,) for k, v in globals().iteritems()
                     if hasattr(v, "testExport")]
        sys.argv.extend(tests)
                            
    unittest.main()
