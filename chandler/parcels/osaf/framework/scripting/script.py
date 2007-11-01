#   Copyright (c) 2005-2007 Open Source Applications Foundation
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


import wx

import hotshot

from application import schema, Globals

from osaf import pim
from osaf import messages
from i18n import ChandlerMessageFactory as _
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
    lastRan = schema.One(schema.DateTime)
    fkey = schema.One(schema.Text, initialValue = u'')
    test = schema.One(schema.Boolean, initialValue = False)

    filePath = schema.One(schema.Text, initialValue = u'')
    lastSync = schema.One(schema.DateTime)

    schema.initialValues(
        private = lambda self: False,    # can share scripts
        displayName = lambda self:
            # XXX check if itsName is a UUID?
            unicode(self.itsName) if self.itsName else messages.UNTITLED,
    )

    def __setup__(self):
        self.lastRan = self.lastSync = datetime.now()

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

    @schema.observer(pim.ContentItem.body)
    def onBodyChanged(self, op, name):
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
                if fileModTime > self.lastSync:
                    msg = _(u"The file associated with this script has changes that are older than your recent edits.\n\nDo you want to overwrite the older changes?")
                    caption = _(u"Overwrite Script File?")
                    if wx.MessageBox(msg, caption, style = wx.YES_NO,
                                     parent = wx.GetApp().mainFrame) == wx.NO:
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
        #Convert fileName to utf8 encoding
        #to bytes to prevent the join function from trying to downcast
        #the unicode fileName to ascii

        if isinstance(fileName, unicode):
            fileName = fileName.encode('utf8')

        #Convert the filePath bytes to unicode for storage
        filePath = unicode(os.path.join(os.path.dirname(siblingPath), \
                           fileName), sys.getfilesystemencoding())
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

    if isinstance(fileName, unicode):
        fileName = fileName.encode('utf8')

    if isinstance(scriptText, unicode):
        scriptText = scriptText.encode('utf8')

    # compile the code
    scriptCode = compile(scriptText, fileName, 'exec')

    # next, build a dictionary of names that are predefined
    if builtIns is None:
        builtIns = {}

    for attr in __all__:
        builtIns[attr] = globals()[attr]

    # now run that script in our predefined scope
    try:
        exec scriptCode in builtIns
    except:
        wx.GetApp().exitValue = 1
        raise            


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
        targetFKey = u"F%(FunctionKeyNumber)s" % {'FunctionKeyNumber':unicode(keycode-wx.WXK_F1+1)}

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
    # On Linux at the time we reach this point the screen has not
    # been updated, i.e. drawn -- and when the screen isn't drawn
    # the focus can't be set to a widget that hasn't been drawn
    # so we explicitely update the screen before running the tests
    app = wx.GetApp()
    mainFrame = app.mainFrame
    mainFrame.Update()
    app.Yield(True)
    mainFrame.Update()
    app.Yield(True)

    global global_cats_profiler
    if Globals.options.testScripts:
        try:
            for aScript in Script.iterItems(view):
                if aScript.test:
                    aScript.execute()
        finally:
            # run the cleanup script
            schema.ns('osaf.app', view).CleanupAfterTests.execute()

    # Execute new framework if chandlerTests option is called
    
    recordedTest = Globals.options.recordedTest
    if recordedTest is not None:
        if not hasattr(Globals, 'test_dict'):
            from datetime import datetime
            Globals.test_dict = {'starttime':datetime.now()}
        from tools.cats.framework.run_recorded import execute_frame
        execute_frame(recordedTest)
    
    chandlerTests = Globals.options.chandlerTests
    if chandlerTests:
        logFileName = Globals.options.chandlerTestLogfile
        testDebug = Globals.options.chandlerTestDebug
        testMask = Globals.options.chandlerTestMask
        from tools.cats.framework.runTests import run_tests
        run_tests(chandlerTests, debug=testDebug, mask=testMask, logName=logFileName)

    # Execute new framework if chandlerPerformanceTests option is called
    chandlerPerformanceTests = Globals.options.chandlerPerformanceTests
    if chandlerPerformanceTests:
        logFileName = Globals.options.chandlerTestLogfile
        testDebug = Globals.options.chandlerTestDebug
        testMask = Globals.options.chandlerTestMask
        from tools.cats.framework.runTests import run_perf_tests
        run_perf_tests(chandlerPerformanceTests, debug=testDebug, mask=testMask, logName=logFileName)

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

    if isinstance(fileName, unicode):
        fileName = fileName.encode('utf8')

    if siblingPath is not None:
        fileName = os.path.join(os.path.dirname(siblingPath), fileName)
    # read the script from a file, and return it.
    scriptFile = open(fileName, 'rt')
    try:
        scriptText = scriptFile.read(-1)
    finally:
        scriptFile.close()
    return scriptText
