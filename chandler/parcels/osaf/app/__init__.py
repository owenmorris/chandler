import datetime, os
import application.schema as schema
from osaf.contentmodel.Notes import Note
from osaf.contentmodel.photos.Photos import Photo
from osaf.contentmodel.contacts import Contact, ContactName
from osaf.framework.sharing.Sharing import WebDAVAccount
from osaf.contentmodel.mail import (IMAPAccount, POPAccount, SMTPAccount,
                                         EmailAddress)
from application.Parcel import Reference
from osaf.contentmodel.ItemCollection import ItemCollection
from repository.schema.Types import Lob

def installParcel(parcel, oldVersion=None):

    curDav = Reference.update(parcel, 'currentWebDAVAccount')
    curMail = Reference.update(parcel, 'currentMailAccount')
    curSmtp = Reference.update(parcel, 'currentSMTPAccount')
    curCon = Reference.update(parcel, 'currentContact')


    # Items created in osaf.app (this parcel):

    WebDAVAccount.update(parcel,
                         'OSAFWebDAVAccount',
                         displayName=u'OSAF sharing',
                         host=u'pilikia.osafoundation.org',
                         path=u'/dev1',
                         username=u'dev1',
                         password=u'd4vShare',
                         useSSL=False,
                         port=80,
                         references=[curDav]
                         )

    WebDAVAccount.update(parcel,
                         'XythosWebDAVAccount',
                         displayName=u'Xythos sharing',
                         host=u'www.sharemation.com',
                         path=u'/OSAFdot5',
                         username=u'OSAFdot5',
                         password=u'osafdemo',
                         useSSL=False,
                         port=80,
                         )

    WebDAVAccount.update(parcel,
                         'VenueWebDAVAccount',
                         displayName=u'Venue sharing',
                         host=u'webdav.venuecom.com',
                         path=u'/calendar/OSAFdot5/calendars',
                         username=u'OSAFdot5',
                         password=u'demo',
                         useSSL=False,
                         port=80,
                         )

    preReply = EmailAddress.update(parcel, 'PredefinedReplyAddress')

    preSmtp = SMTPAccount.update(parcel, 'PredefinedSMTPAccount',
                                 displayName=u'Outgoing SMTP mail',
                                 references=[curSmtp]
                                )

    IMAPAccount.update(parcel, 'PredefinedIMAPAccount',
                       displayName=u'Incoming IMAP mail',
                       replyToAddress=preReply,
                       defaultSMTPAccount=preSmtp,
                       references=[curMail]
                      )

    POPAccount.update(parcel, 'PredefinedPOPAccount',
                      displayName=u'Incoming POP mail',
                      replyToAddress=preReply,
                      defaultSMTPAccount=preSmtp
                      )


    testReply = EmailAddress.update(parcel, 'TestReplyAddress')

    testSmtp = SMTPAccount.update(parcel, 'TestSMTPAccount',
                                 displayName=u'Test SMTP Account',
                                 isActive=False
                                )

    IMAPAccount.update(parcel, 'TestIMAPAccount',
                       displayName=u'Test IMAP mail',
                       replyToAddress=testReply,
                       defaultSMTPAccount=testSmtp,
                       isActive=False
                      )

    POPAccount.update(parcel, 'TestPOPAccount',
                      displayName=u'Test POP mail',
                      replyToAddress=testReply,
                      defaultSMTPAccount=testSmtp,
                      isActive=False
                     )

    ItemCollection.update(parcel, 'trash',
                          displayName=_('Trash'),
                          renameable=False)
    
    welcome = Photo.update(parcel, 'WelcomePhoto',
      displayName=u'Welcome to Chandler 0.5',
      dateTaken=datetime.datetime.now(),
      creator=Contact.update(parcel, 'OSAFContact',
                             emailAddress=u'dev@osafoundation.org',
                             contactName=ContactName.update(parcel,
                                    'OSAFContactName',
                                    firstName=u'OSAF',
                                    lastName=u'Development')
                            )
     )
    welcome.importFromFile(os.path.join(os.path.dirname(__file__),
        "TeamOSAF.jpg"))

    body = u"""Welcome to the Chandler 0.5 Release!

Chandler 0.5 contains support for early adopter developers who want to start building parcels. For example, developers now can create form-based parcels extending the kinds of information that Chandler manages. This release also brings significant improvements to infrastructure areas such as sharing, and to overall performance and reliability.

In addition to the maturing developer infrastructure, Chandler 0.5 begins to focus on fleshing out calendar features and functionality, supporting basic individual and collaborative calendaring tasks.

As you get started, be sure to set up your email and WebDAV account information under the File > Accounts menu.

For a self-guided demo with accompanying screenshots, point your browser to:
   http://www.osafoundation.org/0.5/GuidedTour.htm

For more details on this release, please visit:
    http://wiki.osafoundation.org/bin/view/Chandler/ChandlerZeroPointFiveReadme

Please note, this release is still intended to be experimental, do not trust your real data with this version. An experimental file import/export feature is available to backup your calendar data.

Thank you for trying Chandler. Your feedback is welcome on our mail lists:
    http://wiki.osafoundation.org/bin/view/Chandler/OsafMailingLists

The Chandler Team"""

    welcome.body = welcome.getAttributeAspect('body', 'type').makeValue(body)
