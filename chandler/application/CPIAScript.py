__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import Globals, logging
import repository.item.Query as ItemQuery
import wx

logger = logging.getLogger('CPIA Script')
logger.setLevel(logging.INFO)

# Flag that a ReloadParcels can reload this module
AcceptsReload = True

"""
Handle running a Script.
"""
def RunScript(script=None):
    """
    Run the current script.
    If no script is specified, pick up the global script option, 
          and create a CPIA Script from that text.
    @@@DLD - split this into two methods; one for loading, one for running.
    @@@DLD - stop using globals; run whatever the repository says is the current script
    """
    if script is None:
        if Globals.options.script is not None:
            try:
                createdStartupScript = Globals.CreatedStartupScript
            except AttributeError:
                Globals.CPIAScript = CPIAScript(Globals.options.script)
                Globals.CreatedStartupScript = True
    else:
        Globals.CPIAScript = script

    # if we have a script, execucte it until completion
    try:
        script = Globals.CPIAScript
    except AttributeError:
        script = None
    if script is not None:
        scriptDone = True
        try:
            scriptDone = script.execute()
        finally:
            if scriptDone:
                Globals.CPIAScript = None # done

def getAllBlockEvents():
    blocksPath = wx.GetApp().UIRepositoryView.findPath('//parcels/osaf/framework/blocks/BlockEvent')
    return ItemQuery.KindQuery().run([blocksPath])

class CPIAScript:
    """ Script to be executed at Startup """
    # for now, we simply execute CPIA events by name
    def __init__(self, scriptText):
        self.scriptLines = scriptText.split(',')
        self.line = 0
        self.blockEvents = getAllBlockEvents()

    def execute(self):
        # execute a line from the script, returning True when done
        nextLine = self.scriptLines[self.line].strip()
        self.line += 1

        # simply post the event named in the script
        mainViewRoot = Globals.mainViewRoot
        logger.info("Script execution of '%s'." % nextLine)
        # try to find this command in the blockEvents list
        command = nextLine.upper()
        for anEvent in self.blockEvents:
            try:
                eventName = anEvent.blockName
            except AttributeError:
                try:
                    eventName = anEvent.itsName
                except AttributeError:
                    pass
            if eventName and eventName.upper() == command:
                mainViewRoot.post (anEvent, {})
                break
        else:
            logger.info("Command '%s' not found." % nextLine)
        done = self.line >= len(self.scriptLines)
        if done:
            logger.info("Script completed execution normally")
        return done
