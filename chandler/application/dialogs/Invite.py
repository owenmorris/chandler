#   Copyright (c) 2003-2008 Open Source Applications Foundation
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


import os, wx
from osaf import sharing
from osaf.framework.blocks.Styles import getFont
from osaf.activity import *
import util.task as task
import twisted.internet.defer as defer
import twisted.python.failure as failure
from i18n import ChandlerMessageFactory as _

def Show(collection, parent=None):
    win = InviteFrame(parent, -1, _(u"Invite"), style=wx.DEFAULT_FRAME_STYLE,
        collection=collection)
    win.CenterOnParent()
    win.Show()
    return win

class TicketsTask(task.Task):

    def __init__(self, activity, url, info):
        super(TicketsTask, self).__init__(None)
        self.activity = activity
        self.url = url

        serverHandle = sharing.ChandlerServerHandle(
                            info['host'],
                            port=info['port'],
                            username=info['username'],
                            password=info['password'],
                            useSSL=info['useSSL'],
                            repositoryView=info['view'],
                        )
        self.resource = serverHandle.getResource(info['path'])
        if info['ticket']:
            self.resource.ticketId = info['ticket']
        
    def start(self):
        self.activity.started()
        self.activity.update(totalWork=1)
         # Run in the twisted thread!
        return super(TicketsTask, self).start(inOwnThread=False)

    def error(self, (err, summary, extended)):
        self.result = (summary, extended)
        self.activity.failed(err)

    def success(self, result):
        self.result = result
        self.activity.completed()

    def shutdownInitiated(task):
        self.activity.requestAbort()

    def run(self):
            
        def _createdTickets(results):
            return [res[1] for res in results if res[0]]
        
        def _gotTickets(result):
            if not result:
                dl = defer.DeferredList([
                        self.resource.createTicket(),
                        self.resource.createTicket(write=True)
                    ], consumeErrors=1).addCallback(_createdTickets)
                return dl
            else:
                return result
        
        def _getTicketError(failure):
            return failure
            
        def _ticketsSupported(result):
            if result:
                return self.resource.getTickets().addCallback(_gotTickets)
            else:
                return None
            
        d = self.resource.supportsTickets()
        d.addCallback(_ticketsSupported).addErrback(_getTicketError)

        return d
                
                    

