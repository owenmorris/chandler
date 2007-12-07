#! /usr/bin/env python
# -*- coding: utf-8 -*-
#   Copyright (c) 2006-2007 Open Source Applications Foundation
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

import sys, os
from poUtility import *

potFile = parse(sys.argv[1])
poFile  = parse(sys.argv[2])

potFileName = os.path.split(potFile.poFileName)[-1]
poFileName  = os.path.split(poFile.poFileName)[-1]

print "\n=====================================================================\n"
print "    POT Template / PO File Comparison Utility"
print "    ------------------------------------------\n"
print "   %s msgid's: %s" % (potFileName, len(potFile.poEntries.keys()))
print "   %s msgid's: %s" % (poFileName, len(poFile.poEntries.keys()))




potOnlyEntries = []
poOnlyEntries = []

for msgid in potFile.poEntries:
    if not msgid in poFile.poEntries:
        potOnlyEntries.append(potFile.poEntries[msgid])


for msgid in poFile.poEntries:
    if not msgid in potFile.poEntries:
        poOnlyEntries.append(poFile.poEntries[msgid])

if potOnlyEntries:
    print "\n   ***************************************************************************"
    print "           WARNING: %s missing the following  msgids:" % (poFileName)
    print "   ***************************************************************************\n"

    for poEntry in potOnlyEntries:
        print "     %s:%i: %s" % (potFileName, poEntry.msgidLineNumber, poEntry.msgid)


if poOnlyEntries:
    print "\n   ***************************************************************************"
    print "           WARNING: %s contains msgid's not in %s:" % (poFileName, potFileName)
    print "   ***************************************************************************\n"

    for poEntry in poOnlyEntries:
        print "    %s:%i: %s" % (poFileName, poEntry.msgidLineNumber, poEntry.msgid)



print "\n=====================================================================\n"
