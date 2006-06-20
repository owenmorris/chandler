#!/usr/bin/env python

#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

#
# Helper program to send tinderbox2 status emails
#
# Author:   Mike Taylor (bear@osafoundation.org)
# Version:  1.0
#

import os, time, smtplib
import ConfigParser, optparse

def initOptions():
    """
    Load and parse the command line options, with overrides in **kwds.
    Returns options
    """
    #XXX i18n parcelPath, profileDir could have non-ascii paths
    # option name, (value, short cmd, long cmd, type flag, default, help text)
    _configItems = {'tree':     ('-t', '--tree',     's', 'Chandler', 'Tree Name'),
                    'build':    ('-b', '--build',    's', None, 'Build Name'),
                    'epoch':    ('-e', '--epoch',    's', None, 'Start time (in seconds since epoch)'),
                    'logfile':  ('-f', '--logfile',  's', None, 'Build Log filename'),
                    'logpath':  ('-p', '--logpath',  's', None, 'Build Log path'),
                    'status':   ('-s', '--status',   's', None, 'Build Status'),
                    'toAddr':   ('-T', '--toaddr',   's', 'buildreport',        'Address (name) to send email'),
                    'toDomain': ('-D', '--todomain', 's', '@osafoundation.org', 'Address (domain) to send email'),
                   }

    # %prog expands to os.path.basename(sys.argv[0])
    usage  = "usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage, version="%prog " + __version__)

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
    print options
    return options


def run(options):
    treeName     = options.tree
    buildName    = options.build
    fromAddr     = "builds@osafoundation.org"
    toAddr       = options.toAddr
    toDomain     = options.toDomain
    smtpOutbound = "smtp.osafoundation.org"
    logFile      = options.logfile
    logPath      = options.logpath
    status       = options.status
    logData      = None
    startTime    = options.epoch

    if treeName is None:
        print "Tree name must be specified"
        return
    if buildName is None:
        print "Build name must be specified"
        return
    if startTime is None:
        print "Start time must be specified"
        return
    if logPath is None:
        logPath = os.getcwd()

    if logFile:
        filename = os.path.join(logPath, logFile)
    
        if os.path.isfile(filename):
            try:
                hFile   = file(os.path.join(logPath, logFile), 'r')
                logData = hFile.readlines() 

                hFile.close()

            except Exception, e:
                logData = None
                print "[silk_tbox] - Unable to import %s%s [%s]\n" % (logPath, logFile, str(e))
        else:
            print "Log file %s not found" % filename

    nowTime  = str(int(time.time()))
    subject  = "[tinderbox] %s from %s" % (status, buildName)

    msg  = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (fromAddr, toAddr, subject))
    msg += "tinderbox: tree: %s\n" % treeName
    msg += "tinderbox: buildname: %s\n" % buildName
    msg += "tinderbox: starttime: %s\n" % startTime
    msg += "tinderbox: timenow: %s\n" % nowTime
    msg += "tinderbox: errorparser: unix\n"
    msg += "tinderbox: status: %s\n" % status
    msg += "tinderbox: END\n\n"

    if logData:
        msg += "".join(logData)

    print "Sending email to tinderbox server at %s" % toAddr

    try:
        server = smtplib.SMTP(smtpOutbound)
        server.sendmail(fromAddr, toAddr, msg)
        server.quit()

    except Exception, e:
        print "SendMail error", e

if __name__ == "__main__":
    options = initOptions()
    run(options)