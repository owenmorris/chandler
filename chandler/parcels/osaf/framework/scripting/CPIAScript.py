__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import logging, types
import repository.item.Query as ItemQuery
import osaf.framework.blocks.Block as Block
import osaf.contentmodel.Notes as Notes
import osaf.contentmodel.ContentModel as ContentModel
import KindShorthand
import ScriptingGlobalFunctions
from application import schema
import wx

logger = logging.getLogger('CPIA Script')
logger.setLevel(logging.INFO)

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

    * How does the Pass/Fail result from the TestScript get back
        to SQA?  Just end up raising the exception?  Make sure
        the startup test failure won't hang T-Box.
    """
    newScript = ExecutableScript(scriptText, view)
    return newScript.execute()
    
_dialogScriptName = "DialogScript"
_defaultDialogScript = "New(); About()"

def GetDialogScript(aView):
    # return the text of the special DialogScript, or a suitable default if there is none.
    for aScript in Script.iterItems(aView):
        if aScript.displayName == _dialogScriptName:
            previousScriptString = aScript.GetScriptString()
            break
    else:
        previousScriptString = _defaultDialogScript
    return previousScriptString

def RunDialogScript(theScriptString, aView):
    # set up the special DialogScript, and run it.
    dialogScript = GetSpecialScript(theScriptString, aView, _dialogScriptName)
    dialogScript.execute()

def GetSpecialScript(theScriptString, aView, scriptName):
    # get the special DialogScript, or if not found create a new one.
    for aScript in Script.iterItems(aView):
        if aScript.displayName == scriptName:
            aScript.SetScriptString(theScriptString)
            break
    else:
        aScript = Script(scriptName)
        aScript.SetScriptString(theScriptString)
    return aScript

def HotkeyScript(event, view):
    """
    Check if the event is a hot key to run a script.
    Returns True if it does trigger a script to run, False otherwise.
    """
    keycode = event.GetKeyCode()
    # for now, we just allow function keys to be hot keys.
    if keycode >= wx.WXK_F1 and keycode <= wx.WXK_F24:
        # try to find the corresponding Note
        targetScriptName = "Script F%s" % str(keycode-wx.WXK_F1+1)
        for aNote in Notes.Note.iterItems(view):
            if targetScriptName == aNote.about:
                scriptString = aNote.bodyString
                fKeyScript = ExecutableScript(scriptString, view=view)
                fKeyScript.execute()
                return True

        # maybe we have an existing script?
        for aScript in Script.iterItems(view):
            if targetScriptName == aScript.displayName:
                aScript.execute()
                return True

    # not a hot key
    return False

def RunStartupScript(view):
    script = None
    if not hasattr(Globals, 'CheckedStartupScripts'):
        if Globals.options.script:
            script = ExecutableScript(Globals.options.script, view)
        if Globals.options.scriptFile:
            scriptFile = ScriptFile(Globals.options.scriptFile)
            if scriptFile:
                script = ExecutableScript(scriptFile, view)
        Globals.CheckedStartupScripts = True
    if script:
        script.execute()

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


class Script(ContentModel.ContentItem):
    """ Persistent Script Item, to be executed. """
    schema.kindInfo(displayName="Script", displayAttribute="displayName")

    def __init__(self, name=_('untitled'), parent=None, kind=None):
        super(Script, self).__init__(name, parent, kind, displayName=name)

    # use the bodyString property to get and set the body attribute
    # from string data
    def GetScriptString(self):
        return self.bodyString

    def SetScriptString(self, scriptString):
        self.bodyString = scriptString

    def execute(self):
        executable = ExecutableScript(self.GetScriptString(), self.itsView)
        executable.execute()

class ExecutableScript(object):
    """ Script to be executed. """

    def __init__(self, scriptText, view):
        self.scriptString = scriptText
        self.scriptCode = None
        self.itsView = view

    def execute(self):
        """
        Explore python execution of scripts!
        There are currently some issues which I'm investigating:
        * I may need to implement threading to keep the wx App
           happily processing events in cases like Chandler
           moving to the background during script execution.
        * Is my use of wx.App.Yeild correct?  Dangerous?
        * Can I use __getattr__ for my global properties?
            Send email to pje about how to make an attribute call code.
        """
        # first compile the code
        self.scriptCode = compile(self.scriptString, '<user script>', 'exec')

        # next, build a dictionary of names that are predefined
        builtIns = {}

        # For debugging, reload ScriptingGlobalFunctions and KindShorthand
        # @@@DLD TBD - remove
        reload(ScriptingGlobalFunctions)
        reload(KindShorthand)

        # add all the known BlockEvents as builtin functions
        self._BindCPIAEvents(self.itsView, builtIns)

        # add all the known ContentItem sub-Kinds
        kindKind = self.itsView.findPath('//Schema/Core/Kind')
        allKinds = ItemQuery.KindQuery().run([kindKind])
        contentItemKind = ContentModel.ContentItem.getKind (self.itsView)
        for aKind in allKinds:
            if aKind.isKindOf (contentItemKind):
                self._AddKindShorthand(builtIns, aKind)
                
        # Add Script, Item, BlockEvent and Block kind/shorthands
        itemKind = self.itsView.findPath('//Schema/Core/Item')
        self._AddKindShorthand(builtIns, itemKind)
        scriptKind = self.itsView.findPath('//parcels/osaf/framework/scripting/Script')
        self._AddKindShorthand(builtIns, scriptKind)
        blockEventKind = self.itsView.findPath('//parcels/osaf/framework/blocks/BlockEvent')
        self._AddKindShorthand(builtIns, blockEventKind)
        blockKind = self.itsView.findPath('//parcels/osaf/framework/blocks/Block')
        self._AddKindShorthand(builtIns, blockKind)

        # add my Custom global functions
        for aFunc in dir(ScriptingGlobalFunctions):
            if aFunc[0] != '_':
                builtIns[aFunc] = getattr(ScriptingGlobalFunctions, aFunc)

        # add Globals
        builtIns['Globals'] = Globals

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

    def _AddKindShorthand(self, builtIns, theKind):
        if not theKind:
            return
        kindName = theKind.itsName
        builtIns[kindName] = theKind.getItemClass()

        # add a shorthand dictionary for the kind (ending in 's', e.g. Note-->Notes)
        dict = KindShorthand.KindShorthand(theKind)
        builtIns['%ss' % kindName] = dict

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
        def BlockEventCallableClosure(argDict={}, _eventName=eventName, _view=view, **keys):
            # merge the named parameters, into the dictionary positional arg
            self.FindAndPostBlockEvent(_eventName, _view, argDict, keys)
        # return the template, customized for this event
        return BlockEventCallableClosure

    """
    We need to find the best BlockEvent at runtime on each invokation,
    because the BlockEvents come and go from the soup as UI portions
    are rendered and unrendered.  The best BlockEvent is the one copied
    into the soup and attached to rendered blocks that were also copied.
    """
    def FindAndPostBlockEvent(self, eventName, view, argDict, keys):
        # Find the best BlockEvent to use, by name.  Then post that event.
        # Also, call Yield() on the application, so it gets some time during
        #   script execution.
        best = self.FindBestBlockEvent(eventName, view)
        try:
            argDict.update(keys)
        except AttributeError:
            # make sure the first parameter was a dictionary, or give a friendly error
            logger.error("BlockEvents only support one positional parameter - a dictionary")
            # the eventName parameter may have gotten clobbered too.  Use it if we can.
            if best is not None:
                logger.error("  in function %s" % eventName)
            return
        Globals.mainViewRoot.post(best, argDict)
        # seems like a good time to let the Application get some time
        wx.GetApp().Yield()

    def FindBestBlockEvent(self, eventName, view):
        # Find the best BlockEvent to use, by name.  
        userCandidate = candidate = None
        for anEvent in Block.BlockEvent.iterItems(view):
            if self._BlockEventName(anEvent) == eventName:
                candidate = anEvent
                if self._inUserData(anEvent):
                    if userCandidate:
                        logger.warning("Duplicate events in user data for %s" % eventName)
                    else:
                        userCandidate = anEvent
        if userCandidate:
            return userCandidate
        logger.warning("Can't find event %s in user data - block not rendered." % eventName)
        return candidate

    def _inUserData(self, item):
        try:
            return str(item.itsPath).find('//userdata/') == 0
        except AttributeError:
            return False

    def _BlockEventName(self, event):
        try:
            name = event.blockName
        except AttributeError:
            try:
                name = event.itsName
            except AttributeError:
                name = None
        return name

