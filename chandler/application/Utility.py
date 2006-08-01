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

"""
Application utilities.
"""

import os, sys, logging, logging.config, logging.handlers, string
import i18n, schema
import M2Crypto.Rand as Rand, M2Crypto.threading as m2threading
from optparse import OptionParser

from chandlerdb.util.c import UUID, loadUUIDs
from repository.persistence.DBRepository import DBRepository
from repository.persistence.RepositoryView import NullRepositoryView
from repository.persistence.RepositoryError import \
    VersionConflictError, RepositoryPasswordError, RepositoryVersionError

import version

# Increment this value whenever the schema changes, and replace the comment
# with your name (and some helpful text). The comment's really there just to
# cause Subversion to warn you of a conflict when you update, in case someone 
# else changes it at the same time you do (that's why it's on the same line).
SCHEMA_VERSION = "228" #john: Renamed "My" Collections to Dashboard

logger = None # initialized in initLogging()

def locateWxLocalizationDir():
    """
         This is a temporary method to determine the
         path to the wxstd.mo translation files.

         Wx should know how to find its own translation
         files at install time and it should not be
         the job of Chandler to figure this out.

         Brian K will work with Robin D to come up 
         with a better solution at the WxWidgets layer
         in the near future.
    """
    root = os.getenv("CHANDLERBIN") or locateChandlerDirectory()

    if os.path.isdir(os.path.join(root, "debug")):
        sub = "debug"
    else:
        sub  = "release"

    if os.name == 'nt':
        return os.path.join(root, sub, "bin", "Lib", \
                              "site-packages", "wx", "locale")


    return os.path.join(root, sub, "share", "locale")

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
        chars = string.letters + string.digits
        name = ''.join([chars[ord(c) % len(chars)] for c in os.urandom(8)])
        profileDir = pattern.replace('*', '%s') %(name)
        createProfileDir(profileDir)
        return profileDir

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
                                  'Chandler', version.release)

    elif sys.platform == 'darwin':
        dataDir = os.path.join(os.path.expanduser('~'),
                               'Library',
                               'Application Support')
        profileDir = os.path.join(dataDir,
                                  'Open Source Applications Foundation',
                                  'Chandler', version.release)

    else:
        dataDir = os.path.expanduser('~')
        profileDir = os.path.join(dataDir, '.chandler', version.release)

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

def getPlatformName():
    import platform

    platformName = 'Unknown'

    if os.name == 'nt':
        platformName = 'Windows'
    elif os.name == 'posix':
        if sys.platform == 'darwin':
            if platform.machine() == 'i386':
                platformName = 'Mac OS X (intel)'
            else:
                platformName = 'Mac OS X (ppc)'
        elif sys.platform == 'cygwin':
            platformName = 'Windows (Cygwin)'
        else:
            platformName = 'Linux'

    return platformName

