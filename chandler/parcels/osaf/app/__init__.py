
import datetime, os

from application import schema
from application.Parcel import Reference
from i18n import OSAFMessageFactory as _
from PyICU import ICUtzinfo
from osaf import pim, messages
from osaf.framework import scripting

def installParcel(parcel, oldVersion=None):

    import scripts as Scripts
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
        
    WelcomeEvent = pim.CalendarEvent.update(parcel, 'WelcomeEvent',
        displayName=_(u'Welcome to Chandler 0.6'),
        startTime=noonToday,
        duration=datetime.timedelta(minutes=120),
        anyTime=False,
        creator=osafDev,
        location=pim.Location.update(parcel, "OSAFLocation",
            displayName=u"Open Source Applications Foundation"
        )
    )

    body = _(u"""Welcome to the Chandler 0.6 Release!

For a wealth of information for end-users and developers, point your browser to:
    http://chandler.osafoundation.org

There you can see presentations on the Vision of Chandler, details about this release, screenshots and screencast demos, documentation and tutorials for developers, and how to participate in testing and giving us feedback about your experience in experimenting with Chandler.

This release is focused on "experimentally usable" calendar functionality. It meets the following four goals:

1. Usable Calendar
We intend to use the 0.6 calendar internally at OSAF on a day-to-day basis in order to experience first hand the features, functionality, limitations, and any bugs in the product. We believe using the product ourselves early on is the best way to ensure superlative design and implementation. The calendar now includes timezones, repeating events, all-day events, multiple overlaying calendars, and shared collaborative (multi-author) group calendars using our new CalDAV-based calendar server.

2. Polished User Interface
Adding polish to the UI helps calendar usability. To a lesser extent we have also polished other areas of the application UI.

3. Infrastructure Investment
* Although the focus for this release is usable calendar functionality, we have invested in some projects for both developer and Quality Assurance productivity. For example, we have begun optimizing for performance, and have developed automated QA code tests. We want Chandler to be testable, high quality source code.
* In addition, this release also includes continuing infrastructure work on email and internationalization.

4. Developer Platform
* If you are an experienced Python programmer, you should be able to create simple forms-based parcels like the Flickr, Feeds, and Amazon parcels that are included in the 0.6 release.
* Developer documentation, tutorials, and sample add-in parcels are part of this release.

Please note, this release is still intended to be experimental; do not trust your real data with this version. An experimental file import/export feature is available to back up your calendar data.

Thank you for trying Chandler. Your feedback is welcome on our mail lists:
    http://wiki.osafoundation.org/bin/view/Chandler/OsafMailingLists

The Chandler Team""")

    WelcomeEvent.body = WelcomeEvent.getAttributeAspect('body', 'type').makeValue(body)


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
            ),
            webserver.Resource.update(parcel, "prefResource",
                displayName=u'Preference Editor',
                location=u"prefs",
                resourceClass=schema.importString(
                    "osaf.servlets.prefs.PrefResource"
                ),
                autoView=False
            ),
            webserver.Resource.update(parcel, "xmlrpcResource",
                displayName=u'XML-RPC Service',
                location=u"xmlrpc",
                resourceClass=schema.importString(
                    "osaf.servlets.xmlrpc.XmlRpcResource"
                ),
                autoView=False
            ),
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
                            #test=True, # @@@ reenable this line when bug 4554 is fixed
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

    # Script to paste the clipboard into a new menu item
    newScript = scripting.Script.update(parcel, 'Paste New Item',
                                        displayName=_(u"F5 - Paste new item"),
                                        fkey=_(u"F5"),
                                        creator = osafDev
                                        )
    newScript.set_file(u"PasteNewItem.py", Scripts.__file__)


