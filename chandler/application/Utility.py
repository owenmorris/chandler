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
Application utilities.
"""

import os, sys, logging, logging.config, logging.handlers, string
import i18n, schema
import M2Crypto.Rand as Rand, M2Crypto.threading as m2threading
from optparse import OptionParser
from configobj import ConfigObj

from chandlerdb.util.c import UUID, loadUUIDs
from repository.persistence.DBRepository import DBRepository
from repository.persistence.RepositoryError import \
    VersionConflictError, RepositoryPasswordError, RepositoryVersionError, \
    RepositoryRunRecoveryError

import version

# Increment this value whenever the schema changes, and replace the comment
# with your name (and some helpful text). The comment's really there just to
# cause Subversion to warn you of a conflict when you update, in case someone 
# else changes it at the same time you do (that's why it's on the same line).
SCHEMA_VERSION = "408" # jeffrey: Added icalendarExtra

logger = None # initialized in initLogging()

def createProfileDir(profileDir):
    """
    Create the profile directory with the right permissions. 
    
    Will raise exception if the directory cannot be created.
    """
    os.makedirs(profileDir, 0700)

def locateProfileDir():
    """
    Locate the Chandler repository.
    The location is determined either by parameters, or if not specified, by
    the presence of a .chandler directory in the users home directory.
    """

    def _makeRandomProfileDir(pattern):
        chars = string.ascii_letters + string.digits
        name = ''.join([chars[ord(c) % len(chars)] for c in os.urandom(8)])
        profileDir = pattern.replace('*', '%s') %(name)
        createProfileDir(profileDir)
        return profileDir

    releaseMajorMinor = version.release.split('-', 1)[0]

    if os.name == 'nt':
        dataDir = None

        if os.environ.has_key('APPDATA'):
            dataDir = os.environ['APPDATA']
        elif os.environ.has_key('USERPROFILE'):
            dataDir = os.environ['USERPROFILE']
            if os.path.isdir(os.path.join(dataDir, 'Application Data')):
                dataDir = os.path.join(dataDir, 'Application Data')

        if dataDir is None or not os.path.isdir(dataDir):
            if os.environ.has_key('HOMEDRIVE') and \
                os.environ.has_key('HOMEPATH'):
                dataDir = '%s%s' % (os.environ['HOMEDRIVE'],
                                    os.environ['HOMEPATH'])

        if dataDir is None or not os.path.isdir(dataDir):
            dataDir = os.path.expanduser('~')

        profileDir = os.path.join(dataDir,
                                  'Open Source Applications Foundation',
                                  'Chandler', releaseMajorMinor)

    elif sys.platform == 'darwin':
        dataDir = os.path.join(os.path.expanduser('~'),
                               'Library',
                               'Application Support')
        profileDir = os.path.join(dataDir,
                                  'Open Source Applications Foundation',
                                  'Chandler', releaseMajorMinor)

    else:
        dataDir = os.path.expanduser('~')
        profileDir = os.path.join(dataDir, '.chandler', releaseMajorMinor)

    # Deal with the random part
    pattern = '%s%s*.default' % (profileDir, os.sep)
    try:
        import glob
        profileDir = glob.glob(pattern)[0]
    except IndexError:
        try:
            profileDir = _makeRandomProfileDir(pattern)
        except:
            profileDir = None
    except:
        profileDir = None

    return profileDir

def getDesktopDir():
    """
    Return a reasonable guess at the desktop folder.
    
    On Mac, returns '~/Desktop'; on Linux, it'll return '~/Desktop' if it 
    exists, or just '~' if not.
    """
    if os.name == 'nt':
        if os.environ.has_key('USERPROFILE'):
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            if os.path.isdir(desktop):
                return desktop
        return os.path.realpath('.')

    # Linux or Mac.
    homeDir = os.path.expanduser('~')
    desktopDir = os.path.join(homeDir, 'Desktop')
    if (sys.platform == 'darwin' or os.path.isdir(desktopDir)):
        return desktopDir
    return homeDir

def getPlatformID():
    """
    Return an identifier string that represents what platform
    Chandler is being run on.
    """
    import platform

    platformID = 'Unknown'

    if os.name == 'nt':
        platformID = 'win'
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            # platform.processor() returns 'i386' or 'powerpc'
            # but we need to also check platform.machine()
            # which returns 'Power Macintosh' or 'i386'
            # to determine if we are running under Rosetta

            if platform.processor() == 'i386' and platform.machine() == 'i386':
                platformID = 'osx-intel'
            else:
                platformID = 'osx-ppc'
        elif sys.platform == 'cygwin':
            platformID = 'win-cygwin'
        else:
            platformID = 'linux'

    return platformID

def getPlatformName():
    """
    Return a plain text string that represents what platform
    Chandler is being run on.
    """
    platformID   = getPlatformID()
    platformName = platformID

    if platformID == 'linux':
        platformName = 'Linux'
    elif platformID == 'win' or platformID == 'win-cygwin':
        platformName = 'Windows'
    elif platformID == 'osx-intel':
        platformName = 'Mac OS X (intel)'
    elif platformID == 'osx-ppc':
        platformName = 'Mac OS X (ppc)'

    return platformName

def getUserAgent():
    """
    Construct a rfc spec'd UserAgent string from the platform and version information
    """
    platformID = getPlatformID()
    locale     = i18n.getLocale()

    if platformID == 'win' or platformID == 'win-cygwin':
        platform = 'Windows'
        cpu      = 'i386'
    elif platformID == 'osx-intel':
        platform = 'Macintosh'
        cpu      = 'i386'
    elif platformID == 'osx-ppc':
        platform = 'Macintosh'
        cpu      = 'PPC'
    else:
        platform = 'Linux'
        cpu      = 'i386'

    return 'Chandler/%s (%s; U; %s; %s)' % (version.version, platform, cpu, locale)

# short opt, long opt, type flag, default value, env var, help text
COMMAND_LINE_OPTIONS = {
    'parcelPath': ('-p', '--parcelPath', 's', None,  'PARCELPATH', 'Parcel search path'),
    'pluginPath': (''  , '--pluginPath', 's', 'plugins',  None, 'Plugin search path, relative to CHANDLERHOME'),
    'webserver':  ('-W', '--webserver',  'b', False, 'CHANDLERWEBSERVER', 'Activate the built-in webserver'),
    'profileDir': ('-P', '--profileDir', 's', '',  'PROFILEDIR', 'location of the Chandler user profile directory (relative to CHANDLERHOME)'),
    'testScripts':('-t', '--testScripts','b', False, None, 'run all test scripts'),
    'scriptFile': ('-f', '--scriptFile', 's', None,  None, 'script file to execute after startup'),
    'chandlerTests': ('', '--chandlerTests', 's', None, None, 'file:TestClass,file2:TestClass2 to be executed by new framework'),
    'chandlerTestSuite': ('-T', '--chandlerTestSuite', 'b', False, None, 'run the functional test suite'),
    'chandlerTestDebug': ('-D', '--chandlerTestDebug', 's', 0, None, '0=print only failures, 1=print pass and fail, 2=print pass & fail & check repository after each test'),
    'recordedTest': ('', '--recordedTest', 's', None, None, 'run a recorded test from the recorded_scripts directory. Use "all" to run full suite.'),
    'chandlerTestMask': ('-M', '--chandlerTestMask', 's', 3, None, '0=print all, 1=hide reports, 2=also hide actions, 3=also hide test names'),
    'chandlerPerformanceTests': ('', '--chandlerPerformanceTests', 's', None, None, 'file:TestClass,file2:TestClass2 to be executed by performance new framework'),
    'chandlerTestLogfile': ('', '--chandlerTestLogfile', 's', None, None, 'file for chandlerTests output'),
    'continueTestsOnFailure': ('-F','--continueTestsOnFailure', 'b', False, None, 'Do not stop functional test suite on first failure'),
    'catsProfile':('',   '--catsProfile','s', None,  None, 'file for hotshot profile of script execution'),
    'catsPerfLog':('',   '--catsPerfLog','s', None,  None, 'file to output a performance number'),
    'stderr':     ('-e', '--stderr',     'b', False, None, 'Echo error output to log file'),
    'create':     ('-c', '--create',     'b', False, "CREATE", 'Force creation of a new repository'),
    'ask':        ('',   '--ask',        'b', False, None, 'give repository options on startup'),
    'ramdb':      ('-m', '--ramdb',      'b', False, None, ''),
    'restore':    ('-r', '--restore',    's', None,  None, 'repository backup to restore from before repository open'),
    'recover':    ('-R', '--recover',    'b', False, None, 'open repository with recovery'),
    'reload':     ('',   '--reload',     's', None, None, 'reload a dump file, will clear repository first'),
    # --nocatch is deprecated and will be removed soon: use --catch=tests or --catch=never instead
    'nocatch':    ('-n', '--nocatch',    'b', False, 'CHANDLERNOCATCH', ''),
    'catch':      ('',   '--catch',      's', 'normal', 'CHANDLERCATCH', '"normal" leaves outer and test exception handlers in place (the default); "tests" removes the outer one, and "never" removes both.'),
    'wing':       ('-w', '--wing',       'b', False, None, ''),
    'komodo':     ('-k', '--komodo',     'b', False, None, ''),
    'locale':     ('-l', '--locale',     's', None,  None, 'Set the default locale'),
    'encrypt':    ('-S', '--encrypt',    'b', False, None, 'Request prompt for password for repository encryption'),
    'nosplash':   ('-N', '--nosplash',   'b', False, 'CHANDLERNOSPLASH', ''),
    'logging':    ('-L', '--logging',    's', 'logging.conf',  'CHANDLERLOGCONFIG', 'The logging config file'),
    'verbose':    ('-v', '--verbose',    'b', False, None, 'Verbosity option (currently just for run_tests.py)'),
    'quiet':      ('-q', '--quiet',      'b', False, None, 'Quiet option (currently just for run_tests.py)'),
    'offline':    ('', '--offline',    'b', False, 'CHANDLEROFFLINE', 'Takes the Chandler Mail Service Offline'),
    'verify':     ('-V', '--verify-assignments', 'b', False, None, 'Verify attribute assignments against schema'),
    'debugOn':    ('-d', '--debugOn', 's', None,  None, 'Enter PDB upon this exception being raised'),
    'appParcel':  ('-a', '--app-parcel', 's', "osaf.app",  None, 'Parcel that defines the core application'),
    'nonexclusive':  ('', '--nonexclusive', 'b', False, 'CHANDLERNONEXCLUSIVEREPO', 'Enable non-exclusive repository access'),
    'memorylog':  ('', '--memorylog', 's', None, None, 'Specify a buffer size (in MB) for in-memory transaction logs'),
    'logdir':     ('', '--logdir', 's', None, None, 'Specify a directory for transaction logs (relative to the __repository__ directory'),
    'datadir':    ('', '--datadir', 's', None, None, 'Specify a directory for database files (relative to the __repository__ directory'),
    'repodir':    ('', '--repodir', 's', None, None, "Specify a home directory for the __repository__ directory (relative to the profile directory)"),
    'nodeferdelete':   ('', '--nodeferdelete','b', False, None, 'do not defer item deletions in all views by default'),
    'indexer':    ('-i', '--indexer',    's', '90', None, 'Run Lucene indexing in the background every 90s, in the foreground or none'),
    'checkpoints': ('', '--checkpoints', 's', '10', None, 'Checkpoint the repository in the background every 10min, or none'),
    'uuids':      ('-U', '--uuids',      's', None, None, 'use a file containing a bunch of pre-generated UUIDs'),
    'undo':       ('',   '--undo',       's', None, None, 'undo <n> versions or until <check> or <repair> passes'),
    'backup':     ('',   '--backup',     'b', False, None, 'backup repository before start'),
    'backupdir':  ('',   '--backup-dir', 's', None, None, 'backup repository before start into dir'),
    'repair':     ('',   '--repair',     'b', False, None, 'repair repository before start (currently repairs broken indices)'),
    'mvcc':       ('',   '--mvcc',       'b', True, 'MVCC', 'run repository multi version concurrency control'),
    'nomvcc':     ('',   '--nomvcc',     'b', False, 'NOMVCC', 'run repository without multi version concurrency control'),
    'prune':      ('',   '--prune',      's', '10000', None, 'number of items in a view to prune to after each commit'),
    'prefs':      ('',   '--prefs',      's', 'chandler.prefs', None, 'path to prefs file that contains defaults for command line options, relative to profile directory'),
}

def initDefaults(**kwds):
    """
    Return a default command line options object from
    COMMAND_LINE_OPTIONS dict, optional env vars and optional kwd args
    """

    class _options(object): pass
    options = _options()

    for name, (x, x, optionType, defaultValue, environName,
               x) in COMMAND_LINE_OPTIONS.iteritems():
        if environName and environName in os.environ:
            if optionType == 'b':
                defaultValue = True
            else:
                defaultValue = os.environ[environName]
        setattr(options, name, defaultValue)
    options.__dict__.update(kwds)

    return options

def initOptions(**kwds):
    """
    Load and parse the command line options, with overrides in **kwds.
    Returns options
    """
    #XXX i18n parcelPath, profileDir could have non-ascii paths

    # %prog expands to os.path.basename(sys.argv[0])
    usage  = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version="%prog")

    for name, (shortCmd, longCmd, optionType, defaultValue,
               environName, helpText) in COMMAND_LINE_OPTIONS.iteritems():

        if environName and environName in os.environ:
            if optionType == 'b':
                defaultValue = True
            else:
                defaultValue = os.environ[environName]

        if optionType == 'b':
            parser.add_option(shortCmd,
                              longCmd,
                              dest=name,
                              action='store_true',
                              default=defaultValue,
                              help=helpText)
        else:
            parser.add_option(shortCmd,
                              longCmd,
                              dest=name,
                              default=defaultValue,
                              help=helpText)

    if sys.platform == 'darwin':
        # [Bug:2464]
        # On the Mac, double-clicked apps are launched with an extra
        # argument, '-psn_x_y', where x & y are unsigned integers. This
        # is used to rendezvous between the launched app and the Window Server.
        #
        # We remove it from parser's arguments because it conflicts with
        # the -p (parcel path) option, overriding the PARCELPATH environment
        # variable if set.
        args = [arg for arg in sys.argv[1:] if not arg.startswith('-psn_')]
        (options, args) = parser.parse_args(args=args)
    else:
        (options, args) = parser.parse_args()
        
    for (opt,val) in kwds.iteritems():
        setattr(options, opt, val)

    # Convert a few options
    if options.chandlerTestSuite:
        options.scriptFile = "tools/cats/Functional/FunctionalTestSuite.py"
    if options.nocatch:
        options.catch = "tests"

    # Ensure a profile directory
    initProfileDir(options)

    # Load prefs and override default options from prefs
    prefs = loadPrefs(options).get('options')
    if prefs:
        for name, (shortCmd, longCmd, optionType, defaultValue,
                   environName, helpText) in COMMAND_LINE_OPTIONS.iteritems():
            if name in prefs and getattr(options, name) == defaultValue:
                setattr(options, name, prefs[name])

    # Resolve pluginPath relative to chandlerDirectory
    chandlerDirectory = locateChandlerDirectory()
    options.pluginPath = [os.path.join(chandlerDirectory, path)
                          for path in options.pluginPath.split(os.pathsep)]
        
    # Store up the remaining args
    options.args = args

    # --reload implies a few other changes:
    if options.reload:
        options.create = True
        options.restore = None

    return options


def initProfileDir(options):
    """
    Ensure we have the profile directory.
    """
    #XXX: i18n a users home directory can be non-ascii path

    # set flag if the profileDir parameter was passed in (default is '')
    # this is used downstream by application.CheckIfUpgraded()
    options.profileDirWasPassedIn = len(options.profileDir) > 0

    if not options.profileDir:
        profileDir = locateProfileDir()
        if profileDir is None:
            profileDir = locateChandlerDirectory()
        options.profileDir = os.path.expanduser(profileDir)
    elif not os.path.isdir(options.profileDir):
        createProfileDir(options.profileDir)


def loadPrefs(options):
    """
    Load the chandler.prefs file as a ConfigObj, in profileDir by default.
    If prefs file doesn't exist, an ConfigObj is returned.
    """
    return ConfigObj(os.path.join(options.profileDir or '.', options.prefs),
                     encoding='utf-8')


def initI18n(options):
    #Will discover locale set if options.locale is None
    i18n._I18nManager.initialize(options.locale)

def initLogging(options):
    global logger

    if logger is None:
        # Make PROFILEDIR available within the logging config file
        logging.PROFILEDIR = options.profileDir

        logConfFile = options.logging
        if os.path.isfile(logConfFile):
            logging.config.fileConfig(options.logging)
        else:
            # Log config file doesn't exist
            #logging.basicConfig(level=logging.WARNING,
            #    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
            #    filename=os.path.join(options.profileDir, 'chandler.log'),
            #    filemode='a')

            logger = logging.getLogger()

            fileHandler = logging.handlers.TimedRotatingFileHandler(
                os.path.join(options.profileDir, 'chandler.log'),
                when="midnight", backupCount=3
            )
            fileFormatter = logging.Formatter(
                '%(asctime)s %(name)s %(levelname)s: %(message)s'
            )

            fileHandler.setFormatter(fileFormatter)

            logger.addHandler(fileHandler)
            logger.setLevel(logging.INFO)

        logger = logging.getLogger(__name__)

        logger.warn('=== logging initialized, Chandler version %s ===' % version.version)

        import twisted.python.log

        def translateLog(eventDict):
            if eventDict['isError']:
                level = logging.ERROR
            elif eventDict.has_key('debug'):
                level = logging.DEBUG
            else:
                level = logging.WARNING
                
            failure = eventDict.get('failure')
            if failure is not None:
                # For failures, log the type & value, as well as
                # the traceback. Note that a try/except/logger.exception()
                # here would log as application.Utility, not the value of
                # 'system'
                format = "Twisted failure: %s %s\n%s"
                args = failure.type, failure.value, failure.getTraceback()
            else:
                msg = eventDict.get('message', None)
                
                if msg:
                    format = msg[0]
                    args = msg[1:]
                elif eventDict.has_key('format'):
                    format = eventDict['format']
                    args = eventDict
                else:
                    format = "UNFORMATTABLE: %s"
                    args = (eventDict,)
                

            system = eventDict.get('system', '-')
            lineno = eventDict.get('lineno', None)
            exc_info = None
                
            logRecord = logging.LogRecord("twisted", level, system, lineno, format, args, exc_info, None)
            logRecord.created = eventDict['time']
            logger.handle(logRecord)

        # We want startLoggingWithObserver here to override the
        # twisted logger, since that would write to stdio, I think.
        twisted.python.log.startLoggingWithObserver(translateLog, setStdout=0)

def getLoggingLevel():
    return logging.getLogger().getEffectiveLevel()

def setLoggingLevel(level):
    logging.getLogger().setLevel(level)

def locateChandlerDirectory():
    """
    Find the directory that Chandler lives in by looking up the file that
    the application module lives in.
    """
    return os.path.dirname(os.path.dirname(__file__))


def locateRepositoryDirectory(profileDir, options):
    if options.repodir:
        return os.path.join(options.repodir, '__repository__')
    if profileDir:
        path = os.path.join(profileDir, '__repository__')
    else:
        path = '__repository__'
    return path


def initRepository(directory, options, allowSchemaView=False):

    if options.uuids:
        input = file(options.uuids)
        loadUUIDs([UUID(uuid.strip()) for uuid in input if len(uuid) > 1])
        input.close()

    if options.checkpoints == 'none':
        options.checkpoints = None
    else:
        options.checkpoints = int(options.checkpoints) # minutes

    repository = DBRepository(directory)

    kwds = { 'stderr': options.stderr,
             'ramdb': options.ramdb,
             'create': True,
             'recover': options.recover,
             'exclusive': not options.nonexclusive,
             'memorylog': options.memorylog,
             'mvcc': options.mvcc and not options.nomvcc,
             'prune': int(options.prune),
             'logdir': options.logdir,
             'datadir': options.datadir,
             'nodeferdelete': options.nodeferdelete,
             'refcounted': True,
             'checkpoints': options.checkpoints,
             'logged': not not options.logging,
             'verify': options.verify or __debug__ }

    if options.restore:
        kwds['restore'] = options.restore

    while True:
        try:
            if options.encrypt:
                kwds['password'] = options.getPassword
            else:
                kwds.pop('password', None)

            if options.create:
                repository.create(**kwds)
            else:
                repository.open(**kwds)
        except RepositoryPasswordError, e:
            options.encrypt = e.args[0]
            continue
        except RepositoryVersionError:
            repository.close()
            raise
        except RepositoryRunRecoveryError, e:
            if not (options.recover or e.args[0]):
                repository.logger.warning("reopening repository with recovery")
                kwds['recover'] = True
                continue
            raise
        else:
            del kwds
            break

    if options.backupdir:
        dbHome = repository.backup(os.path.join(options.backupdir,
                                                '__repository__'))
        repository.logger.info("Repository was backed up into %s", dbHome)
    elif options.backup:
        dbHome = repository.backup()
        repository.logger.info("Repository was backed up into %s", dbHome)

    view = repository.createView()

    if options.repair:
        schema.initRepository(view)
        if view.check(True):
            view.commit()

    if options.undo:
        if options.undo in ('check', 'repair'):
            repair = options.undo == 'repair'
            while view.itsVersion > 0L:
                schema.initRepository(view)
                if view.check(repair):
                    if repair:
                        view.commit()
                    break

                repository.logger.info('Undoing version %d', view.itsVersion)
                view.closeView()
                repository.undo()
                view.openView()
        else:
            version = repository.store.getVersion()
            nVersions = long(options.undo)
            toVersion = version - nVersions
            if toVersion >= 0L:
                repository.undo(toVersion)

    schema.initRepository(view)

    if options.indexer == 'foreground':
        # do nothing, indexing happens during commit
        pass

    elif options.indexer == 'none':
        # don't run PyLucene indexing in the main view
        view.setBackgroundIndexed(True)
        # don't start an indexer

    else:
        if options.indexer == 'background':  # backwards compat
            options.indexer = 60
        else:
            options.indexer = int(options.indexer) # seconds

        if options.indexer:
            # don't run PyLucene indexing in the main view
            view.setBackgroundIndexed(True)
            # but in the repository's background indexer
            repository.startIndexer(options.indexer)
        else:
            # no interval == foreground
            pass

    if options.debugOn:
        debugOn = view.classLoader.loadClass(options.debugOn)
        view.debugOn(debugOn)

    return view


def stopRepository(view, commit=True):

    if view.repository.isOpen():
        try:
            if commit:
                try:
                    if view.isOpen():
                        view.commit()
                except VersionConflictError, e:
                    logger.exception(e)
        finally:
            view.repository.close()


def verifySchema(view):

    # Fetch the top-level parcel item to check schema version info
    parcelRoot = view.getRoot('parcels')
    version = getattr(parcelRoot, 'version', None)

    if parcelRoot is not None and version != SCHEMA_VERSION:
        logger.error("Schema version of repository (%s) doesn't match application's (%s)", version, SCHEMA_VERSION)
        return False, version, SCHEMA_VERSION

    return True, version, SCHEMA_VERSION


def initParcelEnv(options, chandlerDirectory):
    """
    PARCEL_IMPORT defines the import directory containing parcels
    relative to chandlerDirectory where os separators are replaced
    with "." just as in the syntax of the import statement.
    """
    PARCEL_IMPORT = 'parcels'

    """
    Load the parcels which are contained in the PARCEL_IMPORT directory.
    It's necessary to add the "parcels" directory to sys.path in order
    to import parcels. Making sure we modify the path as early as possible
    in the initialization as possible minimizes the risk of bugs.
    """
    parcelPath = []
    parcelPath.append(os.path.join(chandlerDirectory,
                      PARCEL_IMPORT.replace('.', os.sep)))

    """
    If PARCELPATH env var is set, append those directories to the
    list of places to look for parcels.
    """
    if options.parcelPath:
        for directory in options.parcelPath.split(os.pathsep):
            if os.path.isdir(directory):
                parcelPath.append(directory)
            else:
                logger.warning("'%s' not a directory; skipping" % directory)

    insertionPoint = 1
    for directory in parcelPath:
        #Convert the directory unicode or str path to the OS's filesystem 
        #charset encoding
        if directory not in sys.path:
            sys.path.insert(insertionPoint, directory)
            insertionPoint += 1

    logger.info("Using PARCELPATH %s" % parcelPath)
    return parcelPath


def initPluginEnv(options, path):

    from pkg_resources import working_set, Environment

    # if options is passed in, use prefs to determine what to bypass
    # otherwise all plugins are added to the working_set

    if options is not None:
        prefs = loadPrefs(options)
        pluginPrefs = prefs.get('plugins', None)
    else:
        prefs = None
        pluginPrefs = None
    
    plugin_env = Environment(path)
    eggs = []

    # remove uninstalled plugins from prefs
    if pluginPrefs is not None:
        for project_name in pluginPrefs.keys():
            if project_name not in plugin_env:
                del prefs['plugins'][project_name]
        prefs.write()

    # add active plugins to working set
    for project_name in sorted(plugin_env):
        if pluginPrefs is not None:
            if pluginPrefs.get(project_name) == 'inactive':
                continue
        for egg in plugin_env[project_name]:
            working_set.add(egg)
            eggs.append(egg)
            break

    return plugin_env, eggs


def initParcels(options, view, path, namespaces=None):
    
    # Delayed so as not to trigger early loading of schema.py
    from Parcel import Manager

    Manager.get(view, path=path).loadParcels(namespaces)

    # Record the current schema version into the repository
    parcelRoot = view.getRoot("parcels")
    if getattr(parcelRoot, 'version', None) != SCHEMA_VERSION:
        parcelRoot.version = SCHEMA_VERSION


def initPlugins(options, view, plugin_env, eggs):

    # Delayed so as not to trigger early loading of schema.py
    from Parcel import load_parcel_from_entrypoint
    from pkg_resources import ResolutionError

    # if options is passed-in save which plugins are active in prefs
    if options is not None:
        prefs = loadPrefs(options)
        if 'plugins' not in prefs:
            prefs['plugins'] = {}
    else:
        prefs = None

    for egg in eggs:
        for entrypoint in egg.get_entry_map('chandler.parcels').values():
            try:
                entrypoint.require(plugin_env)
            except ResolutionError:
                pass
            else:
                load_parcel_from_entrypoint(view, entrypoint)
                if prefs is not None:
                    prefs['plugins'][egg.key] = 'active'
                        
    if prefs is not None:
        prefs.write()

    return prefs


def _randpoolPath(profileDir):
    # Return the absolute path for the file that we use to load
    # initial entropy from in startup/store entropy into in
    # shutdown.
    return os.path.join(profileDir, 'randpool.dat')


def initCrypto(profileDir):
    """
    Initialize the cryptographic services before doing any other
    cryptographic operations.
    
    @param profileDir: The profile directory. Additional entropy will be
                       loaded from a file in this directory. It is not a
                       fatal error if the file does not exist.
    @return:           The number of bytes read from file.
    """
    m2threading.init()
    return Rand.load_file(_randpoolPath(profileDir), -1)


def stopCrypto(profileDir):
    """
    Shut down the cryptographic services. You must call startup()
    before doing cryptographic operations again.
    
    @param profileDir: The profile directory. A snapshot of current entropy
                       state will be saved into a file in this directory. 
                       It is not a fatal error if the file cannot be created.
    @return:           The number of bytes saved to file.
    """
    from osaf.framework.certstore import utils
    ret = 0
    if utils.entropyInitialized:
        ret = Rand.save_file(_randpoolPath(profileDir))
    m2threading.cleanup()
    return ret


class CertificateVerificationError(Exception):
    """
    An error that will be raised when, as part of an SSL/TLS connection
    attempt, the X.509 certificate returned by the peer does not verify.
    """
    def __init__(self, code, message, untrustedCertificates):
        """
        Inialize.
        
        @param code:                  The error code.
        @param message:               The error string. 
        @param untrustedCertificates: List of untrusted certificates in PEM
                                      format.
        """
        Exception.__init__(self, code, message)
        self.untrustedCertificates = untrustedCertificates
        

def initTwisted():
    from osaf.startup import run_reactor
    run_reactor()

def stopTwisted():
    from osaf.startup import stop_reactor
    stop_reactor()

def initWakeup(view):
    from osaf.startup import run_startup
    run_startup(view)


def stopWakeup():
    pass

class SchemaMismatchError(Exception):
    """
    The schema version in the repository doesn't match the application.
    """
    pass
