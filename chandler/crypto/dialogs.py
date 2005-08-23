"""
Crypto dialogs

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""

import logging
import wx
from i18n import OSAFMessageFactory as _
from application.dialogs import messages

log = logging.getLogger(__name__)

class TrustSiteCertificateDialog(wx.Dialog):
    def __init__(self, parent, x509, size=wx.DefaultSize,
     pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        """
        Ask the user if they would like to trust the certificate presented by
        the site we are connecting to.

        @param x509: The certificate the site returned.
        """ 

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, -1, _('Trust site certificate?'), pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Static text

        # XXX depends on parcels
        import osaf.framework.certstore.certificate as certificate
        message = _('Do you want to trust this certificate?\nSHA1 fingerprint: %s') % certificate._fingerprint(x509)
        label = wx.StaticText(self, -1, message)
        sizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # multiline readonly edit control
        
        text = wx.TextCtrl(self, -1, x509.as_text(), wx.DefaultPosition, 
                           [400,-1], style=wx.TE_MULTILINE|wx.TE_READONLY)
        sizer.Add(text, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)

        # radio
        
        radiobox = wx.BoxSizer(wx.VERTICAL)
        
        first = True
        rbs = []
        choices=[_('Trust the authenticity of this certificate until program exit.'),
                 _('Trust the authenticity of this certificate permanently.')]
        for choice in choices:
            if first:
                style = wx.ALIGN_LEFT|wx.RB_GROUP
                first = False
            else:
                style = wx.ALIGN_LEFT
            rb = wx.RadioButton(self, -1, choice, wx.DefaultPosition, 
                                wx.DefaultSize, style)
            rbs += [rb]
            radiobox.Add(rb, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.Add(radiobox, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # OK, Cancel buttons

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK, messages.OK_BUTTON)
        box.Add(btn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        btn = wx.Button(self, wx.ID_CANCEL, messages.CANCEL_BUTTON)
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        sizer.Add(box, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

        self.rbs = rbs

    def GetSelection(self):
        sel = 0
        for rb in self.rbs:
            if rb.GetValue():
                return sel
            sel += 1
            
