CHANDLER 0.1 README

We at OSAF are delighted that you downloaded the 0.1 release of
Chandler!  We hope that this release of Chandler will give you a flavor
of Chandler's architecture and APIs, and a glimse of what Chandler will
do in the future.

Please note that Chandler is still in its *extremely* early stages, with only
a very limited set of capabilities. 

Please also understand that many things are in flux.  In particular, because
our underlying database is undergoing changes, you should not store important 
information in Chandler yet.

REPEAT: You should not store important information in Chandler yet.

For information on how to run Chandler, please see the README appropriate for 
your operating system:
	Windows     README.win.txt
	Mac OS X    README.osx.txt
	Linux       README.linux.txt

--------------------------------------------------------------------------------
LICENSE

Chandler 0.1 Copyright (c) 2002-2003 Open Source Applications Foundation

The 0.1 version of Chandler is available under the GNU General Public License,
version 2, as described in
	LICENSE.txt

An electronic version of the GNU GPL can be found at
	http://www.fsf.org/licenses/

We expect that subsequent versions of Chandler will also be
available under one or more additional licenses. For more detail on our
licensing plans, see the Chandler Licensing Plan at
    http://osafoundation.org/Chandler_licensing_plan_4-2003.htm

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
SoftwareFoundation; either version 2 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.


--------------------------------------------------------------------------------

OVERVIEW

Chandler is a Personal Information Manager for Windows, Linux, and Mac OS X.  
When completed, it will integrate calendar, contacts, tasks, email, and instant 
messaging features.  It will be modular, extensible, peer-to-peer, and enable 
easily sharing information items between users.

This is only the 0.1 release, so it is very primitive.  Many things will 
improve.  However, it does show the skeleton of the framework and APIs.  It 
does have basic sharing enabled.  

--------------------------------------------------------------------------------

REQUIREMENTS

Chandler uses a number of components (e.g. python), but all the software you 
should need to run Chandler is shipped with Chandler.  In general, OSAF 
develops on Windows XP, Linux Red Hat 8 and Red Hat 9, and Mac OS 10.2 
("Jaguar").  We have no reason to believe that it wouldn't work on other 
reasonably current versions of operating systems, but in general, haven't 
tested them.

One occasional difficulty is libraries on Unix machines.  
If you are running with something other than a standard RedHat 8 or RedHat 9 
release, you might need to either install a few modules or rebuild the binaries.

--------------------------------------------------------------------------------

MAJOR KNOWN BUGS AS OF THE 0.1 RELEASE

Localization

+ You cannot set the locale properly on the Mac or Linux (Bug#251).  A 
warning error appears on startup on the Mac; Linux fails silently.  


Documentation

+ We don't have good built-in help.  To see up-to-date end-user help 
documentation, see
   http://wiki.osafoundation.org/bin/view/Main/ChandlerEndUserDocumentation


Calendar

+ Moving events in the Calendar is different across Windows, Mac OS, and 
Linux (Bug#409).  (We inherited behavior from wxWindows and have not yet 
decided if or how we will change that behavior.)
   + Under Windows, drag-and-drop to move calendar events and Control-drag to 
     copy events.
   + Under Linux, drag-and-drop to copy calendar events and Shift-drag to move 
     events.
   + Under MacOS, drag-and-drop to copy events; there is no way (yet) to move 
     events.

+ If you make a copy of an event in the Calendar, it doesn't persist.  In other
words, if you copy an event, switch to a different Parcel (e.g. Contacts), and 
switch back, you won't see the copied event.  You'll only see the original 
event. (Bug#425)

+ Under Linux, if the active locale is UTF-8 (the default on RedHat 8.0 or 9), 
the month panel may display Korean characters in place of Roman letters 
and Arabic numerals.  The work-around is to set the LANG environment variable 
to a non-Unicode value (i.e. "export LANG=en_US") before starting Chandler.

+ Event text does not always display correctly in Month View.  (If it is long, 
it can spill over into the next day's box instead of wrapping into the next 
line of that day.) 

+ You cannot (yet) create events in Month View.


ZaoBao

+ ZaoBao, an RSS aggregator, takes a long time to load the very first time.  
(It goes out to the network to initialize a bunch of RSS feeds.)


Timeclock

+ The second part of the multi-level Timeclock menu "Select currency label" 
does not appear. (Bug#406)

+ When you switch to the Timeclock parcel, only the last digit of the Floss 
Recycling rate appears in the text entry field.  (Bug#474)


Repository

+ On the Mac, the repository view window is too small to be useful (Bug#472).

+ The repository parcel can be slow to load.


Contacts

+ If you add an Interests attribute to a Contact on Linux, you will get an error
messages on standard out. (Bug#275)



--------------------------------------------------------------------------------

WHERE TO GO FOR FURTHER INFORMATION

TECHNICAL DOCUMENTATION

End-user Documentation

You can find a wikified version of this README at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerZeroPointOneREADME

You can find general end-user documentation at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerEndUserDocumentation

A list of all known bugs in the current build (which shortly will not be the 
same as the 0.1 release) is at
   http://bugzilla.osafoundation.org/buglist.cgi?product=Chandler&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&order=Importance

The wikified version of the README will have a more up-to-date list of major 
known bugs in 0.1 at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerZeroPointOneREADME#bugs


If, when you try Chandler, it doesn't perform as expected, you can either file a
bug at
   http://bugzilla.osafoundation.org 
or, if it's a question of the design, you can discuss it on our mailing lists at
   http://www.osafoundation.org/mailing_lists.htm
or on our wiki at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerDiscussionTopics

To see what other parcels people have developed for Chandler, see
   http://wiki.osafoundation.org/bin/view/Main/ThirdPartyParcels


Developer Documentation

General developer documentation (including how to download and build the 
source) is at
   http://wiki.osafoundation.org/bin/view/Main/ChandlerDeveloperDocumentation

For a high-level overview of the Chandler architecture, see
   http://www.osafoundation.org/architecture.htm
   http://wiki.osafoundation.org/bin/view/Main/ArchitectureDiagram

For information on how to write a ViewerParcel for Chandler, see
   http://wiki.osafoundation.org/bin/view/Main/HowToWriteAParcelTutorial

(To a first approximation, you can think of a ViewerParcel as a plug-in.)  

To learn about our data model, see
   http://wiki.osafoundation.org/bin/view/Main/DataModel

If see what our coding guidelines are, see
   http://wiki.osafoundation.org/bin/view/Main/ChandlerCodingStyleGuidelines

If you write your own parcel, please post information about it at
   http://wiki.osafoundation.org/bin/view/Main/ThirdPartyParcels


NON-TECHNICAL INFORMATION

To find out what we think is compelling about Chandler, see
   http://www.osafoundation.org/Chandler_Compelling_Vision.htm

To learn more about the purpose and goals of the 0.1 release, see
   http://wiki.osafoundation.org/bin/view/Main/PurposeandGoals

To learn more about what is in the 0.1 release, see
   http://wiki.osafoundation.org/bin/view/Main/ReleaseComponents

To learn more about the Chandler license, see
   http://osafoundation.org/Chandler_licensing_plan_4-2003.htm

To learn more about our feature introduction strategy, see
   http://wiki.osafoundation.org/bin/view/Main/ProductRoadmap

To see a FAQ for the Chandler product, see
   http://www.osafoundation.org/Chandler-Product_FAQ.htm

To learn about OSAF's background, see
   http://www.osafoundation.org/Corporate_FAQ.htm
