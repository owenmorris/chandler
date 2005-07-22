__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys, os
import application.Globals
import application.Utility as Utility
from repository.persistence.RepositoryError \
    import RepositoryOpenDeniedError, ExclusiveOpenDeniedError
from application.Application import SchemaMismatchError


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
    application.Globals.options = Utility.initOptions(chandlerDirectory)

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

        logFile = os.path.join(application.Globals.options.profileDir,
                               'chandler.log')
        Utility.initLogging(logFile)


        """
          redirect stdio and stderr to a dialog if we're running the debug version.
        This is done to catch asserts, which otherwise will never get seen by
        people who run Chandler using the launchers, e.g. Aparna. If you're
        running release you can also set things up so that you can see
        stderr and stdout if you run in a shell or from wing with a console.
          useBestVisual, uses best screen resolutions on some old computers. See
        wxApp.SetUseBestVisual
        """
        #app = wxApplication(redirect=__debug__, useBestVisual=True)
        app = wxApplication(redirect=False, useBestVisual=True)
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

        except (RepositoryOpenDeniedError, ExclusiveOpenDeniedError):
            message = "Another instance of Chandler currently has the " \
                      "repository open."
            logging.exception(message)
            dialog = wx.MessageDialog(None, message, "Chandler", wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()

        except SchemaMismatchError:
            logging.info("User chose not to clear the repository.  Exiting.")

        except Exception:
            type, value, stack = sys.exc_info()
            formattedBacktrace = "".join (traceback.format_exception (type, value, stack, 5))

            message = ("Chandler encountered an unexpected problem %s\n" + \
                      "Here are the bottom 5 frames of the stack:\n%s") % (message, formattedBacktrace)
            logging.exception(message)
            # @@@ 25Issue - Cannot create wxItems if the app failed to initialize
            dialog = wx.MessageDialog(None, message, "Chandler", wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()

            #Reraising the exception, so wing catches it.
            raise

    #@@@Temporary testing tool written by Morgen -- DJA
    # import util.timing
    # print "\nTiming results:\n"
    # util.timing.results()

if __name__== "__main__":
    main()
