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

from application import schema, Globals
from osaf.framework.twisted import waitForDeferred

class DiscoveryBase(object):
    SETTINGS = []

    def __init__(self, hostname, callback, reconnect, view):
        #callback
        # 0 - means no accounts found
        # 1 - means account was found, return account
        # 2 - means SSL cert dialog displayed

        assert(isinstance(hostname, (str, unicode)))
        assert(callback is not None)
        assert(reconnect is not None)
        assert(view is not None)

        self.hostname = hostname
        self.callback = callback
        self.reconnect = reconnect
        self.view = view

        self.nextSettingsPos = 0
        self.curAccount = None
        self.cancel = False

    def discover(self):
        self.cancel = False
        self._tryNextSetting()

    def cancelDiscovery(self):
        self.cancel = True

    def _tryNextSetting(self):
        if self.cancel:
            return

        if self.nextSettingsPos >= len(self.SETTINGS):
            self.callback((0, None))
            return

        settings = self.SETTINGS[self.nextSettingsPos]

        self._setCurAccount(settings)

        # Commit the view so the twisted thread can
        # see the account changes
        self.view.commit()

        self.nextSettingsPos += 1

        m = getattr(Globals.mailService, "get%sInstance" % settings['type'])

        client = m(self.curAccount)

        self._discoverAccount(client)

    def _setCurAccount(self, settings):
        raise NotImplementedError()

    def _discoverAccount(self, client):
        raise NotImplementedError()

    def _testResults(self, results):
        if self.cancel:
            return

        statusCode = results[0]

        if statusCode == 1:
            # We found an account
            self.callback((1, self.curAccount))

        elif statusCode == 2:
            # The SSL cert dialog was displayed
            self.callback((2, None))

        elif self.nextSettingsPos >= len(self.SETTINGS):
            # We tried all the options in the SETTINGS list
            self.callback((0, None))

        else:
            # Try the next setting in the SETTINGS list
            self._tryNextSetting()


class OutgoingDiscovery(DiscoveryBase):
    SETTINGS = [
        {"type": "SMTP", "port": 465, "connectionSecurity": "SSL"},
        {"type": "SMTP", "port": 587, "connectionSecurity": "TLS"},
        {"type": "SMTP", "port": 25, "connectionSecurity": "TLS"},
        {"type": "SMTP", "port": 587, "connectionSecurity": "NONE"},
        {"type": "SMTP", "port": 25, "connectionSecurity": "NONE"},
    ]

    def __init__(self, hostname, callback, reconnect, view):
        super(OutgoingDiscovery, self).__init__(hostname, callback, reconnect, view)
        self.smtpAccount = schema.ns('osaf.app', self.view).TestSMTPAccount

    def _setCurAccount(self, settings):
        self.smtpAccount.host = self.hostname
        self.smtpAccount.port = settings['port']
        self.smtpAccount.connectionSecurity = settings['connectionSecurity']

        #Reset all username and password info
        self.smtpAccount.useAuth  = False
        self.smtpAccount.username = u""
        waitForDeferred(self.smtpAccount.password.clear())

        self.curAccount = self.smtpAccount

    def _discoverAccount(self, client):
        client.testAccountSettings(self._testResults, self.reconnect)


class IncomingDiscovery(DiscoveryBase):
    IMAP_SETTINGS = [
        {"type": "IMAP", "port": 993, "connectionSecurity": "SSL"},
        {"type": "IMAP", "port": 143, "connectionSecurity": "TLS"},
        {"type": "POP",  "port": 995, "connectionSecurity": "SSL"},
        {"type": "POP",  "port": 110, "connectionSecurity": "TLS"},
        {"type": "IMAP", "port": 143, "connectionSecurity": "NONE"},
        {"type": "POP",  "port": 110, "connectionSecurity": "NONE"},
    ]

    POP_SETTINGS = [
        {"type": "POP",  "port": 995, "connectionSecurity": "SSL"},
        {"type": "POP",  "port": 110, "connectionSecurity": "TLS"},
        {"type": "IMAP", "port": 993, "connectionSecurity": "SSL"},
        {"type": "IMAP", "port": 143, "connectionSecurity": "TLS"},
        {"type": "POP",  "port": 110, "connectionSecurity": "NONE"},
        {"type": "IMAP", "port": 143, "connectionSecurity": "NONE"},
    ]

    def __init__(self, hostname, callback, reconnect, view):
        super(IncomingDiscovery, self).__init__(hostname, callback, reconnect, view)
        self.imapAccount = schema.ns('osaf.app', self.view).TestIMAPAccount
        self.popAccount = schema.ns('osaf.app', self.view).TestPOPAccount

        if hostname.lower().startswith(u"pop."):
            # If the hostname begins with pop
            # then chances are it is a POP3 server
            # so try the POP secure settings first
            # before trying IMAP secure settings
            self.SETTINGS = self.POP_SETTINGS
        else:
            # This is the default which is to
            # try IMAP secure settings first
            self.SETTINGS = self.IMAP_SETTINGS


    def _setCurAccount(self, settings):
        if settings['type'] == "IMAP":
            self.imapAccount.host = self.hostname
            self.imapAccount.port = settings['port']
            self.imapAccount.connectionSecurity = settings['connectionSecurity']
            self.curAccount = self.imapAccount

        elif settings['type'] == "POP":
            self.popAccount.host = self.hostname
            self.popAccount.port = settings['port']
            self.popAccount.connectionSecurity = settings['connectionSecurity']
            self.curAccount = self.popAccount

        else:
            #XXX this should never be reached
            raise Exception()

        # reset all username and password info
        self.curAccount.username = u""
        waitForDeferred(self.curAccount.password.clear())

    def _discoverAccount(self, client):
        client.testAccountSettings(self._testResults, self.reconnect, logIn=False)

