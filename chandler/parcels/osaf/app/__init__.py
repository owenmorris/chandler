#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import datetime, os

from application import schema
from application.Parcel import Reference
from i18n import ChandlerMessageFactory as _
from PyICU import ICUtzinfo
from osaf import pim, messages
from osaf.framework import scripting, password
from chandlerdb.util.c import UUID

import version

def installParcel(parcel, oldVersion=None):

    import scripts as Scripts
    from osaf import sharing, startup
    from osaf.framework import scripting

    pim_ns = schema.ns('osaf.pim', parcel)
    sharing_ns = schema.ns('osaf.sharing', parcel)

    me = pim.Contact.update(parcel, 'me',
        displayName=_(u'Me'),
        contactName=pim.ContactName.update(parcel, 'meName',
           firstName=_(u'Chandler'),
           lastName=_(u'User')
        ),
        references=[pim_ns.currentContact]
    )

    # The Sidebar collection
    sidebarListCollection = pim.ListCollection.update(parcel,
        'sidebarCollection',
        # Hard code the UUID of the sidebar collection so that after a
        # new repository is created we can still find the sidebar
        # for dump and reload
        _uuid = UUID("3c58ae62-d8d6-11db-86bb-0017f2ca1708"),
        inclusions=[pim_ns.allCollection,
                    pim_ns.inCollection,
                    pim_ns.outCollection,
                    pim_ns.trashCollection]
    )

    sharing.WebDAVAccount.update(parcel, 'defaultWebDAVAccount',
        displayName=_(u'Cosmo Sharing Service'),
        host=u'osaf.us',
        path=u'/cosmo/dav/<username>',
        username=u'',
        password=password.Password.update(parcel, 'defaultWebDAVAccountPassword'),
        useSSL=True,
        port=443,
        references=[sharing_ns.currentSharingAccount]
    )

    preReply = pim.EmailAddress.update(parcel, 'defaultReplyAddress')

    preSmtp = pim.mail.SMTPAccount.update(parcel, 'defaultSMTPAccount',
        displayName=_(u'Outgoing mail'),
        password=password.Password.update(parcel, 'defaultSMTPAccountPassword'),
        references=[pim_ns.currentOutgoingAccount]
    )

    pim.mail.IMAPAccount.update(parcel, 'defaultIMAPAccount',
        displayName=_(u'Incoming mail'),
        replyToAddress=preReply,
        password=password.Password.update(parcel, 'defaultIMAPAccountPassword'),
        references=[pim_ns.currentIncomingAccount]
    )

    testReply = pim.mail.EmailAddress.update(parcel, 'TestReplyAddress')

    #[i18n] Test Acccounts are not displayed to the user and do not require localization
    testSmtp = pim.mail.SMTPAccount.update(parcel, 'TestSMTPAccount',
        displayName=u'Test SMTP Account',
        password=password.Password.update(parcel, 'TestSMTPAccountPassword'),
        isActive=False
    )

    pim.mail.IMAPAccount.update(parcel, 'TestIMAPAccount',
        displayName=u'Test IMAP mail',
        replyToAddress=testReply,
        password=password.Password.update(parcel, 'TestIMAPAccountPassword'),
        isActive=False
    )

    pim.mail.POPAccount.update(parcel, 'TestPOPAccount',
        displayName=u'Test POP mail',
        replyToAddress=testReply,
        defaultSMTPAccount=testSmtp,
        password=password.Password.update(parcel, 'TestPOPAccountPassword'),
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
        datetime.time(12, tzinfo=ICUtzinfo.floating))

    WelcomeEvent = pim.EventStamp.update(parcel, 'WelcomeEvent',
        displayName=_(u'Welcome to Chandler %(version)s') % {'version': version.version},
        startTime=noonToday,
        duration=datetime.timedelta(minutes=120),
        anyTime=False,
        creator=osafDev,
        location=pim.Location.update(parcel, "OSAFLocation",
            displayName=_("Open Source Applications Foundation"),
        ),
    )
    schema.ns('osaf.pim', parcel.itsView).allCollection.add(WelcomeEvent)

    body = _(u"""Welcome to the Chandler %(version)s!

For a wealth of information for end-users and developers, point your browser to:
    http://chandler.osafoundation.org

There you can see presentations on the Vision of Chandler, details about this release, screenshots and screencast demos, documentation and tutorials for developers, and how to participate in testing and giving us feedback about your experience in experimenting with Chandler.

This release is focused on "experimentally usable" calendar functionality. It meets the following four goals:

1. Usable Calendar
We intend to use the %(version)s calendar internally at OSAF on a day-to-day basis in order to experience first hand the features, functionality, limitations, and any bugs in the product. We believe using the product ourselves early on is the best way to ensure superlative design and implementation. The calendar now includes timezones, repeating events, all-day events, multiple overlaying calendars, and shared collaborative (multi-author) group calendars using our new CalDAV-based calendar server.

2. Polished User Interface
Adding polish to the UI helps calendar usability. To a lesser extent we have also polished other areas of the application UI.

3. Infrastructure Investment
* Although the focus for this release is usable calendar functionality, we have invested in some projects for both developer and Quality Assurance productivity. For example, we have begun optimizing for performance, and have developed automated QA code tests. We want Chandler to be testable, high quality source code.
* In addition, this release also includes continuing infrastructure work on email and internationalization.

4. Developer Platform
* If you are an experienced Python programmer, you should be able to create simple forms-based parcels like the Flickr, Feeds, and Amazon parcels that are included in the %(version)s release.
* Developer documentation, tutorials, and sample add-in parcels are part of this release.

Please note, this release is still intended to be experimental; do not trust your real data with this version. An experimental file import/export feature is available to back up your calendar data.

Thank you for trying Chandler. Your feedback is welcome on our mail lists:
    http://wiki.osafoundation.org/bin/view/Chandler/OsafMailingLists

The Chandler Team""") % {'version': version.version}

    WelcomeEvent.body = body
    WelcomeEvent.changeEditState(pim.Modification.created)

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
                                        fkey= u"F1",
                                        creator = osafDev
                                        )
    newScript.set_file(u"NewScript.py", Scripts.__file__)

    # Block Inspector
    scripting.Script.update(parcel, 'Block Inspector',
                            displayName=_(u"F2 - Block under cursor"),
                            fkey= u"F2",
                            creator = osafDev, body=scripting.script_file(u"BlockInspector.py", Scripts.__file__)
                            )

    # Item Inspector
    scripting.Script.update(parcel, 'Item Inspector',
                            displayName=_(u"F3 - Item selected"),
                            fkey= u"F3",
                            creator = osafDev,
                            body=scripting.script_file(u"ItemInspector.py", Scripts.__file__)
                            )

    # Browse selected item
    scripting.Script.update(parcel, 'Browse Selected',
                            displayName=_(u"F4 - Browse selected item"),
                            fkey= u"F4",
                            creator = osafDev,
                            body=scripting.script_file(u"BrowseSelected.py", Scripts.__file__)
                            )

    # Scripts whose name starts with "test" can all be run through a command-line option
    scripting.Script.update(parcel, 'Reload Parcels',
                            displayName=_(u"Test - Reload Parcels"),
                            #test=True, # @@@ reenable this line when bug 4554 is fixed
                            creator = osafDev,
                            body=scripting.script_file(u"ReloadParcels.py", Scripts.__file__)
                            )

    scripting.Script.update(parcel, 'Event Timing',
                            displayName=_(u"Test - Event timing example"),
                            test=True,
                            creator = osafDev,
                            body=scripting.script_file(u"EventTiming.py", Scripts.__file__)
                            )

    # The cleanup script, run after all the test scripts
    scripting.Script.update(parcel, 'CleanupAfterTests',
                            displayName=_(u"Cleanup after tests"),
                            creator = osafDev,
                            body=scripting.script_file(u"CleanupAfterTests.py", Scripts.__file__)
                            )

    # Script to paste the clipboard into a new menu item
    newScript = scripting.Script.update(parcel, 'Paste New Item',
                                        displayName=_(u"F5 - Paste new item"),
                                        fkey= u"F5",
                                        creator = osafDev
                                        )
    newScript.set_file(u"PasteNewItem.py", Scripts.__file__)
