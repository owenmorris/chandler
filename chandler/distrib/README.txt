
INTRODUCTION

What is 0.3?

0.3 is the last of our architecture-focused releases as described in
our ProductRoadmap:
   http://wiki.osafoundation.org/twiki/bin/view/Chandler/ProductRoadmap

This release is not intended for end-users but rather
targets developers who want an early preview into our architecture as
we are developing it. Our architecture will continue to evolve, but
starting with 0.3, we are finally able to start developing end-user
features.

The two biggest architecture advancements in this release are the
Chandler Presentation and Interaction Architecture (CPIA) and the
Repository. This release marks the debut of CPIA, which is a UI layer
in our architecture that is uniquely adapted for item-centric
applications based on our repository. Not only does it abstract away
implementation-specific UI widgets, but CPIA elements have direct
access to our repository via data-driven queries. In 0.3, our
repository now implements a transaction and threading model, and is a
lot more robust and scalable.

You can find a comprehensive (but terse) listing of all the changes in
0.3 in HISTORY.txt.


0.3 High-level Deliverables

  * Base architecture framework in place:
       + Chandler Presentation and Interaction Architecture
       + Repository enhancements and maturity
       + Content Model
       + Parcel loading
       + Demonstration of the Notification Framework and Agent
         Framework
       + Unit Tests Framework with many real tests
  * Our initial "Caterpillar" UI

Also, for a general architectural overview of Chandler in 0.3,
please see:
   http://wiki.osafoundation.org/twiki/bin/view/Chandler/ZeroPointThreeMapOfChandler


Chandler Presentation and Interaction Architecture (CPIA)

The broad goals for CPIA are:
 1. Easy creation of both simple and sophisticated view layouts,
    particularly those anticipated in PIM applications (such as an
    email inbox view or a calendar view). These views come bundled
    with a rich set of standard behaviors and interactions.
 2. The contents of a view can be specified by a repository query that
    is stored within the view. Views are thus well integrated with the
    Chandler repository. CPIA objects also know how to load, display
    and save themselves and their contents.
 3. CPIA UI objects (called "Blocks") themselves are stored as
    Chandler items in the repository. As with all Chandler items, CPIA
    Blocks are fully introspectable. This approach provides an
    abstraction, allowing us, architecturally, to more easily create
    versions of Chandler (post-Canoga) for other platforms like web
    browser interfaces and PDAs. It also provides the basis for the
    Chandler UI editing tools that we plan to create after the Canoga
    release.

In 0.3, a large amount of work was spent developing and implementing
CPIA and then converting and re-writing the UI portion of our entire
application. Now almost all the views and high level events are
described by CPIA blocks, with the CPIA blocks and views persisting in
our repository.

Work in CPIA is by no means complete. The architecture will continue
to evolve, so it's premature to write long-lived applications in CPIA
at this point. However, we would very much like comment, feedback and
issues about the architecture itself and our approach.

For more details on CPIA, see:
   http://wiki.osafoundation.org/twiki/bin/view/Chandler/CpiaZeroPointThreeStatus


Chandler Repository

For more details on our Repository, please read our RepositoryBusyDevelopersGuide:
   http://wiki.osafoundation.org/twiki/bin/view/Chandler/RepositoryBusyDevelopersGuide

After introducing the Repository in 0.2, we have made significant
improvements in 0.3 including:
  * Multi-threading support
  * Transaction and roll-back support
  * Limited query support
  * Notification support
  * Large object (text and binary) support
  * Full-text search and integration with Lucene
  * Experimental repository sharing using SOAP as a transport
  * Unit Test Suite including load and performance testing 

We are excited that the repository has reached a level of maturity and
are eager for community validation and feedback:
  * Is our API usable and comprehensible?  See
      http://osafoundation.org/docs/current/api/
  * Can you write performance or load tests/patches to pound on the 
    repository?  
      http://wiki.osafoundation.org/twiki/bin/view/Chandler/HelpUs#repositoryTests
  * Would you like to use our repository in your next application?

We would love to hear from you. Please send your comments, questions,
and suggestions to the development mailing list, dev@osafoundation.org.


Caterpillar UI

Caterpillar UI is our code name for an initial, premature UI. It is a
first step in designing our UI, but definitely not representative of
what will be in Canoga. The main elements are the side bar, navigation
bar, a very crude bookmark bar and the summary and detail views. It is
described in screenshots by Mimi at
  http://wiki.osafoundation.org/twiki/bin/view/Chandler/ZeroPointThreeUI