class InviteFrame(wx.Frame):

    def getInviteURLs(self, share, url):
    
        view = self.collection.itsView
        view.commit(sharing.mergeFunction)
        
        info = sharing.getAccountInfo(share.itsView, url)
        
        self.activity = Activity(_(u"Checking tickets..."))
        self.currentTask = TicketsTask(self.activity, url, info)
        self.listener = Listener(activity=self.activity,
                                 callback=self._getURLsUpdate)
        self.currentTask.start()
    
    def _getURLsUpdate(self, activity, status=None, **kw):
        if status == STATUS_ACTIVE:
            self._setStatusText(activity.title)
        elif status == STATUS_COMPLETE:
            count = len(self.currentTask.result or ())
            newTicketCount = 0
            
            if self.currentTask.result is None:
                # Tickets not supported; unable to fetch, etc, etc
                pass
            else:
                conduit = sharing.getShare(self.collection).conduit
                
                def updateTicket(key, ticket):
                    if getattr(conduit, key, None) != ticket.ticketId:
                        setattr(conduit, key, ticket.ticketId)
                        return 1
                    else:
                        return 0
                
                
                for ticket in self.currentTask.result:
                    if ticket.read and not ticket.write:
                        newTicketCount += updateTicket('ticketReadOnly', ticket)
                    elif ticket.read and ticket.write:
                        newTicketCount += updateTicket('ticketReadWrite', ticket)
                
            
            if count != 0:
                if newTicketCount == 0:
                    self._setStatusText(_("Checked ticket(s)."))
                else:
                    self._setStatusText(
                        _(
                            u"Received %(newTicketCount)d new ticket(s)."
                        ) % dict(newTicketCount=newTicketCount)
                    )
            else:
                self._setStatusText(_(u"Unable to check ticket(s)."))
            
            conduit.itsView.commit() # we changed something eh
            self.update(tryToFetch=False)
                    
        elif status == STATUS_FAILED:
            self._setStatusText(
                _(u"Unable to check tickets: See chandler.log for details.")
            )
            sharing.logger.warning("Unable to check tickets: %s",
                                   "\n".join(self.currentTask.result))
            self.update(tryToFetch=False)

    def _setStatusText(self, text):
        oldWidth = self.statusText.Size.width
        self.statusText.SetLabel(text)
        newWidth = max(420, oldWidth)
        self.statusText.Wrap(newWidth)
        self.statusText.Size = (newWidth, self.statusText.MinSize.height)
        self.sizer.Layout()
        self.sizer.SetSizeHints(self)
        self.sizer.Fit(self)

    def _setURLText(self, text):
        if not text:
            if self.msgCtrl.IsShown():
                self.sizer.Detach(self.msgCtrl)
                self.msgCtrl.Hide()
        else:
            if not self.msgCtrl.IsShown():
                self.sizer.Insert(0, self.msgCtrl, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 6)
                self.msgCtrl.Show()

        self.msgCtrl.SetValue(text)
        
        self.sizer.Layout()
        self.sizer.SetSizeHints(self)
        self.sizer.Fit(self)
        # Hack ... We make sure the scroller doesn't appear ... For some
        # reason this comes out wrong on the Mac, and possibly other platforms.
        if text:
            self.msgCtrl.MinSize = (self.msgCtrl.MinSize.width,
                                    self.msgCtrl.GetVirtualSize().height + 24.0)
            self.sizer.Fit(self)

    def update(self, tryToFetch=True):
        share = sharing.getShare(self.collection)

        if tryToFetch:
            url = share.getLocation(privilege='ticketdiscovery')
            self.CopyButton.Enable(False)
            urlText = ''
            self.getInviteURLs(share, url)
        else:
            urlText = _(u"Give out the URL(s) below to invite others to "
                         "subscribe to '%(collection)s':") % {
                            'collection' : self.collection.displayName
                        }
            urlString = (os.linesep * 2).join(sharing.getLabeledUrls(share))

            urlText = "%s%s%s" % (urlText, (os.linesep * 2), urlString)

            self.CopyButton.Enable(True)
            
        self._setURLText(urlText)
        

    def __init__(self, *args, **kwds):
        self.collection = kwds.pop('collection')
        super(InviteFrame, self).__init__(*args, **kwds)

        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico",
            wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.panel = wx.Panel(self, -1)

        # Main sizer, vertical box
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.msgCtrl = wx.TextCtrl(self.panel, -1, "",
                                   style=wx.TE_MULTILINE|wx.TE_READONLY)

        self._setURLText("")

        self.statusText = wx.StaticText(self.panel, -1, "", style=wx.TE_MULTILINE)
        self.statusText.Font = getFont(size=11.0)
        
        # Sizer to contain buttons at bottom, horizontal box
        buttonSizer = wx.StdDialogButtonSizer()

        self.CancelButton = wx.Button(self.panel, wx.ID_CANCEL)
        self.CopyButton = wx.Button(self.panel, wx.ID_OK, _(u"&Copy URL(s)"))
        self.CopyButton.SetDefault()

        buttonSizer.AddButton(self.CancelButton)
        buttonSizer.AddButton(self.CopyButton)
        buttonSizer.Realize()
        
        self.bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomSizer.Add(self.statusText, 1, wx.ALIGN_BOTTOM|wx.BOTTOM|wx.LEFT, 6)
        self.bottomSizer.Add(buttonSizer, 0, wx.ALIGN_BOTTOM|wx.TOP, 6)
        
        self.sizer.Add(self.bottomSizer, 0, wx.EXPAND|wx.BOTTOM, 12)
        self.sizer.MinSize = (420, 24)
        
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.sizer)

        self.update()

        self.panel.Layout()
        self.sizer.Fit(self)
        self.CenterOnParent()

        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnCopy, id=wx.ID_OK)

    def OnCancel(self, event):
        self.Destroy()

    def OnCopy(self, event):
        gotClipboard = wx.TheClipboard.Open()
        if gotClipboard:
            share = sharing.getShare(self.collection)
            urlString = (os.linesep * 2).join(sharing.getLabeledUrls(share))
            wx.TheClipboard.SetData(wx.TextDataObject(unicode(urlString)))
            wx.TheClipboard.Close()
