CHANDLER 0.2 README

Thank you for downloading Chandler's 0.2 release!

The 0.2 release of Chandler is still very skeletal in functionality,
with very few obvious differences to the end-user from the 0.1
release. However, there are some major changes in the underlying
framework and architecture. We feel that our platform is finally
beginning to be interesting for open source developers to start
contributing and writing code.

Our framework is by no means complete, but 0.2 shows a solid start on
several of our major framework areas:

  * Data Model and Repository, 
    http://wiki.osafoundation.org/bin/view/Main/DataModel
  * Notification Framework,
      http://wiki.osafoundation.org/bin/view/Main/NotificationModel
  * Agent Framework,
      http://wiki.osafoundation.org/bin/view/Main/AgentFrameworkPoint2Status
  * Chandler Presentation and Interaction Architecture,
      http://wiki.osafoundation.org/bin/view/Main/ChandlerPresentationAndInteractionArchitecture
  * Improved Code Development Features,
      http://wiki.osafoundation.org/bin/view/Main/ZeroDotTwoCodeDevelopmentFeatures

For a complete list of changes, see
    HISTORY.txt

0.2 is by no means stable, and should not be used to store important
data. We expect some significant changes in the near future. However,
it should give developers a good understanding of where we are
heading.

REPEAT: You should not store important information in Chandler yet.

Please read the license before installing, in the file named
       LICENSE.txt.

For information on how to run Chandler, please see the README
appropriate for your platform:
	    Windows  README.win.txt
	    Mac OS X README.osx.txt
	    Linux    README.linux.txt
  _________________________________________________________________

LICENSE

Chandler 0.2 Copyright (c) 2002-2003 Open Source Applications
Foundation

The 0.2 version of Chandler is available under the GNU General Public
License, version 2, as described in
	 LICENSE.txt

An electronic version of the GNU GPL can be found at
	http://www.fsf.org/licenses/

We expect that subsequent versions of Chandler will also be available
under one or more additional licenses. For more detail on our
licensing plans, see the Chandler Licensing Plan at
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

REQUIREMENTS

Chandler uses a number of components (e.g. python), but all the
software you should need to run Chandler is shipped with Chandler. In
general, OSAF develops on Windows XP, Linux Red Hat 9, and Mac OS 10.2
("Jaguar").

We keep a list of platforms that Chandler is known to build and
run on at:
  http://wiki.osafoundation.org/bin/view/Main/ChandlerPlatforms
We have no reason to believe that it wouldn't work on other
reasonably current versions of operating systems, but in general,
haven't tested them.

One occasional difficulty is libraries on Unix machines. If you are
running with something other than a standard Red Hat 8 or Red Hat 9
release, you might need to either install a few modules or rebuild the
binaries.
  _________________________________________________________________
MAJOR KNOWN BUGS AS OF THE 0.2 RELEASE

This section has the known major bugs in release 0.2. A more current
list is at:
  http://wiki.osafoundation.org/bin/view/Main/KnownMajorBugs

APPLICATION

