__author__ = "Jed Burgess"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__ = "OSAF License"


from application.Application import wxApplication
from Transaction import get_transaction

if __name__=="__main__":
        
    application = wxApplication()
    application.MainLoop()
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
