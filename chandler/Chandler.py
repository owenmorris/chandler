__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

def main():
    if True: # try:
        message = "while trying to start."

        import sys, logging, traceback, wx
        
        # @@@BJS don't checkin!
        sys.argv.append("-create")
        
        if __debug__ and '-wing' in sys.argv:
            """
              Check for -wing command line argument; if specified, try to connect to
            an already-running WingIDE instance.  See:
              http://wiki.osafoundation.org/bin/view/Chandler/DebuggingChandler#wingIDE". 
            for details.
            """
            import wingdbstub
        from application.Application import wxApplication

        """
          The details of unhandled exceptions are now handled by the logger,
        and logged to a file: chandler.log
        """
        handler = logging.FileHandler('chandler.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.addHandler(handler)

        # Also send twisted output to chandler.log, per bug 1997
        # @@@ Probably not a good long term solution(?)
        import twisted.python.log
        twisted.python.log.startLogging(file('chandler.log', 'a+'), 0)

        """
          Don't redirect stdio to a file. useBestVisual, uses best screen
        resolutions on some old computers. See wxApp.SetUseBestVisual
        """
        application = wxApplication(redirect=False, useBestVisual=True)

        message = "and had to shut down."
        application.MainLoop()

    else: # except Exception, exception:
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

