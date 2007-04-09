#   Copyright (c) 2007 Open Source Applications Foundation
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

__all__ = [
    'get',
    'change',
    'clear',
    'beforeBackup'
]

"""
MasterPassword handles asking the user (if necessary) for the master password
which is used to encrypt and decrypt email and sharing account passwords. The
master password is cached in memory for a period of time.

@warning: Once master password is in memory, it will be possible
          to get the encrypted passwords as well. This may be possible
          even after the master password has timed out and cleared.
@warning: If weak master passwords (like empty) are used, the
          encryption will not be of much help.
"""

import logging, string, os, threading
import wx
from i18n import ChandlerMessageFactory as _
from application import schema
from application.dialogs import Util
from osaf import Preferences
from osaf.framework.twisted import runInUIThread, waitForDeferred

log = logging.getLogger(__name__)
maxTimeout = 2**16/60 # ~18 hours

_masterPassword = None
_timer = None

@runInUIThread
def get(view, window=None, testPassword=None):
    """
    Get the master password. If needed, it will be asked from the user.
    
    Safe to call from from a background thread.

    @raise NoMasterPassword: NoMasterPassword will be raised if we have a
                             non-default master password that has timed out,
                             and the user cancels the dialog where we ask for
                             it.

    @param view:   Repository view.
    @param window: Optional parent window to be used for dialogs (if needed).
    @return:       deferred
    """
    if _timer is not None:
        _timer.cancel()

    prefs = schema.ns("osaf.framework.MasterPassword",
                      view).masterPasswordPrefs

    if not prefs.masterPassword:
        return ''

    # Return the cached password if we have it
    if _masterPassword is not None:
        # Reset timer
        _setTimedPassword(_masterPassword, prefs.timeout * 60)
        return _masterPassword
    
    # Otherwise, let's ask the user...
    from osaf.framework import password

    if testPassword is not None:
        passwords = [testPassword]
    else:
        passwords = [item for item in password.Password.iterItems(view)]
        
    while True:
        dlg = GetMasterPasswordDialog(window, prefs.timeout)
        
        try:
            if dlg.ShowModal() != wx.ID_OK:
                raise password.NoMasterPassword(_(u'No master password'))
            
            pword, timeout = dlg.getPasswordAndTimeout()
        finally:
            dlg.Destroy()

        again = False
        for item in passwords:
            if not waitForDeferred(item.initialized()):
                continue

            try:
                waitForDeferred(item.decryptPassword(masterPassword=pword))
                break
            except password.DecryptionError:
                again = True
                break
        else:
            raise RuntimeError('At least one password was expected to be initialized')
        if again:
            Util.ok(window,
                    _(u'Incorrect password'),
                    _(u'Master password was incorrect, please try again.'))
            continue
        
        break

    if prefs.timeout != timeout:
        prefs.timeout = timeout
        view.commit()
        
    _setTimedPassword(pword, timeout * 60)
    return _masterPassword


@runInUIThread
def change(view, window=None):
    """
    Set or change the master password.
    
    Safe to call from from a background thread.

    @param view:   Repository view.
    @param window: Optional parent window to be used for dialogs (if needed).
    @return:       deferred
    """
    if _timer is not None:
        _timer.cancel()

    prefs = schema.ns("osaf.framework.MasterPassword",
                      view).masterPasswordPrefs

    view.refresh()

    ret = False
    
    while True:
        dlg = ChangeMasterPasswordDialog(window,
                                         changing=prefs.masterPassword,
                                         view=view)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                oldMaster, newMaster = dlg.getMasterPasswords()
    
                if not _change(oldMaster, newMaster, view, prefs):
                    Util.ok(window,
                            _(u'Incorrect password'),
                            _(u'Old password was incorrect, please try again.'))
                    continue
                
                ret = True

        finally:
            dlg.Destroy()
            
        break
    
    return ret


@runInUIThread
def clear():
    """
    Clear the master password.

    Safe to call from from a background thread.

    @return: deferred
    """
    global _masterPassword, _timer
    if _masterPassword is not None:
        _timer.cancel()
        _masterPassword = None
        _timer = None


def beforeBackup(view, window=None):
    """
    Call before doing any kind of backup or export of data that includes
    account passwords. Will prompt the user to set their master password
    if appropriate.
    
    Must be called from the UI thread.
    """
    prefs = schema.ns("osaf.framework.MasterPassword",
                      view).masterPasswordPrefs
    if not prefs.masterPassword:
        # Check if we have any passwords we'd want to protect
        from osaf.framework import password
        count = 0
        for item in password.Password.iterItems(view):
            if not waitForDeferred(item.initialized()):
                continue
            
            if waitForDeferred(item.decryptPassword()):
                count += 1
        if count == 1: # We will always have at least one, the dummy password
            return
        
        if Util.yesNo(window,
                     _(u'Set Master password?'),
                     _(u'Anyone who gets access to your data can view your account passwords. Do you want to protect your account passwords by encrypting them with the master password?')):
            waitForDeferred(change(view, window))


