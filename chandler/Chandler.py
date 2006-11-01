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
Chandler startup
"""

import os, PyLucene
import application.Globals as Globals
import application.Utility as Utility

def main():

    # Process any command line switches and any environment variable values
    Globals.options = Utility.initOptions()

    def realMain():
        
        Utility.initProfileDir(Globals.options)

        from application import feedback
        feedback.initRuntimeLog(Globals.options.profileDir)
        
        Globals.chandlerDirectory = Utility.locateChandlerDirectory()
    
        os.chdir(Globals.chandlerDirectory)
        Utility.initLogging(Globals.options)

        if __debug__ and Globals.options.wing:
            # Check for -wing command line argument; if specified, try to 
            # connect to an already-running WingIDE instance. See
            # http://wiki.osafoundation.org/bin/view/Chandler/DebuggingChandler#wingIDE
            # for details.

            import wingdbstub

        if __debug__ and Globals.options.komodo:
            # Check for -komodo command line argument; if specified, try to 
            # connect to an already-running Komodo instance. See
            # http://wiki.osafoundation.org/bin/view/Chandler/DebuggingChandler#Komodo
            # for details.

            import dbgp.client
            dbgp.client.brk()

        from application.Application import wxApplication

        # Redirect stdio and stderr to a dialog if a non-default --catch option 
        # was specified. This is done to catch asserts, which otherwise will
        # never get seen by people who run Chandler using the launchers, e.g.
        # Aparna. If you're running release you can also set things up so 
        # that you can see stderr and stdout if you run in a shell or from
        # wing with a console.
        #
        # useBestVisual - uses best screen resolutions on some old computers.
        #                 See wxApp.SetUseBestVisual

        redirect = Globals.options.catch == 'normal'
        app = wxApplication(redirect=redirect, useBestVisual=True)

        app.MainLoop()

    if Globals.options.catch != 'normal':
        # When debugging, it's handy to run without the outer exception frame
        realMain()
    else:
        # The normal way: wrap the app in an exception frame
        from repository.persistence.RepositoryError \
            import RepositoryOpenDeniedError, ExclusiveOpenDeniedError

        try:
            import logging, wx
            from i18n import ChandlerSafeTranslationMessageFactory as _
            realMain()

        except (RepositoryOpenDeniedError, ExclusiveOpenDeniedError):
            # This doesn't seem worth the effor to localize, since we don't have a repository
            # which is necessary for localization.
            logging.error("Another instance of Chandler currently has the repository open.")
            dialog = wx.MessageDialog(None,
                                      _(u"Another instance of Chandler currently has the repository open."),
                                      _(u"Chandler"), wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()

        except Utility.SchemaMismatchError:
            logging.info("User chose not to clear the repository.  Exiting.")

        except:
            import sys, traceback
            
            line1 = "Chandler encountered an unexpected problem while trying to start.\n"
            
            type, value, stack = sys.exc_info()
            backtrace = traceback.format_exception(type, value, stack)
            
            longMessage = "".join([line1, "\n"] + backtrace)
            
            logging.error(longMessage)
            
            if getattr(globals(), 'app', None) is None or wx.GetApp() is None:
                app = wx.PySimpleApp()
                app.ignoreSynchronizeWidget = True
            
            try:
                # Let's try the best (and most complicated) option
                # first
                # See if we already have a window up, and if so, reuse it
                from application import feedback
                feedback.destroyAppOnClose = True
                win = feedback.FeedbackWindow()
                win.CreateOutputWindow('')
                for line in backtrace:
                    win.write(line)
                if not app.IsMainLoopRunning():
                    app.MainLoop()
            except:
                # Fall back to our custom (but simple) error dialog
                try:
                    from application.dialogs.UncaughtExceptionDialog import ErrorDialog
                    dialog = ErrorDialog(longMessage)
                except:
                    # Fall back to MessageDialog
                    frames = 8
                    line1 = _(u"Chandler encountered an unexpected problem while trying to start.\n")
                    line2 = _(u"Here are the bottom %(frames)s frames of the stack:\n") % {'frames': frames - 1}
                    shortMessage = u"".join([line1, line2, u"\n"])
                    shortMessage += unicode("".join(backtrace[-frames:]), "UTF-8", "ignore")
                    dialog = wx.MessageDialog(None, shortMessage, _(u"Chandler"), wx.OK | wx.ICON_INFORMATION)
                dialog.ShowModal()
                dialog.Destroy()


    #@@@Temporary testing tool written by Morgen -- DJA
    #import util.timing
    #print "\nTiming results:\n"
    #util.timing.results()

if __name__== "__main__":
    main()
