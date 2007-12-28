#   Copyright (c) 2003-2007 Open Source Applications Foundation
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
    'SharingAccount',
    'WebDAVAccount',
    'Proxy',
    'getProxy',
    'getProxies',
]

from application import schema
from osaf import pim
import conduits, utility, webdav_conduit, caldav_conduit, errors
from shares import Share, SharedItem
import logging
import urlparse, re
from osaf.framework.password import passwordAttribute, Password
from osaf.framework.twisted import waitForDeferred
import zanshin, M2Crypto, twisted
from application.Utility import CertificateVerificationError
import wx
from i18n import ChandlerMessageFactory as _


logger = logging.getLogger(__name__)

class SharingAccount(pim.ContentItem):

    username = schema.One(
        schema.Text, initialValue = u'',
    )

    password = passwordAttribute

    host = schema.One(
        schema.Text,
        doc = 'The hostname of the account',
        initialValue = u'',
    )
    path = schema.One(
        schema.Text,
        doc = 'Base path on the host to use for publishing',
        initialValue = u'',
    )
    port = schema.One(
        schema.Integer,
        doc = 'The non-SSL port number to use',
        initialValue = 80,
    )
    useSSL = schema.One(
        schema.Boolean,
        doc = 'Whether or not to use SSL/TLS',
        initialValue = False,
    )

    accountProtocol = schema.One(
        initialValue = '',
    )

    accountType = schema.One(
        initialValue = '',
    )

    conduits = schema.Sequence(
        conduits.HTTPMixin,
        inverse=conduits.HTTPMixin.account
    )

    def getLocation(self):
        """
        Return the base url of the account
        """

        if self.useSSL:
            scheme = "https"
            defaultPort = 443
        else:
            scheme = "http"
            defaultPort = 80

        if self.port == defaultPort:
            url = "%s://%s" % (scheme, self.host)
        else:
            url = "%s://%s:%d" % (scheme, self.host, self.port)

        sharePath = self.path.strip("/")
        url = urlparse.urljoin(url, sharePath + "/")
        return url

    @classmethod
    def findMatchingAccount(cls, view, url):
        """
        Find a Sharing account which corresponds to a URL.

        The url being passed in is for a collection -- it will include the
        collection name in the url.  We need to find a webdav account who
        has been set up to operate on the parent directory of this collection.
        For example, if the url is http://pilikia.osafoundation.org/dev1/foo/
        we need to find an account whose schema+host+port match and whose path
        starts with /dev1

        Note: this logic assumes only one account will match; you aren't
        currently allowed to have to multiple webdav accounts pointing to the
        same scheme+host+port+path combination.

        @param view: The repository view object
        @type view: L{chandlerdb.persistence.RepositoryView}
        @param url: The url which points to a collection
        @type url: String
        @return: An account item, or None if no WebDAV account could be found.
        """

        (scheme, useSSL, host, port, path, query, fragment, ticket, parentPath,
            shareName) = utility.splitUrl(url)

        # Get the parent directory of the given path:
        # '/dev1/foo/bar' becomes ['dev1', 'foo']
        path = path.strip('/').split('/')[:-1]
        # ['dev1', 'foo'] becomes "dev1/foo"
        path = "/".join(path)

        for account in cls.iterItems(view):
            # Does this account's url info match?
            accountPath = account.path.strip('/')
            if (account.isSetUp() and
                account.useSSL == useSSL and
                account.host == host and
                account.port == port and
                path.startswith(accountPath)):
                return account

        return None

    def isSetUp(self):
        return bool(self.host and self.username)

