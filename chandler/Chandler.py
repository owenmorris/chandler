__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys

# Check for -wing command line argument; if specified, try to connect to
# an already-running WingIDE instance.  See:
#    http://wiki.osafoundation.org/bin/view/Main/DebuggingChandler#wingIDE
# for details.
if '-wing' in sys.argv:
    import wingdbstub

import logging
from application.Application import wxApplication

def main():

    """
    The details of unhandled exceptions are now handled by the logger.
    wxApplication is responsible for configuring the logger with the
    appropriate handlers.

    We are currently reraising the exception, so that wing can notice
    in the default exception handler.
    """

    logging.basicConfig()

    try:
        application = wxApplication(sys.argv)
        application.MainLoop()
        application.OnTerminate()
    except:
        logging.exception("Unhandled exception in Chandler")
        ShowExceptionDialog("Chandler", "Chandler encountered an unexpected problem and had to shut down.")
        raise

        
def ShowExceptionDialog(title, message):
    """
    A note to the user that Chandler has crashed.
    """
    from wxPython.wx import wxMessageDialog, wxOK, wxICON_INFORMATION
    dlg = wxMessageDialog(None, message, title,
                          wxOK | wxICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()

if __name__=="__main__":
    main()
