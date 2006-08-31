#! /usr/bin/env python
# -*- coding: utf-8 -*-

from createBase import LocalizationBase
from distutils.dir_util import copy_tree, remove_tree, mkpath
from distutils.file_util import copy_file
import os, sys

class TranslationEggTool(LocalizationBase):
    PROJECTNAME = None
    PROJECTNAMES = None
    LOCALE = None
    OUTPUTDIR = None
    PLUGINDIR = None
    PLUGINNAME = None
    EGGINFODIR = None
    CWD = None
    POFILE = None
    POFILEPATH = None
    IMGDIR = None
    HTMLDIR = None
    LOCALEDIR = None


    def __init__(self):
        super(TranslationEggTool, self).__init__()

        if sys.platform == 'cygwin':
            self.raiseError("Cygwin is not supported due to filesystem  pathing issues." \
                            "Please use the Windows command prompt instead.")

        self.getOpts()

        self.PLUGINNAME = "%s.%s" % (self.PROJECTNAME, self.LOCALE)
        self.POFILE = os.path.split(self.POFILEPATH)[-1]

        if self.OUTPUTDIR:
             self.PLUGINDIR = os.path.join(self.OUTPUTDIR, self.PLUGINNAME)
        else:
            self.PLUGINDIR = self.PLUGINNAME

        try:
            mkpath(self.PLUGINDIR)

            self.CWD = os.getcwd()
            os.chdir(self.PLUGINDIR)

            self.writeReadMeFile()
            self.writeSetupFile()
            self.putEggInDevelopMode()

            self.LOCALEDIR = os.path.join(self.EGGINFODIR, "locale", self.LOCALE)

            self.writeResourceFile()
            self.createMoFile()

            if self.IMGDIR:
                self.copyImages()

            if self.HTMLDIR:
                self.copyHtml()

            os.chdir(self.CWD)

            if self.OPTIONS.Debug:
                self.debug()

            print "\n\n================================================="
            print "   Translation egg '%s'" % (self.PLUGINNAME)
            print "   created and installed in develop mode"
            if self.OUTPUTDIR:
                print "   to directory '%s'" % self.OUTPUTDIR
            print "=================================================\n\n"

        except Exception, e:
            self.raiseError(str(e))


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

    def createMoFile(self):
        try:
            mkpath(self.LOCALEDIR)
            copy_file(self.POFILEPATH, self.LOCALEDIR)
            cwd = os.getcwd()
            os.chdir(self.LOCALEDIR)
            msgfmt = os.path.join(self.CHANDLERHOME, "tools", "msgfmt.py")
            exp = "%s %s %s" % (self.PYTHON,  msgfmt, self.POFILE)
            os.system(exp)
            os.chdir(cwd)

        except Exception, e:
             self.raiseError("Unable to create mo file from %s': %s." % (self.POFILEPATH, e))

    def putEggInDevelopMode(self):
        exp = "%s setup.py develop" % self.PYTHON
        os.system(exp)

        pluginDir = os.listdir(os.getcwd())
        for item in pluginDir:
            if item.endswith(".egg-info"):
                self.EGGINFODIR = item
                break

        if not self.EGGINFODIR:
            self.raiseError("Unable to locate the %s project .egg-info directory." \
                            % (self.PLUGINNAME))

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
        'Chandler': ('-c', '--chandler',  False, 'Creates a translation egg for the Chandler Project. The egg will be named "Chandler.LOCALENAME" for example "Chandler.fr". If no gettext .po file is specified via the -f command then the current working directory and the CHANDLERHOME are scanned for a gettext po file named "Chandler.po".'),
        'ChandlerExamples': ('-e', '--examples',  False, 'Creates a translation egg for the Chandler Example Projects. The egg will be named "Chandler-ExamplesPlugin.LOCALENAME" for example "Chandler-ExamplesPlugin.fr". If no gettext .po file is specified via the -f command then the current working directory and the CHANDLERHOME are scanned for a gettext po file named "ChandlerExamples.po".'),
        'Project': ('-p', '--project',  True, 'Creates a translation egg for a given Project. The egg will be in the format  "PROJECTNAME.LOCALENAME". Passing a project name of "Test-Plugin" and the French locale will create a translation egg for the "Test-Plugin" project named "Test-Plugin.fr". A relative or full filesystem path to a .po gettext localization file via the -f command is required. A locale specified via the -l command is also required.'),

        'PoFile': ('-f', '--file',  True, 'A relative or full filesystem path to the .po translation file for the egg project. The po file will be copied to the egg and a .mo binary file generated. The .mo file will be registered with the eggs "resources.ini".'),
        'Locale': ('-l', '--locale', True, 'A valid locale name such as "fr", "fr_CA", "en", "en_US". The argument is required and must be specified in order for a translation egg to be generated.'),
        'Directory': ('-d', '--directory', True, 'An optional output directory where the translation egg will be written. The default is the current working directory.'),
        'ImageDir': ('', '--imagedir', True, 'An optional command that when specified will copy all files and directories under the imagedir to the translation eggs .egg-info/locale/LOCALENAME/images directory. The images resource directory will be registed with the eggs "resources.ini" file.'),
        'HtmlDir': ('', '--htmldir', True, 'An optional command that when specified will copy all files and directories under the htmldir to the translation eggs .egg-info/locale/LOCALENAME/html directory. The html resource directory will be registed with the eggs "resources.ini" file.'),
        }

        super(TranslationEggTool, self).getOpts()

        if not self.OPTIONS.Locale:
            self.raiseError("A Locale (-l) must be specified.")

        self.validateLocale()
        self.LOCALE = self.OPTIONS.Locale

        if self.OPTIONS.Directory:
           self.OUTPUTDIR = self.findPath(self.OPTIONS.Directory)

           if not self.OUTPUTDIR:
               self.raiseError("The output directory specified '%s' is invalid." \
                               % self.OPTIONS.Directory)

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
            if self.OPTIONS.ChandlerExamples or\
               self.OPTIONS.Chandler:
                self.raiseError("Invalid arguments passed.")

            if not self.POFILEPATH:
                self.raiseError("A a gettext po file (-f) must be specified " \
                                "for project '%s'." %
                                self.OPTIONS.Project)

            #XXX could perform basic validation i.e. no spaces etc.
            self.PROJECTNAME = self.OPTIONS.Project
            self.PROJECTNAMES = [self.PROJECTNAME]

        elif self.OPTIONS.Chandler:
            if self.OPTIONS.ChandlerExamples or\
               self.OPTIONS.Project:
                self.raiseError("Invalid arguments passed.")

            if not self.POFILEPATH:
                self.POFILEPATH = self.findFile("Chandler.po")

                if not self.POFILEPATH:
                    self.raiseError("Could not locate Chandler.po in current " \
                                    "working directory or CHANDLERHOME")

            self.PROJECTNAME = "Chandler"
            self.PROJECTNAMES = [self.PROJECTNAME]


        elif self.OPTIONS.ChandlerExamples:
            if self.OPTIONS.Chandler or\
               self.OPTIONS.Project:
                self.raiseError("Invalid arguments passed.")

            if not self.POFILEPATH:
                self.POFILEPATH = self.findFile("ChandlerExamples.po")

                if not self.POFILEPATH:
                    self.raiseError("Could not locate ChandlerExamples.po in current " \
                                    "working directory or CHANDLERHOME")

            self.PROJECTNAME = "Chandler-ExamplesPlugin"
            self.PROJECTNAMES = self.CHANDLER_EXAMPLES

        else:
             self.raiseError("Chandler (-c), Chandler Examples (-e), or " \
                             "a Project (-p) must\nbe specified in order " \
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
        try:
            if self.CWD and not os.getcwd() == self.CWD:
                 os.chdir(self.CWD)

            if os.access(self.PLUGINDIR, os.F_OK):
                remove_tree(self.PLUGINDIR)
        except:
             pass

        super(TranslationEggTool, self).raiseError(txt)


if __name__ == "__main__":
    TranslationEggTool()

