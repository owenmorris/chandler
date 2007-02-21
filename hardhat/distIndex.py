#!/usr/bin/python


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


# Chandler script for singlebuild process
#   which produces all the required pages


"""
Notes:
This script is meant to be run on the builds server 
    (currently "oahu.osafoundation.org")
    in the builder's home directory
Instructions for use are in the TWiki at "MakingARelease"
"""

# To appease older Pythons:
True = 1
False = 0

import os, sys, shutil, re, time, string, hardhatutil
from optparse import OptionParser

path = os.environ.get('PATH', os.environ.get('path'))

def main():

    parser = OptionParser(usage="%prog [options] type release-num target-dir", version="%prog 2.0")
    (options, args) = parser.parse_args()
    if len(args) <= 3:
        parser.print_help()
        parser.error("You must provide [M | R | C | S], relase number and a directory name: M 0.5.03 0_5_03")

    rType = args[0]
    release = args[1]
    targetDir = args[2]

    if rType == "R":
        rFormat = "Release"
    elif rType == "M":
        rFormat = "Milestone"
    elif rType == "C":
        rFormat = "Checkpoint"
    elif rType == "SC":
        rFormat = "Checkpoint"
    elif rType == "SR":
        rFormat = "Release"
    else:
        parser.print_help()
        parser.error("You must provide [M | R | C | S], relase number and a directory name: M 0.5.03 0_5_03")

    print "Making index pages for", rFormat, release, rType[0]
    if rType[0] == 'S':
        CreateSnarfIndex(release, rFormat, targetDir, args[3])
    else:
        CreateIndex(release, targetDir)
        MakeMaster(release, rFormat, rType, targetDir)
        MakeJS(release, rFormat, targetDir)

    print "Complete"

_descriptions = {
    'enduser' : ["End-Users' distribution", "If you just want to use Chandler, this distribution contains everything you need -- just download, unpack, run."],
    'developer' : ["Debug distribution", "If you're a developer and want to run Chandler in debugging mode, this distribution contains debug versions of the binaries. It runs a lot slower than the end-users release. Assertions are active, the __debug__ global is set to True, and memory leaks are listed upon exit. You may also want to use this distribution to develop and test your own parcels (See <a href='http://wiki.osafoundation.org/bin/view/Chandler/ParcelLoading'>Parcel Loading</a> for details on loading your own parcels)."],
    'snarf': ["OSAF Sharing Server", "If you want to try out Cosmo this distribution contains everything you need.  Download and extract."]
}

def MakeJS(buildName, buildType, targetDir):
    """
    Generates a javascript 'id.js' page for a Chandler Milestone/Release build
    The file will contain only  "document.write('Milestone 0.3.21, 2004-07-27');"
    """

    fileOut = file(os.path.join("snapshots", targetDir,"id.js"), "w")
    buildName = re.sub(r'_', '.', buildName) 
    text = "document.write(' " + buildType + " " + buildName + ", " + time.strftime("%Y-%m-%d") + "');"

    fileOut.write(text)
    fileOut.close()

def MakeMaster(buildName, buildType, rType, targetDir):
    """
    Generates an index.html page for a Chandler Milestone/Release build
    """

    fileOut = file(os.path.join("snapshots", targetDir,"index.html"), "w")
    fileIn = file("release.index.html", "r")
    text = fileIn.read()

    (text, subs) = re.subn(r'XYZZY', buildName, text)
    print "Replaced %i occurrences of XYZZY with %s" % (subs, buildName)
    (text, subs) = re.subn(r'Plugh', buildType, text)
    print "Replaced %i occurrences of Plugh with %s" % (subs, buildType)
    buildType = string.lower(buildType)
    (text, subs) = re.subn(r'plugh', buildType, text)
    print "Replaced %i occurrences of plugh with %s" % (subs, buildType)

    fileOut.write(text)
    fileOut.close()