(Not all the screenshots are implemented as of the 0.3 release on 24 
February 2004.)

The 0.3 UI is very skeletal. It is mainly intended to test visual and
information design ideas. It's the bare scafolding we will use to
build the final UI and as such contains many "placeholder" pieces. Our
0.4 release will contain a much more complete UI "landscape". Feedback
on the UI is less helpful at this point and not encouraged. You are
welcome to follow our progress as 0.4 develops at
  http://wiki.osafoundation.org/twiki/bin/view/Chandler/ZeroPointFourPlanning


Other Improvements

  * We have a reasonably comprehensive initial version of our
    ContentModel in a nicely auto-generated human-readable format at
       http://www.osafoundation.org/docs/current/model/
  * A "parcel" is our unit of software package or plug-in. We have our
    parcel loading architecture in place in 0.3.
  * CPIA objects are well-integrated and exercise the Notification
    Framework.
  * ZaoBao uses the agent framework to poll for fresh RSS feeds.
  * We have refined our build system and run a much larger suite of
    unit tests.
  * Finally, and perhaps most important, we are gaining developer
    momentum through a DevelopmentProcess that is increasingly
    working well for us. See
       http://wiki.osafoundation.org/twiki/bin/view/Chandler/DevelopmentProcess


Running Chandler

In the normal case, running Chandler is very simple.  You can double-click on
the Chandler executable, named chandler (Linux),  Chandler
(Mac OS X), or Chandler.exe (Windows XP).  Under Linux, you can also
excute Chandler by typing ./chandler.  Additional platform-specific
information is in the README for your platform:
	README.linux.txt
	README.win.txt
	README.osx.txt