def initOptions(**kwds):
    """
    Load and parse the command line options, with overrides in **kwds.
    Returns options
    """
    #XXX i18n parcelPath, profileDir could have non-ascii paths
    #    option name,  (value, short cmd, long cmd, type flag, default, environment variable, help text)
    _configItems = {
        'parcelPath': ('-p', '--parcelPath', 's', None,  'PARCELPATH', 'Parcel search path'),
        'webserver':  ('-W', '--webserver',  'b', False, 'CHANDLERWEBSERVER', 'Activate the built-in webserver'),
        'profileDir': ('-P', '--profileDir', 's', None,  'PROFILEDIR', 'location of the Chandler Repository'),
        'profile':    ('',   '--prof',       'b', False, None, 'save profiling data'),
        'testScripts':('-t', '--testScripts','b', False, None, 'run all test scripts'),
        'scriptFile': ('-f', '--scriptFile', 's', None,  None, 'script file to execute after startup'),
        'chandlerTests': ('', '--chandlerTests', 's', None, None, 'file:TestClass,file2:TestClass2 to be executed by new framework'),
        'chandlerTestDebug': ('-D', '--chandlerTestDebug', 's', 0, None, '0=print only failures, 1=print pass and fail, 2=print pass & fail & check repository after each test'),
        'chandlerTestMask': ('-M', '--chandlerTestMask', 's', 3, None, '0=print all, 1=hide reports, 2=also hide actions, 3=also hide test names'),
        'chandlerPerformanceTests': ('', '--chandlerPerformanceTests', 's', None, None, 'file:TestClass,file2:TestClass2 to be executed by performance new framework'),
        'chandlerTestLogfile': ('', '--chandlerTestLogfile', 's', None, None, 'file for chandlerTests output'),
        'scriptTimeout': ('-s', '--scriptTimeout', 's', 0,  None, 'script file timeout'),
        'catsProfile':('',   '--catsProfile','s', None,  None, 'file for hotshot profile of script execution'),
        'catsPerfLog':('',   '--catsPerfLog','s', None,  None, 'file to output a performance number'),
        'stderr':     ('-e', '--stderr',     'b', False, None, 'Echo error output to log file'),
        'create':     ('-c', '--create',     'b', False, "CREATE", 'Force creation of a new repository'),
        'ask':        ('',   '--ask',        'b', False, None, 'give repository options on startup'),
        'ramdb':      ('-m', '--ramdb',      'b', False, None, ''),
        'restore':    ('-r', '--restore',    's', None,  None, 'repository backup to restore from before repository open'),
        'recover':    ('-R', '--recover',    'b', False, None, 'open repository with recovery'),
        'nocatch':    ('-n', '--nocatch',    'b', False, 'CHANDLERNOCATCH', ''),
        'wing':       ('-w', '--wing',       'b', False, None, ''),
        'komodo':     ('-k', '--komodo',     'b', False, None, ''),
        'refreshui':  ('-u', '--refresh-ui', 'b', False, None, 'Refresh the UI from the repository during startup'),
        'locale':     ('-l', '--locale',     's', None,  None, 'Set the default locale'),
        'encrypt':    ('-S', '--encrypt',    'b', False, None, 'Request prompt for password for repository encryption'),
        'nosplash':   ('-N', '--nosplash',   'b', False, 'CHANDLERNOSPLASH', ''),
        'logging':    ('-L', '--logging',    's', 'logging.conf',  'CHANDLERLOGCONFIG', 'The logging config file'),
        'createData': ('-C', '--createData', 's', None,  None, 'csv file with items definition to load after startup'),
        'verbose':    ('-v', '--verbose',    'b', False, None, 'Verbosity option (currently just for run_tests.py)'),
        'quiet':      ('-q', '--quiet',      'b', False, None, 'Quiet option (currently just for run_tests.py)'),
        'verify':     ('-V', '--verify-assignments', 
                                             'b', False, None, 'Verify attribute assignments against schema'),
        'debugOn':    ('-d', '--debugOn',    's', None,  None, 'Enter PDB upon this exception being raised'),
        'appParcel':  ('-a', '--app-parcel', 's', "osaf.app",  None, 'Parcel that defines the core application'),
        'nonexclusive':  ('', '--nonexclusive', 'b', False, 'CHANDLERNONEXCLUSIVEREPO', 'Enable non-exclusive repository access'),
        'indexer':    ('-i', '--indexer',    's', 'background', None, 'Run Lucene indexing in the background or foreground'),
        'uuids':      ('-U', '--uuids',      's', None, None, 'use a file containing a bunch of pre-generated UUIDs'),
        'undo':       ('',   '--undo',       's', None, None, 'undo <n> versions'),
        'backup':     ('',   '--backup',     'b', False, None, 'backup repository before start'),
        'repair':     ('',   '--repair',     'b', False, None, 'repair repository before start (currently repairs broken indices)'),
    }


    # %prog expands to os.path.basename(sys.argv[0])
    usage  = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version="%prog")

    for key in _configItems:
        (shortCmd, longCmd, optionType, defaultValue, environName, helpText) \
            = _configItems[key]

        if environName and os.environ.has_key(environName):
            defaultValue = os.environ[environName]

        if optionType == 'b':
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
                              action='store_true',
                              default=defaultValue,
                              help=helpText)
        else:
            parser.add_option(shortCmd,
                              longCmd,
                              dest=key,
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

    # Store up the remaining args
    options.args = args

    return options


def initProfileDir(options):
    """
    Ensure we have the profile directory.
    """
    #XXX: i18n a users home directory can be non-ascii path
    if not options.profileDir:
        profileDir = locateProfileDir()
        if profileDir is None:
            profileDir = locateChandlerDirectory()
        options.profileDir = os.path.expanduser(profileDir)
    elif not os.path.isdir(options.profileDir):
        createProfileDir(options.profileDir)


def initI18n(options):
    # These methods are not exposed to 3rd party
    # developers as part of the i18n package
    i18nMan = i18n._I18nManager
    i18nMan.setRootPath(locateChandlerDirectory())

    #XXX: Comment out this code if a issue 
    #     arises with wx translation loading
    #     It's causing failure on mac nightly builds, so commenting it out till
    #     that's fixed, bug 6040
    #i18nMan.setWxPath(locateWxLocalizationDir())

    if options.locale is not None:
        # If a locale is passed in on the command line
        # we set it as the root in the localeset.
        i18nMan.setLocaleSet([options.locale])
    else:
        i18nMan.discoverLocaleSet()


def initLogging(options):
    global logger

    if logger is None:
        # Make PROFILEDIR available within the logging config file
        logging.PROFILEDIR = options.profileDir

        logConfFile = options.logging
        if os.path.isfile(logConfFile):
            # Replacing the standard fileConfig with our own, below
            # logging.config.fileConfig(options.logging)
            fileConfig(options.logging)
        else:
            # Log config file doesn't exist
            #logging.basicConfig(level=logging.WARNING,
            #    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
            #    filename=os.path.join(options.profileDir, 'chandler.log'),
            #    filemode='a')

            logger = logging.getLogger()

            fileHandler   = logging.handlers.RotatingFileHandler(os.path.join(options.profileDir, 'chandler.log'), 'a', 1000000, 2)
            fileFormatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')

            fileHandler.setFormatter(fileFormatter)

            logger.addHandler(fileHandler)
            logger.setLevel(logging.INFO)

        logger = logging.getLogger(__name__)

        # If there is a logging FileHandler writing to a chandler.log,
        # then put twisted.log next to it.  Otherwise send twisted output
        # to twisted.log in the profile directory

        twistedLogDir = options.profileDir
        try:
            rootLogger = logging.getLogger()
            for handler in rootLogger.handlers:
                if isinstance(handler, logging.RotatingFileHandler):
                    if handler.baseFilename.endswith('chandler.log'):
                        # We found the chandler.log handler.  Let's put
                        # twisted.log here next to it
                        chandlerLogDir = os.path.dirname(handler.baseFilename)
                        twistedLogDir  = chandlerLogDir
                        break
        except:
            pass # Just stick with profileDir

        import twisted.python.log
        import twisted.python.logfile

        twistedlog = twisted.python.logfile.LogFile("twisted.log", twistedLogDir)

         # By default, twisted.log doesn't include seconds in its dates,
         # so tweak the format.
        twisted.python.log.FileLogObserver.timeFormat = '%Y-%m-%d %H:%M:%S'
        twisted.python.log.startLogging(twistedlog, 0)
        logger.warning("Twisted logging output to %s folder" % twistedLogDir)


def locateChandlerDirectory():
    """
    Find the directory that Chandler lives in by looking up the file that
    the application module lives in.
    """
    return os.path.dirname(os.path.dirname(__file__))


def locateRepositoryDirectory(profileDir):
    if profileDir:
        path = os.sep.join([profileDir, '__repository__'])
    else:
        path = '__repository__'
    return path


def initRepository(directory, options, allowSchemaView=False):

    if options.uuids:
        input = file(options.uuids)
        loadUUIDs([UUID(uuid.strip()) for uuid in input if len(uuid) > 1])
        input.close()

    repository = DBRepository(directory)

    kwds = { 'stderr': options.stderr,
             'ramdb': options.ramdb,
             'create': True,
             'recover': options.recover,
             'exclusive': not options.nonexclusive,
             'refcounted': True,
             'logged': not not options.logging,
             'verify': options.verify or __debug__ }

    if options.restore:
        kwds['restore'] = options.restore

    while True:
        try:
            if options.encrypt:
                from getpass import getpass
                kwds['password'] = getpass("password> ")

            if options.create:
                repository.create(**kwds)
            else:
                repository.open(**kwds)
        except RepositoryPasswordError, e:
            if options.encrypt:
                print e.args[0]
            else:
                options.encrypt = True
            continue
        except RepositoryVersionError:
            repository.close()
            raise
        else:
            del kwds
            break

    if options.backup:
        dbHome = repository.backup()
        repository.logger.info("Repository was backed up into %s", dbHome)

    if options.repair:
        view = repository.view
        schema.reset(view)
        view.check(True)

    if options.undo:
        if options.undo == 'check':
            view = repository.view
            while view.itsVersion > 0L:
                schema.reset(view)
                if view.check():
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

    view = repository.view

    # tell the schema API about this view so that it doesn't setup its own
    # (also load Chandler pack)
    if isinstance(schema.reset(view), NullRepositoryView):
        if not allowSchemaView:
            raise AssertionError, "schema.py was used before it was initialized here causing it to setup a NullRepositoryView"

    if options.indexer == 'background':   # the default
        # don't run PyLucene indexing in the main view
        view.setBackgroundIndexed(True)
        # but in the repository's background indexer
        repository.startIndexer()

    elif options.indexer == 'foreground':
        # do nothing, indexing happens during commit
        pass

    elif options.indexer == 'none':
        # don't run PyLucene indexing in the main view
        view.setBackgroundIndexed(True)
        # don't start an indexer

    else:
        raise ValueError, ("--indexer", options.indexer)

    if options.debugOn:
        from repository.util.ClassLoader import ClassLoader
        debugOn = ClassLoader.loadClass(options.debugOn)
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
    parcelRoot = view.getRoot("parcels")
    if parcelRoot is not None:
        if (not hasattr(parcelRoot, 'version') or
            parcelRoot.version != SCHEMA_VERSION):
            logger.info("Schema version of repository doesn't match app")
            return False
    return True


def initParcelEnv(chandlerDirectory, path):
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
                      PARCEL_IMPORT.replace ('.', os.sep)))

    """
    If PARCELPATH env var is set, append those directories to the
    list of places to look for parcels.
    """
    if path:
        for directory in path.split(os.pathsep):
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


