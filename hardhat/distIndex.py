#!/usr/bin/python
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
    if len(args) != 3:
        parser.print_help()
        parser.error("You must provide [M | R | C], relase number and a directory name: M 0.5.03 0_5_03")

    rType = args[0]
    release = args[1]
    targetDir = args[2]

    if rType == "R":
        rFormat = "Release"
    elif rType == "M":
        rFormat = "Milestone"
    elif rType == "C":
        rFormat = "Checkpoint"
    else:
        parser.print_help()
        parser.error("You must provide [M | R | C], relase number and a directory name: M 0.5.03 0_5_03")
        
    print "Making index pages for", rFormat, release
    CreateIndex(release, targetDir)
    MakeMaster(release, rFormat, rType, targetDir)
    MakeJS(release, rFormat, targetDir)

    print "Complete"

_descriptions = {
    'enduser' : ["End-Users' distribution", "If you just want to use Chandler, this distribution contains everything you need -- just download, unpack, run."],
    'developer' : ["Developers' distribution", "If you're a developer and want to run Chandler in debugging mode, this distribution contains debug versions of the binaries.  Assertions are active, the __debug__ global is set to True, and memory leaks are listed upon exit.  You can also use this distribution to develop your own parcels (See <a href='http://wiki.osafoundation.org/bin/view/Chandler/ParcelLoading'>Parcel Loading</a> for details on loading your own parcels)."],
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
        urlPath = os.path.join("/chandler/snapshots", targetDir, thisFile)
        if fileName.find("_src_") > 0:
            print "Generating data for ", thisFile
            html += '<strong style="font-size: larger;">'
            html += '<a href="' + thisFile + '">' + thisFile + '</a>'
            html += ' (' + hardhatutil.fileSize(fileName) + ')</strong>\n'
            html += '<p>Source code.</p>'
            html += ' MD5 checksum: ' + hardhatutil.MD5sum(fileName) + '<br>'
            html += ' SHA checksum: ' + hardhatutil.SHAsum(fileName) + '<br>'
            html += '\n<hr>\n'
        elif fileName.find("Chan") > 0:
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

main()