class WebDAVAccount(SharingAccount):

    accountProtocol = schema.One(
        initialValue = 'WebDAV',
    )

    accountType = schema.One(
        initialValue = 'SHARING_DAV',
    )


    def publish(self, collection, displayName=None, activity=None, filters=None,
        overwrite=False, options=None):

        from ics import ICSSerializer
        from translator import SharingTranslator
        from eimml import EIMMLSerializer


        rv = self.itsView

        # Stamp the collection
        if not pim.has_stamp(collection, SharedItem):
            SharedItem(collection).add()

        conduit = webdav_conduit.WebDAVRecordSetConduit(itsView=rv,
            account=self)

        # Interrogate the server associated with the account

        location = self.getLocation()
        if not location.endswith("/"):
            location += "/"
        handle = conduit._getServerHandle()
        resource = handle.getResource(location)

        logger.debug('Examining %s ...', location.encode('utf8', 'replace'))
        exists = handle.blockUntil(resource.exists)
        if not exists:
            logger.debug("...doesn't exist")
            raise errors.NotFound(_(u"%(location)s does not exist.") %
                {'location': location})

        isCalendar = handle.blockUntil(resource.isCalendar)
        logger.debug('...Calendar?  %s', isCalendar)
        isCollection =  handle.blockUntil(resource.isCollection)
        logger.debug('...Collection?  %s', isCollection)

        response = handle.blockUntil(resource.options)
        dav = response.headers.getHeader('DAV')
        logger.debug('...DAV:  %s', dav)
        allowed = response.headers.getHeader('Allow')
        logger.debug('...Allow:  %s', allowed)
        supportsTickets = handle.blockUntil(resource.supportsTickets)
        logger.debug('...Tickets?:  %s', supportsTickets)

        conduit.delete(True) # Clean up the temporary conduit


        # Prepare the share

        share = None

        try:

            if isCalendar:
                # We've been handed a calendar directly.  Just publish directly
                # into this calendar collection rather than making a new one.
                # Create a CalDAV share with empty sharename, doing a GET and
                # PUT

                share = Share(itsView=rv, contents=collection)
                conduit = caldav_conduit.CalDAVRecordSetConduit(itsParent=share,
                    account=self, shareName=u"", translator=SharingTranslator,
                    serializer=ICSSerializer)
                share.conduit = conduit
                if filters:
                    conduit.filters = filters

                share.displayName = displayName or collection.displayName

                alias = 'main'
                try:
                    SharedItem(collection).shares.append(share, alias)
                except ValueError:
                    # There is already a 'main' share for this collection
                    SharedItem(collection).shares.append(share)

                share.sync(activity=activity)

            else:
                # the collection should be published
                # determine a share name
                existing = utility.getExistingResources(self)
                displayName = displayName or collection.displayName

                shareName = displayName

                alias = 'main'

                # See if there are any non-ascii characters, if so, just use
                # UUID
                try:
                    shareName.encode('ascii')
                    pattern = re.compile('[^A-Za-z0-9]')
                    shareName = re.sub(pattern, "_", shareName)
                except UnicodeEncodeError:
                    shareName = unicode(collection.itsUUID)

                # Append .ics extension of publishing a monolithic .ics file
                if options.get('ics', False):
                    shareName = shareName + ".ics"

                shareName = self._uniqueName(shareName, existing)

                if ('calendar-access' in dav or 'MKCALENDAR' in allowed):
                    # We're speaking to a CalDAV server

                    share = Share(itsView=rv, contents=collection)
                    conduit = caldav_conduit.CalDAVRecordSetConduit(
                        itsParent=share,
                        account=self, shareName=shareName,
                        translator=SharingTranslator, serializer=ICSSerializer)
                    share.conduit = conduit
                    if filters:
                        conduit.filters = filters

                    share.displayName = displayName or collection.displayName

                    try:
                        SharedItem(collection).shares.append(share, alias)
                    except ValueError:
                        # There is already a 'main' share for this collection
                        SharedItem(collection).shares.append(share)

                    if share.exists():
                        raise errors.SharingError(_(u"Collection already exists on server."))

                    share.create()
                    # bug 8128, this setDisplayName shouldn't be required, but
                    # cosmo isn't accepting setting displayname in MKCALENDAR
                    share.conduit.setDisplayName(displayName)

                    share.put(activity=activity)

                    # tickets after putting
                    if supportsTickets:
                        share.conduit.createTickets()


                elif dav is not None:

                    # We're speaking to a WebDAV server
                    # Use monolithic ics if options['ics'], else use EIMML

                    share = Share(itsView=rv, contents=collection)

                    if options.get('ics', False):
                        # ICS
                        conduit = webdav_conduit.WebDAVMonolithicRecordSetConduit(
                            itsParent=share,
                            shareName=shareName, account=self,
                            translator=SharingTranslator,
                            serializer=ICSSerializer)

                    else:
                        conduit = webdav_conduit.WebDAVRecordSetConduit(
                            itsParent=share,
                            shareName=shareName, account=self,
                            translator=SharingTranslator,
                            serializer=EIMMLSerializer)

                    share.conduit = conduit
                    if filters:
                        conduit.filters = filters

                    try:
                        SharedItem(collection).shares.append(share, alias)
                    except ValueError:
                        # There is already a 'main' share for this collection
                        SharedItem(collection).shares.append(share)

                    if share.exists():
                        raise errors.SharingError(_(u"Collection already exists on server."))

                    share.create()
                    share.put(activity=activity)

                    if supportsTickets:
                        share.conduit.createTickets()


        except (errors.SharingError,
                zanshin.error.Error,
                M2Crypto.SSL.Checker.WrongHost,
                CertificateVerificationError,
                twisted.internet.error.TimeoutError), e:

            # Clean up share objects
            try:
                share.delete(True)
            except:
                pass # ignore stale shares

            # Note: the following "raise e" line used to just read "raise".
            # However, if the try block immediately preceeding this comment
            # raises an exception, the "raise" following this comment was
            # raising that *new* exception instead of the original exception
            # that got us here, "e".
            raise e

        return share


    def _uniqueName(self, basename, existing):
        name = basename
        counter = 1
        while name in existing:
            name = "%s-%d" % (basename, counter)
            counter += 1
        return name


    def publishOptionsDialog(self, options):
        win = WebDAVOptionsDialog(wx.GetApp().mainFrame, -1, _(u"Options"),
            style=wx.DEFAULT_DIALOG_STYLE, options=options)
        win.CenterOnParent()
        win.ShowModal()
        win.Destroy()

