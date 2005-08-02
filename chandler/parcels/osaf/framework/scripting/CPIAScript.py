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
import ScriptingGlobalFunctions
from application import schema
import wx
import TestAppLib

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
    
def GetDialogScript(aView):
    # return the text of the special DialogScript, or a suitable default if there is none.
    dialogScript = schema.ns('osaf.framework.scripting', aView).DialogScript
    return dialogScript.bodyString

def RunDialogScript(theScriptString, aView):
    # set up the special DialogScript, and run it.
    dialogScript = schema.ns('osaf.framework.scripting', aView).DialogScript
    dialogScript.bodyString = theScriptString
    dialogScript.execute()

def HotkeyScript(event, view):
    """
    Check if the event is a hot key to run a script.
    Returns True if it does trigger a script to run, False otherwise.
    """
    def startsWithScriptNumber(candidateString, numberedStringToMatch):
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

    keycode = event.GetKeyCode()
    # for now, we just allow function keys to be hot keys.
    if keycode >= wx.WXK_F1 and keycode <= wx.WXK_F24:
        # try to find the corresponding Note
        targetScriptNameStart = "Script F%s" % str(keycode-wx.WXK_F1+1)
        for aNote in Notes.Note.iterItems(view):
            try:
                noteTitle = aNote.about
            except AttributeError:
                continue
            else:
                if startsWithScriptNumber(noteTitle, targetScriptNameStart):
                    # make sure it's not a longer number than we're looking for
                    try:
                        nextString = noteTitle[len(targetScriptNameStart)]
                    except IndexError:
                        pass
                    else:
                        if nextString.isdigit():
                            continue
                    # get the body and execute it if we can
                    try:
                        scriptString = aNote.bodyString
                    except AttributeError:
                        continue
                    else:
                        fKeyScript = ExecutableScript(scriptString, view=view)
                        fKeyScript.execute()
                        return True

        # maybe we have an existing script?
        for aScript in Script.iterItems(view):
            if startsWithScriptNumber(aScript.displayName, targetScriptNameStart):          
                aScript.execute()
                return True

    # not a hot key
    return False

def RunStartupScript(view):
    script = None
    if not hasattr(Globals, 'CheckedStartupScripts'):
        Globals.CheckedStartupScripts = True
        if Globals.options.script:
            script = ExecutableScript(Globals.options.script, view)
        if Globals.options.scriptFile:
            scriptFile = ScriptFile(Globals.options.scriptFile)
            if scriptFile:
                script = ExecutableScript(scriptFile, view)
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

    def execute(self):
        executable = ExecutableScript(self.bodyString, self.itsView)
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
        # compile the code
        if __debug__:
            debugFile = open('UserScript.py', 'wt')
            try:
                # to be nice to debuggers, we write the code to a file so it can be located
                # in the case of an error
                debugFile.write(self.scriptString)
            finally:
                debugFile.close()
        self.scriptCode = compile(self.scriptString, 'UserScript.py', 'exec')

        # next, build a dictionary of names that are predefined
        builtIns = {}

        # For debugging, reload modules containing script functions
        # @@@DLD TBD - remove
        reload(ScriptingGlobalFunctions)
        reload(TestAppLib)

        # add all the known BlockEvents as builtin functions
        self._BindCPIAEvents(self.itsView, builtIns)

        # add all the known ContentItem sub-Kinds
        kindKind = self.itsView.findPath('//Schema/Core/Kind')
        allKinds = ItemQuery.KindQuery().run([kindKind])
        contentItemKind = ContentModel.ContentItem.getKind (self.itsView)
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
            self.FindAndPostBlockEvent(eventName, argDict, keys)
        # return the template, customized for this event
        return ScriptInvokedBlockEvent

    """
    We need to find the best BlockEvent at runtime on each invokation,
    because the BlockEvents come and go from the soup as UI portions
    are rendered and unrendered.  The best BlockEvent is the one copied
    into the soup and attached to rendered blocks that were also copied.
    """
    def FindAndPostBlockEvent(self, eventName, argDict, keys):
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
        Globals.mainViewRoot.post(best, argDict)
        # seems like a good time to let the Application get some time
        wx.GetApp().Yield()

    def _inUserData(self, item):
        try:
            return str(item.itsPath).startswith('//userdata/')
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

class CPIAPimModule(object):
    """ 
    Acts as the 'pim' module with attributes
    for the classes that the Personal Information Manager
    defines.  E.g. Note, Task, etc.
    """
    def AddAttr(self, attr, value):
        setattr(self, attr, value)

