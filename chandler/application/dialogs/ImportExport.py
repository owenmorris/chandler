import wx
from wx.lib.filebrowsebutton import FileBrowseButton
import os, logging
from osaf import messages
from i18n import OSAFMessageFactory as _
from application.Utility import getDesktopDir
from application import schema
import itertools
import osaf.sharing
from time import time
import application.Globals as Globals
import osaf.framework.blocks.Block as Block

logger = logging.getLogger(__name__)
MAX_UPDATE_MESSAGE_LENGTH = 50

def showFileChooserWithOptions(parent, dialogTitle, defaultFile, fileMask,
                              fileMode, optionsList):
    """
    Create a simple file chooser with a list of arbitrary checkbox options.
    
    @param dialogTitle: The dialog's title
    @type  dialogTitle: unicode
    
    @param defaultFile: A default filename to be used by the file selection widget
    @type  defaultFile: string
    
    @param fileMask: The default mask that should be used when selecting a file
    @type  fileMask: A string containing a glob pattern
    
    @param fileMode: wx flags (open vs. close, read-only, etc.)
    @type  fileMode: A bitmask of wx flags
    
    @param optionsList: Additional options to provide to the user
    @type  optionsList: A list of dictionaries.  Each dictionary should contain a name
                        entry (string), a label entry (unicode) and a checked
                        entry (boolean)
                       
    @return: A tuple (success, fullpath, resultDict) where success is True only if 
             OK was returned, fullpath is the obvious or None, and resultDict is
             a dictionary with keys equal to the name key in optionsList dictionaries and
             values the boolean state of the dialog checkboxes
    """
    dlg = FileChooserWithOptions(parent, dialogTitle, defaultFile, fileMask,
                                 fileMode, optionsList)
    ret = dlg.ShowModal()
    if ret == wx.ID_OK:
        fullpath = dlg.filechooser.GetValue()
        options = {}
        for key, btn in dlg.options.iteritems():
            options[key] = btn.IsChecked()        
        
        dlg.Destroy()
        return (True, fullpath, options)
    else:
        dlg.Destroy()
        return (False, None, None)



