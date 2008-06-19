#   Copyright (c) 2007 Open Source Applications Foundation
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

from datetime import date
from application.Utility import COMMAND_LINE_OPTIONS

options = []
environment = []

# Do not list test and developer-centric options in the man page,
# they will still be printed with --help.
supressed = ('--recordedTest',
             '-v', '--verbose',
             '-d', '--debugOn',
             '--prune',
             '-k',
             '-T', '--chandlerTestSuite',
             '-m', '--ramdb',
             '-f', '--scriptFile',
             '-n', '--nocatch',
             '--memorylog',
             '--chandlerTestLogfile',
             '--chandlerPerformanceTests',
             '--mvcc',
             '-V', '--verify-assignments',
             '--catsProfile',
             '-M', '--chandlerTestMask',
             '-D', '--chandlerTestDebug',
             '--nodeferdelete',
             '-a', '--app-parcel',
             '--checkpoints',
             '--catsPerfLog',
             '-F', '--continueTestsOnFailure',
             '-U', '--uuids',
             '--expand',
             '--nomvcc',
             '-L', '--logging',
             '--chandlerTests',
             '-q', '--quiet'
             '--pluginPath',
             '-w', '--wing',
             )

for key in COMMAND_LINE_OPTIONS.keys():
    short, long, val, _y, env, desc = COMMAND_LINE_OPTIONS[key]
    if short in supressed or long in supressed:
        continue
    
    short = short.replace('-', '\-')
    long = long.replace('-', '\-')
    desc = desc.replace('-', '\-')
    options.append((short, long, val, desc))
    if env:
        environment.append((env, long))

options.sort()
environment.sort()

print """.\\"DO NOT EDIT. GENERATED FILE.
.\\"
.\\" To view the pretty printed version, do:
.\\"   groff -man -Tascii chandler.1 |less
.\\"
.\\"   Copyright (c) 2007 Open Source Applications Foundation
.\\"
.\\"   Licensed under the Apache License, Version 2.0 (the "License");
.\\"   you may not use this file except in compliance with the License.
.\\"   You may obtain a copy of the License at
.\\"
.\\"       http://www.apache.org/licenses/LICENSE-2.0
.\\"
.\\"   Unless required by applicable law or agreed to in writing, software
.\\"   distributed under the License is distributed on an "AS IS" BASIS,
.\\"   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.\\"   See the License for the specific language governing permissions and
.\\"   limitations under the License.
.\\"
.TH chandler 1  "%s" "CHANDLER_VERSION" "Chandler Manual"
.SH NAME
chandler \- personal information manager
.SH SYNOPSIS
.B chandler""" % date.isoformat(date.today())

for short, long, val, desc in options:
    print '.B',
    if val in ('s', 'v'):
        close = ''
    else:
        close = ']'
    if short and long:
        print '[%s, %s%s' % (short, long, close)
    else:
        assert long
        print '[%s%s' % (long, close)
    if val in ('s', 'v'):
        print '.IB', '" %s"]' % long[4:]
print '.B [...]'

print """\
.SH DESCRIPTION
Chandler Desktop is an open source, standards-based personal information
manager (PIM) built around small group collaboration and a core set of
information management workflows modeled on Inbox usage patterns and
David Allen's GTD methodology.
.SH OPTIONS"""

for short, long, val, desc in options:
    print '.TP'
    if val in ('s', 'v'):
        print '.BI',
    else:
        print '.B',
    if short and long:
        print '"%s, %s"' % (short, long),
    else:
        print '"%s"' % long,
    if val in ('s', 'v'):
        print '" %s"' % long[4:],
    print
    if desc:
        print desc

print """\
.SH FILES
.TP
.I ~/.chandler/[random_string].default
.RS
Chandler default profile directory, where
.IR __repository__ ,
.IR chandler.log ,
.IR chandler.prefs ,
.IR randpool.dat ,
.IR start.log
and possibly
.IR backup.chex
are located.
.SH ENVIRONMENT
.TP
.B CHANDLERHOME
directory where
.I Chandler.py
is located in, set automatically but can be overridden
.TP
.B CHANDLERBIN
directory under which the
.I release
or
.I debug
directories are located in, typically same as
.BR CHANDLERHOME ,
set automatically but can be overridden"""

for env, long in environment:
    print '.TP'
    print '.B', env.upper()
    print 'same as option'
    print '.B', long

print """\
.SH EXIT STATUS
chandler returns 0 on successful exit, non-zero otherwise.
.SH SEE ALSO
http://chandlerproject.org"""
