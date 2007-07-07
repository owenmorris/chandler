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

import datetime, os, wx

import version
from application import schema, Globals
from application.Parcel import Reference
from i18n import ChandlerMessageFactory as _
from osaf import pim, messages, startup, sharing
from osaf.framework import scripting, password
from osaf.usercollections import UserCollection


def installParcel(parcel, oldVersion=None):

    import scripts as Scripts
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
        inclusions=[pim_ns.allCollection,
                    pim_ns.inCollection,
                    pim_ns.outCollection,
                    pim_ns.trashCollection]
    )

    testReply = pim.mail.EmailAddress.update(parcel, 'TestReplyAddress')

    # [i18n] Test Accounts are not displayed to the user and 
    # do not require localization
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
    
    # OOTB collections and items (bug 6545)
    # http://chandlerproject.org/bin/view/Journal/PreviewOOTBChandlerExperience
    #
    # (1) Don't create these in //parcels, or they won't get dumped
    # (2) Don't create these if reloading, or else there will be endless
    #     duplication of items/events
    # (3) We do want new UUIDs, so different users can share these
    #     collections/items to the same morsecode server
    # (4) The Welcome Event should be created regardless of whether
    #     we're reloading, because summaryblocks references it.
    #     (Maybe there's a better way to have it selected in the
    #      detail view?) -- Grant
    
    # OOTB item: Welcome Event
    noonToday = datetime.datetime.combine(
        datetime.date.today(),
        datetime.time(12, tzinfo=parcel.itsView.tzinfo.floating))

    WelcomeEvent = pim.EventStamp.update(parcel, 'WelcomeEvent',
        displayName=_(u'Welcome to Chandler %(version)s') % {'version': version.version},
        startTime=noonToday,
        duration=datetime.timedelta(minutes=60),
        anyTime=False,
        read=False,
        creator=osafDev,
        location=pim.Location.update(parcel, "OSAFLocation",
            displayName=_("Open Source Applications Foundation"),
        ),
    )

    # The URLs used in the Welcome note: those should not go through the localization mechanism!
    url1 = u"http://chandlerproject.org/guide"
    url2 = u"http://hub.chandlerproject.org/signup"
    url3 = u"http://chandlerproject.org/faq"
    url4 = u"http://chandlerproject.org/knownissues"
    url5 = u"http://chandlerproject.org/mailinglists"
    url6 = u"http://chandlerproject.org/"
    url7 = u"http://chandlerproject.org/getinvolved" 

    body = _(u"""Welcome to Chandler %(version)s. Here is a list of resources to help you get started:

1. Check out our Getting Started Guide (%(url1)s) to view screenshots, learn how to report problems and access a wide range of developer documentation.
2. Sign-up for a sharing account on Chandler Hub (%(url2)s).
3. Consult our FAQ (%(url3)s).
4. Read about known issues with the Preview release (%(url4)s).
5. Ask questions and give us feedback by joining the Chandler-Users mailing list (%(url5)s).
6. Learn more about the project on our wiki (%(url6)s).
7. Get involved and contribute to the project (%(url7)s).

Thank you for trying Chandler!

The Chandler Team""") % {'version': version.version, 
                         'url1' : url1, 
                         'url2' : url2, 
                         'url3' : url3, 
                         'url4' : url4, 
                         'url5' : url5, 
                         'url6' : url6, 
                         'url7' : url7 
                     }

    WelcomeEvent.body = body
    WelcomeEvent.changeEditState(pim.Modification.created)
    WelcomeEvent.setTriageStatus(pim.TriageEnum.now)
    pim.TaskStamp(WelcomeEvent).add()
    
    if Globals.options.reload:
        schema.ns('osaf.pim', parcel.itsView).allCollection.add(WelcomeEvent)
    else:
        # OOTB user defined collections: collections should be in mine
        mine = schema.ns("osaf.pim", parcel.itsView).mine
        def makeCollection(name, checked, color):
            collection = pim.SmartCollection(
                            itsView=parcel.itsView,
                            displayName=name
                        )
            # include collection in overlays, as spec'ed
            UserCollection(collection).checked = checked
            # set the collection color as spec'ed
            UserCollection(collection).setColor(color)

            sidebarListCollection.add(collection)
            mine.addSource(collection)
            
            return collection
            
        # OOTB user defined collections: Work, Home and Fun
        work = makeCollection(_(u"Work"), True, u'Blue')
        home = makeCollection(_(u"Home"), True, u'Red')
        fun = makeCollection(_(u"Fun"), False, u'Plum')

        # Add Welcome item to OOTB collections
        home.add(WelcomeEvent)
        work.add(WelcomeEvent)

        # OOTB item1: Try sharing a Home task list
        task1 = pim.Task(
                  itsView=parcel.itsView,
                  displayName=_(u"Try sharing a Home task list"),
                  collections=[home],
                  read=False,
              )
        task1.itsItem.changeEditState(pim.Modification.created)
        task1.itsItem.setTriageStatus(pim.TriageEnum.later)
        floating = parcel.itsView.tzinfo.floating

        reminderTime = datetime.datetime.combine(
                            datetime.datetime.now().date() +
                                datetime.timedelta(days=1),
                            datetime.time(8, 0, tzinfo=floating)
                       )
        task1.itsItem.userReminderTime = reminderTime
        
        # OOTB item2: Play around with the Calendar
        startevent2 = datetime.datetime.combine(
                            datetime.datetime.now().date(),
                            datetime.time(15, 0, tzinfo=floating)
                       )
        event2 = pim.CalendarEvent(
                    itsView=parcel.itsView,
                    displayName=_(u"Play around with the Calendar"),
                    startTime=startevent2,
                    duration=datetime.timedelta(minutes=60),
                    anyTime=False,
                    collections=[home],
                    read=False,
                )
        event2.itsItem.changeEditState(pim.Modification.created)
        event2.itsItem.setTriageStatus(pim.TriageEnum.now)
        
        # OOTB item3: Download Chandler
        startevent3 = datetime.datetime.combine(
                            datetime.datetime.now().date(),
                            datetime.time(11, 0, tzinfo=floating)
                       )
        event3 = pim.CalendarEvent(
                    itsView=parcel.itsView,
                    displayName=_(u"Download Chandler"),
                    startTime=startevent3,
                    duration=datetime.timedelta(minutes=30),
                    anyTime=False,
                    collections=[work],
                    read=False,
                )
        event3.itsItem.changeEditState(pim.Modification.created)
        event3.itsItem.setTriageStatus(pim.TriageEnum.done)
        pim.TaskStamp(event3).add()
        
        # OOTB item4: Set up your accounts
        startevent4 = datetime.datetime.combine(
                            datetime.datetime.now().date(),
                            datetime.time(16, 0, tzinfo=floating)
                       )
        event4 = pim.CalendarEvent(
                    itsView=parcel.itsView,
                    displayName=_(u"Set up your accounts"),
                    startTime=startevent4,
                    duration=datetime.timedelta(minutes=30),
                    anyTime=False,
                    collections=[fun],
                    read=False,
                )
        event4.itsItem.changeEditState(pim.Modification.created)
        event4.itsItem.setTriageStatus(pim.TriageEnum.later)
        m = pim.MailStamp(event4)
        m.add()
        m.toAddress.append(pim.mail.EmailAddress.getEmailAddress(parcel.itsView, "someone@example.org"))
        m.fromMe = True
        pim.TaskStamp(event4).add()

        # OOTB item5: Delete sample items and collections
        note = pim.Note(
                  itsView=parcel.itsView,
                  displayName=_(u"Delete sample items and collections"),
                  collections=[work],
                  read=False,
              )
        note.changeEditState(pim.Modification.created)
        note.setTriageStatus(pim.TriageEnum.later)
        note.body = _(u"The items and collections Chandler creates at startup are examples.  Feel free to delete them.")



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

    # Print selected item to stdout
    scripting.Script.update(parcel, 'Print Selected to stdout',
                            displayName=_(u"F6 - Print selected item to stdout"),
                            fkey= u"F6",
                            creator = osafDev,
                            body=scripting.script_file(u"StdoutSelected.py", Scripts.__file__)
                            )

    from osaf.app import compact
    compact.CompactTask.update(parcel, 'compactTask')
