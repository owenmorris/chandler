__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, os, shutil
import application.Globals

def locateProfileDir(chandlerDirectory):
    """
    Locate the Chandler repository.
    The location is determined either by parameters, or if not specified, by
    the presence of a .chandler directory in the users home directory.
    """
      # if a profileDir is specified then just use it
    if application.Globals.options.profileDir:
        application.Globals.options.profileDir = os.path.expanduser(application.Globals.options.profileDir)
    else:
        if os.name == 'nt':
            dataDir = None

            if os.environ.has_key('APPDATA'):
                dataDir = os.environ['APPDATA']
            elif os.environ.has_key('USERPROFILE'):
                dataDir = os.environ['USERPROFILE']
                if os.path.isdir(os.path.join(dataDir, 'Application Data')):
                    dataDir = os.path.join(dataDir, 'Application Data')

            if dataDir is None or not os.path.isdir(dataDir):
                if os.environ.has_key('HOMEDRIVE') and os.environ.has_key('HOMEPATH'):
                    dataDir = '%s%s' % (os.environ['HOMEDRIVE'], os.environ['HOMEPATH'])
                    
            if dataDir is None or not os.path.isdir(dataDir):
                dataDir = os.path.expanduser('~')
                
            profileDir = os.path.join(dataDir, 'Chandler')
        elif sys.platform == 'darwin':
            dataDir    = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
            profileDir = os.path.join(dataDir, 'Chandler')
        else:
            dataDir    = os.path.expanduser('~')
            profileDir = os.path.join(dataDir, '.chandler')          

        if not os.path.isdir(profileDir):
              # if not found, then figure out where to create one
            if os.path.isdir(dataDir):
                os.mkdir(profileDir, 0700)
            else:
                profileDir = chandlerDirectory
  
        application.Globals.options.profileDir = profileDir

        print 'Using profile directory: %s' % profileDir

def loadConfig(chandlerDirectory):
    """
    Load and parse the command line options.
    Sets Globals.options and Globals.args
    """
                      # option name, (value, short cmd, long cmd, type flag, default, environment variable, help text)
    _configItems = { 'parcelDir':  ('-p', '--parcelDir',  's', None,  'PARCELDIR',         'Location for private/user parcels'),
                     'webserver':  ('-W', '--webserver',  'b', False, 'CHANDLERWEBSERVER', 'Activate the built-in webserver'),
                     'profileDir': ('-P', '--profileDir', 's', None,  'PROFILE_DIR',       'location of the Chandler Repository'),
                     'profile':    ('',   '--prof',       'b', False, None, 'save profiling data'),
                     'stderr':     ('-e', '--stderr',     'b', False, None, 'Echo error output to log file'),
                     'create':     ('-c', '--create',     'b', False, None, 'Force creation of a new repository'),
                     'ramdb':      ('-d', '--ramdb',      'b', False, None, ''),
                     'exclusive':  ('-x', '--exclusive',  'b', False, None, 'open repository exclusive'),
                     'repo':       ('-r', '--repo',       's', None,  None, 'repository to copy during startup'),
                     'nocatch':    ('-n', '--nocatch',    'b', False, None, ''),
                     'wing':       ('-w', '--wing',       'b', False, None, ''),
                     'komodo':     ('-k', '--komodo',     'b', False, None, ''),
                     'refreshui':  ('-u', '--refresh-ui', 'b', False, None, 'Refresh the UI from the repository during startup'),
                      }

    from optparse import OptionParser

    usage  = "usage: %prog [options]"   # %prog expands to os.path.basename(sys.argv[0])
    parser = OptionParser(usage=usage, version="%prog " + __version__)

    for key in _configItems:
        (shortCmd, longCmd, optionType, defaultValue, environName, helpText) = _configItems[key]

        if environName and os.environ.has_key(environName):
            defaultValue = os.environ[environName]

        if optionType == 'b':
            parser.add_option(shortCmd, longCmd, dest=key, action='store_true', default=defaultValue, help=helpText)
        else:
            parser.add_option(shortCmd, longCmd, dest=key, default=defaultValue, help=helpText)

    (application.Globals.options, application.Globals.args) = parser.parse_args()

    locateProfileDir(chandlerDirectory)

def main():
    message = "while trying to start."

    """
    Find the directory that Chandler lives in by looking up the file that
    the application module lives in.
    """
    pathComponents = sys.modules['application'].__file__.split(os.sep)
    assert len(pathComponents) > 3
    chandlerDirectory = os.sep.join(pathComponents[0:-2])

    application.Globals.chandlerDirectory = chandlerDirectory

    os.chdir(chandlerDirectory)

    """
    Process any command line switches and any environment variable values
    """
    loadConfig(chandlerDirectory)

    def realMain():
        if __debug__ and application.Globals.options.wing:
            """
              Check for -wing command line argument; if specified, try to connect to
            an already-running WingIDE instance.  See:
              http://wiki.osafoundation.org/bin/view/Chandler/DebuggingChandler#wingIDE".
            for details.
            """
            import wingdbstub
        if __debug__ and application.Globals.options.komodo:
            """
            Check for -komodo command line argument; if specified, try to connect to
            an already-running Komodo instance.  See:
              http://wiki.osafoundation.org/bin/view/Chandler/DebuggingChandler#Komodo".
            for details.
            """
            import dbgp.client
            dbgp.client.brk()
        from application.Application import wxApplication

        """
          The details of unhandled exceptions are now handled by the logger,
        and logged to a file: chandler.log
        """
        logFile = os.path.join(application.Globals.options.profileDir, 'chandler.log')
        handler = logging.FileHandler(logFile)
        formatter = \
         logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.addHandler(handler)

        # Also send twisted output to chandler.log, per bug 1997
        # @@@ Probably not a good long term solution(?)
        import twisted.python.log
        twisted.python.log.startLogging(file(logFile, 'a+'), 0)

        """
          Don't redirect stdio to a file. useBestVisual, uses best screen
        resolutions on some old computers. See wxApp.SetUseBestVisual
        """
        app = wxApplication(redirect=False, useBestVisual=True)

        message = "and had to shut down."
        app.MainLoop()

    if application.Globals.options.nocatch:
        # When debugging, it's handy to run without the outer exception frame
        import logging, traceback, wx
        realMain()
    else:
        # The normal way: wrap the app in an exception frame
        try:
            import logging, traceback, wx
            realMain()
        except Exception, exception:
            type, value, stack = sys.exc_info()
            formattedBacktrace = "".join (traceback.format_exception (type, value, stack))

            message = "Chandler encountered an unexpected problem %s\n\n%s" % (message, formattedBacktrace)
            logging.exception(message)
            # @@@ 25Issue - Cannot create wxItems if the app failed to initialize
            dialog = wx.MessageDialog(None, message, "Chandler", wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()

            #Reraising the exception, so wing catches it.
            raise

    #@@@Temporary testing tool written by Morgen -- DJA
    # import tools.timing
    # print "\nTiming results:\n"
    # tools.timing.results()

if __name__=="__main__":
    main()

