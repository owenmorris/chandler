#!/usr/bin/env python

#   Copyright (c) 2004-2006 Open Source Applications Foundation
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
#
# Author(s): Heikki Toivonen (heikki@osafoundation.org)

# 29 April 2005 - modified by bear (bear@osafoundation.org) to use the new paths

import os, glob, sha, re, shutil, sys

debug = False

"""
  Assumed directory layout where to look for files:
 
  external
    staging
      windows
        timestamp(s)
      macosx
        timestamp(s)
      maciosx
        timestamp(s)
      linux
        timestamp(s)
 
  The files should be copied into:
 
  external
    windows
    macosx
    maciosx
    linux
 
  It is assumed that timestamp is of the form yyyymmddhhmmss. It is assumed
  that a timestamp dir that has been completely uploaded to, will have file
  called completed in it. It is further assumed that files in the timestamp
  dir are of the form:
    <packagename>-<debug|release>-<relver>.tar.gz<empty or .md5>
  and that for each release version there is a corresponding debug version,
  and that for each *.tar.gz file there is also a corresponding *.md5 file.
  Platforms are also always expected to be in sync, so only packages that
  are available for all platforms will be available for copy. Files will not
  be overwritten.

  This module will import module called pw, which is expected to have the
  login-password dictionary:

  db = {'somelogin' : 'somepasswordhash'}

  where 'somepasswordhash' is computed as follows:

    import sha
    s = sha.new()
    s.update('somelogin' + 'somepassword')
    hash = s.hexdigest()
    print "'%s': '%s'" % (somelogin, hash)
"""

rootDir = '/home/builder/www/docs/external'
stagingRootDir = rootDir + '/staging'
destRootDir = rootDir

rootUrl = '/external'
stagingRootUrl = rootUrl + '/staging'
destRootUrl = rootUrl

lockFile = destRootDir + '/windows/lock'

haveLock = False

allPlatforms = ('windows', 'macosx', 'linux', 'maciosx')

def availableBinaryTarballsForPlatform(platform):
    """
    This function will go through the staging area for a given platform,
    and return a dict of files available in the latest completed directory.
    Format of return dict: {'file-*-x.y-z.tar.gz' : 'platform:timestamp'}
    """
    ret = {}
    os.chdir(stagingRootDir + '/' + platform)
    archiveDirs = glob.glob('[0-9]*')
    archiveDirs.sort()

    if debug:
        print '<p>platform: %s</p>' % platform
    
    for archive in archiveDirs:
        os.chdir(stagingRootDir + '/' + platform)

        if debug:
            print '<li>', archive
            
        if len(archive) != 14 or not os.path.isdir(archive):
            if debug:
                print 'is not dir'
            continue
        if not os.path.isfile(archive + '/completed'):
            if debug:
                print 'is not completed'
            continue

        os.chdir(stagingRootDir + '/' + platform + '/' + archive)
        
        packages = glob.glob('*.tar.gz')
        packages.sort()

        if debug:
            print 'packages=', len(packages), packages

        platTime = platform + ':' + archive
        lastPackage = ''
        for package in packages:
            package = package.replace('-release-', '-*-')
            package = package.replace('-debug-', '-*-')            
            if package == lastPackage:
                ret[package] = platTime
            lastPackage = package
        
    return ret
    
def passwordMatched(login, password):
    """
    Primitive password matching function.
    """
    if not login or not password:
        return False
    
    import pw

    shaObj = sha.new()
    shaObj.update(login + password)

    try:
        if pw.db[login] == shaObj.hexdigest():
            return True
    except KeyError:
        pass

    return False

def inDest(file):
    """
    Return true if file exists in destination area.
    """
    return os.path.isfile(destRootDir + '/windows/' + file.replace('*','debug'))

def buildFrontPage():
    """
    This will build the front page the user goes to.
    """
    results = {}
    for p in allPlatforms:
        results[p] = availableBinaryTarballsForPlatform(p)

    if debug:
        print '<p>results:</p>', results
        
    available = []
    for k, valWin in results['windows'].items():
        for p in allPlatforms:
            if p == 'windows':
                continue
            if not results[p].has_key(k):
                break
        else:
            # This looks weird, but if we get here it means all platforms
            # have the key.
            if not inDest(k):
                s = [k] 
                for p in allPlatforms:
                    s.append('|')
                    s.append(results[p][k])
                available.append(''.join(s))
    
    print '<title>Copy external/internal tarballs</title></head><body>'
    print '<h1>Copy external/internal tarballs</h1>'

    print '<p>Staging:     [<a href="%s">Windows</a>] [<a href="%s">PPC Mac OS X</a>] [<a href="%s">Linux</a>] [<a href="%s">Intel Mac OS X</a>]</p>' % (stagingRootUrl + '/windows', stagingRootUrl + '/macosx', stagingRootUrl + '/linux', stagingRootUrl + '/maciosx')
    print '<p>Destination: [<a href="%s">Windows</a>] [<a href="%s">PPC Mac OS X</a>] [<a href="%s">Linux</a>] [<a href="%s">Intel Mac OS X</a>]</p>' % (destRootUrl + '/windows', destRootUrl + '/macosx', destRootUrl + '/linux', destRootUrl + '/maciosx')


    if not available:
        print '<p>No tarballs available to copy.</p>'
        return

    print '<form action="%s" method="POST">' % os.path.basename(sys.argv[0])
    print '<select name="packages" multiple="multiple" size="5">'
    for file in available:
        print '<option value="%s">%s</option>' % (file, file)
    print '</select>'
    print '<p>Login: <input name="login" size="20"></p>'
    print '<p>Password: <input name="password" type="password" size="20"></p>'
    print '<input type="submit" value="Copy selected files">'
    print '<input type="reset">'
    print '</form>'

