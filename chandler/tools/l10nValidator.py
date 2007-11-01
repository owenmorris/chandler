#! /usr/bin/env python

import os, sys
from createBase import LocalizationBase

""" This is the old createPot.py script.
    The current createPot.py script
    replaced the use of pygettext with
    xgettext since the latter has
    better error checking and
    allows the addition of in-line
    localization comments in Python code.

    Since xgettext is not distributed
    with Chandler and is not installed
    by default on Windows and OS X,
    this script is used to do a rudimentary
    check that localization strings are
    correctly formatted in Chandler and
    is run as part of the unit test suite.
"""


class ValidatorTool(LocalizationBase):
    ROOTDIR = None
    BINROOT = None
    GETTEXT = None
    CWD = None
    XRC_FILES = []
    XRC_PYTHON = ".XRC_STRINGS_VALIDATION.py"
    OUTPUTFILE = ".Chandler-test.pot"
    CONFIG = ["."]

    def __init__(self):
        super(ValidatorTool, self).__init__()

        self.GETTEXT = os.path.join("tools", "pygettext.py")

        self.getOpts()
        self.setLibraryPath()
        self.setWXRC()

        try:
            self.OUTPUTFILE_EXISTS = os.access(self.OUTPUTFILE, os.F_OK)

            self.CWD = os.getcwd()

            os.chdir(self.ROOTDIR)

            self.extractXRCStrings()
            res = self.getText()

            if os.access(self.XRC_PYTHON, os.F_OK):
                # Remove the temp XRC Python file
                os.remove(self.XRC_PYTHON)

            if res != 0:
                # No .pot file is generated at this point since
                # an error was raised parsing the Python and XRC for
                # localizable stings.
                sys.exit(-1)

            os.chdir(self.CWD)

            # checks that there are no %s, %i , %d type
            # values in the msgid strings. These values
            # are not localizable since the ordering can
            # not be changed.
            error = self.checkPOFile(self.OUTPUTFILE)

            if os.access(self.OUTPUTFILE, os.F_OK):
                # Remove the temporary pot file
                os.remove(self.OUTPUTFILE)

            if error is not None:
                self.raiseError(error)

            if self.OPTIONS.Debug:
                self.debug()

        except Exception, e:
            self.raiseError(str(e))

    def debug(self):
        super(ValidatorTool, self).debug()

        print "GETTEXT: ", self.GETTEXT
        print "ROOTDIR: ", self.ROOTDIR
        print "CWD: ", self.CWD
        print "OUTPUTFILE: ", self.OUTPUTFILE
        print "WXRC: ", self.WXRC
        print "XRC_FILES: ", self.XRC_FILES
        print "XRC_PYTHON: ", self.XRC_PYTHON
        print "CONFIG: ", self.CONFIG
        print "\n\n"


    def setLibraryPath(self):
        platform = self.getPlatform()
        if platform == "Mac":
             os.environ["DYLD_LIBRARY_PATH"] = os.path.join(self.BINROOT, "lib")

        elif platform == "Linux":
             os.environ["LD_LIBRARY_PATH"] = os.path.join(self.BINROOT, "lib")


    def setWXRC(self):
        if self.getPlatform() == "Windows":
            self.WXRC = os.path.join(self.BINROOT, "bin", "wxrc.exe")
        else:
            self.WXRC = os.path.join(self.BINROOT, "bin", "wxrc")

        if not os.access(self.WXRC, os.F_OK):
            self.raiseError("Invalid path to wxrc " % self.WXRC)

    def extractXRCStrings(self):
        for dir in self.CONFIG:
            for root, dirs, files in os.walk(dir):
                for file in files:
                    if file.endswith(".xrc"):
                        self.XRC_FILES.append(os.path.join(root, file))

        for xrcFile in self.XRC_FILES:
            exp = "%s %s -g >> %s" % (self.WXRC, xrcFile,self.XRC_PYTHON)
            os.system(exp)

    def getText(self):
        dirs = " ".join(self.CONFIG)

        exp = "%s %s -o %s %s" % (self.PYTHON, self.GETTEXT, self.OUTPUTFILE, dirs)

        if dirs != ".":
            exp += " *.py"

        return os.system(exp)



    def getOpts(self):
        # The tool takes no arguments except --debug which is added to getopt in
        # the base class
        self.CONFIGITEMS = {}

        self.DESC = ""

        super(ValidatorTool, self).getOpts()

        self.CONFIG = self.CHANDLER
        self.ROOTDIR = self.CHANDLERHOME

if __name__ == "__main__":
    ValidatorTool()
