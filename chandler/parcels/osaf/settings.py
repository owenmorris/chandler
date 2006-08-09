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


"""Save and Restore Application Settings"""

import ConfigParser, logging
from application import schema
from osaf import pim, sharing
from application.dialogs import SubscribeCollection
from chandlerdb.util.c import UUID

logger = logging.getLogger(__name__)


def save(rv, filename):
    """Save selected settings information, including all sharing accounts
    and shares (whether published or subscribed), to an INI file"""

    cfg = ConfigParser.ConfigParser()

    # Sharing accounts
    currentAccount = schema.ns('osaf.sharing', rv).currentWebDAVAccount.item
    section_prefix = "sharing_account"
    counter = 1

    for account in sharing.WebDAVAccount.iterItems(rv):
        section_name = "%s_%d" % (section_prefix, counter)
        cfg.add_section(section_name)
        cfg.set(section_name, "type", "webdav account")
        cfg.set(section_name, "uuid", account.itsUUID)
        cfg.set(section_name, "title", account.displayName)
        cfg.set(section_name, "host", account.host)
        cfg.set(section_name, "path", account.path)
        cfg.set(section_name, "username", account.username)
        cfg.set(section_name, "password", account.password)
        cfg.set(section_name, "port", account.port)
        cfg.set(section_name, "usessl", account.useSSL)
        if account is currentAccount:
            cfg.set(section_name, "default", "True")
        counter += 1

    # Subscriptions
    mine = schema.ns('osaf.pim', rv).mine
    section_prefix = "share"
    counter = 1
    for col in pim.ContentCollection.iterItems(rv):
        share = sharing.getShare(col)
        if share:
            section_name = "%s_%d" % (section_prefix, counter)
            cfg.add_section(section_name)
            cfg.set(section_name, "type", "share")
            cfg.set(section_name, "title", share.contents.displayName)
            cfg.set(section_name, "mine", col in mine.sources)
            urls = sharing.getUrls(share)
            if sharing.isSharedByMe(share):
                cfg.set(section_name, "publisher", "True")
                cfg.set(section_name, "url", share.getLocation())
            else:
                cfg.set(section_name, "publisher", "False")
                url = share.getLocation()
                cfg.set(section_name, "url", url)
                if url != urls[0]:
                    cfg.set(section_name, "ticket", urls[0])
            counter += 1


    output = file(filename, "w")
    cfg.write(output)
    output.close()


def restore(rv, filename):
    """Restore accounts and shares from an INI file"""

    cfg = ConfigParser.ConfigParser()
    cfg.read(filename)

    # sharing accounts
    for section in cfg.sections():
        section_type = cfg.get(section, "type")
        if section_type == "webdav account":
            if cfg.has_option(section, "uuid"):
                uuid = cfg.get(section, "uuid")
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = sharing.WebDAVAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            else:
                account = sharing.WebDAVAccount(itsView=rv)

            account.displayName = cfg.get(section, "title")
            account.host = cfg.get(section, "host")
            account.path = cfg.get(section, "path")
            account.username = cfg.get(section, "username")
            account.password = cfg.get(section, "password")
            account.port = cfg.getint(section, "port")
            account.useSSL = cfg.getboolean(section, "usessl")

            if (cfg.has_option(section, "default") and
                cfg.get(section, "default")):
                accountRef = schema.ns("osaf.sharing", rv).currentWebDAVAccount
                accountRef.item = account

    # shares
    for section in cfg.sections():
        section_type = cfg.get(section, "type")
        if section_type == "share":
            url = cfg.get(section, "url")

            mine = False
            if cfg.has_option(section, "mine"):
                # Add to my items
                mine = cfg.getboolean(section, "mine")

            publisher = False
            if cfg.has_option(section, "publisher"):
                # make me the publisher
                publisher = cfg.getboolean(section, "publisher")

            subscribed = False
            for share in sharing.Share.iterItems(rv):
                if url == share.getLocation():
                    subscribed = True

            if not subscribed:
                if cfg.has_option(section, "ticket"):
                    url = cfg.get(section, "ticket")
                title = cfg.get(section, "title")
                SubscribeCollection.Show(None, view=rv, url=url, name=title,
                                         modal=False, immediate=True,
                                         mine=mine, publisher=publisher)

