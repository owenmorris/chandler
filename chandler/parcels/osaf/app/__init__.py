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
from osaf import pim, messages, startup, sharing, preferences
from osaf.framework import scripting, password
from osaf.framework.blocks.calendar import CalendarUtility
from osaf.usercollections import UserCollection

class ApplicationPrefs(preferences.Preferences):
    isOnline = schema.One(schema.Boolean, defaultValue=True)

    backupOnQuit = schema.One(
        schema.Boolean,
        doc = 'Should we backup (export collections and settings) on quit to automate migration?'
    )

    showTip = schema.One(
        schema.Boolean,
        initialValue=False,
        doc = 'Should we show tip of the day on launch?'
    )

    tipIndex = schema.One(
        schema.Integer,
        initialValue=0,
        doc = 'Index of tip of the day to show.'
    )


def installParcel(parcel, oldVersion=None):

    import scripts as Scripts
    from osaf.framework import scripting

    pim_ns = schema.ns('osaf.pim', parcel)
    sharing_ns = schema.ns('osaf.sharing', parcel)

    ApplicationPrefs.update(parcel, 'prefs')

    message = _(u'User')

    me = pim.Contact.update(parcel, 'me',
        # L10N: The word 'Me' is used to represent the
        #       current Chandler user.
        displayName=_(u'Me'),
        contactName=pim.ContactName.update(parcel, 'meName',
           firstName=u'Chandler',
           #XXX Since the notion of 'me' may be going away
           #    there is no current need to refactor the
           #    last name attribute to the LocalizableString type.
           #    Thus for now will convert the c{Message} object
           #    returned from the c{ChandlerMessageFactory}
           #    to Unicode. This decision will be revisited later.
           lastName=unicode(message),
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
    
    # OOTB collections and items (bugs 6545, 11772)
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
    # (5) We create
    
    triageWhenValues = [datetime.datetime.now(parcel.itsView.tzinfo.default)]
    def changeTriage(itemOrStamp, triageValue):
        triageWhen = triageWhenValues.pop()
        item = getattr(itemOrStamp, 'itsItem', itemOrStamp)
        item.setTriageStatus(triageValue, triageWhen)
        triageWhenValues.append(triageWhen - datetime.timedelta(seconds=5))


    # OOTB item: Welcome Event
    noonToday = datetime.datetime.combine(
        datetime.date.today(),
        datetime.time(12, tzinfo=parcel.itsView.tzinfo.floating))

    WelcomeEvent = pim.EventStamp.update(parcel, 'WelcomeEvent',
        # L10N: The Trademark symbol "TM" is represented in Unicode as U+2122
        displayName=_(u'Welcome to Chandler\u2122'),
        startTime=noonToday,
        duration=datetime.timedelta(minutes=60),
        anyTime=False,
        read=False,
        creator=osafDev,
        location=pim.Location.update(parcel, "OSAFLocation",
            displayName="Open Source Applications Foundation",
        ),
    )

    # L10N: The Trademark symbol "TM" is represented in Unicode as U+2122
    body = _(u"""Welcome to Chandler\u2122 %(version)s. Here is a list of resources to help you get started:

1. Get a tour of Chandler
(http://chandlerproject.org/tour).

2. Learn how to import calendars and set up Chandler to back up and share
(http://chandlerproject.org/getstarted).

3. Back up your data and Share by signing up for a Chandler Hub account
(http://hub.chandlerproject.org/signup).

4. Ask for help by sending mail to mailto:chandler-users@osafoundation.org.

5. Learn more about the project on our wiki
(http://chandlerproject.org/wikihome).

6. Get involved and contribute to the project
(http://chandlerproject.org/getinvolved).

Thank you for trying Chandler!

The Chandler Team""") % { 'version' : version.version }

    WelcomeEvent.body = body
    WelcomeEvent.changeEditState(pim.Modification.created)
    changeTriage(WelcomeEvent, pim.TriageEnum.now)
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

        dashboard = schema.ns("osaf.pim", parcel.itsView).allCollection

        # Add Welcome item to OOTB collections
        home.add(WelcomeEvent)
        work.add(WelcomeEvent)
        
        
        thisWeek = CalendarUtility.getCalendarRange(noonToday.date())

        def getDayInThisWeek(weekday):
        
            res = thisWeek[0]
            while res.weekday() != weekday:
                res += datetime.timedelta(days=1)
            return res

        # OOTB item 1: Next dentist appointment?
        event1 = pim.CalendarEvent(
                    itsView=parcel.itsView,
                    displayName=_(u"Next dentist appointment?"),
                    startTime=noonToday.replace(hour=9),
                    anyTime=True,
                    collections=[home],
                    read=True,
                 )
        event1.itsItem.changeEditState(pim.Modification.created,
                                       when=noonToday.replace(hour=8))
        changeTriage(event1, pim.TriageEnum.now)

        # OOTB item #2: Tell a friend about Chandler
        item2 = pim.Note(
                    itsView=parcel.itsView,
                    displayName=_(u"Tell a friend about Chandler"),
                    read=True,
                    body=_(
u"""Try sharing a collection with family, friends or colleagues.

Sign up for a Chandler Hub account to get started: http://hub.chandlerproject.org
"""),
               )

        schema.ns("osaf.pim", parcel.itsView).allCollection.add(item2)
        item2.changeEditState(pim.Modification.created,
                                       when=noonToday.replace(hour=8))
        changeTriage(item2, pim.TriageEnum.now)
        
        # OOTB item #3: Write-up
        task3 = pim.Task(
                    itsView=parcel.itsView,
                    displayName=_(u"Write-up..."),
                    collections=[work],
                    read=True,
                    body=_(
u"""Start jotting down ideas for that big write-up you should really have started last week!

.
.
.
"""),
               )
        task3.itsItem.changeEditState(pim.Modification.created)
        changeTriage(task3, pim.TriageEnum.now)

        # OOTB item #4: Follow up
        task4 = pim.Task(
                    itsView=parcel.itsView,
                    displayName=_(u"Follow up with...on..."),
                    read=True,
                    body=_(
u"""Maintain a list of things you need to discuss with a colleague:
.
.
.

(Click on the clock icon to add this note to the calendar for the next time you're going to meet with them.)
"""),
               )
        dashboard.add(task4.itsItem)
        task4.itsItem.changeEditState(pim.Modification.created)
        changeTriage(task4, pim.TriageEnum.now)

        # OOTB item #5: Start planning vacation
        task5 = pim.Task(
                    itsView=parcel.itsView,
                    displayName=_(u"Start planning vacation"),
                    read=True,
                    collections=[home],
                    body=_(
"""Places you could go?
.
.
.

Activities you'd like to try?
.
.
.

Interesting travel articles?
.
.
.
"""),
               )

        changeTriage(task5, pim.TriageEnum.now)
        task5.itsItem.changeEditState(pim.Modification.created)

        # OOTB item #6: Bi-Weekly Status Report
        event5 = pim.CalendarEvent(
                     itsView=parcel.itsView,
                     displayName=_(u"Bi-Weekly Status Report"),
                     startTime=noonToday,
                     anyTime=True,
                     read=True,
                     collections=[work],
                     body=_(
"""What have you been up to the last couple of weeks?
.
.
.
"""),
                 )
        def makeRecurring(event, **kw):
             rule = pim.calendar.Recurrence.RecurrenceRule(
                        itsView=parcel.itsView,
                        **kw
                    )

             event.rruleset = pim.calendar.Recurrence.RecurrenceRuleSet(
                        itsView=parcel.itsView,
                        rrules=[rule]
                    )
             for item in event.modifications:
                 changeTriage(item, item._triageStatus)

        pim.TaskStamp(event5).add()
        event5.itsItem.changeEditState(pim.Modification.created)

        makeRecurring(event5, freq='weekly', interval=2)

        # OOTB item #6: Office supplies order
        startTime6 = datetime.datetime.combine(getDayInThisWeek(4),
                                               noonToday.timetz())

        event6 = pim.CalendarEvent(
                     itsView=parcel.itsView,
                     displayName=_(u"Office supplies order"),
                     startTime=startTime6,
                     anyTime=True,
                     read=True,
                     collections=[work],
                     body=_(
u"""Maintain a list of supplies you need to get every month:
.
.
.

(Share it with others so you can all maintain the list together!)
""")
                )
        changeTriage(event6, pim.TriageEnum.done)
        event6.itsItem.changeEditState(pim.Modification.created)
        makeRecurring(event6, freq='monthly')

        # OOTB item #7: Salsa class
        startTime7 = noonToday.replace(hour=14, minute=30)
        delta = 14 + startTime7.date().weekday() - 6
        startTime7 -= datetime.timedelta(days=delta)
        until7 = startTime7 + datetime.timedelta(days=28)
        event7 = pim.CalendarEvent(
                     itsView=parcel.itsView,
                     displayName=_(u"Salsa Class"),
                     startTime=startTime7,
                     duration=datetime.timedelta(hours=1),
                     anyTime=False,
                     read=True,
                     collections=[home, fun],
                     body=_(
u"""Assignment for this week:
.
.
.

Remember to bring:
.
.
.
""")
                 )
        event7.itsItem.changeEditState(pim.Modification.created,
                                       when=startTime7)
        changeTriage(event7, pim.TriageEnum.done)
        makeRecurring(event7, freq='weekly', until=until7)

        # A hack to get this occurrence to appear in the dashboard
        event7.getFirstOccurrence().getNextOccurrence().changeThis()
        for m in sorted(event7.modifications,
                        key=lambda o: pim.EventStamp(o).startTime):
            changeTriage(m, m._triageStatus)

        # OOTB item #8: Brunch potluck...
        startTime8 = datetime.datetime.combine(
                        getDayInThisWeek(6),
                        datetime.time(11, 0, tzinfo=noonToday.tzinfo)
                    )
        
        event8 = pim.CalendarEvent(
                     itsView=parcel.itsView,
                     displayName=_(u"Brunch potluck..."),
                     startTime=startTime8,
                     duration=datetime.timedelta(hours=2),
                     anyTime=False,
                     read=True,
                     collections=[home, fun],
                     body=_(
u"""Directions
.
.
.

Ideas for games to bring...
.
.
.

Sign up to bring food...
.
.
.
"""),
                )
        changeTriage(event8, event8.autoTriage())
        event8.itsItem.changeEditState(pim.Modification.created)

        # OOTB Item #9: Ideas for presents
        item9 = pim.Note(
                    itsView=parcel.itsView,
                    displayName=_(u"Ideas for presents"),
                    read=True,
                    collections=[home],
                    body=_(
u"""Maintain a list of possible presents for family, friends and colleagues so you're never short on ideas!
.
.
.
"""),
                )
        changeTriage(item9, pim.TriageEnum.later)
        item9.changeEditState(pim.Modification.edited)

        # OOTB Item #10: Thank you notes
        item10 = pim.Note(
                     itsView=parcel.itsView,
                     displayName=_(u"Thank you notes"),
                     read=True,
                     collections=[home],
                     body=_(
u"""Who do you need to write thank you notes to? and for what reason?
.
.
.


"""),
                )

        changeTriage(item10, pim.TriageEnum.later)
        item10.changeEditState(pim.Modification.created)

        # OOTB Item #11: Movie list
        item11 = pim.Note(
                     itsView=parcel.itsView,
                     displayName=_(u"Movie list"),
                     read=True,
                     collections=[fun, home],
                     body=_(
u"""Movies you want to see:

.
.
.
"""),
                )

        changeTriage(item11, pim.TriageEnum.later)
        item11.changeEditState(pim.Modification.created)

        # OOTB Item #12: Book list
        item12 = pim.Note(
                     itsView=parcel.itsView,
                     displayName=_(u"Book list"),
                     read=True,
                     collections=[fun, home],
                     body=_(
u"""Book recommendations you've been meaning to follow up on:

.
.
.
"""),
                )

        changeTriage(item12, pim.TriageEnum.later)
        item12.changeEditState(pim.Modification.created)

        # OOTB Item #13: File taxes
        startTime13 = noonToday.replace(month=4, day=15)
        alarmTime13 = startTime13.replace(day=1)
        if alarmTime13 < noonToday:
            alarmTime13 = alarmTime13.replace(year=alarmTime13.year + 1)
            startTime13 = startTime13.replace(year=startTime13.year + 1)

        event13 = pim.CalendarEvent(
                      itsView=parcel.itsView,
                      startTime=startTime13,
                      displayName=_(u"File taxes!"),
                      read=True,
                      collections=[home],
                      body=_(
u"""What forms do you have in hand?
.
.
.

What are you missing?
.
.
.

Questions for your accountant?
.
.
.
"""),
                  )

        pim.TaskStamp(event13).add()
        event13.itsItem.changeEditState(pim.Modification.created)
        changeTriage(event13, pim.TriageEnum.later)
        event13.itsItem.userReminderTime = alarmTime13

        # OOTB Item #14: Class Trip: Exhibit on Sound!
        location14 = pim.Location.update(parcel, "Exploratorium",
            displayName="Exploratorium",
        )

        startTime14 = datetime.datetime.combine(
                        getDayInThisWeek(6),
                        datetime.time(15, tzinfo=noonToday.tzinfo))
        
        event14 = pim.CalendarEvent(
                      itsView=parcel.itsView,
                      startTime=startTime14,
                      displayName=_(u"Class Trip: Exhibit on Sound!"),
                      read=True,
                      location=location14,
                      collections=[fun],
                      body=_(
u"""Directions...
.
.
.
"""),
                  )
        event14.itsItem.changeEditState(pim.Modification.edited,
                                        when=startTime14)
        changeTriage(event14, pim.TriageEnum.done)

        # OOTB Item #15: Download Chandler!
        note15 = pim.Note(
                     itsView= parcel.itsView,
                     displayName=_(u"Download Chandler!"),
                     read=True,
                 )
        dashboard.add(note15)
        done15 = datetime.datetime.now(parcel.itsView.tzinfo.default)
        done15 -= datetime.timedelta(minutes=5)
        done15 = done15.replace(second=0, microsecond=0)
        changeTriage(note15, pim.TriageEnum.done)
        note15.changeEditState(pim.Modification.edited, when=done15)

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
                                        displayName=_(u"F1 - Create a new script"),
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
                            displayName=_(u"Clean up after tests"),
                            creator = osafDev,
                            body=scripting.script_file(u"CleanupAfterTests.py", Scripts.__file__)
                            )

    #
    # F5 reserved for triage
    #

    # Print selected item to stdout
    scripting.Script.update(parcel, 'Print Selected to stdout',
                            displayName=_(u"F6 - Print selected item to stdout"),
                            fkey= u"F6",
                            creator = osafDev,
                            body=scripting.script_file(u"StdoutSelected.py", Scripts.__file__)
                            )

    # Script to paste the clipboard into a new menu item
    newScript = scripting.Script.update(parcel, 'Paste New Item',
                                        displayName=_(u"F7 - Paste new item"),
                                        fkey= u"F7",
                                        creator = osafDev
                                        )
    newScript.set_file(u"PasteNewItem.py", Scripts.__file__)

    from osaf.app import updates
    updates.UpdateCheckTask.update(parcel, 'updateCheckTask',
                                   interval=datetime.timedelta(days=7))

    # Compact task should come last
    from osaf.app import compact
    compact.CompactTask.update(parcel, 'compactTask')
