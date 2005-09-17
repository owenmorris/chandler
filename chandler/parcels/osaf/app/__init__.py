import datetime, os
import application.schema as schema
from application.Parcel import Reference
from repository.schema.Types import Lob
import scripts as Scripts
from i18n import OSAFMessageFactory as _
from osaf import pim
from osaf import messages
from osaf.framework.types.DocumentTypes import ColorType


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
        displayName=_(u'%(accountName)s sharing') % {'accountName': 'OSAF'},
        host=u'pilikia.osafoundation.org',
        path=u'/dev1',
        username=u'dev1',
        password=u'd4vShare',
        useSSL=False,
        port=80,
        references=[curDav]
    )

    sharing.WebDAVAccount.update(parcel, 'XythosWebDAVAccount',
        displayName=_(u'%(accountName)s sharing') % {'accountName': 'Xythos'},
        host=u'www.sharemation.com',
        path=u'/OSAFdot5',
        username=u'OSAFdot5',
        password=u'osafdemo',
        useSSL=True,
        port=443,
    )

    sharing.WebDAVAccount.update(parcel, 'VenueWebDAVAccount',
        displayName=_(u'%(accountName)s sharing') % {'accountName': 'Venue'},
        host=u'webdav.venuecom.com',
        path=u'/calendar/OSAFdot5/calendars',
        username=u'OSAFdot5',
        password=u'demo',
        useSSL=False,
        port=80,
    )

    preReply = pim.EmailAddress.update(parcel, 'PredefinedReplyAddress')

    preSmtp = pim.mail.SMTPAccount.update(parcel, 'PredefinedSMTPAccount',
        displayName=_(u'Outgoing %(accountType)s mail') % {'accountType': 'SMTP'},
        references=[curSmtp]
    )

    pim.mail.IMAPAccount.update(parcel, 'PredefinedIMAPAccount',
        displayName=_(u'Incoming %(accountType)s mail') % {'accountType': 'IMAP'},
        replyToAddress=preReply,
        defaultSMTPAccount=preSmtp,
        references=[curMail]
    )

    pim.mail.POPAccount.update(parcel, 'PredefinedPOPAccount',
        displayName=_(u'Incoming %(accountType)s mail') % {'accountType': 'POP'},
        replyToAddress=preReply,
        defaultSMTPAccount=preSmtp
    )


    testReply = pim.mail.EmailAddress.update(parcel, 'TestReplyAddress')

    #[i18n] Test Acccounts are not displayed to the user and do not require localization
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
        displayName=_(u'Welcome to Chandler 0.5'),
        startTime=datetime.datetime.combine(datetime.date.today(),
                                            datetime.time(12)),
        duration=datetime.timedelta(minutes=120),
        anyTime=False,
        creator=osafDev,
        location=pim.Location.update(parcel, "OSAFLocation",
            displayName=u"Open Source Applications Foundation"
        )
    )

    body = _(u"""Welcome to the Chandler 0.5 Release!

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

The Chandler Team""")

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
                displayName=u"Lob Server",
                location="lobs",
                resourceClass=schema.importString(
                    "osaf.servlets.lobviewer.LobViewerResource"
                ),
            ),
            webserver.Resource.update(parcel, "photoResource",
                displayName=u"Photo Viewer",
                location="photos",
                resourceClass=schema.importString(
                    "osaf.servlets.photo.PhotosResource"
                ),
            ),
            webserver.Resource.update(parcel, "repoResource",
                displayName=u"Repository Viewer",
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
    scripting.Script.update(parcel, _(u"Script F1 - Create a New Script"),
                            creator = osafDev,
                            bodyString=scripting.script_file("NewScript.py", Scripts.__file__)
                            )

    # Block Inspector
    scripting.Script.update(parcel, _(u"Script F2 - Block under cursor"),
                            creator = osafDev,
                            bodyString=scripting.script_file("BlockInspector.py", Scripts.__file__)
                            )

    # Item Inspector
    scripting.Script.update(parcel, _(u"Script F3 - Item selected"),
                            creator = osafDev,
                            bodyString=scripting.script_file("ItemInspector.py", Scripts.__file__)
                            )

    # Browse selected item
    scripting.Script.update(parcel, _(u"Script F4 - Browse selected item"),
                            creator = osafDev,
                            bodyString=scripting.script_file("BrowseSelected.py", Scripts.__file__)
                            )

    # Scripts whose name starts with "test" can all be run through a command-line option
    scripting.Script.update(parcel, _(u"Test - Reload Parcels"),
                            creator = osafDev,
                            bodyString=scripting.script_file("ReloadParcels.py", Scripts.__file__)
                            )

    scripting.Script.update(parcel, _(u"Test - Event timing example"),
                            creator = osafDev,
                            bodyString=scripting.script_file("EventTiming.py", Scripts.__file__)
                            )

    # The cleanup script, run after all the test scripts
    scripting.Script.update(parcel, _(u"CleanupAfterTests"),
                            creator = osafDev,
                            bodyString=scripting.script_file("CleanupAfterTests.py", Scripts.__file__)
                            )


def MakeCollections(parcel):

    from osaf.pim import (
        KindCollection, ListCollection, FilteredCollection,
        DifferenceCollection, InclusionExclusionCollection, KindCollection,
        UnionCollection
    )

    TrashCollection = \
        ListCollection.update(parcel, 'TrashCollection',
            displayName=_(u"Trash"),
            renameable=False,
            iconName="Trash",
            color = ColorType(255, 192, 128, 255), #Orange
            colorizeIcon = False
        )

    notes = KindCollection.update(parcel, 'notes')
    # workaround bug 3892
    notes.kind = pim.Note.getKind(parcel.itsView)
    notes.recursive=True

    nonGeneratedNotes = FilteredCollection.update(parcel, 'nonGeneratedNotes',
        source=notes,
        filterExpression='not getattr(item, \'isGenerated\', False)',
        filterAttributes=['isGenerated']
    )

    notMine = UnionCollection.update(parcel, 'notMine')
    # @@@MOR Hmm, I need to somehow make rep's initialValue be a MultiUnion()
    notMine._sourcesChanged()

    mine = DifferenceCollection.update(parcel, 'mine',
        sources=[nonGeneratedNotes, notMine]
    )

    # the "All" collection
    allCollection = InclusionExclusionCollection.update(parcel, 'allCollection',
        displayName=_(u"All My Items"),
        renameable = False,
        iconName = "All",
        colorizeIcon = False,
        iconNameHasKindVariant = True,
        color = ColorType(128, 192, 255, 255), #Blue

        displayNameAlternatives = {'None': _(u'My items'),
                                   'MailMessageMixin': _(u'My mail'),
                                   'CalendarEventMixin': _(u'My calendar'),
                                   'TaskMixin': _(u'My tasks')}
    ).setup(source=mine, exclusions=TrashCollection)


    events = \
        KindCollection.update(parcel, 'events')
    # workaround bug 3892
    events.kind=pim.CalendarEventMixin.getKind(parcel.itsView)
    events.recursive=True


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
    inCollection = InclusionExclusionCollection.update(parcel, 'inCollection',
        displayName=_(u"In"),
        renameable=False,
        iconName="In",
        dontDisplayAsCalendar=True,
        color = ColorType(128, 255, 128, 255), # Green
        colorizeIcon = False
    ).setup(source=inSource, trash=TrashCollection)

    outSource = \
        FilteredCollection.update(parcel, 'outSource',
            source=mailCollection,
            filterExpression='getattr(item, \'isOutbound\', False)',
            filterAttributes=['isOutbound'])

    # The "Out" collection
    outCollection = InclusionExclusionCollection.update(parcel, 'outCollection',
        displayName=_(u"Out"),
        renameable=False,
        iconName="Out",
        dontDisplayAsCalendar=True,
        color = ColorType(255, 128, 128, 255), #Red
        colorizeIcon = False
    ).setup(source=outSource, trash=TrashCollection)

    # The Sidebar collection
    ListCollection.update(parcel, 'sidebarCollection',
                          refCollection=[allCollection,
                                         inCollection,
                                         outCollection,
                                         TrashCollection])

