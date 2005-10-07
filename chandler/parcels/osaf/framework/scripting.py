__version__ = "$Revision: 6708 $"
__date__ = "$Date: 2005-08-19 17:29:03 -0700 (Fri, 19 Aug 2005) $"
__copyright__ = "Copyright (c) 2005 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
import application.schema as schema
import osaf.pim as pim
import osaf.framework.blocks.Block as Block
import osaf.framework.types.DocumentTypes as DocumentTypes
from repository.item.Item import Item as Item
from datetime import datetime
import logging
import wx
import os, sys
from i18n import OSAFMessageFactory as _
from osaf import messages

__all__ = [
    'app_ns', 'hotkey_script', 'run_script', 'run_startup_script', 'Script', 'script_file',
    'User'
]

logger = logging.getLogger(__name__)

def installParcel(parcel, oldVersion=None):
    detail = schema.ns('osaf.framework.blocks.detail', parcel)

    # UI Elements:
    # -----------
    hotkeyArea = detail.makeArea(parcel, 'HotkeyArea',
                            position=0.6,
                            childrenBlocks=[
                                detail.makeLabel(parcel, _(u'Hotkey'), borderTop=4),
                                detail.makeSpacer(parcel, width=6),
                                detail.makeEditor(parcel, 'EditFKey',
                                           viewAttribute=u'fkey',
                                           stretchFactor=0.0,
                                           size=DocumentTypes.SizeType(75, -1)),
                                detail.makeSpacer(parcel, width=60),
                                ]).install(parcel)

    testCheckboxArea = detail.makeArea(parcel, 'TestCheckboxArea',
                            position=0.7,
                            childrenBlocks=[
                                detail.makeLabel(parcel, _(u'test'), borderTop=4),
                                detail.makeSpacer(parcel, width=6),
                                detail.makeEditor(parcel, 'EditTest',
                                           viewAttribute=u'test',
                                           stretchFactor=0.0,
                                           minimumSize=DocumentTypes.SizeType(16,-1))
                                ]).install(parcel)

    # Block Subtree for the Detail View of a Script
    # ------------
    detail.DetailTrunkSubtree.update(parcel, 'script_detail_view',
                                     key=Script.getKind(parcel.itsView),
                                     rootBlocks=[
                                         detail.makeSpacer(parcel, height=6, position=0.01).install(parcel),
                                         detail.HeadlineArea,
                                         hotkeyArea,
                                         testCheckboxArea,
                                         detail.makeSpacer(parcel, height=7, position=0.8).install(parcel),
                                         detail.NotesBlock
                                         ])

"""
Handle running a Script.
"""
def run_script(scriptText, fileName=u""):
    """
    exec the supplied script, in an environment equivalent to
    what you get when you say:
    from scripting.Helpers import *
    """
    assert len(scriptText) > 0, "Empty script"
    assert fileName is not None

    scriptText = scriptText.encode(sys.getfilesystemencoding())
    fileName = fileName.encode(sys.getfilesystemencoding())

    # compile the code
    scriptCode = compile(scriptText, fileName, 'exec')

    # next, build a dictionary of names that are predefined
    builtIns = {}

    for attr in __all__:
        builtIns[attr] = globals()[attr]

    # now run that script in our predefined scope
    exec scriptCode in builtIns

class Script(pim.ContentItem):
    """ Persistent Script Item, to be executed. """
    schema.kindInfo(displayName=_(u"Script"), displayAttribute="displayName")
    lastRan = schema.One(schema.DateTime, displayName = _(u"last ran"))
    fkey = schema.One(schema.Text, initialValue = u'')
    test = schema.One(schema.Boolean, initialValue = False)

    # redirections

    about = schema.One(redirectTo = 'displayName')
    who = schema.One(redirectTo = 'creator')
    date = schema.One(redirectTo = 'lastRan')

    def __init__(self, name=None, parent=None, kind=None, view=None,
                 bodyString=None, *args, **keys):
        if name is None:
            displayName = messages.UNTITLED
        else:
            displayName = name
        super(Script, self).__init__(name, parent, kind, view, displayName=displayName, *args, **keys)

        self.lastRan = datetime.now()
        if bodyString is not None:
            self.bodyString = bodyString # property for the body LOB
        self.private = False # can share scripts

    """
    def isAttributeModifiable(self, attribute):
        # To allow attributes to be modified only if Script was created by "me":
        return self.creator is self.getCurrentMeContact(self.itsView)
    """

    def execute(self, fileName=u""):
        self.lastRan = datetime.now()
        run_script(self.bodyString, fileName)

