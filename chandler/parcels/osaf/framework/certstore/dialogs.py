"""
Certificate store dialogs

@copyright: Copyright (c) 2005 Open Source Applications Foundation
@license:   http://osafoundation.org/Chandler_0.1_license_terms.htm
"""
__parcel__ = "osaf.framework.certstore"

import wx
# XXX Can't import like this, should put utility funcs in util
#from osaf.framework.certstore import certificate

from i18n import OSAFMessageFactory as _
from application.dialogs import messages

class ImportCertificateDialog(wx.Dialog):
    def __init__(self, parent, type, x509, choices, size=wx.DefaultSize,
     pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        """
        Ask the user if they would like to import and trust a certificate.
        
        @param type: Certificate type
        @param x509: The certificate to import.
        @param choices: List of possible trust values.
        """ 

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.
        pre = wx.PreDialog()
        pre.Create(parent, -1, _('Import certificate?'), pos, size, style)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.this = pre.this

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Static text

        from osaf.framework.certstore import certificate
        message = _('Do you want to import this certificate?\nType: %s\nSHA1 fingerprint: %s') % (type, certificate._fingerprint(x509))
        label = wx.StaticText(self, -1, message)
        sizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)

        # multiline readonly edit control
        
        text = wx.TextCtrl(self, -1, x509.as_text(), wx.DefaultPosition, 
                           [400,-1], style=wx.TE_MULTILINE|wx.TE_READONLY)
        sizer.Add(text, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 5)

        # checkboxes
        
        choicebox = wx.BoxSizer(wx.VERTICAL)
        
        cs = []
        for choice in choices:
            cb = wx.CheckBox(self, -1, choice, wx.DefaultPosition, 
                             wx.DefaultSize, style=wx.ALIGN_LEFT)
            cs += [cb]
            choicebox.Add(cb, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        sizer.Add(choicebox, 0, wx.ALIGN_LEFT|wx.ALL, 5)

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

        self.cs = cs
        
    def GetSelections(self):
        sel = []
        index = 0
        for cb in self.cs:
            if cb.IsChecked():
                sel += [index]
            index += 1

        return sel
