__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import logging, types
import repository.item.Query as ItemQuery
import osaf.framework.blocks.Block as Block
import ScriptingGlobalFunctions
from application import schema
from osaf import pim
from datetime import datetime
import wx
from i18n import OSAFMessageFactory as _

__parcel__="osaf.framework.scripting"

logger = logging.getLogger(__name__)

__all__ = [
    'EventTiming', 'FindAndPostBlockEvent', 'HotkeyScript', 
    'RunScript', 'RunStartupScript', 'Script', 'ScriptFile'
]

"""
Handle running a Script.
"""
def RunScript(scriptText, view):
    """
    Create a script from text, and run it.
    Overall plan:
    * Some special scripts are known:
        - TestScript - set up to test Chandler
        - DialogScript - run from the dialog
    * Change --script parameter to something else, to --startupTest
       to run the special test script at startup.
    """
    # update our parcel's NewRunScript Script item with this text
    scriptParcel = schema.ns('osaf.framework.scripting', view).parcel
    newScript = Script.update(scriptParcel, name="NewRunScript", bodyString=scriptText)
    return newScript.execute()
    
def HotkeyScript(event, view):
    """
    Check if the event is a hot key to run a script.
    Returns True if it does trigger a script to run, False otherwise.
    """
    keycode = event.GetKeyCode()
    # for now, we just allow function keys to be hot keys.
    if keycode >= wx.WXK_F1 and keycode <= wx.WXK_F24:
        # try to find the corresponding Note
        targetScriptNameStart = "Script F%s" % str(keycode-wx.WXK_F1+1)

        # maybe we have an existing script?
        script = _findScriptStartingWith(targetScriptNameStart, view)
        if script:          
            wx.CallAfter(script.execute)
            return True

    # not a hot key
    return False

def _findScriptStartingWith(targetScriptNameStart, view):
    # find a script that starts with the given name
    for aScript in Script.iterItems(view):
        if _startsWithScriptNumber(aScript.displayName, targetScriptNameStart):          
            return aScript
    return None

def _startsWithScriptNumber(candidateString, numberedStringToMatch):
    # returns True if the candidate starts with the
    # numberedStringToMatch.  Checks that the candidate
    # isn't really a larger number by checking for 
    # following digits.
    if candidateString.startswith(numberedStringToMatch):
        # make sure it's not a longer number than we're looking for
        try:
            nextString = candidateString[len(numberedStringToMatch)]
        except IndexError:
            return True
        if nextString.isdigit():
            return False
        return True
    return False

def RunStartupScript(view):
    script = None
    fileName = ""
    if Globals.options.testScript:
        script = _findScriptStartingWith("Script F1", view)
    if Globals.options.scriptFile:
        scriptFileText = ScriptFile(Globals.options.scriptFile)
        if scriptFileText:
            scriptParcel = schema.ns('osaf.framework.scripting', view).parcel
            script = Script.update(scriptParcel, name="StartupScriptFile", bodyString=scriptFileText)
            fileName=Globals.options.scriptFile
    if script:
        script.execute(fileName=fileName)

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

