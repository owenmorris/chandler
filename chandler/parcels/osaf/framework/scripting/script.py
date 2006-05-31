__copyright__ = "Copyright (c) 2005-2006 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx

import hotshot
from hotshot import stats

from application import schema, Globals

from osaf import pim
from osaf import messages
from i18n import OSAFMessageFactory as _
from datetime import datetime
import os, sys

"""
This file provides the most basic scripting support. It defines what a
script is, and provides some basic functions for running them.
"""

__all__ = [
    'cats_profiler', 'hotkey_script',
    'Script', 'script_file'
]

class Script(pim.ContentItem):
    """ Persistent Script Item, to be executed. """
    schema.kindInfo(displayName=_(u"Script"), displayAttribute="displayName")
    lastRan = schema.One(schema.DateTime, displayName = _(u"last ran"))
    fkey = schema.One(schema.Text, initialValue = u'')
    test = schema.One(schema.Boolean, initialValue = False)

    filePath = schema.One(schema.Text, initialValue = u'')
    lastSync = schema.One(schema.DateTime)

    # redirections

    about = schema.One(redirectTo = 'displayName')
    who = schema.One(redirectTo = 'creator')
    date = schema.One(redirectTo = 'lastRan')

    def __init__(self, itsName=None, itsParent=None, itsKind=None, itsView=None,
                 body=None, *args, **keys):
        defaultName = messages.UNTITLED
        if itsName is not None:
            defaultName = unicode(itsName)
        keys.setdefault('displayName', defaultName)
        super(Script, self).__init__(
            itsName, itsParent, itsKind, itsView, *args, **keys
        )
        self.lastRan = datetime.now()
        self.lastSync = self.lastRan
        if body is not None:
            self.body = body # property for the body LOB
        self.private = False # can share scripts

    def execute(self):
        self.sync_file_with_model()
        self.lastRan = datetime.now()

        # this is a nasty hack to import from proxy.py.
        # This is the only way that scripts know about app_ns
        # and other chandler-specific proxies
        from proxy import app_ns
        run_script_with_symbols(self.body, fileName=self.filePath,
                                builtIns=dict(app_ns=app_ns))

    def set_body_quietly(self, newValue):
        if newValue != self.body:
            oldQuiet = getattr(self, '_change_quietly', False)
            self._change_quietly = True
            self.body = newValue
            self._change_quietly = oldQuiet

    def onValueChanged(self, name):
        if name == 'body':
            self.model_data_changed()

    def model_data_changed(self):
        if self.filePath and not getattr(self, '_change_quietly', False):
            self.modelModTime = datetime.now()

    def sync_file_with_model(self, preferFile=False):
        """
        Synchronize file and model - which ever is latest wins, with
        conflict dialogs possible if both have changed since the last sync.
        """
        if self.filePath and not getattr(self, '_change_quietly', False):
            writeFile = False
            # make sure we have a model modification time
            if not hasattr(self, 'modelModTime'):
                self.modelModTime = self.lastSync
            # get modification date for the file
            try:
                fileModTime = datetime.fromtimestamp(os.stat(self.filePath)[8])
            except OSError:
                fileModTime = self.lastSync
                writeFile = True
            if preferFile or fileModTime > self.modelModTime:
                self.set_body_quietly(self.file_contents(self.filePath))
            elif writeFile or fileModTime < self.modelModTime:
                # model is newer
                latest = self.modelModTime
                if fileModTime > self.lastSync:
                    caption = _(u"Overwrite script file?")
                    msg = _(u"The file associated with this script has been changed,"
                            "\nbut those changes are older than your recent edits.\n\n"
                            "Do you want to overwrite those file changes with your\n"
                            "recent edits of this script?")
                    if not Util.yesNo(wx.GetApp().mainFrame, caption, msg):
                        return
                self.write_file(self.body)
                fileModTime = datetime.fromtimestamp(os.stat(self.filePath)[8])
            # now the file and model match
            self.lastSync = self.modelModTime = fileModTime

    def file_contents(self, filePath):
        """
        return the contents of our script file
        """
        scriptFile = open(filePath, 'rt')
        try:
            scriptText = scriptFile.read(-1)
        finally:
            scriptFile.close()
        return scriptText

    def write_file(self, scriptText):
        """
        write the contents of our script file into the file
        """
        scriptFile = open(self.filePath, 'wt')
        try:
            scriptText = scriptFile.write(scriptText)
        finally:
            scriptFile.close()

    def set_file(self, fileName, siblingPath):
        #Convert fileName with the system charset encoding
        #to bytes to prevent the join function from trying to downcast
        #the unicode fileName to ascii

        if not isinstance(fileName, unicode):
            fileName = unicode(fileName, "utf8")

        fileName = fileName.encode(sys.getfilesystemencoding())

        #Convert the filePath bytes to unicode for storage
        filePath = unicode(os.path.join(os.path.dirname(siblingPath), fileName), sys.getfilesystemencoding())
        self.body = self.file_contents(filePath)
        self.filePath = filePath