def _clear():
    # Helper to really clear the master password
    d = clear()
    d.addCallback(lambda _x: True)

def _setTimedPassword(password, timeout):
    # Helper to (re)set timer and password
    global _masterPassword, _timer
    if _timer is not None:
        _timer.cancel()
    _masterPassword = password
    _timer = threading.Timer(timeout, _clear)
    _timer.start()

def _change(oldMaster, newMaster, view, prefs):
    # Helper to change or set master password
    from osaf.framework import password
    try:
        again = False
        for item in password.Password.iterItems(view):
            if not waitForDeferred(item.initialized()):
                continue

            try:
                oldPassword = waitForDeferred(item.decryptPassword(masterPassword=oldMaster))
            except password.DecryptionError:
                log.info('Wrong old master password?')
                again = True
                break
            waitForDeferred(item.encryptPassword(oldPassword, masterPassword=newMaster))
        
        if again:
            return False
            
    except:
        view.cancel()
        log.exception('Failed to change master password')
        raise
    
    prefs.masterPassword = True
    view.commit()

    _setTimedPassword(newMaster, prefs.timeout * 60)
    
    return True


class TimeoutValidator(wx.PyValidator):
    """
    This validator allows only timeout values
    between 1 and 2**16/60=1092 minutes (~18 hours).
    """
    def __init__(self, pyVar=None):
        wx.PyValidator.__init__(self)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return TimeoutValidator()

    def Validate(self, win):
        return True

    def TransferToWindow(self):
        return True 

    def TransferFromWindow(self):
        return True

    def OnChar(self, event):
        key = event.GetKeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            # Allow edits and other control chars
            event.Skip()
        elif chr(key).isdigit():
            # And digits if the value stays below our limit
            value = self.GetWindow().GetValue()
            if 1 <= int(value or 0) * 10 + int(chr(key)) <= maxTimeout:
                event.Skip()


