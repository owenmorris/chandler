import datetime, os
import application.schema as schema
from application.Parcel import Reference
from repository.schema.Types import Lob

def installParcel(parcel, oldVersion=None):

    curDav = Reference.update(parcel, 'currentWebDAVAccount')
    curMail = Reference.update(parcel, 'currentMailAccount')
    curSmtp = Reference.update(parcel, 'currentSMTPAccount')
    curCon = Reference.update(parcel, 'currentContact')

    sharing = schema.ns("osaf.framework.sharing", parcel)
    model = schema.ns("osaf.contentmodel", parcel)
    mail = schema.ns("osaf.contentmodel.mail", parcel)
    photos = schema.ns("osaf.contentmodel.photos", parcel)
    contacts = schema.ns("osaf.contentmodel.contacts", parcel)

    # Items created in osaf.app (this parcel):

    sharing.WebDAVAccount.update(parcel, 'OSAFWebDAVAccount',
        displayName=u'OSAF sharing',
        host=u'pilikia.osafoundation.org',
        path=u'/dev1',
        username=u'dev1',
        password=u'd4vShare',
        useSSL=False,
        port=80,
        references=[curDav]
    )

    sharing.WebDAVAccount.update(parcel, 'XythosWebDAVAccount',
        displayName=u'Xythos sharing',
        host=u'www.sharemation.com',
        path=u'/OSAFdot5',
        username=u'OSAFdot5',
        password=u'osafdemo',
        useSSL=False,
        port=80,
    )

    sharing.WebDAVAccount.update(parcel, 'VenueWebDAVAccount',
        displayName=u'Venue sharing',
        host=u'webdav.venuecom.com',
        path=u'/calendar/OSAFdot5/calendars',
        username=u'OSAFdot5',
        password=u'demo',
        useSSL=False,
        port=80,
    )

    preReply = mail.EmailAddress.update(parcel, 'PredefinedReplyAddress')

    preSmtp = mail.SMTPAccount.update(parcel, 'PredefinedSMTPAccount',
        displayName=u'Outgoing SMTP mail',
        references=[curSmtp]
    )

    mail.IMAPAccount.update(parcel, 'PredefinedIMAPAccount',
        displayName=u'Incoming IMAP mail',
        replyToAddress=preReply,
        defaultSMTPAccount=preSmtp,
        references=[curMail]
    )

    mail.POPAccount.update(parcel, 'PredefinedPOPAccount',
        displayName=u'Incoming POP mail',
        replyToAddress=preReply,
        defaultSMTPAccount=preSmtp
    )


    testReply = mail.EmailAddress.update(parcel, 'TestReplyAddress')

    testSmtp = mail.SMTPAccount.update(parcel, 'TestSMTPAccount',
        displayName=u'Test SMTP Account',
        isActive=False
    )

    mail.IMAPAccount.update(parcel, 'TestIMAPAccount',
        displayName=u'Test IMAP mail',
        replyToAddress=testReply,
        defaultSMTPAccount=testSmtp,
        isActive=False
    )

    mail.POPAccount.update(parcel, 'TestPOPAccount',
        displayName=u'Test POP mail',
        replyToAddress=testReply,
        defaultSMTPAccount=testSmtp,
        isActive=False
    )


    model.ItemCollection.ItemCollection.update(parcel, 'trash',
        displayName=_('Trash'),
        renameable=False
    )

    welcome = photos.Photo.update(parcel, 'WelcomePhoto',
        displayName=u'Welcome to Chandler 0.5',
        dateTaken=datetime.datetime.now(),
        creator=contacts.Contact.update(parcel, 'OSAFContact',
             emailAddress=u'dev@osafoundation.org',
             contactName=contacts.ContactName.update(parcel, 'OSAFContactName',
                firstName=u'OSAF',
                lastName=u'Development'
             )
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


    # Set up the main web server
    startup = schema.ns("osaf.startup", parcel)
    webserver = schema.ns("osaf.webserver", parcel)

    startup.Startup.update(parcel, "startServers",
        invoke = "osaf.webserver.start_servers"
    )

    webserver.Server.update(parcel, "mainServer",
        # Port to listen on.  1888 was the year Raymond Chandler was born.
        port=1888,

        # This path specifies the "doc root" of this web server, and is
        # relative to webserver/servers, but you may also put in an
        # absolute path if you wish.
        #
        path="webhome",

        resources = [
            webserver.Resource.update(parcel, "lobsterResource",
                displayName="Lob Server",
                location="lobs",
                resourceClass=schema.importString(
                    "osaf.servlets.lobviewer.LobViewerResource"
                ),
            ),
            webserver.Resource.update(parcel, "photoResource",
                displayName="Photo Viewer",
                location="photos",
                resourceClass=schema.importString(
                    "osaf.servlets.photos.PhotosResource"
                ),
            ),
            webserver.Resource.update(parcel, "repoResource",
                displayName="Repository Viewer",
                location="repo",
                resourceClass=schema.importString(
                    "osaf.servlets.repo.RepoResource"
                ),
            )
        ]
    )