def hotkey_script(event, view):
    """
    Check if the event is a hot key to run a script.
    Returns True if it does trigger a script to run, False otherwise.
    """
    keycode = event.GetKeyCode()
    # for now, we just allow function keys to be hot keys.
    if (keycode >= wx.WXK_F1 and keycode <= wx.WXK_F24
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

def run_startup_script(view):
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
           run_script(scriptFileText, fileName = fileName)

def script_file(fileName, siblingPath=None):
    # fileName relative to the sibling path?
    #Encode the unicode filename to the system character set encoding
    fileName = fileName.encode(sys.getfilesystemencoding())

    if siblingPath is not None:
        fileName = os.path.join(os.path.dirname(siblingPath), fileName)
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
        raise
    return scriptText

class EventTiming(dict):
    """
    dictionary of event timings for events that have
    been sent by CPIA Script since this dictionary was reset.
    Use clear() to reset timings.
    """
    def start_timer(self):
        return datetime.now()

    def end_timer(self, startTime, eventName):
        self.setdefault(eventName, []).append(datetime.now()-startTime)

    def get_strings(self):
        strTimings = {}
        for eName, timingList in self.iteritems():
            strList = []
            for timing in timingList:
                strList.append(str(timing))
            strTimings[eName] = strList
        return strTimings

    strings = property(get_strings)

class BlockProxy(object):
    """
    Proxy for a Block which is dynamically located by name.
    Since Blocks come and go in CPIA, this proxy helps
    provide a solid reference point for locating the
    currently rendered Block by name.
    You can construct it with a set of children block
    attributes which are also located by name.
    """
    def __init__(self, blockName, app_ns, children={}):
        # create an attribute that looks up this block by name
        self.proxy = blockName
        self.children = children
        self.app_ns = app_ns

    def __getattr__(self, attr):
        # if it's a block that's our child, return it
        child_name = self.children.get(attr, None)
        if child_name:
            return getattr(self.app_ns, child_name)
        # delegate the lookup to our View
        block = getattr(self.app_ns, self.proxy)
        return getattr(block, attr)

    def focus(self):
        block = getattr(self.app_ns, self.proxy)
        block.widget.SetFocus()

class RootProxy(BlockProxy):
    """ 
    Proxy to the Main View Root block. 
    Handles BlockEvents as methods.
    """

    def __init__(self, *args, **keys):
        super(RootProxy, self).__init__(*args, **keys)
        # our timing object
        self.timing = EventTiming()

    """
    We need to find the best BlockEvent at runtime on each invokation,
    because the BlockEvents come and go from the soup as UI portions
    are rendered and unrendered.  The best BlockEvent is the one copied
    into the soup and attached to rendered blocks that were also copied.
    """
    def post_script_event(self, eventName, event, argDict=None, timing=None, **keys):
        # Post the supplied event, keeping track of the timing if requested.
        # Also, call Yield() on the application, so it gets some time during
        #   script execution.
        if argDict is None:
            argDict = {}
        try:
            argDict.update(keys)
        except AttributeError:
            # make sure the first parameter was a dictionary, or give a friendly error
            message = "BlockEvents may only have one positional parameter - a dict"
            raise AttributeError, message
        # remember timing information
        if timing is not None:
            startTime = timing.start_timer()
        # post the event
        result = Globals.mainViewRoot.post(event, argDict)
        # finish timing
        if timing is not None:
            timing.end_timer(startTime, eventName)
        # let the Application get some time
        wx.GetApp().Yield()
        return result

    # Attributes that are BlockEvents get converted to functions
    # that invoke that event.
    # All other attributes are redirected to the root view.
    def __getattr__(self, attr):
        def scripted_blockEvent(argDict=None, **keys):
            # merge the named parameters, into the dictionary positional arg
            return self.post_script_event(attr, best, argDict, timing=self.timing, **keys)
        best = Block.Block.findBlockEventByName(attr)
        if best is not None:
            return scripted_blockEvent
        else:
            # delegate the lookup to our View
            return getattr(Globals.mainViewRoot, attr)


"""
Children to use for the Detail View.
This is a mapping of the form:
attribute_name: block_name
"""
detail_children = {
    'title': 'HeadlineBlock',
    'location': 'CalendarLocation',
    'mail_from': 'FromEditField',
    'mail_to': 'ToMailEditField',
    'all_day': 'EditAllDay',
    'start_date': 'EditCalendarStartDate',
    'start_time': 'EditCalendarStartTime',
    'end_date': 'EditCalendarEndDate',
    'end_time': 'EditCalendarEndTime',
    'time_zone': 'EditTimeZone',
    'status': 'EditTransparency',
    'recurrence': 'EditRecurrence',
    'reminder': 'EditReminder',
    'notes': 'NotesBlock',
    }

class AppProxy(object):
    """
    Proxy for the app namespace, and the items you'd expect
    in that namespace.
    Provides easy access to useful attributes, like "view".
    Has attributes for its major children blocks, like
    "root", "sidebar", "calendar", etc.
    All BlockEvents are mapped onto methods in this class, 
    so you can say AppProxy.NewTask() to post the "NewTask"
    event.
    """
    def __init__(self, view):
        # our view attribute
        self.itsView = view
        # we proxy to the app name space
        self.app_ns = schema.ns('osaf.app', view)
        # view proxies
        self.root = RootProxy('MainViewRoot', self)
        self.appbar = BlockProxy('ApplicationBar', self)
        self.markupbar = BlockProxy('MarkupBar', self)
        self.sidebar = BlockProxy('Sidebar', self)
        self.calendar = BlockProxy('CalendarSummaryView', self)
        self.summary = BlockProxy('TableSummaryView', self)
        self.detail = BlockProxy('DetailView', self, children=detail_children)

    def item_named(self, itemClass, itemName):
        for item in itemClass.iterItems(self.itsView):
            if self._name_of(item) == itemName:
                return item
        return None

    def _name_of(self, item):
        try:
            return item.about
        except AttributeError:
            pass
        try:
            return item.blockName
        except AttributeError:
            pass
        try:
            return item.displayName
        except AttributeError:
            pass
        try:
            return item.itsName
        except AttributeError:
            pass
        return None

    # Attributes that are named blocks are found by name.
    # All other attributes are redirected to the app name space.
    def __getattr__(self, attr):
        block = Block.Block.findBlockByName(attr)
        if block is not None:
            return block
        else:
            return getattr(self.app_ns, attr)

    """
    Emulating User-level Actions
    """
class User(object):
    """
    Emulate User Actions
    """
    @classmethod
    def emulate_typing(cls, string, ctrlFlag = False, altFlag = False, shiftFlag = False):
        """ emulate_typing the string into the current focused widget """
        success = True
        def set_event_info(event):
            # setup event info for a keypress event
            event.m_keyCode = keyCode
            event.m_rawCode = keyCode
            event.m_shiftDown = char.isupper() or shiftFlag
            event.m_controlDown = event.m_metaDown = ctrlFlag
            event.m_altDown = altFlag
            event.SetEventObject(widget)
        # for each key, check for specials, then try several approaches
        app = wx.GetApp()
        for char in string:
            keyCode = ord(char)
            if keyCode == wx.WXK_RETURN:
                cls.emulate_return()
            elif keyCode == wx.WXK_TAB:
                cls.emulate_tab(shiftFlag=shiftFlag)
            else:
                # in case the focus has changed, get the new focused widget
                widget = wx.Window_FindFocus()
                # try calling any bound key handler
                keyPress = wx.KeyEvent(wx.wxEVT_KEY_DOWN)
                set_event_info(keyPress)
                downWorked = widget.ProcessEvent(keyPress)
                keyUp = wx.KeyEvent(wx.wxEVT_KEY_UP)
                set_event_info(keyUp)
                upWorked = widget.ProcessEvent(keyUp)
                if not (downWorked or upWorked): # key handler worked?
                    # try calling EmulateKeyPress
                    emulateMethod = getattr(widget, 'EmulateKeyPress', lambda k: False)
                    if '__WXMSW__' in wx.PlatformInfo:
                        emulateMethod = lambda k: False
                    if not emulateMethod(keyPress): # emulate worked?
                        # try calling WriteText
                        writeMethod = getattr(widget, 'WriteText', None)
                        if writeMethod:
                            writeMethod(char)
                        else:
                            success = False # remember we had a failure
                app.Yield()
        return success

    @classmethod 
    def emulate_tab(cls, shiftFlag=False):
        if shiftFlag:
            flags = wx.NavigationKeyEvent.IsBackward
        else:
            flags = wx.NavigationKeyEvent.IsForward
        wx.Window_FindFocus().Navigate(flags)

    @classmethod
    def emulate_click(cls, block, x=None, y=None, double=False):
        """ Simulates left mouse click on the given block or widget """
        try:
            widget =  block.widget
        except AttributeError:
            widget = block
        # event settings
        mouseEnter = wx.MouseEvent(wx.wxEVT_ENTER_WINDOW)
        if double:
            mouseDown = wx.MouseEvent(wx.wxEVT_LEFT_DCLICK)
        else:
            mouseDown = wx.MouseEvent(wx.wxEVT_LEFT_DOWN)
        mouseUp = wx.MouseEvent(wx.wxEVT_LEFT_UP)
        mouseLeave = wx.MouseEvent(wx.wxEVT_LEAVE_WINDOW)
        if x:
            mouseEnter.m_x = mouseDown.m_x = mouseUp.m_x = x
        if y:
            mouseEnter.m_y = mouseDown.m_y = mouseUp.m_y = y
        mouseEnter.SetEventObject(widget)
        mouseDown.SetEventObject(widget)
        mouseUp.SetEventObject(widget)
        mouseLeave.SetEventObject(widget)
        # events processing
        widget.ProcessEvent(mouseEnter)
        widget.ProcessEvent(mouseDown)
        if not double:
            widget.ProcessEvent(mouseUp)
        widget.ProcessEvent(mouseLeave)
        # Give Yield to the App
        wx.GetApp().Yield()

    @classmethod
    def emulate_return(cls, block=None):
        """ Simulates a return-key event in the given block """
        try:
            if block :
                widget = block.widget
            else :
                widget = wx.Window_FindFocus()
        except AttributeError:
            return False
        else:
            # return-key down
            ret_d = wx.KeyEvent(wx.wxEVT_KEY_DOWN)
            ret_d.m_keyCode = wx.WXK_RETURN
            # return-key up
            ret_up = wx.KeyEvent(wx.wxEVT_KEY_UP)
            ret_up.m_keyCode = wx.WXK_RETURN
            # text updated event
            tu = wx.CommandEvent(wx.wxEVT_COMMAND_TEXT_UPDATED)
            tu.SetEventObject(widget)
            # kill focus event
            kf = wx.FocusEvent(wx.wxEVT_KILL_FOCUS)
            kf.SetEventObject(widget)
            # Text enter
            ent = wx.CommandEvent(wx.wxEVT_COMMAND_TEXT_ENTER)
            ent.SetEventObject(widget)

            #work around for mac bug
            widget.ProcessEvent(tu) #for start/end time and location field
            #work around for canvasItem
            widget.ProcessEvent(kf) #for canvasItem title
            # events processing
            widget.ProcessEvent(ret_d)
            widget.ProcessEvent(ret_up)
            # Give Yield & Idle to the App
            app = wx.GetApp()
            app.Yield()
            ev = wx.IdleEvent()
            app.ProcessEvent(ev)
            return True

    @classmethod
    def emulate_sidebarClick(cls, sidebar, cellName, double=False):
        ''' Process a left click on the given cell in the given sidebar'''
        # for All, In, Out, Trash collection find by item rather than itemName
        chandler_collections = {"All":schema.ns('osaf.app', Globals.mainViewRoot).allCollection,
                                "Out":schema.ns('osaf.app', Globals.mainViewRoot).outCollection,
                                "In":schema.ns('osaf.app', Globals.mainViewRoot).inCollection,
                                "Trash":schema.ns('osaf.app', Globals.mainViewRoot).TrashCollection}
        if cellName in chandler_collections.keys():
            cellName = chandler_collections[cellName]

        cellRect = None
        for i in range(sidebar.widget.GetNumberRows()):
            item = sidebar.widget.GetTable().GetValue(i,0)[0]
            if item.displayName == cellName or item == cellName:
                cellRect = sidebar.widget.CalculateCellRect(i)
                break
        if cellRect:
            # events processing
            gw = sidebar.widget.GetGridWindow()
            # +3 work around for the sidebar bug
            cls.emulate_click(gw, x=cellRect.GetX()+3, y=cellRect.GetY()+3, double=double)
            return True
        else:
            return False


def app_ns(view=None):
    if view is None:
        view = wx.GetApp().UIRepositoryView
    return AppProxy(view)


