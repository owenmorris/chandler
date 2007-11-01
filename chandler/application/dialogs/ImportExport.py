#   Copyright (c) 2003-2007 Open Source Applications Foundation
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

from __future__ import with_statement
import wx
from wx.lib.filebrowsebutton import FileBrowseButton
import os, logging
from i18n import ChandlerMessageFactory as _
from application import schema
import itertools
import osaf.sharing
from  osaf.sharing.ICalendar import importICalendarFile, ICalendarImportError
from osaf.framework.blocks.Block import Block
from osaf.pim import Remindable, EventStamp
from osaf.activity import *
from osaf.usercollections import UserCollection

logger = logging.getLogger(__name__)
MAX_UPDATE_MESSAGE_LENGTH = 50

def showFileChooserWithOptions(dialogTitle, defaultFile, fileMask,
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
    dlg = FileChooserWithOptions(dialogTitle, defaultFile, fileMask,
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
    def __init__(self, dialogTitle, defaultFile, fileMask, fileMode,
                 optionsList):

        wx.Dialog.__init__(self, id=-1,
              name=u'FileChooserWithOptions', parent=None,
              style=wx.DIALOG_MODAL | wx.DEFAULT_DIALOG_STYLE,
              title=dialogTitle)

        sizer = wx.BoxSizer(wx.VERTICAL)

        buttonText = _('&Browse')
        labelText = _('&File location: ')
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
    def __init__(self, dialogTitle, view):

        options = [dict(name='cid:reminders-filter@osaf.us', checked = True, 
                        label = _(u"Import &reminders")),
                   dict(name='cid:event-status-filter@osaf.us', checked = True,
                        label = _(u"Import event &status"))]
        
        FileChooserWithOptions.__init__(
            self, dialogTitle,
            schema.ns("osaf.sharing", view).prefs.import_dir,
            _(u"iCalendar files|*.ics|All files (*.*)|*.*"),
            wx.OPEN, options
        )
        
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.onCancel, id=wx.ID_CANCEL)

        sidebarCollection = schema.ns("osaf.app", view).sidebarCollection
        trash             = schema.ns("osaf.pim", view).trashCollection
        selected = Block.findBlockByName("MainView").getSidebarSelectedCollection()
        
        # create a collection chooser
        gs = wx.FlexGridSizer(2, 2, 2, 2)  # rows, cols, hgap, vgap        
        
        self.chooserLabel = wx.StaticText(self, -1, _(u"Import e&vents into:"))
        gs.Add(self.chooserLabel, 0, wx.ALL, 3)

        self.choices = [col for col in sidebarCollection if 
                        (col is not selected) and not isReadOnly(col) and
                        not UserCollection(col).outOfTheBoxCollection]

        selectNew = schema.ns("osaf.sharing", view).prefs.import_as_new
        if selected == trash or isReadOnly(selected):
            selectNew = True
        else:
            self.choices.insert(0, selected)

        displayChoices = [_(u"New collection")]
        displayChoices.extend(col.displayName for col in self.choices)
        
        self.choices.insert(0, None) # make choice indices match displayChoice
        
        self.chooser = wx.Choice(self, -1, choices = displayChoices)
        self.chooser.Bind(wx.EVT_CHOICE, self.OnCollChoice)
        if selectNew:
            self.chooser.SetSelection(0)
        else:
            self.chooser.SetSelection(1)

        gs.Add(self.chooser, 0, wx.ALIGN_LEFT, 0)
    
        self.box.Insert(1, gs, 0, wx.LEFT, 16)

        self.mine = wx.CheckBox(self, -1, _(u"Keep out of Dashboard"))
        self.mine.SetValue(False)
        self.box.Insert(2, self.mine, 0, wx.ALL, 3)

        self.feedbackBox = wx.BoxSizer(wx.VERTICAL)
        
        self.gauge = wx.Gauge(self, size=(360, 15))
        self.feedbackBox.Add(self.gauge, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        
        self.progressText = wx.StaticText(self, -1, _(u"Starting import..."))
        self.feedbackBox.Add(self.progressText, wx.ALIGN_LEFT)
        
        self.box.Insert(3, self.feedbackBox, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        self.box.Hide(self.feedbackBox)
        self.box.Fit(self)

        self.cancelling = False
        self.view = view

    def OnCollChoice(self, event):
        if self.chooser.GetSelection() == 0:
            self.mine.Enable()
        else:
            self.mine.Disable()


    def onOK(self, event):

        self.box.Show(self.feedbackBox, recursive=True)
        self.box.Fit(self)

        widgets = (self.filechooser, self.FindWindowById(wx.ID_OK),
                   self.chooser, self.chooserLabel)
        for widget in itertools.chain(widgets, self.options.itervalues()):
            widget.Disable()
            
        self.mine.Disable()
        
        # simplifying wrapper for complicated callbacks from sharing
        view = self.view

        activity = None
        # defer commits until done processing
        with view.commitDeferred():
            activity = self.importFile()
            if activity:
                event.Skip(True)
                activity.update(msg=_(u"Saving changes..."))
            # The commit() call below ensures that at least one such call gets
            # actually deferred and run when this code block completes. When
            # there are no changes to commit, as in a second call to commit()
            # in succession, the call is more or less a nop.                
            view.commit()
            
        if activity:
            activity.completed()
            self.listener.unregister()
            
    def onCancel(self, event):
        self.cancelling = True
        event.Skip(True)
        
    
    def updateCallback(self, activity, *args, **kwds):

        if 'percent' in kwds:
            percent = kwds['percent']
            if percent is None:
                self.gauge.Pulse()
            else:
                self.gauge.SetValue(percent)

        if 'msg' in kwds:
            msg = kwds['msg']
            # @@@MOR: This is unicode unsafe:
            if len(msg) > MAX_UPDATE_MESSAGE_LENGTH:
                msg = "%s..." % msg[:MAX_UPDATE_MESSAGE_LENGTH]
            self.progressText.SetLabel(msg)
        theApp = wx.GetApp()
        theApp.updateUIInOnIdle = False
        try:
            theApp.Yield(True)
        finally:
            theApp.updateUIInOnIdle = True
        return self.cancelling

    def fail(self, msg):
        self.updateCallback(None, msg=msg, percent=100)
        self.gauge.Disable()

    def importFile(self):
        fullpath = self.filechooser.GetValue()
        (dir, filename) = os.path.split(fullpath)

        coll = targetCollection = self.choices[self.chooser.GetSelection()]
        filterAttributes = set(key for key, val in self.options.iteritems()
                               if not val.IsChecked())

        # set the preference for importing collections into new collections
        prefs = schema.ns("osaf.sharing", self.view).prefs
        prefs.import_as_new = targetCollection is None
        prefs.import_dir = dir

        activity = Activity("Import %s" % filename)
        self.listener = Listener(activity=activity, callback=self.updateCallback)

        try:
            activity.started()
            collection = importICalendarFile(fullpath, self.view, coll,
                                             filterAttributes, activity,
                                             None, logger)
            if coll == None and not self.mine.IsChecked():
                mineCollections = schema.ns('osaf.pim', self.view).mine
                mineCollections.sources.add(collection)

        except ICalendarImportError, e:
            activity.failed(exception=e)
            self.fail(unicode(e))
            self.listener.unregister()
            return False

        return activity # Successful import