def MakeCollections(parcel):

    import wx
    from osaf.pim import (
        KindCollection, ListCollection, FilteredCollection,
        DifferenceCollection, InclusionExclusionCollection,
        UnionCollection, CollectionColors, IntersectionCollection
    )
    from osaf.framework.types.DocumentTypes import ColorType
    
    def GetColorForHue (hue):
        rgb = wx.Image.HSVtoRGB (wx.Image_HSVValue (hue / 360.0, 0.5, 1.0))
        return ColorType (rgb.red, rgb.green, rgb.blue, 255)

    view = parcel.itsView

    collectionColors = CollectionColors.update(
        parcel, 'collectionColors',
        colors = [GetColorForHue (210),
                  GetColorForHue (120),
                  GetColorForHue (0),
                  GetColorForHue (30),
                  GetColorForHue (270),
                  GetColorForHue (240),
                  GetColorForHue (330)],
        colorIndex = 0)
    
    TrashCollection = ListCollection.update(
        parcel, 'TrashCollection',
        displayName=_(u"Trash"),
        renameable=False,
        dontDisplayAsCalendar=True,
        outOfTheBoxCollection = True)

    notes = KindCollection.update(
        parcel, 'notes',
        kind = pim.Note.getKind(view),
        recursive = True)

    nonRecurringNotes = FilteredCollection.update(parcel, 'nonRecurringNotes',
        source=notes,
        filterExpression=u"(not item.hasLocalAttributeValue('isGenerated') or not getattr(item, 'isGenerated', False)) and not item.hasLocalAttributeValue('modificationFor')",
        filterAttributes=['isGenerated', 'modificationFor']
    )

    notMine = UnionCollection.update(parcel, 'notMine')
    # @@@MOR Hmm, I need to somehow make rep's initialValue be a MultiUnion()
    notMine._sourcesChanged()

    mine = DifferenceCollection.update(parcel, 'mine',
        sources=[nonRecurringNotes, notMine]
    )

    # the "All" collection
    allCollection = InclusionExclusionCollection.update(parcel, 'allCollection',
        displayName=_(u"My items"),
        renameable = False,
        color = collectionColors.nextColor(),
        outOfTheBoxCollection = True,

        displayNameAlternatives = {'None': _(u'My items'),
                                   'MailMessageMixin': _(u'My mail'),
                                   'CalendarEventMixin': _(u'My calendar'),
                                   'TaskMixin': _(u'My tasks')}
    ).setup(source=mine, exclusions=TrashCollection, trash=None)
    # kludge to improve on bug 4144 (not a good long term fix but fine for 0.6)
    allCollection.rep.addIndex('__adhoc__', 'numeric')

    events = KindCollection.update(
        parcel, 'events',
        kind = pim.CalendarEventMixin.getKind(view),
        recursive = True)

    events.rep.addIndex("effectiveStart", 'compare', compare='cmpStartTime',
                        monitor=('startTime', 'allDay', 'anyTime'))
    events.rep.addIndex('effectiveEnd', 'compare', compare='cmpEndTime',
                    monitor=('startTime', 'allDay', 'anyTime', 'duration'))
    
    # bug 4477
    eventsWithReminders = FilteredCollection.update(
        parcel, 'eventsWithReminders',
        source=events,
        filterExpression='item.reminders',
        filterAttributes=['reminders'])

    # the monitor list assumes all reminders will be relativeTo
    # effectiveStartTime, which is true in 0.6, but may not be in the future
    eventsWithReminders.rep.addIndex('reminderTime', 'compare',
                                     compare='cmpReminderTime',
                                     monitor=('startTime', 'allDay', 'anyTime'
                                              'reminders'))
    
    masterFilter = "item.hasTrueAttributeValue('occurrences') and "\
                   "item.hasTrueAttributeValue('rruleset')"
    masterEvents = FilteredCollection.update(
        parcel, 'masterEvents',
        source = events,
        filterExpression = masterFilter,
        filterAttributes = ['occurrences', 'rruleset'])

    masterEvents.rep.addIndex("recurrenceEnd", 'compare', compare='cmpRecurEnd',
                        monitor=('recurrenceEnd'))

    locations = KindCollection.update(
        parcel, 'locations',
        kind = pim.Location.getKind(view),
        recursive = True)

    locations.rep.addIndex('locationName', 'attribute', attribute = 'displayName')

    mailCollection = KindCollection.update(
        parcel, 'mail',
        kind = pim.mail.MailMessageMixin.getKind(view),
        recursive = True)

    emailAddressCollection = \
        KindCollection.update(parcel, 'emailAddressCollection',
                              kind=pim.mail.EmailAddress.getKind(view),
                              recursive=True)
    emailAddressCollection.rep.addIndex('emailAddress', 'compare',
                                        compare='_compareAddr')

    inSource = FilteredCollection.update(
        parcel, 'inSource',
        source=mailCollection,
        filterExpression=u'getattr(item, \'isInbound\', False)',
        filterAttributes=['isInbound'])

    # The "In" collection
    inCollection = InclusionExclusionCollection.update(parcel, 'inCollection',
        displayName=_(u"In"),
        renameable=False,
        dontDisplayAsCalendar=True,
        color = collectionColors.nextColor(),
        outOfTheBoxCollection = True,
        visible = False
    ).setup(source=inSource)

    outSource = FilteredCollection.update(
        parcel, 'outSource',
        source=mailCollection,
        filterExpression=u'getattr(item, \'isOutbound\', False)',
        filterAttributes=['isOutbound'])

    # The "Out" collection
    outCollection = InclusionExclusionCollection.update(parcel, 'outCollection',
        displayName=_(u"Out"),
        renameable=False,
        dontDisplayAsCalendar=True,
        color = collectionColors.nextColor(),
        outOfTheBoxCollection = True,
        visible = False
    ).setup(source=outSource)

    # The "Scripts" collection
    scriptsCollection = KindCollection.update(
        parcel, 'scripts',
        kind = scripting.Script.getKind(view))

    InclusionExclusionCollection.update(parcel, 'scriptsCollection',
        displayName = _(u"Scripts"),
        renameable = False,
        private = False,
        dontDisplayAsCalendar=True,
        color = collectionColors.nextColor(),
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
