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

from application.Application import wxApplication
from transaction import get_transaction

def main():

    """
    So that developers can easily see the details of unhandled exceptions,
    a dialog box is displayed.  The exception is then re-raised so that the
    default exception handler takes over.
    """
    try:
        application = wxApplication(sys.argv)
    except:
        ShowExceptionDialog("Unhandled Exception", "During initialization, "+\
         "the following exception occurred:")
        raise 
        
    try:
        application.MainLoop()
    except:
        ShowExceptionDialog("Unhandled Exception", "During MainLoop(), "+\
         "the following exception occurred:")
        raise 
        
    """
      Since Chandler doesn't have a save command and commits typically happen
    only when the user completes a command that changes the user's data, we
    need to add a final commit when the application quits to save data the
    state of the user's world, e.g. window location and size.

    We're using ZODB's transactions here. In the future we may replace ZODB with
    another database that provides similar functionality.
    """
    transaction = get_transaction ()
    transaction.note ("Normal Exit")
    transaction.commit ()

def ShowExceptionDialog(title, message):
    """
    Show the details of the current exception, in a modal dialog box.
    """
    from wxPython.wx import wxMessageDialog, wxOK, wxICON_INFORMATION
    import traceback
    (excType, excValue, excTraceback) = sys.exc_info()
    messageLines = [message + "\n\n"]
    messageLines.append("Exception type: " + excType.__name__ + "\n")
    messageLines.append("Exception value: " + excValue.__str__() + "\n")
    messageLines.append("\nTraceback:\n")
    messageLines += traceback.format_tb(excTraceback)
    completeMessage = "".join(messageLines)
    dlg = wxMessageDialog(None, completeMessage, title, 
     wxOK | wxICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()

if __name__=="__main__":
    main()
