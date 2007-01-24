#!/usr/bin/env python
#   Copyright (c) 2006,2007 Open Source Applications Foundation
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

"""
distribute.py
"""

import sys, os
import string
from optparse import OptionParser


def parseOptions():
    _configItems = {
        'verbose': ('-v', '--verbose', 'b', False, 'enable verbose log messages'),
        'mode':    ('-m', '--mode',    's', None,  'distribute release or debug; defaults to trying both'),
        'tarball': ('-t', '--tarball', 'b', False, 'only create the tarball (or zip) distribution - turns off -D'),
        'dmg':     ('',   '--dmg',     'b', False, 'only create the OS X .dmg bundle - turns off -D'),
        'deb':     ('',   '--deb',     'b', False, 'only create the debian package - turns off -D'),
        'rpm':     ('',   '--rpm',     'b', False, 'only create the rpm package - turns off -D'),
        'exe':     ('',   '--exe',     'b', False, 'only create the windows .exe installer - turns off -D'),
    }
    _usage = 'distribute [options]\n\nBundle installed Chandler working directory into a distribution'

    parser = OptionParser(version="%prog", usage=_usage)

    for key in _configItems:
        (shortCmd, longCmd, optionType, defaultValue, helpText) = _configItems[key]

        if optionType == 'b':
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              action='store_true',
                              default=defaultValue,
                              help=helpText)
        else:
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              default=defaultValue,
                              help=helpText)

    (options, args) = parser.parse_args()
    options.args    = args

    return options


def doCommand(cmd):
    """
    Run the given command and return the results.
    If during the wait a ctrl-c is pressed kill the cmd's process.
    """
    if options.verbose:
        print 'Calling:', cmd

    try:
        p = killableprocess.Popen(' '.join(cmd), shell=True)
        r = p.wait()

    except KeyboardInterrupt:
        _stop_test_run = True

        print '\nKeyboard Interrupt detected, stopping test run\n'

        try:
            r = p.kill(group=True)

        except OSError:
            r = p.wait()

    return r

def getPlatform():
    import platform

    platformName = 'Unknown'

    if os.name == 'nt':
        platformName = 'Windows'
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            platformName = 'OS X'
        elif sys.platform == 'cygwin':
            platformName = 'Windows'
        else:
            platformName = 'Linux'

    return platformName

if __name__ == '__main__':
    options = parseOptions()

    if 'CHANDLERHOME' in os.environ:
        options.chandlerHome = os.path.realpath(os.environ['CHANDLERHOME'])
    else:
        options.chandlerHome = os.getcwd()

    if 'CHANDLERBIN' in os.environ:
        options.chandlerBin = os.path.realpath(os.environ['CHANDLERBIN'])
    else:
        options.chandlerBin = options.chandlerHome

    options.platformName = getPlatform()

    if not os.path.isdir(options.chandlerBin):
        print 'Unable to locate CHANDLERBIN directory'
        sys.exit(3)

    if options.mode:
        options.mode = options.mode.tolower()

        if options.mode in modes:
            modes = [ options.mode ]
        else:
            print 'Invalid mode [%s] specified' % options.mode
            sys.exit(3)
    else:
        options.mode = [ 'release', 'debug' ]

    # if any of the individual options are set then build distrib list
    if options.tarball or options.dmg or options.rpm or options.deb or options.exe:
        options.distribs = []

        if options.tarball:
            options.distribs.append('tarball')

        if options.dmg and options.platformName == 'OS X':
            options.distribs.append('dmg')
        else:
            print 'Platform is [%s] -- ignoring dmg request' % options.platformName

        if options.rpm and options.platformName == 'Linux':
            options.distribs.append('rpm')
        else:
            print 'Platform is [%s] -- ignoring rpm request' % options.platformName

        if options.deb and options.platformName == 'Linux':
            options.distribs.append('deb')
        else:
            print 'Platform is [%s] -- ignoring deb request' % options.platformName

        if options.exe and options.platformName == 'Windows':
            options.distribs.append('exe')
        else:
            print 'Platform is [%s] -- ignoring exe request' % options.platformName
    else:
        if options.platformName == 'Linux':
            options.distribs = [ 'tarball', 'rpm', 'deb' ]
        else:
            if options.platformName == 'Windows':
                options.distribs = [ 'tarball', 'exe' ]
            else:
                options.distribs = [ 'tarball', 'dmg' ]

    print options


