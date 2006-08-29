#! /usr/bin/env python

import os, sys
from optparse import OptionParser


"""

TO DO
=======
1. Test on Linux and Windows
2. Build a po / egg tool
"""

class TranslationTool(object):
    ROOTDIR = ""
    CHANDLERHOME = ""
    CHANDLERBIN = ""
    BINROOT = ""
    PYTHON = ""
    WXRC = ""
    GETTEXT = ""
    OUTPUTFILE = ""
    CWD = ""
    OPTIONS = None
    XRC_FILES = []
    XRC_PYTHON = ""

    CONFIG = ["."]

    CHANDLER_CONFIG = ["application", os.path.join("parcels", "osaf")]


    CHANDLER_EXAMPLES_CONFIG = ["Chandler-AmazonPlugin",
                                "Chandler-EVDPlugin",
                                "Chandler-EventLoggerPlugin",
                                "Chandler-FeedsPlugin",
                                "Chandler-FlickrPlugin",
                                "Chandler-PhotoPlugin",
                        ]


    def __init__(self):
        if os.environ.has_key("CHANDLERHOME"):
            self.CHANDLERHOME = os.environ["CHANDLERHOME"]
        else:
            self.CHANDLERHOME = os.getcwd()

        try:
            if not "Chandler.py" in os.listdir(self.CHANDLERHOME):
                raise Exception()
        except:
            self.raiseError("CHANDLERHOME is invalid '%s'" % self.CHANDLERHOME)

        if os.environ.has_key("CHANDLERBIN"):
            self.CHANDLERBIN = os.environ["CHANDLERBIN"]
        else:
            self.CHANDLERBIN = self.CHANDLERHOME

        try:
            if "debug" in os.listdir(self.CHANDLERBIN):
                self.BINROOT = os.path.join(self.CHANDLERBIN, "debug")

            elif "release" in os.listdir(self.CHANDLERBIN):
                self.BINROOT = os.path.join(self.CHANDLERBIN, "release")

            else:
                self.raiseError("No debug or release directory under CHANDLERBIN")
        except:
            self.raiseError("CHANDLERBIN is invalid '%s'" % self.CHANDLERBIN)

        self.PYTHON = os.path.join(self.BINROOT, "RunPython")
        self.GETTEXT = os.path.join(self.CHANDLERHOME, "tools", "pygettext.py")

        self.getOpts()
        self.setLibraryPath()
        self.setWXRC()

        try:
            self.CWD = os.getcwd()
            os.chdir(self.ROOTDIR)

            self.XRC_PYTHON = "XRC_STRINGS_FOR_%s.py" % self.OUTPUTFILE[:-4].upper()
            self.extractXRCStrings()
            self.getText()

            if os.access(self.XRC_PYTHON, os.F_OK):
                os.remove(self.XRC_PYTHON)

            os.chdir(self.CWD)

            if self.OPTIONS.Verbose:
                self.debug()

        except Exception, e:
            self.raiseError("Directory path '%s' is invalid" % self.ROOTDIR)

    def debug(self):
        print "\n\nProgram run with the following configuration:"
        print "_______________________________________________\n"
        print "CHANDLERHOME: ", self.CHANDLERHOME
        print "CHANDLERBIN: ", self.CHANDLERBIN
        print "BINROOT: ", self.BINROOT
        print "PYTHON: ", self.PYTHON
        print "GETTEXT: ", self.GETTEXT
        print "ROOTDIR: ", self.ROOTDIR
        print "CWD: ", self.CWD
        print "OUTPUTFILE: ", self.OUTPUTFILE
        print "OPTIONS: ", self.OPTIONS
        print "WXRC: ", self.WXRC
        print "XRC_FILES: ", self.XRC_FILES
        print "XRC_PYTHON: ", self.XRC_PYTHON
        print "CONFIG: ", self.CONFIG
        print "\n\n"


    def setLibraryPath(self):
        if sys.platform == 'darwin':
             os.environ["DYLD_LIBRARY_PATH"] = os.path.join(self.BINROOT, "lib")

        elif os.name != 'nt': #Linux
             os.environ["LD_LIBRARY_PATH"] = os.path.join(self.BINROOT, "lib")


    def setWXRC(self):
        if os.name == 'nt':
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

        exp = "%s %s -o %s %s" % (self.PYTHON, self.GETTEXT,
              os.path.join(self.CWD, self.OUTPUTFILE), dirs)

        if dirs != ".":
            exp += " *.py"

        os.system(exp)


    def raiseError(self, txt):
        print "\n\nThe following error was raised: "
        print "----------------------------------------\n%s\n\n" % txt
        sys.exit(-1)

    def getOpts(self):
        _configItems = {
        'Chandler': ('-c', '--Chandler',  False, 'Extract localization strings from Chandler Python and XRC files. A gettext .pot template file "Chandler.pot" is written to the current working directory'),
        'ChandlerExamples': ('-e', '--ChandlerExamples', False, 'Extract localization strings from Chandler Example projects Python and XRC files. A gettext .pot template file "ChandlerExamples.pot" is written to the currentworking directory'),
        'Project': ('-p', '--Project', True, 'Extract localization strings Python and XRC files for the given project. A gettext .pot template file "PROJECTNAME.pot" is written to the current working directory'),
        'Directory': ('-d', '--Directory', True, 'The root directory to search under for XRC and Python files. Can only be used in conjunction with the -p Project command.'),
        'Verbose': ('-v', '--Verbose', False, 'Prints Verbose debugging information to the stdout'),
        }


        # %prog expands to os.path.basename(sys.argv[0])
        usage  = "usage: %prog [options]"
        parser = OptionParser(usage=usage, version="%prog 1.0")

        for key in _configItems:
            (shortCmd, longCmd, argReq, helpText) = _configItems[key]

            if argReq:
                parser.add_option(shortCmd, longCmd, dest=key, help=helpText)
            else:
                parser.add_option(shortCmd, longCmd, dest=key, action="store_true",  help=helpText)

        (self.OPTIONS, args) = parser.parse_args()

        if self.OPTIONS.Chandler:
            if self.OPTIONS.ChandlerExamples or\
            self.OPTIONS.Project or self.OPTIONS.Directory:
                parser.error("Invalid arguments passed")

            self.CONFIG = self.CHANDLER_CONFIG
            self.ROOTDIR = self.CHANDLERHOME
            self.OUTPUTFILE = "Chandler.pot"

        elif self.OPTIONS.ChandlerExamples:
            if self.OPTIONS.Chandler or\
            self.OPTIONS.Project or self.OPTIONS.Directory:
                parser.error("Invalid arguments passed")

            self.CONFIG = self.CHANDLER_EXAMPLES_CONFIG
            self.ROOTDIR = os.path.join(self.CHANDLERHOME, "projects")
            self.OUTPUTFILE = "ChandlerExamples.pot"

        elif self.OPTIONS.Project:
            if self.OPTIONS.Chandler or\
            self.OPTIONS.ChandlerExamples:
                parser.error("Invalid arguments passed")

            if self.OPTIONS.Directory:
                self.ROOTDIR = self.OPTIONS.Directory
            else:
                self.ROOTDIR = os.getcwd()

            # Strip any whitespace
            self.OUTPUTFILE = "%s.pot" % self.OPTIONS.Project.replace(" ", "_")

        else:
            parser.error("At least one argument must be passed")


if __name__ == "__main__":
    TranslationTool()