"""
Handle running a Script.
"""
def run_script_with_symbols(scriptText, fileName=u"", profiler=None, builtIns=None):
    """
    exec the supplied script providing everything from __all__ plus whatever
    globals got passed in.
    """
    assert len(scriptText) > 0, "Empty script"
    assert fileName is not None

    if profiler:
        profiler.stop() # start with the profile turned off

    if not isinstance(fileName, unicode):
        fileName = unicode(fileName, "utf8")

    if not isinstance(scriptText, unicode):
        scriptText = unicode(scriptText, "utf8")

    scriptText = scriptText.encode(sys.getfilesystemencoding())
    fileName = fileName.encode(sys.getfilesystemencoding())

    # compile the code
    scriptCode = compile(scriptText, fileName, 'exec')

    # next, build a dictionary of names that are predefined
    if builtIns is None:
        builtIns = {}

    for attr in __all__:
        builtIns[attr] = globals()[attr]

    # Protect against scripts that don't stop, needed especially by 
    # automated tests.
    scriptTimeout = int(getattr(Globals.options, 'scriptTimeout', 0))
    if scriptTimeout > 0:
        try:
            from signal import signal, alarm, SIGALRM
        except ImportError:
            pass    # no alarm on Windows  :(
        else:
            def timeout(*args):
                sys.exit('Timeout error: Script did not finish within %d seconds.' % scriptTimeout)
            signal(SIGALRM, timeout)
            alarm(scriptTimeout)

    # now run that script in our predefined scope
    exec scriptCode in builtIns

def hotkey_script(event, view):
    """
    Check if the event is a hot key to run a script.
    Returns True if it does trigger a script to run, False otherwise.
    """
    keycode = event.GetKeyCode()
    # for now, we just allow function keys to be hot keys.
    if (wx.WXK_F1 <= keycode <= wx.WXK_F24
            and not event.AltDown()
            and not event.CmdDown()
            and not event.ControlDown()
            and not event.MetaDown()
            and not event.ShiftDown()):
        # try to find the corresponding Script
        targetFKey = _(u"F%(FunctionKeyNumber)s") % {'FunctionKeyNumber':unicode(keycode-wx.WXK_F1+1)}

        # maybe we have an existing script?
        script = _findHotKeyScript(targetFKey, view)
        if script:
            wx.CallAfter(script.execute)
            return True

    # not a hot key
    return False

def _findHotKeyScript(targetFKey, view):
    # find a script that starts with the given name
    for aScript in Script.iterItems(view):
        if aScript.fkey == targetFKey:
            return aScript
    return None

def run_startup_script_with_symbols(view, builtIns):
    global global_cats_profiler
    if Globals.options.testScripts:
        try:
            for aScript in Script.iterItems(view):
                if aScript.test:
                    aScript.execute()
        finally:
            # run the cleanup script
            schema.ns('osaf.app', view).CleanupAfterTests.execute()

    fileName = Globals.options.scriptFile
    if fileName:
        scriptFileText = script_file(fileName)
        if scriptFileText:
            # check if we should turn on the profiler for this script
            if Globals.options.catsProfile:
                profiler = hotshot.Profile(Globals.options.catsProfile)
                global_cats_profiler = profiler
                profiler.runcall(run_script_with_symbols,
                                 scriptFileText,
                                 fileName=fileName, 
                                 profiler=profiler,
                                 builtIns=builtIns)
                profiler.close()
                global_cats_profiler = None
            else:
                run_script_with_symbols(scriptFileText, fileName = fileName,
                                        builtIns=builtIns)
                
global_cats_profiler = None # remember the CATS profiler here

def cats_profiler():
    return global_cats_profiler

def script_file(fileName, siblingPath=None):
    """
    Return the script from the file, given a file name
    and a path to a sibling file.
    """

    if not isinstance(fileName, unicode):
        fileName = unicode(fileName, "utf8")

    #Encode the unicode filename to the system character set encoding
    fileName = fileName.encode(sys.getfilesystemencoding())

    if siblingPath is not None:
        fileName = os.path.join(os.path.dirname(siblingPath), fileName)
    # read the script from a file, and return it.
    scriptFile = open(fileName, 'rt')
    try:
        scriptText = scriptFile.read(-1)
    finally:
        scriptFile.close()
    return scriptText
