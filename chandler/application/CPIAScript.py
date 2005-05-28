__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import Globals, logging

logger = logging.getLogger('CPIA Script')
logger.setLevel(logging.INFO)

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

class CPIAScript:
    """ Script to be executed at Startup """
    # for now, we simply execute CPIA events by name
    def __init__(self, scriptText):
        self.scriptLines = scriptText.splitlines()
        self.line = 0

    def execute(self):
        # execute a line from the script, returning True when done
        nextLine = self.scriptLines[self.line]
        self.line += 1

        # simply post the event named in the script
        mainViewRoot = Globals.mainViewRoot
        logger.info("Script execution of '%s'." % nextLine)
        mainViewRoot.postEventByName (nextLine, {})
        done = self.line >= len(self.scriptLines)
        if done:
            logger.info("Script completed execution normally")
        return done
