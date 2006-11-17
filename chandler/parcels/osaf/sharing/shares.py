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
    'Share',
    'OneTimeShare',
    'OneTimeFileSystemShare',
]


from application import schema
from osaf import pim
from i18n import ChandlerMessageFactory as _
import errors
from callbacks import *
import logging

import logging
logger = logging.getLogger(__name__)




class modeEnum(schema.Enumeration):
    values = "put", "get", "both"


class Share(pim.ContentItem):
    """
    Represents a set of shared items, encapsulating contents, location,
    access method, data format, sharer and sharees.
    """

    schema.kindInfo(
        description="Represents a shared collection",
    )

    hidden = schema.One(
        schema.Boolean,
        doc = 'This attribute is used to denote which shares have been '
              'created by the user via the detail view (hidden=False) versus '
              'those that are being created for other purposes (hidden=True), '
              'such as transient import/export shares, .ics publishing, etc.',
        initialValue = False,
    )

    active = schema.One(
        schema.Boolean,
        doc = "This attribute indicates whether this share should be synced "
              "during a 'sync all' operation.",
        initialValue = True,
    )

    established = schema.One(
        schema.Boolean,
        doc = "This attribute indicates whether the share has been "
              "successfully subscribed/published at least once.",
        initialValue = False,
    )

    mode = schema.One(
        modeEnum,
        doc = 'This attribute indicates the sync mode for the share:  '
              'get, put, or both',
        initialValue = 'both',
    )

    error = schema.One(
        schema.Text,
        doc = 'A message describing the last error; empty string otherwise',
        initialValue = u''
    )

    contents = schema.One(pim.ContentItem,otherName='shares',initialValue=None)

    items = schema.Sequence(pim.ContentItem, initialValue=[],
        otherName = 'sharedIn')

    conduit = schema.One(initialValue=None)
    # inverse of Conduit.share

    format = schema.One(initialValue=None)
    # inverse of ImportExportFormat.share

    sharer = schema.One(
        pim.Contact,
        doc = 'The contact who initially published this share',
        initialValue = None,
        otherName = 'sharerOf',
    )

    sharees = schema.Sequence(
        pim.Contact,
        doc = 'The people who were invited to this share',
        initialValue = [],
        otherName = 'shareeOf',
    )

    filterClasses = schema.Sequence(
        schema.Text,
        doc = 'The list of classes to import/export',
        initialValue = [],
    )

    filterAttributes = schema.Sequence(schema.Text, initialValue=[])

    # @@@ [grant] Try inverse, and explicit attributes
    leads = schema.Sequence('Share', initialValue=[], otherName='follows')
    follows = schema.One('Share', otherName='leads')

    schema.addClouds(
        sharing = schema.Cloud(
            literal = [filterAttributes],
            byCloud = [contents, sharer, sharees]
        ),
        copying = schema.Cloud(byCloud=[format, conduit])
    )

    def __init__(self, *args, **kw):
        defaultDisplayName = getattr(kw.get('contents'),'displayName',u'')
        kw.setdefault('displayName',defaultDisplayName)
        super(Share, self).__init__(*args, **kw)

    def create(self):
        self.conduit.create()

    def destroy(self):
        self.conduit.destroy()

    def open(self):
        self.conduit.open()

    def close(self):
        self.conduit.close()

    def sync(self, modeOverride=None, updateCallback=None, forceUpdate=None):
        return self.conduit.sync(modeOverride=modeOverride,
                                 updateCallback=updateCallback,
                                 forceUpdate=forceUpdate)

    def put(self, updateCallback=None):
        return self.sync(modeOverride='put', updateCallback=updateCallback,
                         forceUpdate=None)

    def get(self, updateCallback=None):
        return self.sync(modeOverride='get', updateCallback=updateCallback)

    def exists(self):
        return self.conduit.exists()

    def getLocation(self, privilege=None):
        return self.conduit.getLocation(privilege=privilege)

    def getSharedAttributes(self, kind, cloudAlias='sharing'):
        """
        Examine sharing clouds and filterAttributes to determine which
        attributes to share for a given kind
        """

        attributes = set()
        skip = getattr(self, 'filterAttributes', [])

        for cloud in kind.getClouds(cloudAlias):
            for alias, endpoint, inCloud in cloud.iterEndpoints(cloudAlias):
                # @@@MOR for now, don't support endpoint attribute 'chains'
                attrName = endpoint.attribute[0]

                # An includePolicy of 'none' is how we override an inherited
                # endpoint
                if not (endpoint.includePolicy == 'none' or
                        attrName in skip):
                    attributes.add(attrName)

        return attributes

    def getLinkedShares(self):

        def getFollowers(share):
            if hasattr(share, 'leads'):
                for follower in share.leads:
                    yield follower
                    for subfollower in getFollowers(follower):
                        yield subfollower

        # Find the root leader
        root = self
        leader = getattr(root, 'follows', None)
        while leader is not None:
            root = leader
            leader = getattr(root, 'follows', None)

        shares = [root]
        for follower in getFollowers(root):
            shares.append(follower)

        return shares







class OneTimeShare(Share):
    """
    Delete format, conduit, and share after the first get or put.
    """

    def remove(self):
        # With deferred deletes, we need to also remove the Share from the
        # collection's shares ref collection
        if self.contents:
            self.contents.shares.remove(self)
        self.conduit.delete(True)
        self.format.delete(True)
        self.delete(True)

    def put(self, updateCallback=None):
        super(OneTimeShare, self).put(updateCallback=updateCallback)
        collection = self.contents
        self.remove()
        return collection

    def get(self, updateCallback=None):
        super(OneTimeShare, self).get(updateCallback=updateCallback)
        collection = self.contents
        self.remove()
        return collection




class OneTimeFileSystemShare(OneTimeShare):
    def __init__(self, path, itsName, formatclass, itsKind=None, itsView=None,
                 contents=None):

        import filesystem_conduit
        conduit = filesystem_conduit.FileSystemConduit(
            itsKind=itsKind, itsView=itsView, sharePath=path, shareName=itsName
        )
        format  = formatclass(itsView=itsView)
        super(OneTimeFileSystemShare, self).__init__(
            itsKind=itsKind, itsView=itsView,
            contents=contents, conduit=conduit, format=format
        )

