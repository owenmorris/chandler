
#   Copyright (c) 2003-2007 Open Source Applications Foundation
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


"""
Notes:
Start() is responsible for capturing all pertinent output to the open file
object, log.  True is returned if a new build was created, False is returned
if no code has changed, and an exception is raised if there are problems.
"""

import os, sys, re, glob, shutil, time
import urllib2
import traceback
import hardhatutil, hardhatlib

path         = os.environ.get('PATH', os.environ.get('path'))
whereAmI     = os.path.dirname(os.path.abspath(hardhatlib.__file__))
svnProgram   = hardhatutil.findInPath(path, "svn")
tarProgram   = hardhatutil.findInPath(path, "tar")
wgetProgram  = hardhatutil.findInPath(path, "wget")
logPath      = 'hardhat.log'
separator    = "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n"

treeName     = "Cosmo"
sleepMinutes = 30

reposRoot    = 'http://svn.osafoundation.org/server'

def Start(hardhatScript, workingDir, buildVersion, clobber, log, skipTests=False, upload=False, branchID=None, revID=None):

      # make sure workingDir is absolute
    workingDir = os.path.abspath(workingDir)
    outputDir  = os.path.join(workingDir, 'output')
    scriptDir  = os.path.join(whereAmI, 'buildscripts')

    if os.path.exists(outputDir):
        hardhatutil.rmdirRecursive(outputDir)

    os.chdir(workingDir)

    windmillDir = os.path.join(workingDir, 'windmill')

    buildVersionEscaped = "\'" + buildVersion + "\'"
    buildVersionEscaped = buildVersionEscaped.replace(" ", "|")

    ret = runWindmill(scriptDir, workingDir, windmillDir, outputDir, log)

    print ret + '-nochanges'

    return (ret + '-nochanges', '0000')

def fetchLatest(workingDir, outputDir, log):
    log.write("[tbox] Downloading latest continuous build\n")

    url = 'http://builds.osafoundation.org/cosmo/continuous/cosmo-full-linux'

    indexfile = fetch('%s/latest.html' % url)
    buildid   = None
    tarball   = None

    # <a href="20070703215444">20070703215444</a>
    for line in indexfile.split('\n'):
        if line.startswith('<a href='):
            buildid = line.split('"')[1]
            break

    if buildid is not None:
        indexfile = fetch('%s/%s/index.html' % (url, buildid))

        # <p>Debug: <a href="osaf-server-bundle-0.7.0-SNAPSHOT.tar.gz">osaf-server-bundle-0.7.0-SNAPSHOT.tar.gz</a>
        for line in indexfile.split('\n'):
            if '<a href="osaf-server-bundle' in line:
                tarball = line.split('"')[1]
                break

    if tarball is not None:
        if os.path.exists(outputDir):
            log.write('***Output directory could not be cleared [%s]\n' % outputDir)
            return None

        os.mkdir(outputDir)
        os.chdir(outputDir)

        try:
            outputList = hardhatutil.executeCommandReturnOutput([wgetProgram, '-q', '%s/%s/%s' % (url, buildid, tarball)])

            hardhatutil.dumpOutputList(outputList, log)

        except hardhatutil.ExternalCommandErrorWithOutputList, e:
            print "tarball fetch error"
            log.write("\n***Error retrieving tarball***\n")
            log.write(separator)
            log.write("Build log:" + "\n")
            hardhatutil.dumpOutputList(e.outputList, log)
            if e.exitCode == 0:
                err = ''
            else:
                err = '***Error '
            log.write("%sexit code=%s\n" % (err, e.exitCode))
            return None

        except Exception, e:
            print "tarball fetch error"
            log.write("\n***Error retrieving tarball***\n")
            log.write(separator)        
            log.write("No build log!\n")
            log.write(separator)
            return None

        try:
            outputList = hardhatutil.executeCommandReturnOutput([tarProgram, '-xzf', tarball])

            hardhatutil.dumpOutputList(outputList, log)

        except hardhatutil.ExternalCommandErrorWithOutputList, e:
            print "tarball extraction error"
            log.write("\n***Error exracting tarball***\n")
            log.write(separator)
            log.write("Build log:" + "\n")
            hardhatutil.dumpOutputList(e.outputList, log)
            if e.exitCode == 0:
                err = ''
            else:
                err = '***Error '
            log.write("%sexit code=%s\n" % (err, e.exitCode))
            return None

        except Exception, e:
            print "tarball extraction error"
            log.write("\n***Error extracting tarball***\n")
            log.write(separator)        
            log.write("No build log!\n")
            log.write(separator)
            return None

    return tarball

