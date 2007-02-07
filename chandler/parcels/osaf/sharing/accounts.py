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

__all__ = [
    'WebDAVAccount',
]

from application import schema
from osaf import pim
import conduits, utility
import logging
import urlparse
from i18n import ChandlerMessageFactory as _

logger = logging.getLogger(__name__)

class WebDAVAccount(pim.ContentItem):
    schema.kindInfo(
        description="A WebDAV 'Account'\n\n"
            "Issues:\n"
            "   Long term we're probably not going to treat WebDAV as an "
            "account, but rather how a web browser maintains URL-to-ACL "
            "mappings.\n",
    )
    username = schema.One(
        schema.Text, initialValue = u'',
    )
    password = schema.One(
        schema.Text,
        description =
            'Issues: This should not be a simple string. We need some solution for '
            'encrypting it.\n',
        initialValue = u'',
    )
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
        initialValue = 'WebDAV',
    )

    accountType = schema.One(
        initialValue = 'SHARING_DAV',
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
        Find a WebDAV account which corresponds to a URL.

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
        @type view: L{repository.persistence.RepositoryView}
        @param url: The url which points to a collection
        @type url: String
        @return: An account item, or None if no WebDAV account could be found.
        """

        (useSSL, host, port, path, query, fragment, ticket, parentPath,
            shareName) = utility.splitUrl(url)

        # Get the parent directory of the given path:
        # '/dev1/foo/bar' becomes ['dev1', 'foo']
        path = path.strip('/').split('/')[:-1]
        # ['dev1', 'foo'] becomes "dev1/foo"
        path = "/".join(path)

        for account in cls.iterItems(view):
            # Does this account's url info match?
            accountPath = account.path.strip('/')
            if account.useSSL == useSSL and account.host == host and \
               account.port == port and path.startswith(accountPath):
                return account

        return None

