__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import logging, types
import repository.item.Query as ItemQuery
import osaf.framework.blocks.Block as Block
import osaf.contentmodel.Notes as Notes
import wx

logger = logging.getLogger('CPIA Script')
logger.setLevel(logging.INFO)

# Flag that a ReloadParcels can reload this python module
AcceptsReload = True

"""
Handle running a Script.
"""
def RunScript(script=None):
    """
    Run the current script.
    If no script is specified, pick up the global script option, 
          and create a CPIA Script from that text.
    @@@DLD - stop using globals; run whatever the repository says is the current script
    """
    
    if script is None:
        scriptArg = GetGlobalScriptArg()
        if scriptArg:
            Globals.currentCPIAScript = scriptArg
    elif isinstance(script, types.StringType):
        Globals.currentCPIAScript = CPIAScript(script)
    else:
        Globals.currentCPIAScript = script

    # if we have a script, execucte one of it's commands and return
    try:
        curScript = Globals.currentCPIAScript
    except AttributeError:
        pass
    else:
        scriptDone = True
        try:
            scriptDone = curScript.execute()
        finally:
            if scriptDone:
                del Globals.currentCPIAScript # done

def GetGlobalScriptArg():
    script = None
    if not hasattr(Globals, 'CheckedStartupScripts'):
        if Globals.options.script:
            script = CPIAScript(Globals.options.script)
        if Globals.options.scriptFile:
            scriptFile = ScriptFile(Globals.options.scriptFile)
            if scriptFile:
                script = CPIAScript(scriptFile)
        Globals.CheckedStartupScripts = True
    return script

def ScriptFile(fileName):
    # read the script from a file, and return it.
    scriptText = None
    try:
        scriptFile = open(fileName, 'rt')
        try:
            scriptText = scriptFile.read(-1)
        finally:
            scriptFile.close()
    except IOError:
        logger.warning("Unable to open script file '%s'" % fileName)
    return scriptText
    
def HotkeyScript(event):
    """
    Check if the event is a hot key to run a script.
    Returns True if it does trigger a script to run, False otherwise.
    """
    keycode = event.GetKeyCode()
    # for now, we just allow function keys to be hot keys.
    if keycode >= wx.WXK_F1 and keycode <= wx.WXK_F24:
        # try to find the corresponding script
        targetScriptName = "Script F%s" % str(keycode-wx.WXK_F1+1)
        for note in Notes.Note.iterItems(Globals.mainViewRoot.itsView):
            # is there a Note named "Script Fn"?
            try:
                scriptName = str(note.displayName)
            except AttributeError:
                continue
            if scriptName == targetScriptName:
                # make a script object from the body, and run it.
                scriptString = note.body.getReader().read()
                RunScript(CPIAScript(scriptString))
                return True
    return False

class CPIAScript:
    """ Script to be executed. """
    def __init__(self, scriptText):
        # split the script into separate lines for exectuion
        newText = scriptText.replace(';', '\n') # map ';' to newline
        self.scriptLines = newText.split('\n') 
        self.line = 0
        self.blockEvents = self.getAllBlockEvents()
        self.reentrancyDepth = 0
        self.atEnd = False

    def getAllBlockEvents(self):
        events = []
        for i in Block.BlockEvent.iterItems(Globals.mainViewRoot.itsView):
            events.append(i)
        return events

    def execute(self):
        # execute a line from the script, returning True when done
        if not self.atEnd:
            nextLine = self.scriptLines[self.line].strip()
            self.line += 1
            self.atEnd = self.line == len(self.scriptLines)
    
            # simply post the event named in the script
            if nextLine:
                mainViewRoot = Globals.mainViewRoot
                logger.info("Script execution of '%s'." % nextLine)
                # try to find this command in the blockEvents list
                for anEvent in self.blockEvents:
                    eventName = self.eventName(anEvent)
                    if eventName and eventName == nextLine:
                        self.reentrancyDepth += 1
                        try:
                            mainViewRoot.post (anEvent, {})
                        except:
                            logger.error("Exception during script execution of %s" % nextLine)
                        self.reentrancyDepth -= 1
                        break
                else:
                    logger.info("Command '%s' not found." % nextLine)
            
        done = self.atEnd and self.reentrancyDepth == 0
        if done:
            logger.info("Script completed execution normally")
        return done

    def eventName(self, event):
        try:
            name = event.blockName
        except AttributeError:
            try:
                name = event.itsName
            except AttributeError:
                name = None
        return name
        
        