class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, headers):
        result = urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)
        result.status = code
        return result

def fetch(url):
    result  = None
    request = urllib2.Request(url)

    opener = urllib2.build_opener(DefaultErrorHandler())

    try:
        f = opener.open(request)

        try:
            if f.status != 200:
                print 'fetch returned status', f.status
        except AttributeError:
            pass

        result = f.read()
    except:
        dumpException('error during fetch for [%s]' % url)

    return result

def runWindmill(scriptDir, workingDir, windmillDir, snarfDir, log):
    result    = 'failed'
    tarball   = fetchLatest(workingDir, snarfDir, log)
    snarfRoot = os.path.join(snarfDir, tarball[:-7])

    if startCosmo(snarfRoot, log):
        log.write('[tbox] Starting Windmill')
        print 'starting windmill', os.path.join(workingDir, 'run_windmill.sh')

        try:
            try:
                outputList = hardhatutil.executeCommandReturnOutput([os.path.join(scriptDir, 'run_windmill.sh')])

                hardhatutil.dumpOutputList(outputList, log)

                for line in outputList:
                    if line.startswith('#TINDERBOX# Status ='):
                        #TINDERBOX# Status = SUCCESS\n
                        #TINDERBOX# Status = FAILED\n
                        if line.split('=')[1].strip()[:-1] == 'SUCCESS':
                            result = 'success'
                        else:
                            result = 'test_failed'

                        break;

            except hardhatutil.ExternalCommandErrorWithOutputList, e:
                print "windmill error"
                log.write("\n***Error during Windmill run***\n")
                log.write(separator)
                log.write("Build log:" + "\n")
                hardhatutil.dumpOutputList(e.outputList, log)
                if e.exitCode == 0:
                    err = ''
                else:
                    err = '***Error '
                log.write("%sexit code=%s\n" % (err, e.exitCode))

            except Exception, e:
                print "windmill error"
                log.write("\n***Error during Windmill run***\n")
                log.write(separator)
                log.write("No build log!\n")
                log.write(separator)

        finally:
            stopCosmo(snarfRoot, log)

    return result

