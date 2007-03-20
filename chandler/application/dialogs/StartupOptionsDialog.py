#   Copyright (c) 2003-2006 Open Source Applications Foundation
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


"""
Dialog box that conditionally runs at startup.
Provides repository-manipulation tools and a GUI for setting command-line options.
See: http://lists.osafoundation.org/pipermail/chandler-dev/2006-May/005901.html
"""

import os, sys, wx, tarfile
from datetime import datetime, timedelta
from application import Globals
from application.Utility import getDesktopDir, locateRepositoryDirectory
from repository.persistence.DBRepository import DBRepository


# We can't use the regular localization mechanism because the repository isn't
# open yet, but we might someday have a better way of doing this, so I'm leaving
# the hook in place.
_ = lambda msg: msg

class StartupOptionsDialog(wx.Dialog):
    @classmethod
    def run(cls, exception=None):
        dialog = StartupOptionsDialog(exception)

        if Globals.options.create and hasattr(dialog, 'create'):
            # if --create was on the cmd line, and we have an existing repo, 
            # default to that choice.
            dialog.create.SetValue(True)
        else:
            dialog.normalStartup.SetValue(True)

        dialog.ShowModal()
        dialog.Destroy()
        
    def __init__(self, exception=None):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        style = wx.CAPTION
        pre.Create(None, -1, _(u"Start-up options for Chandler"), 
                   wx.DefaultPosition, wx.DefaultSize, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Do we have an existing repository?
        repoDir = locateRepositoryDirectory(Globals.options.profileDir, Globals.options)
        repoExists = os.path.exists(repoDir)

        # Construct the controls and lay them out; their member names match 
        # the options they set in Globals.options below.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer((0, 3)) 
        
        self.normalStartup = wx.RadioButton(self, -1, 
            _(u"Continue with normal startup"))
        sizer.Add(self.normalStartup, flag=wx.ALL, border=5)
        self.normalStartup.Bind(wx.EVT_LEFT_DCLICK, self.onButton)

        if repoExists:
            self.refreshui = wx.RadioButton(self, -1, 
                _(u"Do internal clean-up, but save my data and preferences"))
            sizer.Add(self.refreshui, flag=wx.ALL, border=5)
            self.refreshui.Bind(wx.EVT_LEFT_DCLICK, self.onButton)

            self.undoRepair = wx.RadioButton(self, -1, 
                _(u"Discard recent changes until data integrity tests pass"))
            sizer.Add(self.undoRepair, flag=wx.ALL, border=5)
            self.undoRepair.Bind(wx.EVT_LEFT_DCLICK, self.onButton)

            self.create = wx.RadioButton(self, -1, 
                _(u"Discard all my data and start from scratch"))
            sizer.Add(self.create, flag=wx.ALL, border=5)
            self.create.Bind(wx.EVT_LEFT_DCLICK, self.onButton)
            
            sizer.AddSpacer((0,8))
            self.snapshot = wx.RadioButton(self, -1, 
                _(u"Make a snapshot of all data to submit with a bug report, then exit"))
            sizer.Add(self.snapshot, flag=wx.ALL, border=5)
            self.snapshot.Bind(wx.EVT_LEFT_DCLICK, self.onButton)
            
            self.restore = wx.RadioButton(self, -1, 
                _(u"Discard all my data and restore from a previous snapshot (this can take a few minutes)"))
            sizer.Add(self.restore, flag=wx.ALL, border=5)
            self.restore.Bind(wx.EVT_LEFT_DCLICK, self.onButton)
        else:
            self.restore = wx.RadioButton(self, -1, 
                _(u"Restore from a previous snapshot (this can take a few minutes)"))
            sizer.Add(self.restore, flag=wx.ALL, border=5)
            self.restore.Bind(wx.EVT_LEFT_DCLICK, self.onButton)

        box = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(self, wx.OK, _(u"OK"))
        okButton.Bind(wx.EVT_BUTTON, self.onButton)
        box.Add(okButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        sizer.Add(box, 1, flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.CenterOnScreen()
            
    def onButton(self, event):
        buttonID = event.GetEventObject().GetId()
        if hasattr(self, 'create'):
            Globals.options.create = self.create.GetValue()
        
        if hasattr(self, 'refreshui') and self.refreshui.GetValue():
            Globals.options.refreshui = True
            Globals.options.repair = True
            Globals.options.recover = True

        elif hasattr(self, 'undoRepair') and self.undoRepair.GetValue():
            Globals.options.undo = 'repair'

        elif hasattr(self, 'snapshot') and self.snapshot.GetValue():
            if self.makeSnapshot():
                # Quit. Yes, it's weird having an exit point here, but we
                # only get here at startup before any other UI has been
                # presented and before twisted has started or the repo is
                # opened, etc. Plus, this dialog is a developmental hack to
                # allow us to collect crash info with less impact on users,
                # so it's worth it - that's all I'm saying. So sue me.
                sys.exit(0)
            return # user canceled save box - keep going.

        elif self.restore.GetValue():
            restorePath = wx.FileSelector(_(u"Snapshot to restore?"),
                                          getDesktopDir(),
                                           u"", u".tgz",
                                          u"*.tgz",
                                          flags=wx.OPEN|wx.FILE_MUST_EXIST,
                                          parent=self)
            if not restorePath:
                return # user canceled.
            Globals.options.restore = restorePath
            
        self.EndModal(wx.OK)

    def makeSnapshot(self):
        """
        Take a snapshot of our repository.

        Try to do a backup first. If that fails, take a full snapshot of the
        __repository__ directory instead.
        """

        tarPath = wx.FileSelector(_(u"Save snapshot as..."),
                                  getDesktopDir(),
                                  _(u"ChandlerSnapshot.tgz"), u".tgz",
                                  u"*.tgz",
                                  flags=wx.SAVE | wx.OVERWRITE_PROMPT,
                                  parent=self)
        if not tarPath:
            return False # user canceled.

        archive = tarfile.open(tarPath, 'w:gz')
        repoDir = locateRepositoryDirectory(Globals.options.profileDir,
                                            Globals.options)
        try:
            repository = DBRepository(repoDir)
            repository.open(recover=True, exclusive=False)
            repoDir = repository.backup(os.path.join(os.path.dirname(tarPath),
                                                     '__repository__'))
            repository.close()
        except:
            # if repoDir is unchanged, the original is taken instead
            pass

        # tar up the backup or the original repoDir + log + prefs + version.py
        if isinstance(repoDir, unicode):
            repoDir = repoDir.encode(sys.getfilesystemencoding())
        archive.add(repoDir, '.')
        archive.add('version.py')
        for log in 'chandler.log', 'chandler.prefs':
            logPath = os.path.join(Globals.options.profileDir, log)
            if os.path.isfile(logPath):
                archive.add(logPath, log)
        archive.close()

        return True
