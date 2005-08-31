import datetime, os
import application.schema as schema
from application.Parcel import Reference
from repository.schema.Types import Lob
from osaf import pim
from osaf.pim import KindCollection, ListCollection, FilteredCollection, \
     DifferenceCollection, InclusionExclusionCollection, KindCollection
from feeds import FeedChannel
import scripts as Scripts
from i18n import OSAFMessageFactory as _

#XXX[i18n] this file needs to have displayName converted to _()

def installParcel(parcel, oldVersion=None):

    curDav = Reference.update(parcel, 'currentWebDAVAccount')
    curMail = Reference.update(parcel, 'currentMailAccount')
    curSmtp = Reference.update(parcel, 'currentSMTPAccount')
    curCon = Reference.update(parcel, 'currentContact')

    sharing = schema.ns("osaf.sharing", parcel)
    pim = schema.ns("osaf.pim", parcel)
    mail = schema.ns("osaf.pim.mail", parcel)
    photos = schema.ns("photos", parcel)
    contacts = schema.ns("osaf.pim.contacts", parcel)
    startup = schema.ns("osaf.startup", parcel)
    scripting = schema.ns("osaf.framework.scripting", parcel)

    # Items created in osaf.app (this parcel):

    MakeCollections(parcel)

    startup.PeriodicTask.update(parcel, "FeedUpdateTask",
        invoke="feeds.FeedUpdateTaskClass",
        run_at_startup=True,
        interval=datetime.timedelta(minutes=30)
    )

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
        useSSL=True,
        port=443,
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

    osafDev = contacts.Contact.update(parcel, 'OSAFContact',
        emailAddress=u'dev@osafoundation.org',
        contactName=contacts.ContactName.update(parcel, 'OSAFContactName',
           firstName=u'OSAF',
           lastName=u'Development'
        )
    )

    welcome = photos.Photo.update(parcel, 'WelcomePhoto',
        displayName=u'Welcome to Chandler 0.5',
        dateTaken=datetime.datetime.now(),
        creator=osafDev
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
                    "osaf.servlets.photo.PhotosResource"
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

    """
    Scripts.  These files are located in our Scripts parcel.
    """

    # Startup script used to test Chandler startup
    scripting.Script.update(parcel, _("Script F1 - Startup Test Script"),
                            creator = osafDev,
                            bodyString=scripting.script_file("StartupTest.py", Scripts.__file__)
                            )

    scripting.Script.update(parcel, _("Script F12 - Create a New Script"),
                            creator = osafDev,
                            bodyString=scripting.script_file("NewScript.py", Scripts.__file__)
                            )

    scripting.Script.update(parcel, _("Event timing example"),
                            creator = osafDev,
                            bodyString=scripting.script_file("EventTiming.py", Scripts.__file__)
                            )


def MakeCollections(parcel):
    
    TrashCollection = \
        pim.ListCollection.update(parcel, 'TrashCollection',
            displayName=_('Trash'),
            renameable=False
        )
    
    notes = \
        KindCollection.update(parcel, 'notes')
    # workaround bug 3892
    notes.kind = pim.Note.getKind(parcel.itsView)
    notes.recursive=True
    
    events = \
        KindCollection.update(parcel, 'events')
    # workaround bug 3892
    events.kind=pim.CalendarEventMixin.getKind(parcel.itsView)
    events.recursive=True
                                  
    generatedEvents = \
        FilteredCollection.update(parcel, 'generatedEvents',
            source=events,
            filterExpression='getattr(item, \'isGenerated\', True)',
            filterAttributes=['isGenerated'])

    notesMinusGeneratedEvents = \
        DifferenceCollection.update(parcel, 'notesMinusGeneratedEvents',
            sources=[notes, generatedEvents])
    
    allSource = \
        DifferenceCollection.update(parcel, 'allSource',
            sources=[notesMinusGeneratedEvents, TrashCollection])

    allSourceMinusAllExclusions = \
        DifferenceCollection.update(parcel, 'allSourceMinusAllExclusions',
            sources=[allSource,
                     ListCollection.update(parcel, 'allExclusions')])

    # the "All" collection
    InclusionExclusionCollection.update(parcel, 'allCollection',
        displayName=_('All'),
        renameable=False,
        sources=[allSourceMinusAllExclusions,
                 ListCollection.update(parcel, 'allInclusions')])

    mail = \
         KindCollection.update(parcel, 'mail')
    # workaround bug 3892
    mail.kind=pim.mail.MailMessageMixin.getKind(parcel.itsView)
    mail.recursive=True
    
    inSource = \
        FilteredCollection.update(parcel, 'inSource',
            source=mail,
            filterExpression='getattr(item, \'isInbound\', False)',
            filterAttributes=['isInbound'])

    inSourceMinusInExclusions = \
        DifferenceCollection.update(parcel, 'inSourceMinusInExclusions',
            sources=[inSource,
                     ListCollection.update(parcel, 'inExclusions')])

    # The "In" collection
    InclusionExclusionCollection.update(parcel, 'inCollection',
        displayName=_('In'),
        renameable=False,
        sources=[inSourceMinusInExclusions,
                 ListCollection.update(parcel, 'inInclusions')])

    outSource = \
        FilteredCollection.update(parcel, 'outSource',
            source=mail,
            filterExpression='getattr(item, \'isOutbound\', False)',
            filterAttributes=['isOutbound'])

    outSourceMinusOutExclusions = \
        DifferenceCollection.update(parcel, 'outSourceMinusOutExclusions',
            sources=[outSource,
                     ListCollection.update(parcel, 'outExclusions')])
                                               
    InclusionExclusionCollection.update(parcel, 'outCollection',
        displayName=_('Out'),
        renameable=False,
        sources=[outSourceMinusOutExclusions,
                 ListCollection.update(parcel, 'outInclusions')])
