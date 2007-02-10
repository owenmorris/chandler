#!/usr/bin/env python
#   Copyright (c) 2006,2007 Open Source Applications Foundation
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

# Original work on hardhat code was done by various OSAF'rs before me:
#     Andi, Morgen, Mark, Heikki

import os, sys
import subprocess
import glob
import fnmatch
import shutil
import fileinput
import errno


def log(msg, logfile=None, error=False):
    if logfile:
        logfile.write('%s\n' % msg)
    else:
        if error:
            sys.stderr.write('%s\n' % msg)
        else:
            sys.stdout.write('%s\n' % msg)


def runCommand(cmd, env=None):
    print 'Calling:', cmd

    p = subprocess.Popen(cmd, env=env, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in p.stdout.readlines():
        print line[:-1]

    p.wait()

    return p.returncode

def loadModuleFromFile(modulePath, moduleName):
    if os.access(modulePath, os.R_OK):
        moduleFile = open(modulePath)

        # Here's a cool bug I had to workaround:  if module_name has a "." in
        # it, bad things happen down the road (exceptions get created within
        # invalid package); example:  if module_name is 'wxWindows-2.4' then
        # hardhatlib throws an exception and it gets created as 
        # wxWindows-2.hardhatlib.HardHatError.  The fix is to replace "." with
        # "_"
        moduleName = moduleName.replace(".", "_")

        import imp

        module = imp.new_module(moduleName)

        sys.modules[moduleName] = module

        exec moduleFile in module.__dict__

        return module
    else:
        print 'Unable to load module - %s not found' % modulePath

def versionInformation(chandlerDirectory, platformName, versionTag=None):
    major   = ''
    minor   = ''
    release = ''
    version = ''

    versionFilename = os.path.join(chandlerDirectory, 'version.py')

    versionFile = open(versionFilename, 'a+')
    versionFile.write('\nplatform = "%s"\n' % platformName)
    versionFile.close()

        # when building a milestone, checkpoint or release the version info
        # is set in version.py and passed to the distribute program

    if versionTag:
        version = versionTag
    else:
        vmodule = loadModuleFromFile(versionFilename, "vmodule")
        version = vmodule.version

    s = version.split('.')

    if len(s) == 2:
        major = s[0]
        s     = s[1].split('-')

        if len(s) == 2:
            minor   = s[0]
            release = s[1]
        else:
            minor = s[0]
    else:
        if len(s) == 3:
            major   = s[0]
            minor   = s[1]
            release = s[2]
        else:
            major = version

    return major, minor, release, version

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Manifest processing functions

# A manifest file describes which files to copy and where they should go in
# order to create a binary distribution.  Comments are denoted by #; empty
# lines are skipped.  There are five "variables" that you set in order to
# control what's going on:  src, dest, recursive, exclude and glob.  The file
# is processed sequentially; variables maintain their values until reassigned.
# The "src" variable should be set to a path relative to buildenv['root'],
# and "dest" should be set to a path relative to buildenv['distdir']; either
# can be set to an empty string (e.g. "dest=").  When a non-assignment line
# is reached (meaning it doesn't have an "=" in it), that line is assumed
# to represent a path relative to "src".  If a file exists there, that file
# is copied to the "dest" directory; if instead a directory exists there, 
# then the patterns specified in the most recent "glob" line are used to
# look for matching files to copy.  Then if "recursive" is set to "yes",
# subdirectories are recursively copied (but only the files matching the
# current pattern). If any file or directory matches any pattern in the 
# "excludes" parameter/list, it is skipped.

def handleManifest(buildDir, outputDir, distribDir, manifestFile, platformID):
    result = True

    if os.path.isfile(manifestFile):
        params = {}
        params["src"]       = None
        params["dest"]      = None
        params["link"]      = None
        params["recursive"] = True
        params["glob"]      = "*"
        params["exclude"]   = "\.svn"

        srcdir  = buildDir
        destdir = outputDir
        linkdir = None

        filedata = fileinput.input(manifestFile)

        try:
            for line in filedata:
                line = line.strip()
                if len(line) == 0:
                    continue
                if line[0:1] == "#":
                    continue

                #line = expandVars(line)

                if line.find('=') != -1:
                    (name,value) = line.split("=")
                    params[name] = value
                    if name == 'src':
                        srcdir = os.path.join(buildDir, value)
                        print 'src=%s' % srcdir
                        #log(buildenv, HARDHAT_MESSAGE, "HardHat", "src=" + srcdir)
                    if name == 'dest':
                        destdir = os.path.join(distribDir, value)
                        print 'dest=%s' % destdir
                        #log(buildenv, HARDHAT_MESSAGE, "HardHat", "dest=" + destdir)
                    if name == 'link':
                        linkdir = value
                        print 'link=%s' % linkdir
                        #log(buildenv, HARDHAT_MESSAGE, "HardHat", "link=" + linkdir)
                    if name == 'glob':
                        params['glob'] = value.split(',')
                        print 'pattern=%s' % value
                        #log(buildenv, HARDHAT_MESSAGE, "HardHat", "pattern=" + value)
                    if name == 'recursive':
                        if value == 'yes':
                            params['recursive'] = True
                        else:
                            params['recursive'] = False
                        print 'recursive=%s' % value
                        #log(buildenv, HARDHAT_MESSAGE, "HardHat", "recursive=" + value)
                    if name == 'exclude':
                        params['exclude'] = value.split(',')
                        print 'exclude=%s' % value
                        #log(buildenv, HARDHAT_MESSAGE, "HardHat", "exclude=" + value)
                    if name == 'egg':
                        print 'Copying egg related files from %s to %s' % (os.path.join(buildDir, value), destdir)
                        #log(buildenv, HARDHAT_MESSAGE, "HardHat", 'Copying egg related files from %s to %s' % (os.path.join(buildenv['root'], value), destdir))
                        copyEggs(os.path.join(buildDir, value), destdir, params['glob'], params['exclude'])
                else:
                    if linkdir is not None:
                        if platformID <> 'win':
                            srcpath  = os.path.abspath(os.path.join(destdir, linkdir, line))
                            linkpath = os.path.join(linkdir, line)

                            if os.path.isdir(srcpath):
                                print 'linking %s to %s in %s' % (linkpath, line, destdir)
                                #log(buildenv, HARDHAT_MESSAGE, "HardHat", "linking %s to %s in %s" % (linkpath, line, destdir))

                                mkdirs(destdir)
                                os.chdir(destdir)
                                os.symlink(linkpath, line)
                            else:
                                print 'Linking only allowed for directories'
                                #log(buildenv, hhMsg, "HardHat", "Linking only allowed for directories")
                        else:
                            print 'Linking only allowed for POSIX systems'
                            #log(buildenv, hhMsg, "HardHat", "Linking only allowed for POSIX systems")

                        linkdir = None
                    else:
                        abspath = os.path.join(srcdir, line)

                        if os.path.isdir(abspath):
                            print abspath
                            #log(buildenv, HARDHAT_MESSAGE, "HardHat", abspath)
                            copyto = os.path.join(distribDir, params['dest'], line)
                            copyTree(abspath, copyto, params['recursive'], params['glob'], params['exclude'])
                        else:
                            if os.path.exists(abspath):
                                print abspath
                                #log(buildenv, HARDHAT_MESSAGE, "HardHat", abspath)
                                copyto = os.path.join(distribDir, params["dest"], line)
                                createpath = os.path.dirname(copyto)
                                mkdirs(createpath)
                                if os.path.islink(abspath):
                                    linkto = os.readlink(abspath)
                                    os.symlink(linkto, copyto)
                                else:
                                    shutil.copy(abspath, copyto)
                            else:
                                print 'File missing [%s]' % abspath
                                #log(buildenv, hhMsg, "HardHat", "File missing: " + abspath)
                                result = False
                                break
        finally:
            filedata.close()
    else:
        print 'Unable to locate manifest file [%s]' % manifestFile

    return result

def copyTree(srcdir, destdir, recursive, patterns, excludes):
    """
    This function implements a directory-tree copy from one place (srcdir)
    to another (destdir), whether it should be recursive, what file patterns
    to copy (may be a list), and what file patterns to exclude (may be a list)
    """
    os.chdir(srcdir)
    # iterate over the file patterns to be copied
    for pattern in patterns:
        # matches contains a list of files matching the current pattern
        matches = glob.glob(pattern)
        excludesMatch = []
        # prepare a list of files to be excluded
        for filePat in excludes:
            # add to the excludes list all files in the match list which match the current exclude pattern
            excludesMatch += fnmatch.filter(matches, filePat)
            # (debug) display current excludes list
            # print "%s matches %s " % (excludesMatch, filePat)

        # (debug) display current excludes list
        # print "excluding %s for %s " % (excludesMatch, srcdir)

        # iterate over the match list for each file
        for match in matches:
            # if the current match is a file that is NOT in the excludes list, then try to copy
            if os.path.isfile(match) and not match in excludesMatch:
                try:
                    if not os.path.exists(destdir):
                        mkdirs(destdir)
                    if os.path.islink(match):
                        linkto = os.readlink(match)
                        os.symlink(linkto, os.path.join(destdir,match))
                    else:
                        shutil.copy(match, destdir)
                except (IOError, os.error), why:
                    print "Can't copy %s to %s: %s" % (match, destdir, str(why))
    if recursive:
        for name in os.listdir(srcdir):
            full_name = os.path.join(srcdir, name)
            # we are only checking one pattern here; 
            # directory excludes so far only being for one pattern - .svn
            # if we need to add more, this will have to change to match method of file excludes above
            if os.path.isdir(full_name) and not name in excludes:
                if os.path.islink(full_name):
                    if not os.path.exists(destdir):
                        mkdirs(destdir)
                    os.symlink(os.readlink(full_name), os.path.join(destdir, name))
                else:
                    copyTree(full_name, os.path.join(destdir, name), True, patterns, excludes)

def copyEggs(srcdir, destdir, patterns, excludes):
    os.chdir(srcdir)
    # iterate over the file patterns to be copied
    for pattern in patterns:
        # matches contains a list of files matching the current pattern
        matches = glob.glob(pattern)
        excludesMatch = []
        # prepare a list of files to be excluded
        for filePat in excludes:
            # add to the excludes list all files in the match list which match the current exclude pattern
            excludesMatch += fnmatch.filter(matches, filePat)
            # (debug) display current excludes list
            # print "%s matches %s " % (excludesMatch, filePat)

        # (debug) display current excludes list
        # print "excluding %s for %s " % (excludesMatch, srcdir)

        # iterate over the match list for each file
        for match in matches:
            # if the current match is a file that is NOT in the excludes list, then try to copy
            if not match in excludesMatch:
                if os.path.isdir(match):
                    if os.path.islink(match):
                        if not os.path.exists(destdir):
                            mkdirs(destdir)
                        os.symlink(os.readlink(match), os.path.join(destdir, match))
                    else:
                        copyTree(os.path.join(srcdir, match), os.path.join(destdir, match), True, '*', excludes)
                        os.chdir(srcdir)

                elif os.path.isfile(match):
                    try:
                        if not os.path.exists(destdir):
                            mkdirs(destdir)
                        if os.path.islink(match):
                            linkto = os.readlink(match)
                            os.symlink(linkto, os.path.join(destdir,match))
                        else:
                            shutil.copy(match, destdir)
                    except (IOError, os.error), why:
                        print "Can't copy %s to %s: %s" % (match, destdir, str(why))

def mkdirs(directory, mode=0777):
    try:
        os.makedirs(directory, mode)
    except OSError, err:
        # Reraise the error unless it's about an already existing directory
        if err.errno != errno.EEXIST or not os.path.isdir(directory):
            raise

def rmdirs(directory):
    if os.path.islink(directory):
        os.remove(directory)
    else:
        for filename in os.listdir(directory):
            fullname = os.path.join(directory, filename)

            # on Windows, if we don't have write permission we can't remove
            # the file/directory either, so turn that on
            if os.name == 'nt':
                if not os.access(fullname, os.W_OK):
                    os.chmod(fullname, 0600)

            if os.path.isdir(fullname):
                rmdirs(fullname)
            else:
                os.remove(fullname)

        os.rmdir(directory)

