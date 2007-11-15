#! /usr/bin/env python
#   Copyright (c) 2006-2007 Open Source Applications Foundation
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


import os, sys
from createBase import LocalizationBase
import build_lib

def ignore(output):
    pass


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

        self.GETTEXT = "xgettext"

        try:
            result = build_lib.runCommand("xgettext", timeout=5, logger=ignore)
        except:
            self.raiseError("The xgettext utility is required to run createPot.py")

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

            # checks that there are no %s, %i , %d type
            # values in the msgid strings. These values
            # are not localizable since the ordering can
            # not be changed.
            error = self.checkPOFile(self.OUTPUTFILE)

            if (self.OPTIONS.ValidateOnly or error is not None) and \
               not self.OUTPUTFILE_EXISTS and \
               os.access(self.OUTPUTFILE, os.F_OK):
                # If the optional ValidateOnly command is passed
                # then remove the generated .pot file.
                os.remove(self.OUTPUTFILE)

            if error is not None:
                self.raiseError(error)

            if os.access(self.OUTPUTFILE, os.F_OK):
                # Add the Chandler license banner
                # and glossary overview
                self.addHeader()

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

    def getPythonFiles(self):
        pFiles = []

        for dir in self.CONFIG:
            for root, dirs, files in os.walk(dir):
                for file in files:
                    if file.endswith(".py"):
                        pFiles.append(os.path.join(root, file))

        return pFiles

    def getText(self):
        dirs = " ".join(self.CONFIG)

        files = " ".join(self.getPythonFiles())

        if dirs != ".":
            files = "Chandler.py setup.py %s %s" % (self.XRC_PYTHON, files)

        exp = "%s --msgid-bugs-address=bkirsch@osafoundation.org --from-code=utf-8 --no-wrap --add-comments=L10N: -L Python -o %s %s" % (self.GETTEXT, os.path.join(self.CWD, self.OUTPUTFILE), files)


        return os.system(exp)

    def addHeader(self):
        newHeader = """#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


################
#
# Chandler Project is an open source, standards-based personal information
# manager (PIM) built around small group collaboration and a core set of
# information management workflows modeled on Inbox usage patterns and
# David Allen's GTD methodology.
#
# 'Item' Chandler has four kinds of items: Note, Message, Task and Event.
#        Chandler items can be of multiple kinds, e.g. Scheduled Tasks and Invitations.
#
# 'Collection' Chandler's primary mechanism for grouping items. Collections can contain
#              items of any kind.
#
# 'Application Area' Chandler has four application areas: Mail, Tasks,
#                    Calendar and an all-inclusive All area. Chandler's application areas
#                    are a way to filter down your collections by item kind.
#
# 'Triage Status' An attribute on every item that is Chandler's
#                 principle mechanism for helping you manage what you're working on.
#                 The three triage statuses are NOW, LATER and DONE.
#
# 'Tickler Alarm' A custom alarm you can set on any item to automatically
#                 triage that item to NOW at a time you specify.
#
# For the complete Glossary of Chandler terminology please visit:
#   http://chandlerproject.org/Projects/ChandlerGlossary
#
################

"""
        try:
            handle = open(self.OUTPUTFILE, "r")
            buf = handle.readlines()
            handle.close()

            # Replace the first 5 lines of the po file
            # which contain the stock header with
            # the custom Chandler header.
            text =  newHeader + "".join(buf[5:])
            handle = open(self.OUTPUTFILE, "w")
            handle.write(text)
            handle.close()
        except Exception, e:
            self.raiseError(str(e))

    def getOpts(self):
        self.CONFIGITEMS = {
        'Chandler': ('-c', '--chandler',  False, 'Extract localization strings from Chandler Python and XRC files. A gettext .pot template file "Chandler.pot" is written to the current working directory.'),
        'Project': ('-p', '--project', True, 'Extract localization strings Python and XRC files for the given project. A gettext .pot template file "PROJECTNAME.pot" is written to the current working directory.'),
        'Directory': ('-d', '--directory', True, 'The root directory to search under for XRC and Python files. Can only be used in conjunction with the -p Project command.'),
        'ValidateOnly': ('-v', '--validate_only',  False, 'optional argrument that when specified will only validate formating of localizable strings in Python and XRC files. No .pot will be generated.'),
        }

        self.DESC = ""

        super(TranslationTool, self).getOpts()

        if self.OPTIONS.Chandler:
            if self.OPTIONS.Project or self.OPTIONS.Directory:
                self.raiseError("Invalid arguments passed")

            self.CONFIG = self.CHANDLER
            self.ROOTDIR = self.CHANDLERHOME
            self.OUTPUTFILE = "Chandler.pot"

        elif self.OPTIONS.Project:
            if self.OPTIONS.Chandler:
                self.raiseError("Invalid arguments passed")

            if self.OPTIONS.Directory:
                self.ROOTDIR = self.OPTIONS.Directory
            else:
                self.ROOTDIR = os.getcwd()

            # Strip any whitespace
            self.OUTPUTFILE = "%s.pot" % self.OPTIONS.Project.replace(" ", "_")

        elif self.OPTIONS.Directory:
            if self.OPTIONS.Chandler:
                self.raiseError("Invalid arguments passed")
            if not self.OPTIONS.Project:
                self.raiseError("Directory '-d' argument can only be used with the '-p' Project argument")

        else:
            self.raiseError("At least one argument must be passed")


if __name__ == "__main__":
    TranslationTool()