def CreateIndex(buildName, targetDir):
    """Generates a <buildName>_index.html page from the hint files that hardhat creates
    which contain the actual distro filenames"""

    html =  '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'
    html += '<html><head>\n'
    html += '<link rel="Stylesheet" href="http://builds.osafoundation.org/tinderbox/OSAF.css" type="text/css" charset="iso-8859-1">\n'
    html += '<title>Downloads for Chandler Build: ' + buildName + '</title>\n'
    html += '</head><body<img src="http://builds.osafoundation.org/tinderbox/OSAFLogo.gif" alt="[OSAF Logo]">\n'
    html += '<h2>Chandler Build: ' + buildName + '</h2>\n'
    files = os.listdir(os.path.join("/home/builder/snapshots", targetDir))
    for thisFile in files:
        fileName = os.path.join("/home/builder/snapshots", targetDir, thisFile)
        if fileName.find("_src_") > 0:
            print "Generating data for ", thisFile
            html += '<strong style="font-size: larger;">'
            html += '<a href="' + thisFile + '">' + thisFile + '</a>'
            html += ' (' + hardhatutil.fileSize(fileName) + ')</strong>\n'
            html += '<p>Source code.</p>'
            html += ' MD5 checksum: ' + hardhatutil.MD5sum(fileName) + '<br>'
            html += ' SHA checksum: ' + hardhatutil.SHAsum(fileName) + '<br>'
            html += '\n<hr>\n'
        elif fileName.lower().find("chandler") > 0:
            print "Generating data for ", thisFile
            html += '<strong style="font-size: larger;">'            
            html += '<a href="' + thisFile + '">' + thisFile + '</a>'
            html += ' (' + hardhatutil.fileSize(fileName) + ')</strong>\n'
            if fileName.find("_debug_") > 0:
                html += '<p>' + _descriptions['developer'][1] + '</p>'
            else:
                html += '<p>' + _descriptions['enduser'][1] + '</p>'
            html += ' MD5 checksum: ' + hardhatutil.MD5sum(fileName) + '<br>'
            html += ' SHA checksum: ' + hardhatutil.SHAsum(fileName) + '<br>'
            html += '\n<hr>\n'
        else:
            print "skipping ", thisFile

    html += '</body></html>\n'

    fileOut = file(buildName+"_index.html", "w")
    fileOut.write(html)
    fileOut.close()

    shutil.move(fileOut.name, os.path.join("snapshots", targetDir, fileOut.name))


def CreateSnarfIndex(buildName, buildType, targetDir, distribName):
    html =  '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'
    html += '<html><head>\n'
    html += '<link rel="Stylesheet" href="http://www.osafoundation.org/css/OSAF.css" type="text/css" charset="iso-8859-1">\n'
    html += '<title>Downloads for OSAF Sharing Server: ' + buildName + '</title>\n'
    html += '</head><body<img src="http://www.osafoundation.org/images/OSAFLogo.gif" alt="[OSAF Logo]">\n'
    html += '<h2>OSAF Server: ' + buildName + '</h2>\n'

    if buildType == "Release":
        workDir = os.path.join('/www/downloads/cosmo/releases', targetDir)
    else:
        workDir = os.path.join('/www/downloads/cosmo/checkpoints', targetDir)
    filename      = os.path.join(workDir, distribName)
    indexTemplate = 'snarf.index.html'
    lcBuildType   = buildType.lower()

    print 'Generating data for %s' % filename

    html += '<strong style="font-size: larger;">'
    html += '<a href="%s">%s</a>'    % (filename, filename)
    html += ' (%s)</strong>\n'       % hardhatutil.fileSize(filename)
    html += '<p>%s</p>'              % _descriptions['snarf'][1]
    html += ' MD5 checksum: %s<br/>' % hardhatutil.MD5sum(filename)
    html += ' SHA checksum: %s<br/>' % hardhatutil.SHAsum(filename)
    html += '\n<hr>\n'
    html += '</body></html>\n'

    text = "document.write(' %s %s, %s');" % (buildType, re.sub(r'_', '.', buildName), time.strftime("%Y-%m-%d"))

    fileIn = file(indexTemplate, "r")
    index  = fileIn.read()
    fileIn.close()

    (index, n1) = re.subn(r'XYZZY', buildName, index)
    (index, n2) = re.subn(r'Plugh', buildType, index)
    (index, n3) = re.subn(r'plugh', lcBuildType, index)
    (index, n4) = re.subn(r'YZZXX', distribName, index)

    print "Replaced %i occurrences of XYZZY with %s" % (n1, buildName)
    print "Replaced %i occurrences of Plugh with %s" % (n2, buildType)
    print "Replaced %i occurrences of plugh with %s" % (n3, lcBuildType)
    print "Replaced %i occurrences of YZZXX with %s" % (n4, distribName)

    fileOut = file(os.path.join(workDir, buildName + "_index.html"), "w")
    fileOut.write(html)
    fileOut.close()

    fileOut = file(os.path.join(workDir, "id.js"), "w")
    fileOut.write(text)
    fileOut.close()

    fileOut = file(os.path.join(workDir, "index.html"), "w")
    fileOut.write(index)
    fileOut.close()


main()