class Script(pim.ContentItem):
    """ Persistent Script Item, to be executed. """
    schema.kindInfo(displayName="Script", displayAttribute="displayName")
    lastRan = schema.One(schema.DateTime, displayName = _(u'last ran'))

    # redirections

    about = schema.One(redirectTo = 'displayName')
    who = schema.One(redirectTo = 'creator')
    date = schema.One(redirectTo = 'lastRan')

    def __init__(self, name=None, parent=None, kind=None, 
                 bodyString=None, creator=None):
        super(Script, self).__init__(name, parent, kind, displayName=name)
        if name is None:
            self.displayName = _('Untitled')
        self.lastRan = datetime.now()
        if bodyString is not None:
            self.bodyString = bodyString
        if creator is not None:
            self.creator = creator
        self.isPrivate = True

    def isAttributeModifiable(self, attribute):
        return True

    defaultFileName = 'UserScript.py'

    def execute(self, fileName=""):
        assert len(self.bodyString) > 0, "Empty script body"

        self.lastRan = datetime.now()

        # compile the code
        if __debug__ and not fileName:
            fileName = self.defaultFileName
            debugFile = open(self.defaultFileName, 'wt')
            try:
                # to be nice to debuggers, we write the code to a file so it can be located
                # in the case of an error
                debugFile.write(self.bodyString)
            finally:
                debugFile.close()

        self.scriptCode = compile(self.bodyString, fileName, 'exec')

        # next, build a dictionary of names that are predefined
        builtIns = {}

        # For debugging, reload modules containing script functions
        # @@@DLD TBD - remove
        reload(ScriptingGlobalFunctions)

        # add all the known BlockEvents as builtin functions
        self._BindCPIAEvents(self.itsView, builtIns)

        # add all the known ContentItem sub-Kinds
        kindKind = self.itsView.findPath('//Schema/Core/Kind')
        allKinds = ItemQuery.KindQuery().run([kindKind])
        contentItemKind = pim.ContentItem.getKind (self.itsView)
        for aKind in allKinds:
            if aKind.isKindOf (contentItemKind):
                self._AddPimClass(builtIns, aKind)
                
        # Add Script, Item, BlockEvent and Block kind/shorthands
        itemKind = self.itsView.findPath('//Schema/Core/Item')
        self._AddPimClass(builtIns, itemKind)
        scriptKind = self.itsView.findPath('//parcels/osaf/framework/scripting/Script')
        self._AddPimClass(builtIns, scriptKind)
        blockEventKind = self.itsView.findPath('//parcels/osaf/framework/blocks/BlockEvent')
        self._AddPimClass(builtIns, blockEventKind)
        blockKind = self.itsView.findPath('//parcels/osaf/framework/blocks/Block')
        self._AddPimClass(builtIns, blockKind)

        # add my Custom global functions
        for aFunc in dir(ScriptingGlobalFunctions):
            if aFunc[0] != '_':
                builtIns[aFunc] = getattr(ScriptingGlobalFunctions, aFunc)

        # add Globals
        builtIns['Globals'] = Globals
        
        # add the current view      
        builtIns['__view__'] = self.itsView

        # add the event timing object      
        builtIns['EventTiming'] = EventTiming

        # now run that script in our predefined scope
        try:
            exec self.scriptCode in builtIns, {}
        except Exception:
            self.ExceptionMessage('Error in script:')
            raise

    def ExceptionMessage(self, message):
        import sys, traceback
        type, value, stack = sys.exc_info()
        formattedBacktrace = "".join (traceback.format_exception (type, value, stack, 5))
        message += "\nHere are the bottom 5 frames of the stack:\n%s" % formattedBacktrace
        logger.exception( message )
        return message

    def _AddPimClass(self, builtIns, theKind):
        if not theKind:
            return
        kindName = theKind.itsName
        try:
            pim = builtIns['pim']
        except KeyError:
            pim = CPIAPimModule()
            builtIns['pim'] = pim
        pim.AddAttr(kindName, theKind.getItemClass())

    def _BindCPIAEvents(self, view, dict):
        # add all the known BlockEvents as builtin functions
        # iterate through all events
        for anEvent in Block.BlockEvent.iterItems(view):
            eventName = self._BlockEventName(anEvent)
            if eventName:
                # add the entry
                dict[eventName] = self._make_BlockEventCallable(eventName, view)

    # Factory method for functions for each BlockEvent
    # Each function can take a single dictionary argument, or keyword arguments
    def _make_BlockEventCallable(self, eventName, view):
        # This is the template for a callable function for the given event
        # Copies of this function are invoked by user scripts for BlockEvent commands.
        def ScriptInvokedBlockEvent(argDict={}, **keys):
            # merge the named parameters, into the dictionary positional arg
            return FindAndPostBlockEvent(eventName, argDict, keys)
        # return the template, customized for this event
        return ScriptInvokedBlockEvent

    def _BlockEventName(self, event):
        try:
            name = event.blockName
        except AttributeError:
            try:
                name = event.itsName
            except AttributeError:
                name = None
        return name

"""
We need to find the best BlockEvent at runtime on each invokation,
because the BlockEvents come and go from the soup as UI portions
are rendered and unrendered.  The best BlockEvent is the one copied
into the soup and attached to rendered blocks that were also copied.
"""
def FindAndPostBlockEvent(eventName, argDict, keys):
    # Find the BlockEvent to use by name.  Then post that event.
    # Also, call Yield() on the application, so it gets some time during
    #   script execution.
    best = Block.Block.findBlockEventByName(eventName)
    try:
        argDict.update(keys)
    except AttributeError:
        # make sure the first parameter was a dictionary, or give a friendly error
        message = "BlockEvents may only have one positional parameter - a dict"
        raise AttributeError, message
    # remember timing information
    startTime = EventTiming.startTimer()
    # post the event
    result = Globals.mainViewRoot.post(best, argDict)
    # finish timing
    EventTiming.endTimer(startTime, eventName)
    # let the Application get some time
    wx.GetApp().Yield()
    return result

class CPIAPimModule(object):
    """ 
    Acts as the 'pim' module with attributes
    for the classes that the Personal Information Manager
    defines.  E.g. Note, Task, etc.
    """
    def AddAttr(self, attr, value):
        setattr(self, attr, value)

class CPIAEventTiming(dict):
    """
    dictionary of event timings for events that have
    been sent by CPIA script since this dictionary was reset.
    Use clear() to reset timings.
    """
    def startTimer(self):
        return datetime.now()

    def endTimer(self, startTime, eventName):
        self.setdefault(eventName, []).append(datetime.now()-startTime)
    
    def timingStrings(self):
        strTimings = {}
        for eName, timingList in self.iteritems():
            strList = []
            for timing in timingList:
                strList.append(str(timing))
            strTimings[eName] = strList
        return strTimings

# global to use for event timing
EventTiming = CPIAEventTiming()