def startCosmo(snarfRoot, log):
    result = False

    snarfBin = os.path.join(snarfRoot, 'bin')
    snarfLog = os.path.join(snarfRoot, 'logs', 'osafsrv.log')

    log.write('[tbox] starting Cosmo [%s]' % snarfBin)
    print 'starting Cosmo', snarfBin

    os.chdir(snarfBin)

    try:
        outputList = hardhatutil.executeCommandReturnOutput(['./osafsrvctl', 'start'])

        hardhatutil.dumpOutputList(outputList, log)

        print 'Waiting for %s to be created' % snarfLog
        n = 10
        while not os.path.isfile(snarfLog) and n > 0:
            time.sleep(6)
            n -= 1

        if os.path.isfile(snarfLog):
            print 'Tailing log for signs of life'
            start   = time.time()
            logtail = Tail(snarfLog)
            while True:
                line = logtail.nextline()
                if '[Catalina] Server startup in' in line:
                    result = True
                    break
                if time.time() - start > 3600:
                    log.write('[tbox] Cosmo has not started within 5 minutes')
                    break
        else:
            log.write('[tbox] Cosmo log file not found with a minute of starting the script')

    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "cosmo start error"
        log.write("\n***Error starting Cosmo***\n")
        log.write(separator)
        log.write("Build log:" + "\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        if e.exitCode == 0:
            err = ''
        else:
            err = '***Error '
        log.write("%sexit code=%s\n" % (err, e.exitCode))

    except Exception, e:
        print "cosmo start error"
        log.write("\n***Error starting Cosmo***\n")
        log.write(separator)        
        log.write("No build log!\n")
        log.write(separator)

    return result

def stopCosmo(snarfRoot, log):
    snarfBin = os.path.join(snarfRoot, 'bin')

    log.write('[tbox] stopping Cosmo [%s]' % snarfBin)
    print 'stopping Cosmo', snarfBin

    os.chdir(snarfBin)

    try:
        outputList = hardhatutil.executeCommandReturnOutput(['./osafsrvctl', 'stop'])

        hardhatutil.dumpOutputList(outputList, log)

    except hardhatutil.ExternalCommandErrorWithOutputList, e:
        print "cosmo stop error"
        log.write("***Error during build***\n")
        log.write(separator)
        log.write("Build log:" + "\n")
        hardhatutil.dumpOutputList(e.outputList, log)
        if e.exitCode == 0:
            err = ''
        else:
            err = '***Error '
        log.write("%sexit code=%s\n" % (err, e.exitCode))

    except Exception, e:
        print "cosmo start error"
        log.write("***Error during build***\n")
        log.write(separator)
        log.write("No build log!\n")
        log.write(separator)

def determineRevision(outputList):
    """
    Scan output of svn up command and extract the revision #
    """
    revision = ""

    for line in outputList:
        s = line.lower()

          # handle "Update to revision ####." - svn up
        if s.find("updated to revision") != -1:
            revision = s[19:-2]
            break
          # handle "At revision ####." - svn up
        if s.find("at revision") != -1:
            revision = s[12:-2]
            break
          # handler "Checked out revision ####." - svn co
        if s.find("checked out revision") != -1:
            revision = s[21:-2]
            break

    return revision

def NeedsUpdate(outputList):
    for line in outputList:
        if line.lower().startswith('at revision'):
            # used to prevent the message that SVN produces when
            # nothing was updated from tripping the 'A' check below
            continue
        if line.lower().find("ide scripts") != -1:
            # this hack is for skipping some Mac-specific files that
            # under Windows always appear to be needing an update
            continue
        if line.lower().find("xercessamples") != -1:
            # same type of hack as above
            continue
        if line.lower().startswith('restored'):
            # treat a restored file as if it is a modified file
            print "needs update because of", line
            return True

        s = line[:4]  # in subversion, there are 3 possible positions
                      # the update flags are found

        if s.find("U") != -1:
            print "needs update because of", line
            return True
        if s.find("P") != -1:
            print "needs update because of", line
            return True
        if s.find("A") != -1:
            print "needs update because of", line
            return True
        if s.find("G") != -1:
            print "needs update because of", line
            return True
        if s.find("!") != -1:
            print "needs update because of", line
            return True
    return False

def doCopyLog(msg, workingDir, logPath, log):
    log.write(msg + "\n")
    log.write(separator)
    logPath = os.path.join(workingDir, logPath)
    log.write("Contents of " + logPath + ":\n")
    if os.path.exists(logPath):
        CopyLog(logPath, log)
    else:
        log.write(logPath + ' does not exist!\n')
    log.write(separator)

def CopyLog(file, fd):
    input = open(file, "r")
    line = input.readline()
    while line:
        fd.write(line)
        line = input.readline()
    input.close()

def getVersion(fileToRead):
    input = open(fileToRead, "r")
    line = input.readline()
    while line:
        if line == "\n":
            line = input.readline()
            continue
        else:
            m=re.match('VERSION=(.*)', line)
            if not m == 'None' or m == 'NoneType':
                version = m.group(1)
                input.close()
                return version

        line = input.readline()
    input.close()
    return 'No Version'

def dumpException(message):
    t, v, tb = sys.exc_info()

    print '%s %s' % (time.strftime('%H:%M on %A, %d %B'), msg)
    print string.join(traceback.format_exception(t, v, tb), '')

# pulled from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/436477/index_txt
#
# Copyright (C) 2005 by The Trustees of the University of Pennsylvania
# Author: Jon Moore

class Tail(object):
    """
    Module to allow for reading lines from a continuously-growing file (such as
    a system log). Handles log files that get rotated/trucated out from under
    us. Inspired by the Perl File::Tail module.

    Example:

      t = filetail.Tail("log.txt")
      while True:
          line = t.nextline()
          # do something with the line

    or:

      t = filetail.Tail("log.txt")
      for line in t:
          # do something
          pass

    """

    def __init__(self, path, only_new = False,
                 min_sleep = 1,
                 sleep_interval = 1,
                 max_sleep = 60):
        """Initialize a tail monitor.
             path: filename to open
             only_new: By default, the tail monitor will start reading from
               the beginning of the file when first opened. Set only_new to
               True to have it skip to the end when it first opens, so that
               you only get the new additions that arrive after you start
               monitoring. 
             min_sleep: Shortest interval in seconds to sleep when waiting
               for more input to arrive. Defaults to 1.0 second.
             sleep_interval: The tail monitor will dynamically recompute an
               appropriate sleep interval based on a sliding window of data
               arrival rate. You can set sleep_interval here to seed it
               initially if the default of 1.0 second doesn't work for you
               and you don't want to wait for it to converge.
             max_sleep: Maximum interval in seconds to sleep when waiting
               for more input to arrive. Also, if this many seconds have
               elapsed without getting any new data, the tail monitor will
               check to see if the log got truncated (rotated) and will
               quietly reopen itself if this was the case. Defaults to 60.0
               seconds.
        """

        # remember path to file in case I need to reopen
        self.path = os.path.abspath(path)
        self.f = open(self.path,"r")
        self.min_sleep = min_sleep * 1.0
        self.sleep_interval = sleep_interval * 1.0
        self.max_sleep = max_sleep * 1.0
        if only_new:
            # seek to current end of file
            file_len = os.stat(path)[stat.ST_SIZE]
            self.f.seek(file_len)
        self.pos = self.f.tell()        # where am I in the file?
        self.last_read = time.time()    # when did I last get some data?
        self.queue = []                 # queue of lines that are ready
        self.window = []                # sliding window for dynamically
                                        # adjusting the sleep_interval

    def _recompute_rate(self, n, start, stop):
        """Internal function for recomputing the sleep interval. I get
        called with a number of lines that appeared between the start and
        stop times; this will get added to a sliding window, and I will
        recompute the average interarrival rate over the last window.
        """
        self.window.append((n, start, stop))
        purge_idx = -1                  # index of the highest old record
        tot_n = 0                       # total arrivals in the window
        tot_start = stop                # earliest time in the window
        tot_stop = start                # latest time in the window
        for i, record in enumerate(self.window):
            (i_n, i_start, i_stop) = record
            if i_stop < start - self.max_sleep:
                # window size is based on self.max_sleep; this record has
                # fallen out of the window
                purge_idx = i
            else:
                tot_n += i_n
                if i_start < tot_start: tot_start = i_start
                if i_stop > tot_stop: tot_stop = i_stop
        if purge_idx >= 0:
            # clean the old records out of the window (slide the window)
            self.window = self.window[purge_idx+1:]
        if tot_n > 0:
            # recompute; stay within bounds
            self.sleep_interval = (tot_stop - tot_start) / tot_n
            if self.sleep_interval > self.max_sleep:
                self.sleep_interval = self.max_sleep
            if self.sleep_interval < self.min_sleep:
                self.sleep_interval = self.min_sleep

    def _fill_cache(self):
        """Internal method for grabbing as much data out of the file as is
        available and caching it for future calls to nextline(). Returns
        the number of lines just read.
        """
        old_len = len(self.queue)
        line = self.f.readline()
        while line != "":
            self.queue.append(line)
            line = self.f.readline()
        # how many did we just get?
        num_read = len(self.queue) - old_len
        if num_read > 0:
            self.pos = self.f.tell()
            now = time.time()
            self._recompute_rate(num_read, self.last_read, now)
            self.last_read = now
        return num_read

    def _dequeue(self):
        """Internal method; returns the first available line out of the
        cache, if any."""
        if len(self.queue) > 0:
            line = self.queue[0]
            self.queue = self.queue[1:]
            return line
        else:
            return None

    def _reset(self):
        """Internal method; reopen the internal file handle (probably
        because the log file got rotated/truncated)."""
        self.f.close()
        self.f = open(self.path, "r")
        self.pos = self.f.tell()
        self.last_read = time.time()

    def nextline(self):
        """Return the next line from the file. Blocks if there are no lines
        immediately available."""

        # see if we have any lines cached from the last file read
        line = self._dequeue()
        if line:
            return line

        # ok, we are out of cache; let's get some lines from the file
        if self._fill_cache() > 0:
            # got some
            return self._dequeue()

        # hmm, still no input available
        while True:
            time.sleep(self.sleep_interval)
            if self._fill_cache() > 0:
                return self._dequeue()
            now = time.time()
            if (now - self.last_read > self.max_sleep):
                # maybe the log got rotated out from under us?
                if os.stat(self.path)[stat.ST_SIZE] < self.pos:
                    # file got truncated and/or re-created
                    self._reset()
                    if self._fill_cache() > 0:
                        return self._dequeue()

    def close(self):
        """Close the tail monitor, discarding any remaining input."""
        self.f.close()
        self.f = None
        self.queue = []
        self.window = []

    def __iter__(self):
        """Iterator interface, so you can do:

        for line in filetail.Tail('log.txt'):
            # do stuff
            pass
        """
        return self

    def next(self):
        """Kick the iterator interface. Used under the covers to support:

        for line in filetail.Tail('log.txt'):
            # do stuff
            pass
        """
        return self.nextline()

