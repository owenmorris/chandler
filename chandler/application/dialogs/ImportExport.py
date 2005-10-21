import wx
from wx.lib.filebrowsebutton import FileBrowseButton
import os
from osaf import messages
from i18n import OSAFMessageFactory as _

def showFileDialog(parent, message, defaultDir, defaultFile, wildcard, style):
    if defaultDir is None:
        defaultDir = u""

    dlg = wx.FileDialog(parent, message, unicode(defaultDir), unicode(defaultFile),
                        wildcard, style)

    """Blocking call"""
    cmd = dlg.ShowModal()
    (dir, filename) = os.path.split(dlg.GetPath())
    dlg.Destroy()

    return (cmd, dir, filename)

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
        
        buttonSizer = wx.FlexGridSizer(cols=0, hgap=0, rows=1, vgap=0)
        okButton = wx.Button(self, id=wx.ID_OK, label=messages.OK)
        buttonSizer.AddWindow(okButton, 0, border=5, flag=wx.ALL)
        buttonSizer.AddWindow(wx.Button(self, id=wx.ID_CANCEL, label=messages.CANCEL),
                              2, border=5, flag=wx.ALL)

        sizer.Add(buttonSizer, 0, flag=wx.ALIGN_RIGHT)

        # begin with the OK button selected
        okButton.SetFocus()
        
        box = wx.BoxSizer()
        box.Add(sizer, 0, wx.ALL, 10)
        self.SetSizer(box)
        box.Fit(self)

        self.Layout()
        self.CenterOnScreen()