def parseEntry(entry):
    """
    Parse entry in format:
    
    foobar-*-x.y.z-w.tar.gz|windows:12345678901234|macosx:22345678901234|linux:32345678901234|...

    and return the parsed fields in a tuple.
    """
    s = ['^(.+\-\*\-.+\.tar\.gz)']
    for p in allPlatforms:
        s.append('\|%s\:([0-9]{14})' % p)
    s.append('$')
    entryMatch = re.compile(''.join(s)).match(entry)
    if not entryMatch:
        raise Exception, 'bad entry'
    file    = entryMatch.group(1)
    
    times = {}
    i = 2
    for p in allPlatforms:
        times[p] = entryMatch.group(i)
        i += 1

    if file.count('*') != 1:
        raise Exception, 'bad file name'            
    if not re.compile('[a-zA-Z0-9.\-_*]').match(file):
        raise Exception, 'bad file name'            
    relFile   = file.replace('*', 'release')
    relFileMd = relFile + '.md5'
    debFile   = file.replace('*', 'debug')
    debFileMd = debFile + '.md5'
    return (relFile, relFileMd, debFile, debFileMd, times)

def copyWanted(wantedCopyList):
    """
    Try to copy the wanted files from staging area to real downloads area.
    """

    for entry in wantedCopyList:
        (relFile, relFileMd, debFile, debFileMd, times) = parseEntry(entry)


        for platform in allPlatforms:
            srcDir = '%s/%s/%s/' % (stagingRootDir, platform, times[platform])
            dstDir = '%s/%s/' % (destRootDir, platform)

            if debug:
                print srcDir + relFile, dstDir + relFile

            # XXX Any way to get around these race conditions?
            if os.path.exists(dstDir + relFile):
                raise Exception, 'file exists'
            shutil.copy(srcDir + relFile, dstDir + relFile)

            if os.path.exists(dstDir + relFileMd):
                raise Exception, 'file exists'
            try:
                shutil.copy(srcDir + relFileMd, dstDir + relFileMd)
            except IOError:
                pass # .md5 are optional

            if os.path.exists(dstDir + debFile):
                raise Exception, 'file exists'
            shutil.copy(srcDir + debFile, dstDir + debFile)

            if os.path.exists(dstDir + debFileMd):
                raise Exception, 'file exists'
            try:
                shutil.copy(srcDir + debFileMd, dstDir + debFileMd)
            except IOError:
                pass # .md5 are optional

def buildSubmitPage(form):
    """
    This will build the page that is given to the user once they submit on
    the front page.
    """
    if not (form.has_key("login") and form.has_key("password")):
        print '<title>Error</title></head><body>'
        print '<h1>Error</h1>'
        print "Please fill in the login and password fields."
        return
    if not passwordMatched(form.getvalue('login'), form.getvalue('password')):
        print '<title>Error</title></head><body>'
        print '<h1>Error</h1>'
        print "Invalid login."
        return
    if not (form.has_key("packages")):
        print '<title>Error</title></head><body>'
        print '<h1>Error</h1>'
        print "Please select at least one package."
        return

    lock()

    wantedCopyList = form.getlist("packages")

    copyWanted(wantedCopyList)

    print '<title>Done</title></head><body>'
    print '<h1>Done</h1>'

class LockingError(Exception):
    """
    Raised when lock can't be obtained.
    """
    pass

def lock():
    """
    Try to lock the staging area so that only one user at a time can
    do the copy operations. Will raise an exception if lock can't be obtained.
    """
    try:
        os.open(lockFile, os.O_CREAT | os.O_EXCL)
    except OSError, e:
        if debug:
            print e
        raise LockingError, 'can not create lock file'

    global haveLock
    haveLock = True

def unlock():
    """
    Try to unlock if a lock exists. Will raise an exception if lock can't
    be removed. Safe to call even if there is no lock.
    """
    global haveLock
    
    if debug:
        print 'haveLock=', haveLock
        
    if haveLock:
        os.remove(lockFile)

if __name__ == "__main__":
    import cgi

    print 'Content-Type: text/html\n\n'

    print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">'
    print '<html><head>'
    
    try:
        form = cgi.FieldStorage()
        
        if form.has_key('login'):
            buildSubmitPage(form)
        else:
            buildFrontPage()
    except LockingError:
        print '<title>Error</title></head><body>'
        print '<h1>Error</h1>'
        print '<p>Could not acquire lock, please try again later.</p>'
    except Exception, e:
        print '<title>Error</title></head><body>'
        print '<h1>Error</h1>'
        print '<p>Internal error!</p>'
        if debug:
            print '<pre>' + str(e) + '</pre>'

    print '</body></html>'

    try:
        unlock()
    except Exception, e:
        if debug:
            print e
