#!/usr/bin/env python

__author__       = "Mike Taylor <bear@code-bear.com>"
__copyright__    = "Copyright (c) 2006 Open Source Applications Foundation"
__version__      = "1.0"

import sys, os, string, subprocess, smtplib
import ConfigParser, optparse
from xml.dom.minidom import parseString


# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52560/index_txt
def unique(s):
    """
    Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u


class status:
    def __init__(self):
        self._app_path = os.getcwd()
        self._options  = { 'tbox_data':   '.',    # raw .status files
                           'status_data': '.',    # where to store generated data
                           'html_data':   '.',    # where to output generated .html
                           'files':       False,  # include file detail in message
                           'verbose':     False,
                           'debug':       False,
                           'cleanup':     False,  # remove .status files when processed
                           'configfile':  'status.cfg',
                           'section':     'base',
                         }

        self.OSAF = '@osafoundation.org'

        self.IgnoreTBoxes    = []
        self.SVNRepos        = {}
        self.SVNReposModules = {}
        self.SVNEmails       = {}

        self.SMTPServer         = 'smtp.osafoundation.org'
        self.SheriffEmails      = ['bear' + self.OSAF]
        self.fromAddress        = 'builder' + self.OSAF
        self.DefaultEmail       = 'dev' + self.OSAF

        self.SVNRoot            = 'http://svn.osafoundation.org/'
        self.ViewCVSURL         = 'http://viewcvs.osafoundation.org/'
        self.ViewCVSRevisionURL = '%s%s?view=rev&rev=%s'      # (ViewCVSURL, SVNRepos, revision #)
        self.ViewCVSFileURL     = '%s%s%s?rev=%s&view=markup' # (ViewCVSURL, SVNRepos, file, revision #)
        self.TBoxLogURL         = 'http://builds.osafoundation.org/tinderbox/tbox/gunzip.cgi?tree=%s&full-log=%s'
        self.TBoxNoteURL        = 'http://builds.osafoundation.org/tinderbox/tbox/addnote.cgi?tree=%s'

        self.Instructions = """What should you do:

1. Get on IRC if you are not already and let people know you are looking
   at the failure. Keep people up to date with your progress.
2. Post a note to Tinderbox (see link above). Post progress reports too.
3. Look at the log (see link above) to figure out what is wrong. You may
   need to do tests locally if the log isn't helping (please file bugs
   for any issues with the log).
4. If you determine that you are not the reason for the failure, let
   people know on IRC and Tinderbox note. It would still be appreciated
   if you could help fix the problem.
5. If you did cause the issue, you have to make a decision. If you think
   you can fix the issue within an hour, do so. Otherwise, back out the
   change so your breakage does not impact other developers.

