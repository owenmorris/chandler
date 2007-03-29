#   Copyright (c) 2005-2007 Open Source Applications Foundation
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
Test Password
"""

import unittest, time
from binascii import hexlify, unhexlify
import wx
from application import schema
from osaf.framework import password, MasterPassword
from osaf.pim.tests import TestDomainModel
from osaf.framework.twisted import waitForDeferred
from i18n.tests import uw

class PasswordTestCase(TestDomainModel.DomainModelTestCase):
    def _dontBeStupid(self, pw, pword, masterPassword, expectedLen=192):
        self.assertNotEqual(unicode(hexlify(pw.ciphertext), 'utf8'), pword)
        self.assertNotEqual(unicode(hexlify(pw.iv), 'utf8'), pword)
        self.assertNotEqual(unicode(hexlify(pw.salt), 'utf8'), pword)

        self.assertNotEqual(pw.ciphertext, pword.encode('utf8'))
        self.assertNotEqual(pw.iv, pword.encode('utf8'))
        self.assertNotEqual(pw.salt, pword.encode('utf8'))
        
        self.assertNotEqual(unicode(hexlify(pw.ciphertext), 'utf8'), masterPassword)
        self.assertNotEqual(unicode(hexlify(pw.iv), 'utf8'), masterPassword)
        self.assertNotEqual(unicode(hexlify(pw.salt), 'utf8'), masterPassword)
        
        self.assertNotEqual(pw.ciphertext, masterPassword.encode('utf8'))
        self.assertNotEqual(pw.iv, masterPassword.encode('utf8'))
        self.assertNotEqual(pw.salt, masterPassword.encode('utf8'))
        
        self.assertEqual(len(hexlify(pw.ciphertext)), expectedLen)
        self.assertEqual(len(hexlify(pw.iv)), 64)
        self.assertEqual(len(hexlify(pw.salt)), 64)
        self.assertNotEqual(pw.salt, pw.iv)
    
    def testPassword(self):
        self.loadParcel("osaf.framework.MasterPassword")
        self.loadParcel("osaf.framework.password")

        pword = uw('my secr3t p4ssw0rd')
        masterPassword = uw('M0r3 s3cr3t')
        
        self.assertEqual(masterPassword, unicode(masterPassword.encode('utf8'), 'utf8'))
        
        # create
        pw = password.Password(itsView=self.rep.view)

        # check that we can't get password yet
        self.assertRaises(password.UninitializedPassword, waitForDeferred, pw.decryptPassword(masterPassword))
        
        # Check that empty values lead to UninitializedPassword as well
        pw.ciphertext = ''
        pw.iv   = ''
        pw.salt = ''
        self.assertRaises(password.UninitializedPassword, waitForDeferred, pw.decryptPassword(masterPassword))
        # And that bad values leads to DecryptionError
        pw.ciphertext = \
                  unhexlify('0001efa4bd154ee415b9413a421cedf04359fff945a30e7c115465b1c780a85b65c0e45c')
        pw.iv   = unhexlify('5cd148eeaf680d4ff933aed83009cad4110162f53ef89fd44fad09611b0524d4')
        pw.salt = unhexlify('a48e09ba0530422c7e96fe62643e149efce2a17e026ba98da8ee51a895ead25b')
        self.assertRaises(password.DecryptionError, waitForDeferred, pw.decryptPassword(masterPassword))
                
        # What happens if we supply wrong master password?
        pw.ciphertext = unhexlify('908ed5801146c55f7305dd8a07fa468f68fd0e3e7e075c6e42a9f922f8f5b461a2d32cc2eda4130085fa27c2a124d89f6e1c004245f3a1f9f101cb9bb30b6bcfe8685d01bffa2e659f567c9d1c44d564e87b469884de3dd070e9611be4666391')
        pw.iv = unhexlify('2a4c722617afd356bc0dc9c2cb26aa0013fbaf81928769485ed7c01d333f2952')
        pw.salt = unhexlify('0ee664ffa11c6856d5c6dc553413b6a3ee7d43b3b2c4252c1b8a4ca308387b9c')
        self.assertEqual(waitForDeferred(pw.decryptPassword(masterPassword=masterPassword)), pword)
        self.assertRaises(password.DecryptionError, waitForDeferred, pw.decryptPassword(masterPassword=uw('M0r3 wrongt')))
        self.assertRaises(password.DecryptionError, waitForDeferred, pw.decryptPassword(masterPassword=''))

        # check that we can use even empty master password
        waitForDeferred(pw.encryptPassword(pword, masterPassword=''))
        # make sure we didn't do anything stupid
        self._dontBeStupid(pw, pword, masterPassword='')
        # confirm we can get the password out
        self.assertEqual(waitForDeferred(pw.decryptPassword(masterPassword='')), pword)

        # check normal
        waitForDeferred(pw.encryptPassword(pword, masterPassword=masterPassword))        
        # make sure we didn't do anything stupid
        self._dontBeStupid(pw, pword, masterPassword)
        # confirm we can get the password out
        self.assertEqual(waitForDeferred(pw.decryptPassword(masterPassword=masterPassword)), pword)
        # and double check...
        self._dontBeStupid(pw, pword, masterPassword)

        # check long password
        waitForDeferred(pw.encryptPassword('12345678901234567890123456789012345678901234567890123456789012345678901234567890', masterPassword=masterPassword))
        # make sure we didn't do anything stupid
        self._dontBeStupid(pw, '12345678901234567890123456789012345678901234567890123456789012345678901234567890', masterPassword, 320)
        # confirm we can get the password out
        self.assertEqual(waitForDeferred(pw.decryptPassword(masterPassword=masterPassword)), '12345678901234567890123456789012345678901234567890123456789012345678901234567890')

        # check empty passwords
        waitForDeferred(pw.encryptPassword('', masterPassword=''))
        # make sure we didn't do anything stupid
        self._dontBeStupid(pw, '', '', 160)
        # confirm we can get the password out
        self.assertEqual(waitForDeferred(pw.decryptPassword(masterPassword='')), '')
        
        # test async deferred (in our case more like sync...)
        d = pw.decryptPassword(masterPassword='')
        self.called = False
        def callback(passwordString):
            self.assertEqual(passwordString, '')
            self.called = True
        d.addCallback(callback)
        self.assertTrue(self.called)
        
        # clear
        waitForDeferred(pw.clear())
        self.assertRaises(password.UninitializedPassword, waitForDeferred, pw.decryptPassword(masterPassword))

        d = pw.clear()
        self.called = False
        def nonecallback(a):
            self.assertTrue(a is None)
            self.called = True
        d.addCallback(nonecallback)
        self.assertTrue(self.called)

        
    def testMasterPassword(self):
        self.loadParcel("osaf.framework.MasterPassword")
        self.loadParcel("osaf.framework.password")
        self.loadParcel("osaf.app") # Include default Passwords in count

        # Check master password when it is not set
        masterPassword = waitForDeferred(MasterPassword.get(self.rep.view))
        self.assertEqual(masterPassword, '')

        prefs = schema.ns("osaf.framework.MasterPassword",
                          self.rep.view).masterPasswordPrefs

        # check prefs
        self.assertEqual(prefs.masterPassword, False)
        self.assertEqual(prefs.timeout, 15)

        prefs.masterPassword = True

        # make sure that get at least tries to use wx, and creates MasterPassword
        self.assertRaises(wx.PyNoAppError, waitForDeferred, MasterPassword.get(self.rep.view))
        self.assertTrue(MasterPassword._masterPassword is None)
        self.assertTrue(MasterPassword._timer is None)

        # make sure we get the password ok when it's set
        MasterPassword._masterPassword = 'pass'
        self.assertEqual(waitForDeferred(MasterPassword.get(self.rep.view)), 'pass')
        
        # timeout
        prefs.timeout = 1.0/60.0 # 1 second
        MasterPassword._setTimedPassword('pass', 1)
        self.assertEqual(waitForDeferred(MasterPassword.get(self.rep.view)), 'pass')
        time.sleep(1.1)
        # XXX Don't know how to test timeout, _clear is called and d.addCallback has been called
        # XXX but what do we need to do to process those callbacks?
        #self.assertRaises(wx.PyNoAppError, waitForDeferred, MasterPassword.get(self.rep.view))
        prefs.timeout = 15

        waitForDeferred(MasterPassword.clear())
        
        # make sure that change at least tries to use wx, and creates MasterPassword
        self.assertRaises(wx.PyNoAppError, waitForDeferred, MasterPassword.change(self.rep.view))
        self.assertTrue(MasterPassword._masterPassword is None)
        self.assertTrue(MasterPassword._timer is None)

        # change for real
        # make some passwords to change
        pw1 = password.Password(itsView=self.rep.view)
        pw2 = password.Password(itsView=self.rep.view)
        waitForDeferred(pw1.encryptPassword('foobar', masterPassword=''))
        waitForDeferred(pw2.encryptPassword('barfoo', masterPassword=''))
        # try with bad old password first
        self.assertFalse(MasterPassword._change('dont know',
                                                'secret',
                                                self.rep.view,
                                                prefs))
        # now change
        self.assertTrue(MasterPassword._change('', 'secret',
                                               self.rep.view,
                                               prefs))
        # verify that the new password works
        self.assertEqual(waitForDeferred(pw1.decryptPassword(masterPassword='secret')), u'foobar')
        self.assertEqual(waitForDeferred(pw2.decryptPassword(masterPassword='secret')), u'barfoo')
        # and that the old raises the correct exception
        self.assertRaises(password.DecryptionError, waitForDeferred, pw1.decryptPassword(masterPassword=''))
        self.assertRaises(password.DecryptionError, waitForDeferred, pw2.decryptPassword(masterPassword=''))

        # clear
        MasterPassword._masterPassword = 'pass'
        waitForDeferred(MasterPassword.clear())
        self.assertTrue(MasterPassword._masterPassword is None)
        self.assertTrue(MasterPassword._timer is None)

        # reset
        count = 0
        for item in password.Password.iterItems(self.rep.view):
            count += 1
        self.assertEqual(count, 9) # dummy + 2 above + 6 default
        MasterPassword.reset(self.rep.view) # now reset
        self.assertTrue(MasterPassword._masterPassword is None)
        self.assertTrue(MasterPassword._timer is None)
        # we should have just one initialized password (the dummy)
        count = 0
        for item in password.Password.iterItems(self.rep.view):
            try:
                waitForDeferred(item.decryptPassword(masterPassword=''))
                self.assertEqual(item.itsName, 'dummyPassword')
                count += 1
            except password.UninitializedPassword:
                pass
        self.assertEqual(count, 1)
        
        # quality tests
        self.assertEqual(MasterPassword.quality(''), (0, 35))
        self.assertEqual(MasterPassword.quality('a'), (0, 35))
        self.assertEqual(MasterPassword.quality('abb'), (6, 35))
        self.assertEqual(MasterPassword.quality('aghj5s'), (14, 35))
        self.assertEqual(MasterPassword.quality('aGhj5s'), (16, 35))
        self.assertEqual(MasterPassword.quality('aGh!5s'), (21, 35))
        self.assertEqual(MasterPassword.quality('aGh!5s.Vos2dd'), (34, 35))
        self.assertEqual(MasterPassword.quality('aGh!5s.Vos2ddd'), (35, 35))
        self.assertEqual(MasterPassword.quality('aGh!5s.Vos2dddF#@8'), (35, 35))
        self.assertEqual(MasterPassword.quality(uw('aghj5s')), (18, 35)) #i18n


if __name__ == "__main__":
    unittest.main()
