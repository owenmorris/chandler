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

import os, sys, shutil, re, time, string
from optparse import OptionParser

path = os.environ.get('PATH', os.environ.get('path'))

def main():

    parser = OptionParser(usage="%prog [options] type release-num", version="%prog 2.0")
    (options, args) = parser.parse_args()
    if len(args) != 2:
        parser.print_help()
        parser.error("You must provide M | R and a release number")

    rType = args[0]
    release = args[1]
    if rType == "R":
        rFormat = "Release"
    elif rType == "M":
        rFormat = "Milestone"
    else:
        parser.print_help()
        parser.error("You must provide M | R and a release number")
        
    print "Making index pages for", rFormat, release
    CreateIndex(release)
    MakeMaster(release, rFormat)
    MakeJS(release, rFormat)

    print "Complete"

_descriptions = {
    'enduser' : ["End-Users' distribution", "If you just want to use Chandler, this distribution contains everything you need -- just download, unpack, run."],
    'developer' : ["Developers' distribution", "If you're a developer and want to run Chandler in debugging mode, this distribution contains debug versions of the binaries.  Assertions are active, the __debug__ global is set to True, and memory leaks are listed upon exit.  You can also use this distribution to develop your own parcels (See <a href='http://wiki.osafoundation.org/bin/view/Chandler/ParcelLoading'>Parcel Loading</a> for details on loading your own parcels)."],
}

def MakeJS(buildName, buildType):
    """
    Generates a javascript 'id.js' page for a Chandler Milestone/Release build
    The file will contain only  "document.write('Milestone 0.3.21, 2004-07-27');"
    """

    fileOut = file(os.path.join("snapshots", buildName,"id.js"), "w")
    buildName = re.sub(r'_', '.', buildName) 
    text = "document.write(' " + buildType + " " + buildName + ", " + time.strftime("%Y-%m-%d") + "');"

    fileOut.write(text)
    fileOut.close()

def MakeMaster(buildName, buildType):
    """
    Generates an index.html page for a Chandler Milestone/Release build
    """

    fileOut = file(os.path.join("snapshots", buildName,"index.html"), "w")
    fileIn = file(os.path.join("singlebuild","chandler", "distrib", "release.index.html"), "r")
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


def CreateIndex(buildName):
    """Generates a <buildName>_index.html page from the hint files that hardhat creates
    which contain the actual distro filenames"""

    fileOut = file(buildName+"_index.html", "w")
    fileOut.write("<html><head><META HTTP-EQUIV=Pragma CONTENT=no-cache>\n")
    fileOut.write("<link rel=Stylesheet href=http://builds.osafoundation.org/tinderbox/OSAF.css type=text/css charset=iso-8859-1>\n")
    fileOut.write("<title>Downloads for Chandler Build: " + buildName + "</title>\n")
    fileOut.write("</head><body topmargin=0 leftmargin=0 marginwith=0 marginheight=0><img src=http://builds.osafoundation.org/tinderbox/OSAFLogo.gif>\n")
    fileOut.write("<table border=0><tr><td width=450>\n")
    fileOut.write("<h2>Chandler Build: " + buildName + "</h2>\n")
    fileOut.write("</td></tr>\n<tr><td><hr></td></tr>\n")
    files = os.listdir(os.path.join("/home/builder/snapshots", buildName))
    for thisFile in files:
        fileName = os.path.join("/home/builder/snapshots", buildName,thisFile)
        if fileName.find("_src_") > 0:
            print "Generating data for ", thisFile
            fileOut.write("<tr><td>\n")
            fileOut.write("<h3><a href=http://builds.osafoundation.org" + fileName + ">" + thisFile + "</a></h3>\n</td></tr>\n")
            fileOut.write("<tr><td>\n")
            fileOut.write(" MD5 checksum: " + hardhatutil.MD5sum(fileName) +\
                          "<br>")
            fileOut.write(" SHA checksum: " + hardhatutil.SHAsum(fileName) +\
                          "<br>")
            fileOut.write("</td></tr>\n<tr><td><hr></td></tr>\n")
        elif fileName.find("Chan") > 0:
            print "Generating data for ", thisFile
            fileOut.write("<tr><td>\n")
            fileOut.write("<h3><a href=http://builds.osafoundation.org" + fileName + ">" + thisFile + "</a></h3>\n</td></tr>\n")
            fileOut.write("<tr><td>\n")
            fileOut.write("<tr><td>\n")
            if fileName.find("_debug_") > 0:
                fileOut.write( _descriptions['developer'][1])
            else:
                fileOut.write( _descriptions['enduser'][1])
            fileOut.write("<tr><td>\n")
            fileOut.write(" MD5 checksum: " + hardhatutil.MD5sum(fileName) +\
                          "<br>")
            fileOut.write(" SHA checksum: " + hardhatutil.SHAsum(fileName) +\
                          "<br>")
            fileOut.write("</td></tr>\n<tr><td><hr></td></tr>\n")
        else:
            print "skipping ", thisFile


    fileOut.write("</table></body></html>\n")
    fileOut.close()
    shutil.move(fileOut.name, os.path.join("snapshots", buildName, fileOut.name))

main()
