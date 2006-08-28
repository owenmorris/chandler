#   Copyright (c) 2006 Open Source Applications Foundation
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


import os, sys, time, codecs
from cgi import escape
import wx
from i18n import ChandlerSafeTranslationMessageFactory as _
import Globals
import version
from feedback_xrc import *


activeWindow = None
destroyAppOnClose = False


def initRuntimeLog(profileDir):
    """
    Append the current time as application start time to run time log,
    creating the log file if necessary.
    """
    try:
        f = open(os.path.join(profileDir, 'start.log'), 'a+')
        f.write('start:%s\n' % long(time.time()))
        f.close()
    except:
        pass


def stopRuntimeLog(profileDir):
    """
    Append the current time as application stop time.
    """
    try:
        logfile = os.path.join(profileDir, 'start.log') 
        f = open(logfile, 'a+')
        f.write('stop:%s\n' % long(time.time()))
        f.close()
        return logfile
    except:
        pass


class FeedbackWindow(wx.PyOnDemandOutputWindow):
    """
    An error dialog that would be shown in case there is an uncaught
    exception. The user can send the error report back to us as well.
    """
    def _fillOptionalSection(self):
        try:    
            # columns
            self.frame.sysInfo.InsertColumn(0, 'key')
            self.frame.sysInfo.InsertColumn(1, 'value')

            # data
            self.frame.sysInfo.InsertStringItem(0, 'os.getcwd')
            self.frame.sysInfo.SetStringItem(0, 1, '%s' % os.getcwd())
            index = 1
            for argv in sys.argv:
                self.frame.sysInfo.InsertStringItem(index, 'sys.argv')
                self.frame.sysInfo.SetStringItem(index, 1, '%s' % argv)
                index += 1
            for path in sys.path:
                self.frame.sysInfo.InsertStringItem(index, 'sys.path')
                self.frame.sysInfo.SetStringItem(index, 1, '%s' % path)
                index += 1
            for key in os.environ.keys():
                self.frame.sysInfo.InsertStringItem(index, 'os.environ')
                self.frame.sysInfo.SetStringItem(index, 1, '%s: %s' % (key, os.environ[key]))
                index += 1
            try:
                f = codecs.open(os.path.join(Globals.options.profileDir,
                                             'chandler.log'),
                                encoding='utf-8', mode='r', errors='ignore')
                for line in f.readlines()[-20:]:
                    self.frame.sysInfo.InsertStringItem(index, 'chandler.log')
                    self.frame.sysInfo.SetStringItem(index, 1, '%s' % line)
                    index += 1
            except:
                pass
            try:
                f = codecs.open(os.path.join(Globals.options.profileDir,
                                             'twisted.log'),
                                encoding='utf-8', mode='r', errors='ignore')
                for line in f.readlines()[-20:]:
                    self.frame.sysInfo.InsertStringItem(index, 'twisted.log')
                    self.frame.sysInfo.SetStringItem(index, 1, '%s' % line)
                    index += 1
            except:
                pass

            self.frame.sysInfo.SetColumnWidth(0, wx.LIST_AUTOSIZE)
            self.frame.sysInfo.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        except:
            pass

        self.frame.delButton.Bind(wx.EVT_BUTTON, self.OnDelItem, self.frame.delButton)
        self.frame.sysInfo.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        self.frame.sysInfo.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.frame.sysInfo.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def OnItemSelected(self, event):
        self.frame.delButton.Enable()

    def OnItemDeselected(self, event):
        if self.frame.sysInfo.GetSelectedItemCount() < 1:
            self.frame.delButton.Disable()
            # Disabling the focused button disables keyboard navigation
            # unless we set the focus to something else - let's put it
            # on the list control.
            self.frame.sysInfo.SetFocus()

    def OnKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            return self.OnDelItem(event)
        event.Skip()

    def OnDelItem(self, event):
        while True:
            index = self.frame.sysInfo.GetNextItem(-1, state=wx.LIST_STATE_SELECTED)
            if index < 0:
                break
            self.frame.sysInfo.DeleteItem(index)

    def _fillRequiredSection(self, st):
        # Time since last failure
        try:
            logfile = stopRuntimeLog(Globals.options.profileDir)
            try:
                timeSinceLastError = 0
                start = 0
                for line in open(logfile):
                    verb, value = line.split(':')
                    # We may have corrupted start, start; stop, stop entries but that is ok,
                    # we only count the time between start, stop pairs.
                    if verb == 'start':
                        start = long(value)
                    elif start != 0:
                        stop = long(value)
                        if stop > start: # Skip over cases where we know system clock has changed
                            timeSinceLastError += stop - start
                        start = 0
            except:
                timeSinceLastError = 0
            
            self.frame.text.AppendText('Seconds since last error: %d\n' % timeSinceLastError)
            
            # Clear out the logfile
            f = open(logfile, 'w')
            f.close()
        except:
            pass
        
        # Version and other miscellaneous information
        try:
            self.frame.text.AppendText('Chandler Version: %s\n' % version.version)
            
            self.frame.text.AppendText('OS: %s\n' % os.name)
            self.frame.text.AppendText('Platform: %s\n' % sys.platform)
            try:
                self.frame.text.AppendText('Windows Version: %s\n' % str(sys.getwindowsversion()))
            except:
                pass
            self.frame.text.AppendText('Python Version: %s\n' % sys.version)
        except:
            pass
        
        # Traceback (actually just the first line of it)
        self.frame.text.AppendText(st)

    def CreateOutputWindow(self, st):
        global activeWindow
        activeWindow = self
        
        self.frame = xrcFRAME(None)
        self.text = self.frame.text # superclass expects self.text
        
        self._fillRequiredSection(st)
        self._fillOptionalSection()
        self.frame.delButton.Disable()
        
        # Need accelerators so that we can make ESC close the window
        accelerators = wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_ESCAPE,
                                             wx.ID_CANCEL)
                                           ])
        self.frame.SetAcceleratorTable(accelerators)

        size = wx.Size(450, 400)
        self.frame.SetMinSize(size)
        self.frame.Fit()
        self.frame.Show(True)
        
        self.frame.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.frame.Bind(wx.EVT_BUTTON, self.OnCloseWindow, self.frame.closeButton)
        self.frame.Bind(wx.EVT_MENU, self.OnCloseWindow)
        self.frame.Bind(wx.EVT_BUTTON, self.OnSend, self.frame.sendButton)

    def OnCloseWindow(self, event):
        if self.frame.disableFeedback.IsChecked():
            wx.GetApp().RestoreStdio()
        global activeWindow
        wx.PyOnDemandOutputWindow.OnCloseWindow(self, event)
        activeWindow = None
        if destroyAppOnClose:
            import sys
            sys.exit(0)
            # XXX This would probably be better (we might leak resources with
            # XXX sys.exit), but causes Python crash            
            #wx.GetApp().Destroy()

    def OnSend(self, event):
        self.frame.sendButton.Disable()
        # Disabling the focused button disables keyboard navigation
        # unless we set the focus to something else - let's put it
        # on close button
        self.frame.closeButton.SetFocus() 
        self.frame.sendButton.SetLabel(_(u'Sending...'))
        
        try:
            from M2Crypto import httpslib, SSL
            # Try to load the CA certificates for secure SSL.
            # If we can't load them, the data is hidden from casual observation,
            # but a man-in-the-middle attack is possible.
            ctx = SSL.Context()
            opts = {}
            if ctx.load_verify_locations('parcels/osaf/framework/certstore/cacert.pem') == 1:
                ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert, 9)
                opts['ssl_context'] = ctx
            c = httpslib.HTTPSConnection('feedback.osafoundation.org', 443, opts)
            body = buildXML(self.frame.comments, self.frame.email,
                            self.frame.sysInfo, self.frame.text)
            c.request('POST', '/desktop/post/submit', body)
            response = c.getresponse()
            if response.status != 200:
                raise Exception('response.status=' + response.status)
            c.close()
        except:
            self.frame.sendButton.SetLabel(_(u'Failed to send'))
        else:
            self.frame.sendButton.SetLabel(_(u'Sent'))
        

