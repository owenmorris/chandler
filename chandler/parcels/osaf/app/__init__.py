import datetime, os
import application.schema as schema
from application.Parcel import Reference
from repository.schema.Types import Lob
import scripts as Scripts
from i18n import OSAFMessageFactory as _
from osaf import pim

#XXX[i18n] this file needs to have displayName converted to _()

def installParcel(parcel, oldVersion=None):

    from osaf import sharing, startup
    from osaf.framework import scripting

    curDav = Reference.update(parcel, 'currentWebDAVAccount')
    curMail = Reference.update(parcel, 'currentMailAccount')
    curSmtp = Reference.update(parcel, 'currentSMTPAccount')
    curCon = Reference.update(parcel, 'currentContact')

    # Items created in osaf.app (this parcel):

    MakeCollections(parcel)

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

    preReply = pim.EmailAddress.update(parcel, 'PredefinedReplyAddress')

    preSmtp = pim.mail.SMTPAccount.update(parcel, 'PredefinedSMTPAccount',
        displayName=u'Outgoing SMTP mail',
        references=[curSmtp]
    )

    pim.mail.IMAPAccount.update(parcel, 'PredefinedIMAPAccount',
        displayName=u'Incoming IMAP mail',
        replyToAddress=preReply,
        defaultSMTPAccount=preSmtp,
        references=[curMail]
    )

    pim.mail.POPAccount.update(parcel, 'PredefinedPOPAccount',
        displayName=u'Incoming POP mail',
        replyToAddress=preReply,
        defaultSMTPAccount=preSmtp
    )


    testReply = pim.mail.EmailAddress.update(parcel, 'TestReplyAddress')

    testSmtp = pim.mail.SMTPAccount.update(parcel, 'TestSMTPAccount',
        displayName=u'Test SMTP Account',
        isActive=False
    )

    pim.mail.IMAPAccount.update(parcel, 'TestIMAPAccount',
        displayName=u'Test IMAP mail',
        replyToAddress=testReply,
        defaultSMTPAccount=testSmtp,
        isActive=False
    )

    pim.mail.POPAccount.update(parcel, 'TestPOPAccount',
        displayName=u'Test POP mail',
        replyToAddress=testReply,
        defaultSMTPAccount=testSmtp,
        isActive=False
    )

    osafDev = pim.Contact.update(parcel, 'OSAFContact',
        emailAddress=u'dev@osafoundation.org',
        contactName=pim.ContactName.update(parcel, 'OSAFContactName',
           firstName=u'OSAF',
           lastName=u'Development'
        )
    )

    welcome = pim.CalendarEvent.update(parcel, 'WelcomeEvent',
        displayName=u'Welcome to Chandler 0.5',
        startTime=datetime.datetime.combine(datetime.date.today(),
                                            datetime.time(12)),
        duration=datetime.timedelta(minutes=120),
        anyTime=False,
        creator=osafDev,
        location=pim.Location.update(parcel, "OSAFLocation",
            displayName="Open Source Applications Foundation"
        )
    )

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
    from osaf import webserver

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
        path=os.path.join("parcels", "osaf", "app", "webhome"),

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
    # Script to create a new user script item
    scripting.Script.update(parcel, _("Script F1 - Create a New Script"),
                            creator = osafDev,
                            bodyString=scripting.script_file("NewScript.py", Scripts.__file__)
                            )

    # Block Inspector
    scripting.Script.update(parcel, _("Script F2 - Block under cursor"),
                            creator = osafDev,
                            bodyString=scripting.script_file("BlockInspector.py", Scripts.__file__)
                            )

    # Item Inspector
    scripting.Script.update(parcel, _("Script F3 - Item selected"),
                            creator = osafDev,
                            bodyString=scripting.script_file("ItemInspector.py", Scripts.__file__)
                            )

    # Browse selected item
    scripting.Script.update(parcel, _("Script F4 - Browse selected item"),
                            creator = osafDev,
                            bodyString=scripting.script_file("BrowseSelected.py", Scripts.__file__)
                            )

    # Scripts whose name starts with "test" can all be run through a command-line option
    scripting.Script.update(parcel, _("Test - Reload Parcels"),
                            creator = osafDev,
                            bodyString=scripting.script_file("ReloadParcels.py", Scripts.__file__)
                            )

    scripting.Script.update(parcel, _("Test - Event timing example"),
                            creator = osafDev,
                            bodyString=scripting.script_file("EventTiming.py", Scripts.__file__)
                            )

    # The cleanup script, run after all the test scripts
    scripting.Script.update(parcel, _("CleanupAfterTests"),
                            creator = osafDev,
                            bodyString=scripting.script_file("CleanupAfterTests.py", Scripts.__file__)
                            )


def MakeCollections(parcel):
    
    from osaf.pim import KindCollection, ListCollection, FilteredCollection, \
         DifferenceCollection, InclusionExclusionCollection, KindCollection
    
    TrashCollection = \
        ListCollection.update(parcel, 'TrashCollection',
            displayName=_('Trash'),
            renameable=False,
            iconName="Trash"
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

    mineItems = \
        FilteredCollection.update(parcel, 'mineItems',
            source=notes,
            filterExpression='getattr(item, \'isMine\', True)',
            filterAttributes=['isMine'])

    mineMinusGeneratedEvents = \
        DifferenceCollection.update(parcel, 'mineMinusGeneratedEvents',
            sources=[mineItems, generatedEvents])

    # the "All" collection
    InclusionExclusionCollection.update(parcel, 'allCollection',
        displayName=_('All'),
        renameable=False,
        iconName="All",
        iconNameHasKindVariant=True,
        displayNameAlternatives={'None': u'My items',
                                 'MailMessageMixin': u'My mail',
                                 'CalendarEventMixin': u'My calendar',
                                 'TaskMixin': u'My tasks'}
    ).setup(source=mineMinusGeneratedEvents, exclusions=TrashCollection)

    mailCollection = \
         KindCollection.update(parcel, 'mail')
    # workaround bug 3892
    mailCollection.kind=pim.mail.MailMessageMixin.getKind(parcel.itsView)
    mailCollection.recursive=True
    
    inSource = \
        FilteredCollection.update(parcel, 'inSource',
            source=mailCollection,
            filterExpression='getattr(item, \'isInbound\', False)',
            filterAttributes=['isInbound'])

    # The "In" collection
    InclusionExclusionCollection.update(parcel, 'inCollection',
        displayName=_('In'),
        renameable=False,
        iconName="In",
        dontDisplayAsCalendar=True
    ).setup(source=inSource, trash=TrashCollection)

    outSource = \
        FilteredCollection.update(parcel, 'outSource',
            source=mailCollection,
            filterExpression='getattr(item, \'isOutbound\', False)',
            filterAttributes=['isOutbound'])

    # The "Out" collection
    InclusionExclusionCollection.update(parcel, 'outCollection',
        displayName=_('Out'),
        renameable=False,
        iconName="Out",
        dontDisplayAsCalendar=True
    ).setup(source=outSource, trash=TrashCollection)


    # Ensure child parcels are loaded
    schema.synchronize(parcel.itsView, "osaf.framework.certstore")

