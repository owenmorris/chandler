                               0.4 README

Welcome to Chandler!

This is Chandler's 0.4 release, and while it is still far from complete, we
have made enormous progress since 0.3.

Note: there is an HTML version of this README at:
   http://www.osafoundation.org/0.4/ReadMe.htm

    + Introduction and Overview 
         o Purpose of release
         o Running Chandler
         o Setting Preferences
         o Email Account
         o WebDAV Account
         o Requirements
    + How to get involved
    + Further information
    + Known Major Bugs
    + License 
    + 0.5 Planning
_________________________________________________________________

INTRODUCTION AND OVERVIEW

PURPOSE OF RELEASE

The high-level goal of the 0.4 release is to be "experimentally usable" for
a few key end-user tasks. In 0.4, you can:

  * Create, edit, and view PIM Items: Email, Calendar Events, 
    Tasks, and Notes.
  * Add and modify Task, Email, or Event properties to any PIM item, 
    in a process we call "Stamping".
  * Share collections (including calendars) via a WebDAV server 
    with other Chandler users.
  * Perform very basic email and calendar operations (e.g. send and 
    receive email, create and modify calendar events).

In addition, the 0.4 Release provides:
  * Sending and receiving of mail over a TLS/SSL connection (a fully 
    secure TLS transport is not implemented yet)
  * Base UI landscape: Sidebar, Tabs, Summary & Detail views

RUNNING CHANDLER

For  OS  X  and  Windows  XP, running Chandler is very simple. You can
double-click on the Chandler executable, named Chandler (Mac OS X), or
Chandler.exe (Windows XP). If you are running Mac OS X, you need to copy
Chandler from your .dmg disk image to somewhere else on your file system
first.

There is a problem with the Linux distribution such that you cannot simply
double-click on the the binary. (See Bug #1672.) You will need to change to
the chandler subdirectory, then type release/RunChandler. Note that you must
be in the chandler directory; you cannot change to the release directory and
type ./RunChandler.

Additional   platform-specific  information  is  in  README.linux.txt,
README.win.txt, and README.osx.txt.

If  you  compile Chandler yourself, the instructions are slightly more
complicated.  See: 
http://wiki.osafoundation.org/bin/view/Chandler/RunningChandlerFromSourceReleases

SETTING PREFERENCES

To use the sharing features of Chandler revision 0.4, you will need accounts
on IMAP, SMTP, and WebDAV servers. The WebDAV server acts as an intermediary
for Items, while email is used to send and receive invitations to share
data.

To set the preferences, select File->Preferences->Accounts. You will then
have options for setting the IMAP, SMTP, and WebDAV server accounts.

EMAIL ACCOUNT

For IMAP and SMTP preferences, you should be able to look at the preferences
in your normal email program to figure out what the settings should be in
Chandler. For "Full Name" in the IMAP preferences, use your own full name,
e.g. "Mabel Garcia".

Note that if you check the SSL box in either the IMAP or SMTP dialogs, be 
sure to enter the correct port number for your server.  (Many email clients 
will change the port number for you automatically, but not Chandler.  Yet.)

WEBDAV ACCOUNT

You will also need a WebDAV account.

If you do not already have a WebDAV account, you can get a free account from
Sharemation at 
	http://www.sharemation.com
If  you  want  to set up your own WebDAV server, see
	http://www.webdav.org/mod_dav.

For a Sharemation account, for Server, type in
  http://www.sharemation.com

For Path, type in the userid (e.g. mabelgarcia).

IMPORTANT: Do not put a slash (/) at the beginning of the path field! That
will confuse Chandler.

REQUIREMENTS

Chandler uses a number of components (e.g. Python), but all the software you
need to run Chandler is shipped with Chandler. In general, OSAF
develops on Microsoft Windows XP, Red Hat Fedora Core 2, and Apple Mac OS
10.3 ("Panther").

We keep a list of platforms that Chandler is known to build and run on:
   http://wiki.osafoundation.org/bin/view/Chandler/ChandlerPlatforms

We have no reason to believe that it wouldn't work on other reasonably
current versions of operating systems, but in general, haven't tested them.

One occasional difficulty is libraries on Unix machines. If you are running
with something other than a standard Red Hat Fedora Core 2 system, you might
need to either install a few modules or rebuild the binaries.
_________________________________________________________________

HOW TO GET INVOLVED

There are several ways that you can get involved.

The first is to download Chandler and try it out.  You can follow the
Guided Tour, available at:
   http://www.osafoundation.org/0.4/GuidedTour.htm

If you find a bug,
please check the list of known bugs in 0.4 at
   http://wiki.osafoundation.org/bin/view/Chandler/ZeroPointFourKnownMajorBugs

If you find a bug that isn't listed, please report it at:
   http://wiki.osafoundation.org/bin/view/Chandler/ReportingBugs

If you have an idea for a feature request, the best thing to do is to post
it to our mailing lists.  You can find more about our mailing lists at:
   http://www.osafoundation.org/mailing_lists.htm

We also have a list of small, self-contained projects -- not necessarily
technical -- that we could use some help with on our wiki at:
   http://wiki.osafoundation.org/bin/view/Chandler/HelpUs

_________________________________________________________________

FURTHER INFORMATION

For more information, please see documentation on our wiki at:
   http://wiki.osafoundation.org/bin/view/Chandler/GettingChandler
   http://wiki.osafoundation.org/bin/view/Chandler/EndUserDocumentation
   http://wiki.osafoundation.org/bin/view/Chandler/DeveloperDocumentation
   http://wiki.osafoundation.org/bin/view/Chandler/LicensingTopics

_________________________________________________________________

KNOWN MAJOR BUGS

For information about major bugs in the 0.4 release, see
http://wiki.osafoundation.org/bin/view/Chandler/ZeroPointFourKnownMajorBugs

_________________________________________________________________

LICENSE

Chandler 0.4 Copyright (c) 2002-2004 Open Source Applications Foundation

The  0.4 version of Chandler is available under the GNU General Public
License, version 2, as described in LICENSE.txt in the distribution.

You can also see the authoritative version of the GNU GPL at:
   http://www.fsf.org/licenses/

We expect that subsequent versions of Chandler will also be available under
one or more additional licenses. For more detail on our licensing plans, see
the Chandler Licensing Plan at:
   http://osafoundation.org/Chandler_licensing_plan_4-2003.htm

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY  WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.
_________________________________________________________________

0.5 Planning

For more on our future plans, see
  http://wiki.osafoundation.org/bin/view/Chandler/ZeroPointFivePlanning