def buildXML(comments, email, optional, required):
    """
    Given the possible fields in the error dialog, build an XML file
    of the data.
    """
    ret = ['<feedback xmlns="http://osafoundation.org/xmlns/feedback" version="0.1">']
    
    # The required field consists of field: value lines, followed by either
    # traceback or arbitrary output that was printed to stdout or stderr.
    lastElem = ''
    for line in required.GetValue().split('\n'):
        if lastElem == '':
            sep = line.find(':')
            if line.startswith('Traceback'):
                lastElem = 'traceback'
                ret.append('<%s>' % lastElem)
                ret.append(escape(line))
            elif sep < 0:
                lastElem = 'output'
                ret.append('<%s>' % lastElem)
                ret.append(escape(line))
            else:
                field = line[:sep].replace(' ', '-')
                value = line[sep + 1:].strip()
                ret.append('<%s>%s</%s>' % (field, escape(value), field))
        else:
            ret.append(escape(line))
    if lastElem != '':
        ret.append('</%s>' % lastElem)
    
    # Optional email
    ret.append('<email>%s</email>' % escape(email.GetValue()))
    
    # Optional comments
    ret.append('<comments>')
    ret.append(escape(comments.GetValue()))
    ret.append('</comments>')
    
    # Optional system information and logs
    for i in range(optional.GetItemCount()):
        field = optional.GetItem(i, 0).GetText()
        value = optional.GetItem(i, 1).GetText()
        ret.append('<%s>%s</%s>' % (field, escape(value), field))

    ret.append('</feedback>')
    
    s = '\n'.join(ret)
    
    if isinstance(s, unicode):
        s = s.encode('utf8')
    
    # For debugging purposes:
    #f = open('feedback.xml', 'w')
    #f.write(s)
    #f.close()

    return s