class GetMasterPasswordDialog(wx.Dialog):
    """
    Get master password dialog
    """
    def __init__(self, parent, timeout, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        """
        constructor
        
        @param timeout: Master password timeout, in minutes.
        """ 
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, -1, _(u'Enter master password'), pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents

        self.SetIcon(wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico", wx.BITMAP_TYPE_ICO))

        sizer = wx.BoxSizer(wx.VERTICAL)

        grid = wx.GridSizer(2, 2)

        # password
        label = wx.StaticText(self, -1, _(u'Master pass&word:'))
        grid.Add(label, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.masterPassword = wx.TextCtrl(self, -1, '', wx.DefaultPosition,
                                          [150, -1], wx.TE_PASSWORD)
        grid.Add(self.masterPassword, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.masterPassword.SetFocus()

        # timeout
        label = wx.StaticText(self, -1, _(u'&Timeout (minutes):'))
        grid.Add(label, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.timeout = wx.TextCtrl(self, -1, str(timeout), wx.DefaultPosition,
                                   [150, -1],
                                   validator=TimeoutValidator())
        grid.Add(self.timeout, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        
        sizer.Add(grid, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # ok button
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.ok = wx.Button(self, wx.ID_OK)
        box.Add(self.ok, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.ok.Disable()

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        btn.SetFocus()

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.masterPassword.Bind(wx.EVT_KEY_UP, self.OnKeyPress)
        self.timeout.Bind(wx.EVT_KEY_UP, self.OnKeyPress)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        
    def OnKeyPress(self, evt):
        if len(self.masterPassword.GetValue()) > 0 and \
           len(self.timeout.GetValue()) > 0:
            self.ok.Enable()
            self.ok.SetDefault()
        else:
            self.ok.Disable()
        evt.Skip()
        
    def getPasswordAndTimeout(self):
        """
        Get the master password and timeout.
        """
        return self.masterPassword.GetValue(), int(self.timeout.GetValue())


class ChangeMasterPasswordDialog(wx.Dialog):
    """
    Change master password dialog
    """
    def __init__(self, parent, changing, view, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
        """
        constructor
        
        @param changing: Should be true if you are changing
                         the master password. Otherwise you will be creating
                         the master password.
        """ 
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        self.view = view
        if changing:
            title = _(u'Change Master Password')
        else:
            title = _(u'Set Master Password')
        pre.Create(parent, -1, title, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents

        self.SetIcon(wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico", wx.BITMAP_TYPE_ICO))

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Static text
        message = _(u'Sensitive information, such as email and sharing account passwords, are protected with a master password. Do not forget the master password or the protected information will be lost.')
        label = wx.StaticText(self, -1, message)
        label.Wrap(400)
        sizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        if changing:
            grid = wx.GridSizer(4, 2)

            label = wx.StaticText(self, -1, _(u'Ol&d master password:'))
            grid.Add(label, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
            self.oldMaster = wx.TextCtrl(self, -1, '', wx.DefaultPosition, [150, -1],
                                         wx.TE_PASSWORD)
            grid.Add(self.oldMaster, 0, wx.ALIGN_LEFT|wx.ALL, 5)
            self.oldMaster.SetFocus()
        else:
            grid = wx.GridSizer(3, 2)

        label = wx.StaticText(self, -1, _(u'Master pass&word:'))
        grid.Add(label, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.newMaster = wx.TextCtrl(self, -1, '', wx.DefaultPosition, [150, -1],
                                     wx.TE_PASSWORD)
        grid.Add(self.newMaster, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        if not changing:
            self.newMaster.SetFocus()

        label = wx.StaticText(self, -1, _(u'Con&firm password:'))
        grid.Add(label, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.confirmMaster = wx.TextCtrl(self, -1, '', wx.DefaultPosition, [150, -1],
                                         wx.TE_PASSWORD)
        grid.Add(self.confirmMaster, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        

        # Quality progress meter
        label = wx.StaticText(self, -1, _(u'Quality meter:'))
        grid.Add(label, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.gauge = wx.Gauge(self, -1, quality('')[1], wx.DefaultPosition, [150, -1])
        grid.Add(self.gauge, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.Add(grid, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # buttons
        box = wx.BoxSizer(wx.HORIZONTAL)

        if changing:
            self.reset = wx.Button(self, -1, _(u'&Reset Master Password...'))
            box.Add(self.reset, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.ok = wx.Button(self, wx.ID_OK)
        box.Add(self.ok, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.ok.Disable()

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        btn.SetFocus()

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.newMaster.Bind(wx.EVT_KEY_UP, self.OnPasswordKeyPress)
        self.confirmMaster.Bind(wx.EVT_KEY_UP, self.OnConfirmKeyPress)
        if changing:
            self.reset.Bind(wx.EVT_BUTTON, self.OnReset)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def getMasterPasswords(self):
        """
        Get the old and the new master passwords.
        """
        try:
            oldMaster = self.oldMaster.GetValue()
        except AttributeError:
            oldMaster = ''
        return oldMaster, self.newMaster.GetValue()

    def OnPasswordKeyPress(self, evt):
        self.gauge.SetValue(quality(self.newMaster.GetValue())[0])
        evt.Skip()

    def OnConfirmKeyPress(self, evt):
        if self.newMaster.GetValue() == self.confirmMaster.GetValue() and \
           len(self.newMaster.GetValue()) > 0:
            self.ok.Enable()
            self.ok.SetDefault()
        else:
            self.ok.Disable()
        evt.Skip()

    def OnReset(self, evt):
        if Util.yesNo(self,
                      _(u'Confirm Reset?'),
                      _(u'Protected information will be deleted.\nAre you sure you want to reset Master Password?')):
            try:
                reset(self.view)
            finally:
                self.EndModal(wx.ID_CANCEL)


def reset(view):
    """
    Reset master password. Will clear all passwords as well.
    """
    view.refresh()

    try:
        # clear all passwords
        from osaf.framework import password
        for item in password.Password.iterItems(view):
            waitForDeferred(item.clear())

        # Turn off pref
        prefs = schema.ns("osaf.framework.MasterPassword",
                          view).masterPasswordPrefs
        prefs.masterPassword = False

        # set new dummy password
        prefs = schema.ns("osaf.framework.password",
                          view).passwordPrefs
        password = ''.join([string.printable[ord(c) % len(string.printable)] \
                            for c in os.urandom(16)])                  
        waitForDeferred(prefs.dummyPassword.encryptPassword(password, masterPassword=''))
    except:
        try:
            log.exception('Failed to reset master password')
            view.cancel()
        finally:
            raise
    
    view.commit()
    
    # clear the master password itself
    clear()


def quality(password):
    """
    Get a rough idea of the password quality.
    
    @param password: Password to check
    @return:         A tuple: (quality, maximum)
    """
    # length bonus
    q = len(password)
    
    letters = {}
    for letter in password:
        letters[letter] = letters.get(letter, 1)
    
    # variety bonus
    q += len(letters)

    # different classes of characters bonus
    up = lo = di = al = 0
    for letter in letters:
        if not up and letter.isupper():
            up = 1
            q = q*1.1 + 1
        elif not lo and letter.islower():
            lo = 1
            q = q*1.1 + 1
        elif not di and letter.isdigit():
            di = 1
            q = q*1.1 + 1
        elif not al and not letter.isalnum():
            al = 1
            q = q*1.2 + 2
        else:
            break

    maximum = 35
    q = int(q)
    if q > maximum:
        q = maximum
    
    return (q, maximum) if q > 5 else (0, maximum)


class MasterPasswordPrefs(Preferences):
    masterPassword = schema.One(
        schema.Boolean,
        initialValue = False,
        doc = 'Has the master password been set?'
    )

    timeout = schema.One(
        schema.Integer,
        initialValue = 15,
        doc = 'Timeout, in minutes, for the master password'
    )


def installParcel(parcel, oldVersion = None):
    MasterPasswordPrefs.update(parcel, 'masterPasswordPrefs')
