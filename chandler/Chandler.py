__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import sys
if __debug__ and '-wing' in sys.argv:
    """
      Check for -wing command line argument; if specified, try to connect to
    an already-running WingIDE instance.  See:
      http://wiki.osafoundation.org/bin/view/Main/DebuggingChandler#wingIDE
    for details.
    """
    import wingdbstub
import logging
from wxPython.wx import *
from application.Application import wxApplicationNew

def main():

    """
      The details of unhandled exceptions are now handled by the logger,
    and logged to a file: chandler.log
    """
    handler = logging.FileHandler('chandler.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)

    try:
        """
          Don't redirect stdio to a file. useBestVisual, uses best screen
        resolutions on some old computers. See wxApp.SetUseBestVisual
        """
        exceptionMessage = "while trying to start."
        application = wxApplicationNew(redirect=False, useBestVisual=True)

        exceptionMessage = "and had to shut down."
        application.MainLoop()

    except Exception, e:
        message = "Chandler encountered an unexpected problem %s" % exceptionMessage
        logging.exception(message)
        dialog = wxMessageDialog(None, message, "Chandler", wxOK | wxICON_INFORMATION)
        dialog.ShowModal()
        dialog.Destroy()
        
        # Reraising the exception, so wing catches it.
        raise

if __name__=="__main__":
    main()

