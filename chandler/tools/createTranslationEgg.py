#! /usr/bin/env python
# -*- coding: utf-8 -*-
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


from createBase import LocalizationBase
from poUtility import *
from distutils.dir_util import copy_tree, remove_tree, mkpath
from distutils.file_util import copy_file
import os, sys
import build_lib

try:
    from PyICU import Locale
    # We want the English textual representation
    # of the locale to display to the user.
    Locale.setDefault(Locale("en"))

    PYICU_INSTALLED = True
except:
    PYICU_INSTALLED = False

def ignore(output):
    pass

try:
    build_lib.runCommand("msgfmt", timeout=5, logger=ignore)
    MSGFMT_INSTALLED = True
except:
    MSGFMT_INSTALLED = False



class TranslationEggTool(LocalizationBase):
    PROJECTNAME = None
    PROJECTNAMES = None
    LOCALE = None
    OUTPUTDIR = None
    PLUGINDIR = None
    PLUGINDIR_EXISTS = False
    PLUGINNAME = None
    EGGINFODIR = None
    CWD = None
    POFILE = None
    POFILEPATH = None
    POFILEOBJECT = None
    IMGDIR = None
    HTMLDIR = None
    LOCALEDIR = None
    DISTEGG = False
    DISTNAME = None
    USE_MSGFMT_BINARY = False


    def __init__(self):
        super(TranslationEggTool, self).__init__()

        if sys.platform == 'cygwin':
            self.raiseError("Cygwin is not supported due to filesystem\n" \
                            "pathing issues.\n\n" \
                            "Please use the Windows Command Prompt instead.")

        self.getOpts()

        self.PLUGINNAME = "%s.%s" % (self.PROJECTNAME, self.LOCALE)
        self.POFILE = os.path.split(self.POFILEPATH)[-1]

        if self.OUTPUTDIR:
            self.PLUGINDIR = os.path.join(self.OUTPUTDIR, self.PLUGINNAME)
        else:
            self.PLUGINDIR = self.PLUGINNAME

        # Did the Localization Egg Plug-In directory exist.
        # If so do not delete the directory on dist or error.
        self.PLUGINDIR_EXISTS = os.access(self.PLUGINDIR, os.F_OK)

        try:
            # Validate that PO exists and is correctly formatted
            self.validatePOFile()

            mkpath(self.PLUGINDIR)

            self.CWD = os.getcwd()
            os.chdir(self.PLUGINDIR)

            self.writeReadMeFile()
            self.writeSetupFile()
            self.createEggInfoDir()

            self.LOCALEDIR = os.path.join(self.EGGINFODIR, "locale", self.LOCALE)

            self.writeResourceFile()
            self.createMoFile()

            if self.IMGDIR:
                self.copyImages()

            if self.HTMLDIR:
                self.copyHtml()

            if self.DISTEGG:
                self.packageEggForDistribution()
                # When packaging an egg for distribution
                # if the plugin directory did not already
                # exist then remove the newly created
                # directory.

                if not self.PLUGINDIR_EXISTS:
                    self.removePluginDir()
            else:
                self.putEggInDevelopMode()

            os.chdir(self.CWD)

            if self.OPTIONS.Debug:
                self.debug()

            print "\n\n           EGG CREATION COMPLETED"
            print "==========================================================="

            if self.DISTEGG:
                print " Translation egg '%s' has been built\nfor distribution.\n" % (self.DISTNAME)
            else:
                print " Translation egg '%s' has been" % (self.PLUGINDIR)
                print " installed in develop mode.\n"

                if self.OPTIONS.Chandler:
                    print " To test, start Chandler and select '%s'" % self.getLocaleName()
                    print " from the File -> Switch Language... dialog."

            acWarnings = checkAccelerators(self.POFILEOBJECT)
            nWarnings  = checkNewLines(self.POFILEOBJECT)

            if acWarnings or nWarnings:
                print "\n  PARSER WARNINGS:"

            for warning in acWarnings:
                print "    %s:%i: msgstr missing keyboard accelerator '&'" % \
                      (self.POFILE, warning.msgstrLineNumber)

            for warning in nWarnings:
                print "    %s:%i: msgid and msgstr entries do not both end with '\\n'" % \
                      (self.POFILE, warning.msgstrLineNumber)

            print "\n  TRANSLATION STATISTICS: "
            print "     total strings: ", self.POFILEOBJECT.getMsgIDCount()
            print "     fuzzy strings: ", self.POFILEOBJECT.getFuzzyCount()
            print "        translated: ", self.POFILEOBJECT.getTranslatedCount()
            print "      untranslated: ", self.POFILEOBJECT.getUntranslatedCount()
            print "===========================================================\n\n"

        except Exception, e:
            self.raiseError(str(e))

    def getLocaleName(self):
        if PYICU_INSTALLED:
            return Locale(self.LOCALE).getDisplayName()

        return self.LOCALE


    def copyImages(self):
        imgDir = os.path.join(self.LOCALEDIR, "images")

        try:
            copy_tree(self.IMGDIR, imgDir)

        except Exception, e:
            self.raiseError("Unable to copy images from '%s': %s." % (self.IMGDIR, e))


    def copyHtml(self):
        htmlDir = os.path.join(self.LOCALEDIR, "html")

        try:
            copy_tree(self.HTMLDIR, htmlDir)
        except Exception, e:
            self.raiseError("Unable to copy html from '%s': %s." % (self.HTMLDIR, e))

    def validatePOFile(self):
        try:
            #Save the POFile Object in an instance variable so
            # that the it can later be used to display statistics
            # from the po file such as the number of translated
            # strings as well as any warnings.
            self.POFILEOBJECT = parse(self.POFILEPATH)
        except ParserError, e:
            # The po file contains one or more formating errors.
            # Raising an exception here will result in the program
            # terminating and an error message displayed to the user.
            desc = "%s:%i: Parser error '%s'\n" % \
                   (e.poFileName, e.lineNumber, str(e.exception))
            raise Exception(desc)

        # Make sure that all Python replaceable dict values
        # that are in the msgid's got copied correctly to
        # translated msgstr's.
        errors = checkReplaceableValues(self.POFILEOBJECT)

        desc = ""

        if errors:
            for poEntry, values in errors:
                desc += "%s:%i: Replaceable value%s %s missing from msgstr.\n" % \
                        (self.POFILE, poEntry.msgstrLineNumber, len(values) > 1 and 's' or '',
                         ", ".join(values))

        # Make sure that there are no %s %i type values in the msgstr's.
        errors = checkPrintValues(self.POFILEOBJECT, 'msgstr')

        if errors:
            for poEntry, values in errors:
                desc += "%s:%i: Invalid value%s %s found. Only replaceable values are " \
                        "allowed in msgstr.\n" % \
                         (self.POFILE, poEntry.msgstrLineNumber, len(values) > 1 and 's' or '',
                          ", ".join(values))

        if len(desc):
            # Raising an exception here will result in the program
            # terminating and an error message displayed to the user.
            raise Exception(desc)

    def createMoFile(self):
        try:
            mkpath(self.LOCALEDIR)
            copy_file(self.POFILEPATH, self.LOCALEDIR)
            cwd = os.getcwd()
            os.chdir(self.LOCALEDIR)

            if self.USE_MSGFMT_BINARY:
                # The msgfmt binary that ships as part of GNU gettext tools
                # is more robust then the Python version and includes
                # error checking capabilities.
                moFile = self.POFILE[:-2] + "mo"
                exp = ["msgfmt", "-c", "--check-accelerators", "-o%s" % moFile,
                       self.POFILE]

            else:
                # The msgfmt gettext binary is not installed by default on
                # Windows and OS X. The Python version of msgfmt is included
                # however with Chandler.
                msgfmt = os.path.join(self.CHANDLERHOME, "tools", "msgfmt.py")
                exp = [self.PYTHON,  msgfmt, self.POFILE]

            result = build_lib.runCommand(exp, timeout=60, logger=ignore)
            os.chdir(cwd)

            if result != 0:
                raise Exception(' '.join(exp) + ' failed with error code %d' % result)

        except Exception, e:
            self.raiseError("Unable to create mo file from %s': %s." % (self.POFILEPATH, e))

    def createEggInfoDir(self):
        exp = [self.PYTHON, 'setup.py', 'egg_info']
        result = build_lib.runCommand(exp, timeout=60, logger=ignore)

        if result != 0:
            self.raiseError(' '.join(exp) + ' failed with error code %d' % result)

        for item in os.listdir(os.getcwd()):
            if item.endswith(".egg-info"):
                self.EGGINFODIR = item
                break

        if not self.EGGINFODIR:
            self.raiseError("An Error occurred while building %s project. Please try again." \
                            % (self.PLUGINNAME))


    def putEggInDevelopMode(self):
        exp = [self.PYTHON, "setup.py", "develop", "--install-dir=%s" % self.CHANDLERHOME]
        result = build_lib.runCommand(exp, timeout=60, logger=ignore)
        if result != 0:
            self.raiseError(' '.join(exp) + ' failed with error code %d' % result)

    def packageEggForDistribution(self):
        exp = [self.PYTHON, "setup.py", "bdist_egg"]
        result = build_lib.runCommand(exp, timeout=60, logger=ignore)
        if result != 0:
            self.raiseError(' '.join(exp) + ' failed with error code %d' % result)

        distDir = os.path.join(os.getcwd(), "dist")

        for item in os.listdir(distDir):
            if item.endswith(".egg"):
                self.DISTNAME = item
                break

        if not self.DISTNAME:
            self.raiseError("An Error occurred while building %s project.\n" \
                            "Unable to build distribution egg." % (self.PLUGINNAME))

        copy_file(os.path.join(distDir, self.DISTNAME), \
                  self.OUTPUTDIR and self.OUTPUTDIR or self.CWD)

    def writeReadMeFile(self):
        txt = "README File for translation egg '%s'" % (self.PLUGINNAME)
        f = file("README.txt", "w")
        f.write(txt)
        f.close()

    def writeSetupFile(self):
        setup = """\
# -*- coding: utf-8 -*-
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

# import packages
from setuptools import setup

# the setup block
setup(
    # package description
    name = "%s",
    version = "1.0",
    author = "",
    author_email = "",
    description = "'%s' locale translation egg for Project '%s'",
    license = "Apache License, Version 2.0",
    include_package_data = True,
    zip_safe = True,
)
""" % (self.PLUGINNAME, self.LOCALE, self.PROJECTNAME)
        f = file("setup.py", "w")
        f.write(setup)
        f.close()


    def writeResourceFile(self):
        buffer = []
        outDir = "locale/%s" % self.LOCALE

        for project in self.PROJECTNAMES:
            buffer.append("[%s::%s]" % (project, self.LOCALE))
            buffer.append("gettext.catalog = %s/%s.mo" % \
                          (outDir, self.POFILE[:-3]))

            if self.IMGDIR:
                buffer.append("img.resources = %s/images" % outDir)
            if self.HTMLDIR:
                buffer.append("html.resources = %s/html" % outDir)

        iniText = "\n".join(buffer)
        iniFile = os.path.join(self.EGGINFODIR, "resources.ini")

        f = file(iniFile, "w")
        f.write(iniText)
        f.close()

    def debug(self):
        super(TranslationEggTool, self).debug()
        print "PROJECTNAME: ", self.PROJECTNAME
        print "PROJECTNAMES: ", self.PROJECTNAMES
        print "LOCALE: ", self.LOCALE
        print "LOCALEDIR: ", self.LOCALEDIR
        print "OUTPUTDIR: ", self.OUTPUTDIR
        print "PLUGINDIR: ", self.PLUGINDIR
        print "PLUGINNAME: ", self.PLUGINNAME
        print "EGGINFODIR: ", self.EGGINFODIR
        print "CWD: ", self.CWD
        print "POFILE: ", self.POFILE
        print "POFILEPATH: ", self.POFILEPATH

        if self.IMGDIR:
            print "IMGDIR: ", self.IMGDIR

        if self.HTMLDIR:
            print "HTMLDIR: ", self.HTMLDIR

        print "\n\n"

    def getOpts(self):
        self.CONFIGITEMS = {
        'Chandler': ('-c', '--chandler',  False, 'Creates a translation egg for the Chandler Project. The egg will be named "Chandler.LOCALENAME" for example "Chandler.fr". If no gettext .po file is specified via the -f command then the current working directory and the CHANDLERHOME are scanned for a gettext po file named "Chandler-LOCALNAME.po". For example "Chandler-fr.po"'),
        'Project': ('-p', '--project',  True, 'Creates a translation egg for a given Project. The egg will be in the format  "PROJECTNAME.LOCALENAME". Passing a project name of "Test-Plugin" and the French locale will create a translation egg for the "Test-Plugin" project named "Test-Plugin.fr". A relative or full filesystem path to a .po gettext localization file via the -f command is required. A locale specified via the -l command is also required.'),

        'PoFile': ('-f', '--file',  True, 'A relative or full filesystem path to the .po translation file for the egg project. The po file will be copied to the egg and a .mo binary file generated. The .mo file will be registered with the eggs "resources.ini".'),
        'Locale': ('-l', '--locale', True, 'A valid locale name such as "fr", "fr_CA", "en", "en_US". The argument is required and must be specified in order for a translation egg to be generated.'),
        'Directory': ('-d', '--directory', True, 'An optional output directory where the translation egg will be written. The default is the current working directory.'),
        'ImageDir': ('', '--imagedir', True, 'An optional command that when specified will copy all files and directories under the imagedir to the translation eggs .egg-info/locale/LOCALENAME/images directory. The images resource directory will be registed with the eggs "resources.ini" file.'),
        'HtmlDir': ('', '--htmldir', True, 'An optional command that when specified will copy all files and directories under the htmldir to the translation eggs .egg-info/locale/LOCALENAME/html directory. The html resource directory will be registed with the eggs "resources.ini" file.'),
        'DistEgg': ('', '--dist', False, 'An optional command that when specified will build and package a localization egg for distribution. The translation egg name will contain the project, locale, version, and python version used to build the egg. For example, "Chandler.fr-1.0-py2.5.egg"'),
        }

        if MSGFMT_INSTALLED:
            self.CONFIGITEMS['UseMsgFmtBinary'] = ('', '--msgfmt', False, 'An optional command that when specified will use the msgfmt binary that ships with GNU gettext instead of the default Python msgfmt.py program. The msgfmt binary is more robust and includes error checking capabilities.')

        super(TranslationEggTool, self).getOpts()

        self.DESC = ""

        if not self.OPTIONS.Locale:
            self.raiseError("A Locale (-l) must be specified.")

        self.validateLocale()
        self.LOCALE = self.OPTIONS.Locale

        if self.OPTIONS.Directory:
            self.OUTPUTDIR = self.findPath(self.OPTIONS.Directory)

            if not self.OUTPUTDIR:
                self.raiseError("The output directory specified '%s' is invalid." \
                               % self.OPTIONS.Directory)

        if self.OPTIONS.DistEgg:
            self.DISTEGG = True

        if MSGFMT_INSTALLED and self.OPTIONS.UseMsgFmtBinary:
            self.USE_MSGFMT_BINARY = True

        if self.OPTIONS.ImageDir:
            self.IMGDIR = self.findPath(self.OPTIONS.ImageDir)

            if not self.IMGDIR:
                self.raiseError("The image directory specified '%s' is invalid." \
                               % self.OPTIONS.ImageDir)

        if self.OPTIONS.HtmlDir:
            self.HTMLDIR = self.findPath(self.OPTIONS.HtmlDir)

            if not self.HTMLDIR:
                self.raiseError("The html directory specified '%s' is invalid." \
                               % self.OPTIONS.HtmlDir)

        if  self.OPTIONS.PoFile:
            if not self.OPTIONS.PoFile.endswith(".po"):
                self.raiseError("'%s' is not a valid po file it does not end with a '.po' extension." \
                               %self.OPTIONS.PoFile)

            self.POFILEPATH = self.findPath(self.OPTIONS.PoFile)

            if not self.POFILEPATH:
                self.raiseError("The po file path specified '%s' is invalid." \
                               % self.OPTIONS.PoFile)


        if self.OPTIONS.Project:
            if self.OPTIONS.Chandler:
                self.raiseError("Invalid arguments passed.")

            if not self.POFILEPATH:
                self.raiseError("A a gettext po file (-f) must be specified " \
                                "for project '%s'." %
                                self.OPTIONS.Project)

            #XXX could perform basic validation i.e. no spaces etc.
            self.PROJECTNAME = self.OPTIONS.Project
            self.PROJECTNAMES = [self.PROJECTNAME]

        elif self.OPTIONS.Chandler:
            if self.OPTIONS.Project:
                self.raiseError("Invalid arguments passed.")

            if not self.POFILEPATH:
                self.POFILEPATH = self.findFile("Chandler-%s.po" % self.OPTIONS.Locale)

                if not self.POFILEPATH:
                    self.raiseError("Could not locate Chandler-%s.po in current " \
                                    "working directory or CHANDLERHOME" % self.OPTIONS.Locale)

            self.PROJECTNAME = "Chandler"
            self.PROJECTNAMES = [self.PROJECTNAME]


        else:
            self.raiseError("Chandler (-c) or " \
                            "a Project (-p) must be specified\nin order " \
                            "to build a translation egg.")


    def validateLocale(self):
        size = len(self.OPTIONS.Locale)

        if size == 2:
            return

        if size == 5:
            if self.OPTIONS.Locale[2] == "_":
                return

        self.raiseError("'%s' is not a valid Locale format" % self.OPTIONS.Locale)


    def raiseError(self, txt):
        self.removePluginDir()

        buf = ["\n\n           EGG CREATION FAILED"]
        buf.append("===========================================================\n")
        buf.append(txt)
        buf.append("\n===========================================================\n\n")

        super(TranslationEggTool, self).raiseError("\n".join(buf), banner=False)

    def removePluginDir(self):
        try:
            if self.CWD and not os.getcwd() == self.CWD:
                os.chdir(self.CWD)

            if not self.PLUGINDIR_EXISTS and \
                    os.access(self.PLUGINDIR, os.F_OK):
                remove_tree(self.PLUGINDIR)
        except:
            pass


if __name__ == "__main__":
    TranslationEggTool()