If you compile Chandler yourself, the instructions are slightly more
complicated: see RunningChandlerFromSourceReleases.

 
What should you expect when you run 0.3?

  * Starting up 0.3 is known to be very slow (30 secs to over a
    minute, depending on platform and machine) the first time you run
    the app. It's a little faster on subsequent launches.
  * Clicking on the Repository View in the side bar gives you a list
    of all Chandler items. It's a good diagnostic tool and also gives
    a good technical sense of what we mean by Chandler content items
    being item-centric. This is currently our most polished view.
  * The Demo view is a simple demonstration of CPIA. It is best viewed
    in conjuction with its associated source code, and is intended to
    show how easy it is to create CPIA views and elements.
  * ZaoBao (Chandler's RSS aggregator) has not only been CPIA-ized,
    but also exercises the Chandler Agent Framework to poll for fresh
    RSS feeds. You cannot add or delete feeds at this time.
  * The Mixed view is intended to test out ideas on how we can show
    items of various types in the same table. Bug#1207 describes
    some problems we are trying to fix on this view:
         http://bugzilla.osafoundation.org/show_bug.cgi?id=1207
  * Calendar, Contacts and Notes contain exactly those items. You will
    only see a calendar item initially. Under the "Test" menu, you can
    choose to generate different Items with completely fake data. When
    Items are generated, a Notification is broadcast via our
    Notification Framework to the views, causing an update of all
    relevant views.
  * Things you cannot do in 0.3:
       + Create any items (except by "auto-generating" fake items)
       + Edit or delete items
       + Any form of drag and drop
  * Our Bugzilla component list needs work. For now, most end-user
    bugs can probably be filed under "CPIA". If you're not sure what
    component to assign a bug. just leave it as "to be assigned".
  * We have a number of known bugs; see the KNOWN MAJOR BUGS section
    later in this document.

0.4 Release

For a preview to what we're planning for 0.4, see:
  http://wiki.osafoundation.org/twiki/bin/view/Chandler/ZeroPointFourPlanning
_________________________________________________________________

REQUIREMENTS

Chandler uses a number of components (e.g. Python), but all the
software you should need to run Chandler is shipped with Chandler. In
general, OSAF develops on Windows XP, Linux Red Hat 9, and Mac OS 10.3
("Panther").

We keep a list of platforms that Chandler is known to build and
run on at:
  http://wiki.osafoundation.org/twiki/bin/view/Chandler/ChandlerPlatforms

We have no reason to believe that it wouldn't work on other
reasonably current versions of operating systems, but in general,
haven't tested them.

One occasional difficulty is libraries on Unix machines. If you are
running with something other than a standard Red Hat 8 or Red Hat 9
release, you might need to either install a few modules or rebuild the
binaries.
_________________________________________________________________

HOW TO GET INVOLVED

There are several ways that you can get involved.

The first is to download Chandler (which you've already done) and try 
it out. If you find a bug, please check the list of known bugs in 0.3, 
and if it isn't listed, please report it.  See:
  22. http://wiki.osafoundation.org/twiki/bin/view/Chandler/ReportingBugs

We expect the visual design of the user
interface of the 1.0 version of Chandler to be compellingly gorgeous
as well as functionally elegant. The 0.3 release is neither; we
already know that, so you don't need to bother reminding us.

If you have an idea for a feature request, the best thing to do is to
post it to our mailing lists.  To subscribe, see:
  http://www.osafoundation.org/mailing_lists.htm

We also have a list of small, self-contained projects -- not
necessarily technical -- that we could use some help with. See:
  http://wiki.osafoundation.org/twiki/bin/view/Chandler/HelpUs
_________________________________________________________________

FURTHER INFORMATION

For Chandler end user documentation, see:
  http://wiki.osafoundation.org/twiki/bin/view/Chandler/EndUserDocumentation

For Chandler developer documentation, see:
  http://wiki.osafoundation.org/twiki/bin/view/Chandler/DeveloperDocumentation

For Chandler licensing information, see:
  http://wiki.osafoundation.org/twiki/bin/view/Chandler/ChandlerLicensingDocumentation
_________________________________________________________________

KNOWN MAJOR BUGS

These are the known bugs in the 0.3 release as of the release date.

  * There are a few bugs in 0.3 related to hangs. These might all be
    different manifestations of the same bug:
       + Quitting on the Mac is problematic. You might need to
         force-quit. (Bug#1278)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1278
       + Chandler can hang if you quit very quickly after you launch
         Chandler. (Bug#1296)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1296
       + Clicking wildly right after startup can cause a crash.
         (Bug#1297)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1297

Less serious errors include:
  * If you click on the sidebar, you can get an error. (Bug#1290)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1290
  * Running Check Repository can show some errors. (Bug#1311)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1311
  * You can't click on the Back button to take you all the way back to
    the starting view. (Bug#1275)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1275
  * Clicking on some links causes an error. (Bug#1280)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1280
  * You can't click on a column header to sort the column by that
    header. (Bug#1230)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1230
  * The unit test TestText:testAppend fails for release versions of
    Chandler (but not debug versions). (Bug#1169)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1169
  * A clean build of libxml2 can fail. (Bug#1116)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1116

  Mac OS X-specific problems

  * In OS X, some of the buttons in the Demo are ugly. (Bug#1213)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1213
  * On startup under OS X, you can sometimes get side-by-side windows.
    (Bug#1288)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1288
  * On Mac OS, Chandler takes a lot of processing power, even when
    doing nothing. (Bug#1279)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1279
  * Locale can't be set on Mac and Linux (Bug#251)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=251
  * If you switch from one sidebar item to another, you might see some
    flashing under Mas OS. (Bug#1212)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1212
  * The splitter bar and the column-header width are not always
    synched. (Bug#1323)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1323
  * The popup menu at the bottom of the Controls pane of the Demo view
    is empty. (Bug#1237)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1237

  Linux-specific problems

  * The Linux version requires GLIBC 2.3.2, which does not come with
    Red Hat 8. (Bug#1156)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1156
  * Under Linux, there can be poor refresh of Chandler windows that
    are obscured by other windows. (Bug#1273)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1273
  * Locale can't be set on Mac and Linux (Bug#251)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=251
  * Unit tests fail on Linux when DISPLAY isn't set to an X server.
    (Bug#1117)
           http://bugzilla.osafoundation.org/show_bug.cgi?id=1117

For the most up-to-date list, see: 
   http://wiki.osafoundation.org/twiki/bin/view/Chandler/ZeroPointThreeKnownMajorBugs

_________________________________________________________________

LICENSE

Chandler 0.3 Copyright (c) 2002-2004 Open Source Applications
Foundation

The 0.3 version of Chandler is available under the GNU General Public
License, version 2, as described in LICENSE.txt.

You can also see the authoritative version of the GNU GPL at
  http://www.fsf.org/licenses/

We expect that subsequent versions of Chandler will also be available
under one or more additional licenses. For more detail on our
licensing plans, see: 
  http://osafoundation.org/Chandler_licensing_plan_4-2003.htm

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.
_________________________________________________________________