class WebDAVOptionsDialog(wx.Dialog):

    def __init__(self, *args, **kwds):

        self.options = kwds['options']
        del kwds['options']

        super(WebDAVOptionsDialog, self).__init__(*args, **kwds)
        icon = wx.Icon("Chandler.egg-info/resources/icons/Chandler_32.ico",
            wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.panel = wx.Panel(self, -1)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.messageLabel = wx.StaticText(self.panel, -1,
            _("WebDAV Publish Options:"))
        self.sizer.Add(self.messageLabel, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        self.ICSCheckbox = wx.CheckBox(self.panel, -1,
            _(u"Publish as ICS file"))
        self.sizer.Add(self.ICSCheckbox, 1, wx.ALIGN_LEFT|wx.ALL, 5)

        if self.options and self.options.get('ics', False):
            self.ICSCheckbox.SetValue(True)

        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.CancelButton = wx.Button(self.panel, wx.ID_CANCEL, _(u"Cancel"))
        self.OkButton = wx.Button(self.panel, wx.ID_OK, _(u"OK"))
        self.OkButton.SetDefault()
        self.buttonSizer.Add(self.CancelButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.buttonSizer.Add(self.OkButton, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.sizer.Add(self.buttonSizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.panel.SetAutoLayout(True)
        self.panel.SetSizer(self.sizer)
        self.panel.Layout()
        self.sizer.Fit(self)

        self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=wx.ID_CANCEL)

    def OnOK(self, evt):
        self.options['ics'] = self.ICSCheckbox.GetValue()
        self.EndModal(True)

    def OnCancel(self, evt):
        self.EndModal(True)



class Proxy(schema.Item):
    host = schema.One(schema.Text, defaultValue = u'')
    port = schema.One(schema.Integer, defaultValue = 8080)
    protocol = schema.One(schema.Text, defaultValue = u'HTTP')
    useAuth = schema.One(schema.Boolean, defaultValue = False)
    username = schema.One(schema.Text, defaultValue = u'')
    password = passwordAttribute
    active = schema.One(schema.Boolean, defaultValue = False)
    bypass = schema.One(schema.Text, defaultValue = u'localhost, .local, 127.0.0.1')

    def getPasswd(self):
        pw = getattr(self, "password", None)
        if pw is None:
            return ""
        else:
            return waitForDeferred(pw.decryptPassword())

    def setPasswd(self, text):
        pw = getattr(self, "password", None)
        if pw is None:
            if text is None:
                return
            pw = Password(itsParent=self)
            self.password = pw
        waitForDeferred(pw.encryptPassword(text))

    def delPasswd(self):
        if hasattr(self, "password"):
            pw = self.password
            if pw is not None:
                pw.Delete(recursive=True)
            del self.password

    # use 'proxy.passwd' for convenience.  I would have named this property
    # 'password', but Password.holders seems to require 'password' to be a
    # persistent attribute.
    passwd = property(getPasswd, setPasswd, delPasswd)

    def appliesTo(self, host):
        if not self.bypass:
            return True # not bypassing anything

        host = host.lower()
        for s in self.bypass.lower().split(','):
            if s:
                s = s.strip()
                if s[0].isalpha() or s[0] == '.': # hostname/domain
                    if host.endswith(s):
                        return False # a match; we're not proxying this host
                else: # IP address
                    if host.startswith(s):
                        return False # a match; we're not proxying this host

        return True


def getProxy(rv, protocol=u'HTTP'):
    for proxy in Proxy.iterItems(rv):
        if proxy.protocol == protocol:
            return proxy
    return Proxy(itsView=rv, protocol=protocol, active=False)

def getProxies(rv):
    return list(Proxy.iterItems(rv))
