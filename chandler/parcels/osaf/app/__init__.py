import datetime, os
import application.schema as schema
from application.Parcel import Reference
from repository.schema.Types import Lob
import scripts as Scripts
from i18n import OSAFMessageFactory as _
from PyICU import ICUtzinfo
from osaf import pim
from osaf import messages
from osaf.framework.types.DocumentTypes import ColorType
import osaf.framework.scripting as scripting
import wx


def installParcel(parcel, oldVersion=None):

    from osaf import sharing, startup
    from osaf.framework import scripting

    curDav = Reference.update(parcel, 'currentWebDAVAccount')
    curMail = Reference.update(parcel, 'currentMailAccount')
    curSmtp = Reference.update(parcel, 'currentSMTPAccount')
    curCon = Reference.update(parcel, 'currentContact')

    me = pim.Contact.update(parcel, 'me',
        displayName=_(u'Me'),
        contactName=pim.ContactName.update(parcel, 'meName',
           firstName=_(u'Chandler'),
           lastName=_(u'User')
        ),
        references=[curCon]
    )

    # Items created in osaf.app (this parcel):

    MakeCollections(parcel)

    sharing.WebDAVAccount.update(parcel, 'CosmoWebDAVAccount',
        displayName=_(u'Sharing'),
        host=u'cosmo-demo.osafoundation.org',
        path=u'',
        username=u'',
        password=u'',
        useSSL=True,
        port=443,
        references=[curDav]
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

    noonToday = datetime.datetime.combine(
        datetime.date.today(),
        datetime.time(12, tzinfo=ICUtzinfo.getDefault()))
        
    welcome = pim.CalendarEvent.update(parcel, 'WelcomeEvent',
        displayName=_(u'Welcome to Chandler 0.5'),
        startTime=noonToday,
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
        path=unicode(os.path.join("parcels", "osaf", "app", "webhome")),

        resources = [
            webserver.Resource.update(parcel, "lobsResource",
                displayName=u"Lob Server",
                location=u"lobs",
                resourceClass=schema.importString(
                    "osaf.servlets.lobviewer.LobViewerResource"
                ),
            ),
            webserver.Resource.update(parcel, "photoResource",
                displayName=u"Photo Viewer",
                location=u"photos",
                resourceClass=schema.importString(
                    "osaf.servlets.photo.PhotosResource"
                ),
            ),
            webserver.Resource.update(parcel, "repoResource",
                displayName=u"Repository Viewer",
                location=u"repo",
                resourceClass=schema.importString(
                    "osaf.servlets.repo.RepoResource"
                ),
                autoView=False
            )
        ]
    )

    """
    Scripts.  These files are located in our Scripts parcel.
    """
    # Script to create a new user script item
    newScript = scripting.Script.update(parcel, 'New Script',
                                        displayName=_(u"F1 - Create a New Script"),
                                        fkey=_(u"F1"),
                                        creator = osafDev
                                        )
    newScript.set_file(u"NewScript.py", Scripts.__file__)

    # Block Inspector
    scripting.Script.update(parcel, 'Block Inspector',
                            displayName=_(u"F2 - Block under cursor"),
                            fkey=_(u"F2"),
                            creator = osafDev,
                            bodyString=scripting.script_file(u"BlockInspector.py", Scripts.__file__)
                            )

    # Item Inspector
    scripting.Script.update(parcel, 'Item Inspector',
                            displayName=_(u"F3 - Item selected"),
                            fkey=_(u"F3"),
                            creator = osafDev,
                            bodyString=scripting.script_file(u"ItemInspector.py", Scripts.__file__)
                            )

    # Browse selected item
    scripting.Script.update(parcel, 'Browse Selected',
                            displayName=_(u"F4 - Browse selected item"),
                            fkey=_(u"F4"),
                            creator = osafDev,
                            bodyString=scripting.script_file(u"BrowseSelected.py", Scripts.__file__)
                            )

    # Scripts whose name starts with "test" can all be run through a command-line option
    scripting.Script.update(parcel, 'Reload Parcels',
                            displayName=_(u"Test - Reload Parcels"),
                            test=True,
                            creator = osafDev,
                            bodyString=scripting.script_file(u"ReloadParcels.py", Scripts.__file__)
                            )

    scripting.Script.update(parcel, 'Event Timing',
                            displayName=_(u"Test - Event timing example"),
                            test=True,
                            creator = osafDev,
                            bodyString=scripting.script_file(u"EventTiming.py", Scripts.__file__)
                            )

    # The cleanup script, run after all the test scripts
    scripting.Script.update(parcel, 'CleanupAfterTests',
                            displayName=_(u"CleanupAfterTests"),
                            creator = osafDev,
                            bodyString=scripting.script_file(u"CleanupAfterTests.py", Scripts.__file__)
                            )


def MakeCollections(parcel):

    from osaf.pim import (
        KindCollection, ListCollection, FilteredCollection,
        DifferenceCollection, InclusionExclusionCollection,
        UnionCollection, CollectionColors, IntersectionCollection
    )
    
    def GetColorForHue (hue):
        rgb = wx.Image.HSVtoRGB (wx.Image_HSVValue (hue / 360.0, 0.5, 1.0))
        return ColorType (rgb.red, rgb.green, rgb.blue, 255)

    collectionColors = CollectionColors.update(parcel, 'collectionColors',
                                               colors = [GetColorForHue (210),
                                                         GetColorForHue (120),
                                                         GetColorForHue (0),
                                                         GetColorForHue (30),
                                                         GetColorForHue (270),
                                                         GetColorForHue (240),
                                                         GetColorForHue (330)],
                                               colorIndex = 0
                       )
    
    TrashCollection = \
        ListCollection.update(parcel, 'TrashCollection',
            displayName=_(u"Trash"),
            renameable=False,
            iconName="Trash",
            colorizeIcon = False,
            dontDisplayAsCalendar=True,
            outOfTheBoxCollection = True
        )

    notes = KindCollection.update(parcel, 'notes')
    # workaround bug 3892
    notes.kind = pim.Note.getKind(parcel.itsView)
    notes.recursive=True

    nonRecurringNotes = FilteredCollection.update(parcel, 'nonRecurringNotes',
        source=notes,
        filterExpression=u'not getattr(item, \'isGenerated\', False) and not getattr(item, \'modificationFor\', None)',
        filterAttributes=['isGenerated', 'modificationFor']
    )

    notMine = UnionCollection.update(parcel, 'notMine')
    # @@@MOR Hmm, I need to somehow make rep's initialValue be a MultiUnion()
    notMine._sourcesChanged()

    mine = DifferenceCollection.update(parcel, 'mine',
        sources=[nonRecurringNotes, notMine]
    )

    reminders = \
        KindCollection.update(parcel, 'reminders')
    reminders.kind = pim.Reminder.getKind(parcel.itsView)
    reminders.recursive = True
    
    # the "All" collection
    allCollection = InclusionExclusionCollection.update(parcel, 'allCollection',
        displayName=_(u"All My Items"),
        renameable = False,
        iconName = "All",
        colorizeIcon = False,
        iconNameHasKindVariant = True,
        color = collectionColors.nextColor(),
        outOfTheBoxCollection = True,

        displayNameAlternatives = {'None': _(u'My items'),
                                   'MailMessageMixin': _(u'My mail'),
                                   'CalendarEventMixin': _(u'My calendar'),
                                   'TaskMixin': _(u'My tasks')}
    ).setup(source=mine, exclusions=TrashCollection, trash=None)


    events = \
        KindCollection.update(parcel, 'events')
    # workaround bug 3892
    events.kind=pim.CalendarEventMixin.getKind(parcel.itsView)
    events.recursive=True

    locations = \
       KindCollection.update(parcel, 'locations')
    # workaround bug 3892
    locations.kind = pim.Location.getKind(parcel.itsView)
    locations.recursive = True
    locations.rep.addIndex('locationName', 'attribute', attribute = 'displayName')

    mailCollection = \
         KindCollection.update(parcel, 'mail')
    # workaround bug 3892
    mailCollection.kind=pim.mail.MailMessageMixin.getKind(parcel.itsView)
    mailCollection.recursive=True

    inSource = \
        FilteredCollection.update(parcel, 'inSource',
            source=mailCollection,
            filterExpression=u'getattr(item, \'isInbound\', False)',
            filterAttributes=['isInbound'])

    # The "In" collection
    inCollection = InclusionExclusionCollection.update(parcel, 'inCollection',
        displayName=_(u"In"),
        renameable=False,
        iconName="In",
        dontDisplayAsCalendar=True,
        color = collectionColors.nextColor(),
        colorizeIcon = False,
        outOfTheBoxCollection = True,
        visible = False
    ).setup(source=inSource)

    outSource = \
        FilteredCollection.update(parcel, 'outSource',
            source=mailCollection,
            filterExpression=u'getattr(item, \'isOutbound\', False)',
            filterAttributes=['isOutbound'])

    # The "Out" collection
    outCollection = InclusionExclusionCollection.update(parcel, 'outCollection',
        displayName=_(u"Out"),
        renameable=False,
        iconName="Out",
        dontDisplayAsCalendar=True,
        color = collectionColors.nextColor(),
        colorizeIcon = False,
        outOfTheBoxCollection = True,
        visible = False
    ).setup(source=outSource)

    # The "Scripts" collection
    scriptsCollection = KindCollection.update(parcel, 'scripts')
    scriptsCollection.kind = scripting.Script.getKind(parcel.itsView)

    InclusionExclusionCollection.update(parcel, 'scriptsCollection',
        displayName = _(u"Scripts"),
        renameable = False,
        private = False,
        iconName="Script",
        dontDisplayAsCalendar=True,
        color = collectionColors.nextColor(),
        colorizeIcon = False
        ).setup(source=scriptsCollection)

    # The Sidebar collection
    sidebarListCollection = ListCollection.update(parcel,
                                                  'sidebarCollection',
                                                  refCollection=[allCollection,
                                                                 TrashCollection])

    TrashCollection.color = collectionColors.nextColor()


    InclusionExclusionCollection.update (parcel,
                                         'untitledCollection',
                                         displayName=messages.UNTITLED)

    allEventsCollection = IntersectionCollection.update(parcel, 'allEventsCollection', sources=[allCollection, events])