class FileChooserWithOptions(wx.Dialog):
    def __init__(self, parent, dialogTitle, defaultFile, fileMask, fileMode,
                 optionsList):

        wx.Dialog.__init__(self, id=-1,
              name=u'FileChooserWithOptions', parent=parent,
              style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
              title=dialogTitle)

        sizer = wx.BoxSizer(wx.VERTICAL)

        buttonText = _('Browse')
        labelText = _('File location: ')
        initialPath = os.path.join(os.path.realpath(os.path.curdir), defaultFile)
        self.filechooser = FileBrowseButton(self, -1, size=(400, -1),
                                   labelText=labelText, buttonText=buttonText,
                                   dialogTitle=dialogTitle, fileMask=fileMask,
                                   startDirectory=os.path.curdir, 
                                   initialValue=initialPath, fileMode=fileMode)

        sizer.Add(self.filechooser, 0, wx.ALL, 5)
        
        self.options = {}
        for opt in optionsList:
            cb = self.options[opt['name']] = wx.CheckBox(self, -1, opt['label'])
            cb.SetValue(opt['checked'])
            sizer.Add(cb, 0, wx.ALL, 3)
        
        buttonSizer = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
                
        self.box = box = wx.BoxSizer(wx.VERTICAL)
        box.Add(sizer)
        box.Add(buttonSizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.SetSizer(box)
        box.Fit(self)

        self.Layout()
        self.CenterOnScreen()

def isReadOnly(collection):
    share = osaf.sharing.getShare(collection)
    return share and share.mode == 'get'


class ImportDialog(FileChooserWithOptions):
    def __init__(self, parent, dialogTitle, view):

        options = [dict(name='reminders', checked = True, 
                        label = _(u"Import reminders")),
                   dict(name='transparency', checked = True,
                        label = _(u"Import event status"))]
        
        FileChooserWithOptions.__init__(
            self, parent, dialogTitle,
            schema.ns("osaf.sharing", view).prefs.import_dir,
            _(u"iCalendar files|*.ics|All files (*.*)|*.*"),
            wx.OPEN | wx.HIDE_READONLY, options
        )
        
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.onCancel, id=wx.ID_CANCEL)

        
        chooserBox = wx.BoxSizer(wx.HORIZONTAL)
        
        self.chooserLabel = wx.StaticText(self, -1, _(u"Import events into:"))
        chooserBox.Add(self.chooserLabel, 0, wx.ALL, 3)

        sidebarCollection = schema.ns("osaf.app", view).sidebarCollection
        trash             = schema.ns("osaf.app", view).TrashCollection
        selected = Globals.views[0].getSidebarSelectedCollection()
        
        self.choices = [col for col in sidebarCollection if 
                        (col not in (trash, selected) and not isReadOnly(col))]

        selectNew = schema.ns("osaf.sharing", view).prefs.import_as_new
        if selected == trash or isReadOnly(selected):
            selectNew = True
        else:
            self.choices.insert(0, selected)

        displayChoices = [_(u"New collection")]
        displayChoices.extend(col.displayName for col in self.choices)
        
        self.choices.insert(0, None) # make choice indices match displayChoice
        
        self.chooser = wx.Choice(self, -1, choices = displayChoices)
        if selectNew:
            self.chooser.SetSelection(0)
        else:
            self.chooser.SetSelection(1)
            
        chooserBox.Add(self.chooser, 0, wx.LEFT, 10)
    
        self.box.Insert(1, chooserBox, 0, wx.LEFT, 16)

        self.feedbackBox = wx.BoxSizer(wx.VERTICAL)
        
        self.gauge = wx.Gauge(self, size=(360, 15))
        self.feedbackBox.Add(self.gauge, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        self.progressText = wx.StaticText(self, -1, _(u"Starting import"))
        self.feedbackBox.Add(self.progressText, wx.ALIGN_LEFT)
        
        self.box.Insert(2, self.feedbackBox, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        self.box.Hide(self.feedbackBox)
        self.box.Fit(self)

        self.cancelling = False
        self.view = view
        

    def onOK(self, event):

        self.box.Show(self.feedbackBox, recursive=True)
        self.box.Fit(self)

        widgets = (self.filechooser, self.FindWindowById(wx.ID_OK),
                   self.chooser, self.chooserLabel)
        for widget in itertools.chain(widgets, self.options.itervalues()):
            widget.Disable()
        
        # simplifying wrapper for complicated callbacks from sharing
        if self.importFile():
            event.Skip(True)
            

    def onCancel(self, event):
        self.cancelling = True
        event.Skip(True)
        
    
    def updateCallback(self, msg = None, percent = None):
        if percent is not None:
            self.gauge.SetValue(percent)
        if msg is not None:
            # @@@MOR: This is unicode unsafe:
            if len(msg) > MAX_UPDATE_MESSAGE_LENGTH:
                msg = "%s..." % msg[:MAX_UPDATE_MESSAGE_LENGTH]            
            self.progressText.SetLabel(msg)
        wx.GetApp().yieldNoIdle()
        return self.cancelling

    def fail(self, msg):
        self.updateCallback(msg, 100)
        self.gauge.Disable()

    def importFile(self):
        fullpath = self.filechooser.GetValue()
        if not os.path.isfile(fullpath):
            self.fail(_(u"File does not exist, import cancelled."))
            return False
        
        (dir, filename) = os.path.split(fullpath)
        prefs = schema.ns("osaf.sharing", self.view).prefs
        prefs.import_dir = dir
        
        targetCollection = self.choices[self.chooser.GetSelection()]            

        # set the preference for importing collections into new collections
        prefs.import_as_new = targetCollection is None
        
        share = osaf.sharing.OneTimeFileSystemShare(
            dir, filename, osaf.sharing.ICalendarFormat, itsView=self.view,
            contents = targetCollection
        )

        for key, val in self.options.iteritems():
            if not val.IsChecked():
                share.filterAttributes.append(key)

        monitor = osaf.sharing.ProgressMonitor(100, self.updateCallback)
        before = time()
        try:
            collection = share.get(monitor.callback)
        except:
            logger.exception("Failed importFile %s" % fullpath)
            self.fail(_(u"Problem with the file, import cancelled."))
            return False

        if targetCollection is None:
            name = "".join(filename.split('.')[0:-1]) or filename
            collection.displayName = name
            schema.ns("osaf.app", self.view).sidebarCollection.add(collection)
            sideBarBlock = Block.Block.findBlockByName ('Sidebar')
            sideBarBlock.postEventByName ("SelectItemsBroadcast",
                                          {'items':[collection]})
        logger.info("Imported collection in %s seconds" % (time() - before))
        assert (hasattr (collection, 'color'))
        return True # Successful import