def initParcels(view, path, namespaces=None):
    from Parcel import Manager # Delayed so as not to trigger
                               # early loading of schema.py

    Manager.get(view, path=path).loadParcels(namespaces)

    # Record the current schema version into the repository
    parcelRoot = view.getRoot("parcels")
    if getattr(parcelRoot, 'version', None) != SCHEMA_VERSION:
        parcelRoot.version = SCHEMA_VERSION


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

# Replacement for logging.config.fileConfig, which doesn't disable loggers:

def fileConfig(fname, defaults=None):
    """
    Read the logging configuration from a ConfigParser-format file.

    This can be called several times from an application, allowing an end user
    the ability to select from various pre-canned configurations (if the
    developer provides a mechanism to present the choices and load the chosen
    configuration).
    In versions of ConfigParser which have the readfp method [typically
    shipped in 2.x versions of Python], you can pass in a file-like object
    rather than a filename, in which case the file-like object will be read
    using readfp.
    """
    import ConfigParser

    cp = ConfigParser.ConfigParser(defaults)
    if hasattr(cp, 'readfp') and hasattr(fname, 'readline'):
        cp.readfp(fname)
    else:
        cp.read(fname)
    #first, do the formatters...
    flist = cp.get("formatters", "keys")
    if len(flist):
        flist = string.split(flist, ",")
        formatters = {}
        for form in flist:
            sectname = "formatter_%s" % form
            opts = cp.options(sectname)
            if "format" in opts:
                fs = cp.get(sectname, "format", 1)
            else:
                fs = None
            if "datefmt" in opts:
                dfs = cp.get(sectname, "datefmt", 1)
            else:
                dfs = None
            f = logging.Formatter(fs, dfs)
            formatters[form] = f
    #next, do the handlers...
    #critical section...
    logging._acquireLock()
    try:
        try:
            #first, lose the existing handlers...
            logging._handlers.clear()
            #now set up the new ones...
            hlist = cp.get("handlers", "keys")
            if len(hlist):
                hlist = string.split(hlist, ",")
                handlers = {}
                fixups = [] #for inter-handler references
                for hand in hlist:
                    try:
                        sectname = "handler_%s" % hand
                        klass = cp.get(sectname, "class")
                        opts = cp.options(sectname)
                        if "formatter" in opts:
                            fmt = cp.get(sectname, "formatter")
                        else:
                            fmt = ""
                        klass = eval(klass, vars(logging))
                        args = cp.get(sectname, "args")
                        args = eval(args, vars(logging))
                        h = apply(klass, args)
                        if "level" in opts:
                            level = cp.get(sectname, "level")
                            h.setLevel(logging._levelNames[level])
                        if len(fmt):
                            h.setFormatter(formatters[fmt])
                        #temporary hack for FileHandler and MemoryHandler.
                        if klass == logging.handlers.MemoryHandler:
                            if "target" in opts:
                                target = cp.get(sectname,"target")
                            else:
                                target = ""
                            if len(target): #the target handler may not be loaded yet, so keep for later...
                                fixups.append((h, target))
                        handlers[hand] = h
                    except:     #if an error occurs when instantiating a handler, too bad
                        pass    #this could happen e.g. because of lack of privileges
                #now all handlers are loaded, fixup inter-handler references...
                for fixup in fixups:
                    h = fixup[0]
                    t = fixup[1]
                    h.setTarget(handlers[t])
            #at last, the loggers...first the root...
            llist = cp.get("loggers", "keys")
            llist = string.split(llist, ",")
            llist.remove("root")
            sectname = "logger_root"
            root = logging.root
            log = root
            opts = cp.options(sectname)
            if "level" in opts:
                level = cp.get(sectname, "level")
                log.setLevel(logging._levelNames[level])
            for h in root.handlers[:]:
                root.removeHandler(h)
            hlist = cp.get(sectname, "handlers")
            if len(hlist):
                hlist = string.split(hlist, ",")
                for hand in hlist:
                    log.addHandler(handlers[hand])
            #and now the others...
            #we don't want to lose the existing loggers,
            #since other threads may have pointers to them.
            #existing is set to contain all existing loggers,
            #and as we go through the new configuration we
            #remove any which are configured. At the end,
            #what's left in existing is the set of loggers
            #which were in the previous configuration but
            #which are not in the new configuration.
            existing = root.manager.loggerDict.keys()
            #now set up the new ones...
            for log in llist:
                sectname = "logger_%s" % log
                qn = cp.get(sectname, "qualname")
                opts = cp.options(sectname)
                if "propagate" in opts:
                    propagate = cp.getint(sectname, "propagate")
                else:
                    propagate = 1
                logger = logging.getLogger(qn)
                if qn in existing:
                    existing.remove(qn)
                if "level" in opts:
                    level = cp.get(sectname, "level")
                    logger.setLevel(logging._levelNames[level])
                for h in logger.handlers[:]:
                    logger.removeHandler(h)
                logger.propagate = propagate
                logger.disabled = 0
                hlist = cp.get(sectname, "handlers")
                if len(hlist):
                    hlist = string.split(hlist, ",")
                    for hand in hlist:
                        logger.addHandler(handlers[hand])
            #Disable any old loggers. There's no point deleting
            #them as other threads may continue to hold references
            #and by disabling them, you stop them doing any logging.
            # for log in existing:
            #     root.manager.loggerDict[log].disabled = 1
        except:
            import traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            del ei
    finally:
        logging._releaseLock()

