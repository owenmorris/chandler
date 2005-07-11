__version__ = "$Revision: 5915 $"
__date__ = "$Date: 2005-07-09 11:49:30 -0700 (Sat, 09 Jul 2005) $"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


import gettext, os, sys, crypto, logging
from optparse import OptionParser
from repository.persistence.DBRepository import DBRepository
from repository.persistence.RepositoryError \
     import VersionConflictError, MergeError, RepositoryPasswordError, \
     RepositoryOpenDeniedError, ExclusiveOpenDeniedError
from repository.item.RefCollections import RefList

SCHEMA_VERSION = "24"

logger = None # initialized in initLogging()


def locateProfileDir():
    """
    Locate the Chandler repository.
    The location is determined either by parameters, or if not specified, by
    the presence of a .chandler directory in the users home directory.
    """

    def _makeRandomProfileDir(pattern):
        import M2Crypto.BN as BN
        profileDir = pattern.replace('*', '%s') % (BN.randfname(8))
        os.makedirs(profileDir, 0700)
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
                                  'Chandler')

    elif sys.platform == 'darwin':
        dataDir = os.path.join(os.path.expanduser('~'),
                               'Library',
                               'Application Support')
        profileDir = os.path.join(dataDir,
                                  'Open Source Applications Foundation',
                                  'Chandler')

    else:
        dataDir = os.path.expanduser('~')
        profileDir = os.path.join(dataDir, '.chandler')

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


def initOptions(chandlerDirectory, **kwds):
    """
    Load and parse the command line options, with overrides in **kwds.
    Returns options
    """

    #    option name,  (value, short cmd, long cmd, type flag, default, environment variable, help text)
    _configItems = {
        'parcelPath':  ('-p', '--parcelPath','s', None,  'PARCELPATH', 'Parcel search path'),
        'webserver':  ('-W', '--webserver',  'b', False, 'CHANDLERWEBSERVER', 'Activate the built-in webserver'),
        'profileDir': ('-P', '--profileDir', 's', None,  'PROFILEDIR', 'location of the Chandler Repository'),
        'profile':    ('',   '--prof',       'b', False, None, 'save profiling data'),
        'script':     ('-s', '--script',     's', None,  None, 'script to execute after startup'),
        'stderr':     ('-e', '--stderr',     'b', False, None, 'Echo error output to log file'),
        'create':     ('-c', '--create',     'b', False, "CREATE", 'Force creation of a new repository'),
        'ramdb':      ('-d', '--ramdb',      'b', False, None, ''),
        'repo':       ('-r', '--repo',       's', None,  None, 'repository to copy during startup'),
        'recover':    ('-R', '--recover',    'b', False, None, 'open repository with recovery'),
        'nocatch':    ('-n', '--nocatch',    'b', False, None, ''),
        'wing':       ('-w', '--wing',       'b', False, None, ''),
        'komodo':     ('-k', '--komodo',     'b', False, None, ''),
        'refreshui':  ('-u', '--refresh-ui', 'b', False, None, 'Refresh the UI from the repository during startup'),
        'locale':     ('-l', '--locale',     's', None,  None, 'Set the default locale'),
        'encrypt':    ('-S', '--encrypt',    'b', False, None, 'Request prompt for password for repository encryption'),
    }


    # %prog expands to os.path.basename(sys.argv[0])
    usage  = "usage: %prog [options]"
    parser = OptionParser(usage=usage, version="%prog " + __version__)

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

    (options, args) = parser.parse_args()

    if not options.profileDir:
        profileDir = locateProfileDir()
        if profileDir is None:
            profileDir = chandlerDirectory
        options.profileDir = os.path.expanduser(profileDir)

    for (opt,val) in kwds.iteritems():
        setattr(options, opt, val)

    if options.locale is not None:
        from PyICU import Locale
        Locale.setDefault(Locale(options.locale))

    return options


def initLogging(logFile):
    global logger

    if logger is None:
        handler = logging.FileHandler(logFile)
        formatter = \
         logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.addHandler(handler)

        logger = logging.getLogger('util')
        logger.setLevel(logging.INFO)

        # Also send twisted output to chandler.log, per bug 1997
        # @@@ Probably not a good long term solution(?)
        import twisted.python.log
        twisted.python.log.startLogging(file(logFile, 'a+'), 0)


def locateChandlerDirectory():
    return os.getenv('CHANDLERHOME')


def locateRepositoryDirectory(profileDir):
    if profileDir:
        path = os.sep.join([profileDir, '__repository__'])
    else:
        path = '__repository__'
    return path


def initRepository(directory, options):

    repository = DBRepository(directory)

    kwds = { 'stderr': options.stderr,
             'ramdb': options.ramdb,
             'create': True,
             'recover': options.recover,
             'exclusive': True,
             'refcounted': True }

    if options.repo:
        kwds['fromPath'] = options.repo

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
        else:
            del kwds
            break

    view = repository.getCurrentView()

    if not view.findPath("//Packs/Chandler"):
        view.loadPack("repository/packs/chandler.pack")

    return view


def stopRepository(view):
    try:
        try:
            view.commit()
        except VersionConflictError, e:
            logger.warning(str(e))
    finally:
        view.repository.close()


def verifySchema(view):
    # Fetch the top-level parcel item to check schema version info
    parcelRoot = view.findPath("//parcels")
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
        sys.path.insert(insertionPoint, directory)
        insertionPoint += 1

    logger.info("Using PARCELPATH %s" % parcelPath)

    return parcelPath


def initParcels(view, path):
    import Parcel # Delayed so as not to trigger an extra logging addHandler().
                  # Importing Parcel has the side effect of importing schema
                  # which has the side effect of creating a NullRepositoryView
                  # which calls addHandler( ).

    Parcel.Manager.get(view, path=path).loadParcels()

    # Record the current schema version into the repository
    parcelRoot = view.findPath("//parcels")
    parcelRoot.version = SCHEMA_VERSION


def initLocale(locale):
    """
      Setup internationalization
    To experiment with a different locale, try 'fr' and wx.LANGUAGE_FRENCH
    """
    os.environ['LANGUAGE'] = locale
    gettext.install('chandler', 'locale')


def initCrypto(profileDir):
    crypto.startup(profileDir)


def stopCrypto(profileDir):
    crypto.shutdown(profileDir)


def initTwisted():
    from osaf.framework.twisted.TwistedReactorManager \
        import TwistedReactorManager
    reactorManager = TwistedReactorManager()
    reactorManager.startReactor()
    return reactorManager


def stopTwisted(reactorManager):
    reactorManager.stopReactor()


def initWakeup(view):
    from osaf.framework.wakeup.WakeupCaller import WakeupCaller
    wakeupCaller = WakeupCaller(view.repository)
    wakeupCaller.startup()
    return wakeupCaller


def stopWakeup(wakeupCaller):
    wakeupCaller.shutdown()