Full instructions are at http://wiki.osafoundation.org/twiki/bin/view/Projects/???
"""

        self.loadConfiguration()
        self.loadTBoxConfig()

        self.verbose = self._options['verbose']

        if self._options['debug']:
            print 'Configuration Values:'
            for key in self._options:
                print '\t%s: [%r]' % (key, self._options[key])

    def loadConfiguration(self):
        items = { 'configfile':  ('-c', '--config',     's', self._options['configfile'],  '', ''),
                  'verbose':     ('-v', '--verbose',    'b', self._options['verbose'],     '', ''),
                  'debug':       ('-d', '--debug',      'b', self._options['debug'],       '', ''),
                  'cleanup':     ('-x', '--cleanup',    'b', self._options['cleanup'],     '', ''),
                  'tbox_data':   ('-t', '--tboxdata',   's', self._options['tbox_data'],   '', ''),
                  'status_data': ('-s', '--statusdata', 's', self._options['status_data'], '', ''),
                  'html_data':   ('-o', '--htmldata',   's', self._options['html_data'],   '', ''),
                  'files':       ('-f', '--files',      'b', self._options['files'],       '', ''),
                }

        parser = optparse.OptionParser(usage="usage: %prog [options]", version="%prog " + __version__)

        for key in items:
            (shortCmd, longCmd, optionType, defaultValue, environName, helpText) = items[key]

            if environName and os.environ.has_key(environName):
                defaultValue = os.environ[environName]

            if optionType == 'b':
                parser.add_option(shortCmd, longCmd, dest=key, action='store_true', default=defaultValue, help=helpText)
            else:
                if optionType == 'f':
                    parser.add_option(shortCmd, longCmd, dest=key, type='float', default=defaultValue, help=helpText)
                else:
                    parser.add_option(shortCmd, longCmd, dest=key, default=defaultValue, help=helpText)

        (options, self._args) = parser.parse_args()

        for key in items:
            self._options[key] = options.__dict__[key]

        config = ConfigParser.ConfigParser()

        if os.path.isfile(self._options['configfile']):
            config.read(self._options['configfile'])

            if config.has_section(self._options['section']):
                for (item, value) in config.items(self._options['section']):
                    if self._options.has_key(item) and items.has_key(item):
                        optionType = items[item][2]

                        if optionType == 'b':
                            self._options[item] = (string.lower(value) == 'true')
                        else:
                            if optionType == 'f':
                                self._options[item] = float(value)
                            else:
                                self._options[item] = value
        else:
            print 'Unable to locate the configuration file %s' % self._options['configfile']
            sys.exit(0)

    def loadTBoxConfig(self):
        configfile = os.path.join(self._options['status_data'], 'status_tbox.dat')
        lines       = file(configfile).readlines()

        for line in lines:
            line = line[:-1]

            (buildname, svnrepos, svnmodule) = string.split(line, ',')

            buildname = buildname.strip()
            svnrepos  = svnrepos.strip()
            svnmodule = svnmodule.strip()

            if len(svnrepos) == 0:
                self.IgnoreTBoxes.append(buildname)
            else:
                self.SVNRepos[buildname]        = svnrepos
                self.SVNReposModules[buildname] = svnmodule

        emailfile = os.path.join(self._options['status_data'], 'status_email.dat')
        lines       = file(emailfile).readlines()

        for line in lines:
            line = line[:-1]

            (author, email) = string.split(line, ',')

            author = author.strip()
            email  = email.strip()

            if len(email) != 0:
                self.SVNEmails[author] = email

    def process(self):
        builds = {}

        statusfiles = os.listdir(self._options['tbox_data'])

        if self.verbose:
            print 'Scanning %d files from %s' % (len(statusfiles), self._options['tbox_data'])

        for status in statusfiles:
            (statusFilename, statusExtension) = os.path.splitext(status)

            if statusExtension == '.status':
                statusfile  = os.path.join(self._options['tbox_data'], status)
                lines       = file(statusfile).readlines()

                for line in lines:
                    line = line[:-1]
                      # each line of a .status file has the following format
                      # treename | buildname | status | date | time | svn rev #
                    (treename, buildname, status, date, time, revision) = string.split(line, '|')

                    buildname = buildname.lower()
                    status    = status.lower()

                    if self._options['verbose']:
                        print statusFilename, buildname, status  

                    if not buildname in self.IgnoreTBoxes:
                          # skip events with status 'building' as they don't have revision numbers
                        if status != 'building':
                            if not builds.has_key(buildname):
                                builds[buildname] = []

                            builds[buildname].append((treename, statusFilename, status, date, time, revision))

                if self._options['cleanup']:
                    os.remove(statusfile)

        last_good_build   = {}
        last_failed_build = {}

        for buildname in builds.keys():
            last_good_build[buildname]   = (None, None, None, None, None, None)
            last_failed_build[buildname] = (None, None, None, None, None, None)

          # seed the last_good_build dictionary with the results
          # from any prior runs
        last_good_file = os.path.join(self._options['status_data'], 'last_known_good.dat')

        if os.path.isfile(last_good_file):
            for line in file(last_good_file):
                (buildname, treename, build_id, build_status, build_date, build_time, build_revision) = string.split(line[:-1], '|')

                last_good_build[buildname] = (treename, build_id, build_status, build_date, build_time, build_revision)

        # walk thru the entries for a build and see who needs to be notified
        # This is the algorithm from pje:
        #
        # Each tbox keeps the revision number of its last successful build+test, and notifies
        # authors of revisions greater than that revision when there's a failure.  If the failure
        # is against a version that previously tested OK, it's an intermittent failure and the
        # notice has to go to the build sherriff (and ideally, the author of the failing test,
        # but identifying them is a bit trickier).  Here's the pseudocode:
        #
        # good_revision = 0
        # 
        # while True:
        #     current_rev = svn_update()
        #     try:
        #         build_and_test()
        #     except:
        #         authors = []
        #         for rev in range(good_revision+1, current_rev+1):
        #             authors.append(get_author(rev))
        #         if authors:
        #             send_notice_to(authors)
        #         else:
        #             # this revision previously tested OK, therefore
        #             # it's an intermittent failure
        #             send_notice_to([get_test_author(),build_sheriff()])
        #     else:
        #        good_revision = current_rev

        for buildname in builds.keys():
            if self.verbose:
                print buildname
                print "   ",last_good_build[buildname]

            for (treename, build_id, build_status, build_date, build_time, build_revision) in builds[buildname]:
                if build_status == 'success':
                    last_good_build[buildname]   = (treename, build_id, build_status, build_date, build_time, build_revision)
                    last_failed_build[buildname] = (None, None, None, None, None, None)

                    if self.verbose:
                        print "   --- resetting failed, lgb = ", last_good_build[buildname]
                else:
                    last_failed_build[buildname] = (treename, build_id, build_status, build_date, build_time, build_revision)

            (lgb_treename, lgb_id, lgb_status, lgb_date, lgb_time, lgb_revision)       = last_good_build[buildname]
            (treename, build_id, build_status, build_date, build_time, build_revision) = last_failed_build[buildname]

            if self.verbose:
                print "    Last good build:   ", last_good_build[buildname]
                print "    Last failed build: ", last_failed_build[buildname]

            if build_revision:
                authors = []
                rev_msg = []

                if lgb_revision:
                    cmd = ['svn', 'log', '-v', '--xml', '-r',
                            '%s:%s' % (lgb_revision, build_revision),
                            '%s%s%s' % (self.SVNRoot, self.SVNRepos[buildname], self.SVNReposModules[buildname])
                          ]

                    if self.verbose:
                        print "    running command [%s]" % " ".join(cmd)

                    cmd_output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]

                    if self._options['debug']:
                        print "[[%s]]" % cmd_output

                    try:
                        dom = parseString(cmd_output)

                        for entry in dom.getElementsByTagName('logentry'):
                            revision        = entry.getAttribute('revision')
                            revision_author = entry.getElementsByTagName('author')[0].firstChild.nodeValue
                            revision_date   = entry.getElementsByTagName('date')[0].firstChild.nodeValue
                            revision_msg    = entry.getElementsByTagName('msg')[0].firstChild.nodeValue
                            revision_files  = []
                            msg             = ''

                            authors.append(revision_author)

                            msg += 'Revision %s by %s. For details: ' % (revision, revision_author)
                            msg += self.ViewCVSRevisionURL % (self.ViewCVSURL, self.SVNRepos[buildname], revision)
                            msg += '\n%s-------------------\n' % revision_msg

                            if self._options['files']:
                                paths = entry.getElementsByTagName('path')

                                for node in paths:
                                    for child in node.childNodes:
                                        revision_files.append(child.nodeValue)

                                msg += '\nFiles:\n'

                                for item in revision_files:
                                    msg += '%s  [' % item
                                    msg += self.ViewCVSFileURL % (self.ViewCVSURL, self.SVNRepos[buildname], item, revision)
                                    msg += ']\n'

                            rev_msg.append(msg)

                    finally:
                        dom.unlink()

                rev_msg.reverse()

                hook_list = unique(authors)
                to_list   = []

                for author in hook_list:
                    if author in self.SVNEmails:
                        to_list.append(self.SVNEmails[author])

                if len(to_list) == 0:
                    to_list = [self.DefaultEmail]

                to_list.extend(self.SheriffEmails)

                body =        'From: %s\n'    % self.fromAddress
                body += 'To: %s\n'      % ','.join(to_list)
                body += 'Subject: %s\n' % 'Build failed on %s\n' % buildname
                body += '\n'
                body += 'Tinderbox build has failed on %s.\n' % buildname
                body += 'You are being notified because you are listed as a revision author.\n\n'
                body += 'On Hook:      %s\n\n' % ", ".join(hook_list)
                body += 'You can view the Tinderbox log here: '
                body += self.TBoxLogURL % (treename, branch_id)
                body += '\n\n'
                body += 'To add a Notice to the Tinderbox, visit this link: '
                body += self.TBoxNoteURL % treename
                body += '\n\n'
                body += '\n'.join(rev_msg)
                body += '\n'
                body += self.Instructions
                body += '\n'

                try:
                    server = smtplib.SMTP(self.SMTPServer)
                    server.sendmail(self.fromAddress, to_list, body)
                    server.quit()

                except Exception, e:
                    print "SendMail error", e
            else:
                if self.verbose:
                    print "    Last status was successful"

        f = file(last_good_file, 'w')

        for buildname in last_good_build.keys():
            if last_good_build[buildname][0]:
                f.write('%s|%s\n' % (buildname, "|".join(last_good_build[buildname])))

        f.close()

if __name__ == '__main__':
  o = status()
  o.process()
