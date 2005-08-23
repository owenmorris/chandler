import wx
import os

"""
[i18n]: Are the paths being return i18n complaint across all target OS's?
It does not look like it
"""
def showFileDialog(parent, message, defaultDir, defaultFile, wildcard, style):
    if defaultDir is None:
        defaultDir = ""

    dlg = wx.FileDialog(parent, message, unicode(defaultDir), unicode(defaultFile),
                        wildcard, style)

    """Blocking call"""
    cmd = dlg.ShowModal()
    (dir, filename) = os.path.split(dlg.GetPath())
    dlg.Destroy()

    return (cmd, dir, filename)
