#!/usr/bin/env python

# Make Chandler distributions from an existing tinderbox directory

# run this from the ~/hardhat directory

import hardhatlib, hardhatutil, time, os, sys, md5, sha

# args:  buildName, outputDir

buildName = sys.argv[1]
outputDir = sys.argv[2]

distCmd = {'debug':'-dD', 'release':'-D'}

homeDir = os.environ['HOME']
buildDir = os.path.join(homeDir, "tinderbuild")
whereAmI = os.path.dirname(os.path.abspath(hardhatutil.__file__))
hardhatFile = os.path.join(whereAmI, "hardhat.py")
workingDir = os.path.join(homeDir,"tinderbuild","chandler")

def main():
    global outputDir
    
    path = os.environ.get('PATH', os.environ.get('path'))
    rsyncProgram = hardhatutil.findInPath(path, "rsync")
    # print "rsync =", rsyncProgram
    outputDir = os.path.abspath(outputDir)
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)

    nowString = time.strftime("%Y-%m-%d %H:%M:%S")
    buildVersion = hardhatutil.RemovePunctuation(nowString)
    print "Making distribution for: ", nowString, buildVersion
    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")

    os.chdir(workingDir)
    for releaseMode in ('debug', 'release'):

        print "Creating " + releaseMode + " distribution archive"
        outputList = hardhatutil.executeCommandReturnOutput(
         [hardhatFile, "-o", os.path.join(outputDir, buildVersion), distCmd[releaseMode], 
         buildVersionEscaped])
        hardhatutil.dumpOutputList(outputList)

    newDir = os.path.join(outputDir, buildVersion)
    if os.path.exists(outputDir+os.sep+"index.html"):
        os.remove(outputDir+os.sep+"index.html")
    if os.path.exists(outputDir+os.sep+"time.js"):
        os.remove(outputDir+os.sep+"time.js")
    print "Calling  RotateDirectories \n"
    RotateDirectories(outputDir)
    print "Calling CreateIndex with " + newDir + "\n"
    CreateIndex(outputDir, buildVersion, nowString, buildName)
    
    buildNameNoSpaces = buildName.replace(" ", "")
    print "Rsyncing..."
    outputList = hardhatutil.executeCommandReturnOutputRetry(
     [rsyncProgram, "-e", "ssh", "-avzp", "--delete",
     outputDir + os.sep, 
     "192.168.101.46:continuous/" + buildNameNoSpaces])

def RotateDirectories(dir):
    """Removes all but the 3 newest subdirectories from the given directory;
    assumes the directories are named with timestamps (numbers) because it 
    uses normal sorting to determine the order."""

    dirs = os.listdir(dir)
    dirs.sort()
    for subdir in dirs[:-3]:
        print "  subdir = ", subdir
        if os.path.isdir(subdir):
            hardhatutil.rmdirRecursive(os.path.join(dir, subdir))


_descriptions = {
    'enduser' : ["End-Users' distribution", "If you just want to use Chandler, this distribution contains everything you need -- just download, unpack, run."],
    'developer' : ["Developers' distribution", "If you're a developer and want to run Chandler in debugging mode, this distribution contains debug versions of the binaries.  Assertions are active, the __debug__ global is set to True, and memory leaks are listed upon exit.  You can also use this distribution to develop your own parcels (See <a href='http://wiki.osafoundation.org/bin/view/Chandler/ParcelLoading'>Parcel Loading</a> for details on loading your own parcels)."],
}

def MD5sum(filename):
    """Compute MD5 checksum for the file
    """
    m = md5.new()
    fileobj = open(filename)
    filedata = fileobj.read()
    fileobj.close()
    m.update(filedata)
    return m.hexdigest()

def SHAsum(filename):
    """Compute SHA-1 checksum for the file
    """
    s = sha.new()
    fileobj = open(filename)
    filedata = fileobj.read()
    fileobj.close()
    s.update(filedata)
    return s.hexdigest()

def CreateIndex(outputDir, newDirName, nowString, buildName):
    """Generates an index.html page from the hint files that hardhat creates
    which contain the actual distro filenames
    """
    fileOut = file(outputDir+os.sep+"index.html", "w")
    fileOut.write("<html><head><META HTTP-EQUIV=Pragma CONTENT=no-cache><link rel=Stylesheet href=http://www.osafoundation.org/css/OSAF.css type=text/css charset=iso-8859-1></head><body topmargin=0 leftmargin=0 marginwith=0 marginheight=0><img src=http://www.osafoundation.org/images/OSAFLogo.gif><table border=0><tr><td width=19>&nbsp;</td><td width=550>\n")
    fileOut.write("<h2>Chandler Build: " + nowString + " PDT (machine: " + buildName +")</h2>\n")
    for x in ["enduser", "developer"]:
        actual = _readFile(outputDir+os.sep+newDirName+os.sep+x)
        fileOut.write("<p><a href="+x+".html> "+ _descriptions[x][0] +"</a>: " + _descriptions[x][1] +"</p>\n")
        fileOut2 = file(outputDir+os.sep+x+".html", "w")
        fileOut2.write("<html><head><META HTTP-EQUIV=Pragma CONTENT=no-cache><link rel=Stylesheet href=http://www.osafoundation.org/css/OSAF.css type=text/css charset=iso-8859-1></head><body topmargin=0 leftmargin=0 marginwith=0 marginheight=0><img src=http://www.osafoundation.org/images/OSAFLogo.gif><table border=0><tr><td width=19>&nbsp;</td><td width=550>\n")
        fileOut2.write("<h2>Chandler Build: " + nowString + " PDT (machine: " + buildName +")</h2>\n")
        fileOut2.write("<p>Download <a href="+newDirName+"/"+actual+"> "+ _descriptions[x][0] +"</a>: <br>")
        fileOut2.write(" MD5 checksum: " + MD5sum(outputDir+os.sep+newDirName+os.sep+actual) + "<br>")
        fileOut2.write(" SHA checksum: " + SHAsum(outputDir+os.sep+newDirName+os.sep+actual) + "<br>")
        fileOut2.write("<p> " + _descriptions[x][1] +"</p>\n")
        fileOut2.write("</td></tr></table></body></html>\n")
        fileOut2.close()

    fileOut.write("</td></tr></table></body></html>\n")
    fileOut.close()
    fileOut = file(outputDir+os.sep+"time.js", "w")
    fileOut.write("document.write('" + nowString + "');\n")
    fileOut.close()

def _readFile(path):
    fileIn = open(path, "r")
    line = fileIn.readline()
    fileIn.close()
    return line.strip()


main()
