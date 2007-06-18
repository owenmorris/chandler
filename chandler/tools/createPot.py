#! /usr/bin/env python

import os, sys
from createBase import LocalizationBase


class TranslationTool(LocalizationBase):
    ROOTDIR = None
    BINROOT = None
    GETTEXT = None
    OUTPUTFILE = None
    OUTPUTFILE_EXISTS = False
    CWD = None
    XRC_FILES = []
    XRC_PYTHON = None
    CONFIG = ["."]

    def __init__(self):
        super(TranslationTool, self).__init__()

        self.GETTEXT = os.path.join(self.CHANDLERHOME, "tools", "pygettext.py")

        self.getOpts()
        self.setLibraryPath()
        self.setWXRC()

        try:
            self.OUTPUTFILE_EXISTS = os.access(self.OUTPUTFILE, os.F_OK)

            self.CWD = os.getcwd()

            os.chdir(self.ROOTDIR)

            self.XRC_PYTHON = "XRC_STRINGS_FOR_%s.py" % self.OUTPUTFILE[:-4].upper()
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

            if self.OPTIONS.ValidateOnly and \
               not self.OUTPUTFILE_EXISTS and \
               os.access(self.OUTPUTFILE, os.F_OK):
                # If the optional ValidateOnly command is passed
                # then remove the generated .pot file.
                os.remove(self.OUTPUTFILE)

            if self.OPTIONS.Debug:
                self.debug()

        except Exception, e:
            self.raiseError(str(e))

    def debug(self):
        super(TranslationTool, self).debug()

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

        exp = "%s %s -o %s %s" % (self.PYTHON, self.GETTEXT,
              os.path.join(self.CWD, self.OUTPUTFILE), dirs)

        if dirs != ".":
            exp += " *.py"

        return os.system(exp)



    def getOpts(self):
        self.CONFIGITEMS = {
        'Chandler': ('-c', '--chandler',  False, 'Extract localization strings from Chandler Python and XRC files. A gettext .pot template file "Chandler.pot" is written to the current working directory.'),
        'ChandlerExamples': ('-e', '--examples', False, 'Extract localization strings from Chandler Example projects Python and XRC files. A gettext .pot template file "ChandlerExamples.pot" is written to the current working directory.'),
        'Project': ('-p', '--project', True, 'Extract localization strings Python and XRC files for the given project. A gettext .pot template file "PROJECTNAME.pot" is written to the current working directory.'),
        'Directory': ('-d', '--directory', True, 'The root directory to search under for XRC and Python files. Can only be used in conjunction with the -p Project command.'),
        'ValidateOnly': ('-v', '--validate_only',  False, 'optional argrument that when specified will only validate formating of localizable strings in Python and XRC files. No .pot will be generated.'),
        }

        self.DESC = ""

        super(TranslationTool, self).getOpts()

        if self.OPTIONS.Chandler:
            if self.OPTIONS.ChandlerExamples or\
            self.OPTIONS.Project or self.OPTIONS.Directory:
                self.raiseError("Invalid arguments passed")

            self.CONFIG = self.CHANDLER
            self.ROOTDIR = self.CHANDLERHOME
            self.OUTPUTFILE = "Chandler.pot"

        elif self.OPTIONS.ChandlerExamples:
            if self.OPTIONS.Chandler or\
            self.OPTIONS.Project or self.OPTIONS.Directory:
                self.raiseError("Invalid arguments passed")

            self.CONFIG = self.CHANDLER_EXAMPLES
            self.ROOTDIR = os.path.join(self.CHANDLERHOME, "projects")
            self.OUTPUTFILE = "ChandlerExamples.pot"

        elif self.OPTIONS.Project:
            if self.OPTIONS.Chandler or\
            self.OPTIONS.ChandlerExamples:
                self.raiseError("Invalid arguments passed")

            if self.OPTIONS.Directory:
                self.ROOTDIR = self.OPTIONS.Directory
            else:
                self.ROOTDIR = os.getcwd()

            # Strip any whitespace
            self.OUTPUTFILE = "%s.pot" % self.OPTIONS.Project.replace(" ", "_")

        elif self.OPTIONS.Directory:
            if self.OPTIONS.Chandler or\
            self.OPTIONS.ChandlerExamples:
                self.raiseError("Invalid arguments passed")
            if not self.OPTIONS.Project:
                self.raiseError("Directory '-d' argument can only be used with the '-p' Project argument")

        else:
            self.raiseError("At least one argument must be passed")


if __name__ == "__main__":
    TranslationTool()
