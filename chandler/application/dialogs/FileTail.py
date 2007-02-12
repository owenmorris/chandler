
import wx, os, stat, time
from util import task
from i18n import ChandlerMessageFactory as _

def displayFileTailWindow(frame, path):

    win = FileTailWindow(frame, -1, path)
    win.CenterOnScreen()
    win.Show()

class FileTailWindow(wx.Dialog):
    def __init__(self, parent, ID, path, size=wx.DefaultSize,
           pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE):
           # |wx.RESIZE_BORDER):

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, ID, path, pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this


        self.fontsize = 9

        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.text = wx.TextCtrl(self, -1, "",
            pos=wx.DefaultPosition, size=[600,700], style=wx.TE_MULTILINE)
        self.UpdateFont()
        sizer.Add(self.text, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)

        btn = wx.Button(self, -1, _(u"Mark"))
        self.Bind(wx.EVT_BUTTON, self.OnMark, id=btn.GetId())
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _(u"Clear"))
        self.Bind(wx.EVT_BUTTON, self.OnClear, id=btn.GetId())
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _(u"Copy to Clipboard"))
        self.Bind(wx.EVT_BUTTON, self.OnCopy, id=btn.GetId())
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _(u"Font++"))
        self.Bind(wx.EVT_BUTTON, self.OnFontIncrease, id=btn.GetId())
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        btn = wx.Button(self, -1, _(u"Font--"))
        self.Bind(wx.EVT_BUTTON, self.OnFontDecrease, id=btn.GetId())
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        recent = "".join(file(path, "r").readlines()[-500:])
        self.AddLine(recent)

        self.task = TailTask(path, self)
        self.task.start(inOwnThread=True)

    def UpdateFont(self):
        font = wx.Font(self.fontsize, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self.text.SetFont(font)
        wx.Yield()
        self.text.ShowPosition(self.text.GetLastPosition())

    def OnFontIncrease(self, evt):
        self.fontsize += 1
        self.UpdateFont()

    def OnFontDecrease(self, evt):
        self.fontsize -= 1
        self.UpdateFont()

    def AddLine(self, text):
        position = self.text.GetLastPosition()
        if position > 200000: # max size
            self.text.Remove(0, 50000) # trim amount
            position = self.text.GetLastPosition()
        self.text.AppendText(text)
        wx.Yield()
        self.text.ShowPosition(self.text.GetLastPosition())
        wx.Yield()

    def OnMark(self, evt):
        self.AddLine("- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n")

    def OnClear(self, evt):
        self.text.Clear()
        self.UpdateFont()

    def OnCopy(self, evt):
        gotClipboard = wx.TheClipboard.Open()
        if gotClipboard:
            wx.TheClipboard.SetData(wx.TextDataObject(self.text.GetValue()))
            wx.TheClipboard.Close()

    def ShutdownInitiated(self):
        self.task.cancelRequested = True
        self.task.window = None
        self.Destroy()

    def OnOK(self, evt):
        self.ShutdownInitiated()


class TailTask(task.Task):

    def __init__(self, path, window):
        super(TailTask, self).__init__()
        self.path = path
        self.window = window

    def error(self, err):
        pass
        # print "task error", err

    def success(self, result):
        pass
        # print "task success", result

    def shutdownInitiated(self, arg):
        if self.window is not None:
            self.callInMainThread(self.window.ShutdownInitiated, None)

    def run(self):
        self.cancelRequested = False
        tail = Tail(self.path, only_new=True)
        while not self.cancelRequested:
            line = tail.nextline(self.checkForCancel)
            if line is not None and self.window is not None:
                self.callInMainThread(self.window.AddLine, line)

    def checkForCancel(self):
        return self.cancelRequested



# The following portion of this module was originally copied from the
# Python Cookbook at:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/436477
# Where it says, "Python Cookbook code is freely available for use and review."

# Attached notice:
# Copyright (C) 2005 by The Trustees of the University of Pennsylvania
# Author: Jon Moore

# Modified by Morgen Sagen (to add an interruption callback to nextline())

class Tail(object):
    """The Tail monitor object."""

    def __init__(self, path, only_new = False,
                 min_sleep = 1,
                 sleep_interval = 1,
                 max_sleep = 60):
        """Initialize a tail monitor.
             path: filename to open
             only_new: By default, the tail monitor will start reading from
               the beginning of the file when first opened. Set only_new to
               True to have it skip to the end when it first opens, so that
               you only get the new additions that arrive after you start
               monitoring. 
             min_sleep: Shortest interval in seconds to sleep when waiting
               for more input to arrive. Defaults to 1.0 second.
             sleep_interval: The tail monitor will dynamically recompute an
               appropriate sleep interval based on a sliding window of data
               arrival rate. You can set sleep_interval here to seed it
               initially if the default of 1.0 second doesn't work for you
               and you don't want to wait for it to converge.
             max_sleep: Maximum interval in seconds to sleep when waiting
               for more input to arrive. Also, if this many seconds have
               elapsed without getting any new data, the tail monitor will
               check to see if the log got truncated (rotated) and will
               quietly reopen itself if this was the case. Defaults to 60.0
               seconds.
        """

        # remember path to file in case I need to reopen
        self.path = os.path.abspath(path)
        self.f = open(self.path,"r")
        self.min_sleep = min_sleep * 1.0
        self.sleep_interval = sleep_interval * 1.0
        self.max_sleep = max_sleep * 1.0
        if only_new:
            # seek to current end of file
            file_len = os.stat(path)[stat.ST_SIZE]
            self.f.seek(file_len)
        self.pos = self.f.tell()        # where am I in the file?
        self.last_read = time.time()    # when did I last get some data?
        self.queue = []                 # queue of lines that are ready
        self.window = []                # sliding window for dynamically
                                        # adjusting the sleep_interval

    def _recompute_rate(self, n, start, stop):
        """Internal function for recomputing the sleep interval. I get
        called with a number of lines that appeared between the start and
        stop times; this will get added to a sliding window, and I will
        recompute the average interarrival rate over the last window.
        """
        self.window.append((n, start, stop))
        purge_idx = -1                  # index of the highest old record
        tot_n = 0                       # total arrivals in the window
        tot_start = stop                # earliest time in the window
        tot_stop = start                # latest time in the window
        for i, record in enumerate(self.window):
            (i_n, i_start, i_stop) = record
            if i_stop < start - self.max_sleep:
                # window size is based on self.max_sleep; this record has
                # fallen out of the window
                purge_idx = i
            else:
                tot_n += i_n
                if i_start < tot_start: tot_start = i_start
                if i_stop > tot_stop: tot_stop = i_stop
        if purge_idx >= 0:
            # clean the old records out of the window (slide the window)
            self.window = self.window[purge_idx+1:]
        if tot_n > 0:
            # recompute; stay within bounds
            self.sleep_interval = (tot_stop - tot_start) / tot_n
            if self.sleep_interval > self.max_sleep:
                self.sleep_interval = self.max_sleep
            if self.sleep_interval < self.min_sleep:
                self.sleep_interval = self.min_sleep

    def _fill_cache(self):
        """Internal method for grabbing as much data out of the file as is
        available and caching it for future calls to nextline(). Returns
        the number of lines just read.
        """
        old_len = len(self.queue)
        line = self.f.readline()
        while line != "":
            self.queue.append(line)
            line = self.f.readline()
        # how many did we just get?
        num_read = len(self.queue) - old_len
        if num_read > 0:
            self.pos = self.f.tell()
            now = time.time()
            self._recompute_rate(num_read, self.last_read, now)
            self.last_read = now
        return num_read

    def _dequeue(self):
        """Internal method; returns the first available line out of the
        cache, if any."""
        if len(self.queue) > 0:
            line = self.queue[0]
            self.queue = self.queue[1:]
            return line
        else:
            return None

    def _reset(self):
        """Internal method; reopen the internal file handle (probably
        because the log file got rotated/truncated)."""
        self.f.close()
        self.f = open(self.path, "r")
        self.pos = self.f.tell()
        self.last_read = time.time()

    def nextline(self, callback=None):
        """Return the next line from the file. Blocks if there are no lines
        immediately available."""

        # see if we have any lines cached from the last file read
        line = self._dequeue()
        if line:
            return line

        # ok, we are out of cache; let's get some lines from the file
        if self._fill_cache() > 0:
            # got some
            return self._dequeue()

        # hmm, still no input available
        while True:
            if callback and callback():
                return None
            time.sleep(self.sleep_interval)
            if self._fill_cache() > 0:
                return self._dequeue()
            now = time.time()
            if (now - self.last_read > self.max_sleep):
                # maybe the log got rotated out from under us?
                if os.stat(self.path)[stat.ST_SIZE] < self.pos:
                    # file got truncated and/or re-created
                    self._reset()
                    if self._fill_cache() > 0:
                        return self._dequeue()

    def close(self):
        """Close the tail monitor, discarding any remaining input."""
        self.f.close()
        self.f = None
        self.queue = []
        self.window = []

    def __iter__(self):
        """Iterator interface, so you can do:

        for line in filetail.Tail('log.txt'):
            # do stuff
            pass
        """
        return self

    def next(self):
        """Kick the iterator interface. Used under the covers to support:

        for line in filetail.Tail('log.txt'):
            # do stuff
            pass
        """
        return self.nextline()