The first time you start Chandler, the list of parcels appears all
squished together vertically, then immediately redraws. (Bug#923)

You cannot set the locale properly on the Mac or Linux (Bug#251).
(A warning error appears on startup on the Mac; Linux fails silently.)
This means, for example, that you can't localize how dates appear in
the Calendar e.g. under Table View. In Linux, Calendar's Table View
shows DD/MM/YY; on the Mac, the Table View shows dates as MM/DD/YY.

The first time a Repository commit() is done, it takes several seconds
to initialize everything.

Cut/Copy/Paste don't work. (Bug#920)

Chandler is slow to launch.

DOCUMENTATION

We don't have good built-in help. See the up-to-date end-user help
documentation.

CALENDAR

The Del key doesn't work when editing a Calendar Event description
(Bug#928).

Month and Table/List views are read-only. (No bug yet, just not
implemented).

Moving events in the Calendar is different across Windows, Mac OS, and
Linux (Bug#409). (We inherited behavior from wxWindows and have
not yet decided if or how we will change that behavior.)
  * Under Windows, drag-and-drop to move calendar events and
    Control-drag to copy events.
  * Under Linux, drag-and-drop to copy calendar events and Shift-drag
    to move events.
  * Under MacOS, drag-and-drop to copy events; there is no way (yet)
    to move events.

Under Linux, if the active locale is UTF-8 (the default on RedHat 8.0
or 9), the month panel may display Korean characters in place of Roman
letters and Arabic numerals. The work-around is to set the LANG
environment variable to a non-Unicode value (i.e. "export LANG=en_US")
before starting Chandler.

Event text does not always display correctly in Month View. (If it is
long, it can spill over into the next day's box instead of wrapping
into the next line of that day.)

You cannot (yet) create events in Month View.

CONTACTS

There are several bugs in Contacts related to creating or editing new
Views (Bug#824, Bug#829, Bug#914, Bug#889)

Text editing doesn't look right in Contacts edit boxes. (Bug#927)

There are several bugs related to Company Contacts (Bug#933,
Bug#935)

If you add an Interests attribute to a Contact on Linux, you will get
error messages on standard out. (Bug#275)

JABBER

Adding a well-formed but incorrect Jabber ID throws an exception
(Bug#883)

SHARING

Sharing does not work at all. (Bug#918)

ZAOBAO

To refresh the sites for new feeds, click on the Reload button.

ZaoBao crashes on some RSS feeds. (Bug#943)



_________________________________________________________________
WHERE TO GO FOR FURTHER INFORMATION

END-USER DOCUMENTATION

You can find a wikified version of this README at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerZeroPointTwoREADME

You can find general end-user documentation at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerEndUserDocumentation

A list of all known bugs in release 0.2 is at:
  http://wiki.osafoundation.org/bin/view/Main/KnownMajorBugs

If, when you try Chandler, it doesn't perform as expected, you can either file a
bug at
   http://bugzilla.osafoundation.org/enter_bug.cgi
or, if it's a question of the design, you can discuss it on our mailing lists at
   http://www.osafoundation.org/mailing_lists.htm
or on our wiki at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerDiscussionTopics

To see what other parcels people have developed for Chandler, see
   http://wiki.osafoundation.org/bin/view/Main/ThirdPartyParcels

DEVELOPER DOCUMENTATION

General developer documentation (including how to download and build the 
source) is at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerDeveloperDocumentation

For a high-level overview of the Chandler architecture, see
   http://www.osafoundation.org/architecture.htm
   http://wiki.osafoundation.org/bin/view/Main/ArchitectureDiagram

For information on how to write a ViewerParcel for Chandler, see
   http://wiki.osafoundation.org/bin/view/Main/ChandlerDeveloperDocumentation#parcels
(To a first approximation, you can think of a ViewerParcel as a plug-in.)  

To learn about our data model, see
   http://wiki.osafoundation.org/bin/view/Main/DataModel

To learn more about our Agent framework, see
   http://wiki.osafoundation.org/bin/view/Main/AgentFrameworkPoint2Status   

To learn more about our Notification framework, see
   http://wiki.osafoundation.org/bin/view/Main/NotificationModel

To learn more about the Chandler Presentation and Interaction Architecture,
see
   http://wiki.osafoundation.org/bin/view/Main/ChandlerPresentationAndInteractionArchitecture

If see what our coding guidelines are, see
   http://wiki.osafoundation.org/bin/view/Main/ChandlerCodingStyleGuidelines

If you write your own parcel, please post information about it at
   http://wiki.osafoundation.org/bin/view/Main/ThirdPartyParcels

NON-TECHNICAL INFORMATION

To find out what we think is compelling about Chandler, see
   http://www.osafoundation.org/OSAF_Our_Vision.htm

To learn more about the purpose and goals of the 0.2 release, see
   http://wiki.osafoundation.org/bin/view/Main/DotTwoPurposeSummary

To learn more about the Chandler license, see
   http://osafoundation.org/Chandler_licensing_plan_4-2003.htm

To learn more about our feature introduction strategy, see
   http://wiki.osafoundation.org/bin/view/Main/ProductRoadmap

To see a FAQ for the Chandler product, see
   http://www.osafoundation.org/Chandler-Product_FAQ.htm

To learn about OSAF's background, see
   http://www.osafoundation.org/Corporate_FAQ.htm
