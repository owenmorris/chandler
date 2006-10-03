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
from osaf import pim, sharing, usercollections
from osaf.framework.blocks import Block
from osaf.pim.structs import ColorType
from application.dialogs import SubscribeCollection
from chandlerdb.util.c import UUID

logger = logging.getLogger(__name__)


def save(rv, filename):
    """Save selected settings information, including all sharing accounts
    and shares (whether published or subscribed), to an INI file"""

    cfg = ConfigParser.ConfigParser()

    # Sharing accounts
    currentAccount = schema.ns("osaf.sharing", rv).currentWebDAVAccount.item
    section_prefix = "sharing_account"
    counter = 1

    for account in sharing.WebDAVAccount.iterItems(rv):
        if account.username: # skip account if not configured
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
    mine = schema.ns("osaf.pim", rv).mine
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
            uc = usercollections.UserCollection(col)
            if getattr(uc, "color", False):
                color = uc.color
                cfg.set(section_name, "red", color.red)
                cfg.set(section_name, "green", color.green)
                cfg.set(section_name, "blue", color.blue)
                cfg.set(section_name, "alpha", color.alpha)
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
                ticketFreeBusy = getattr(share.conduit, "ticketFreeBusy", None)
                if ticketFreeBusy:
                    cfg.set(section_name, "freebusy", "True")
            counter += 1

    # SMTP accounts
    section_prefix = "smtp_account"
    counter = 1

    for account in pim.mail.SMTPAccount.iterItems(rv):
        if account.isActive and account.host:
            section_name = "%s_%d" % (section_prefix, counter)
            cfg.add_section(section_name)
            cfg.set(section_name, "type", "smtp account")
            cfg.set(section_name, "uuid", account.itsUUID)
            cfg.set(section_name, "title", account.displayName)
            cfg.set(section_name, "host", account.host)
            cfg.set(section_name, "auth", account.useAuth)
            cfg.set(section_name, "username", account.username)
            cfg.set(section_name, "password", account.password)
            cfg.set(section_name, "name", account.fromAddress.fullName)
            cfg.set(section_name, "address",
                account.fromAddress.emailAddress)
            cfg.set(section_name, "port", account.port)
            cfg.set(section_name, "security", account.connectionSecurity)
            counter += 1

    # IMAP accounts
    currentAccount = schema.ns("osaf.pim", rv).currentMailAccount.item
    section_prefix = "imap_account"
    counter = 1

    for account in pim.mail.IMAPAccount.iterItems(rv):
        if account.isActive and account.host:
            section_name = "%s_%d" % (section_prefix, counter)
            cfg.add_section(section_name)
            cfg.set(section_name, "type", "imap account")
            cfg.set(section_name, "uuid", account.itsUUID)
            cfg.set(section_name, "title", account.displayName)
            cfg.set(section_name, "host", account.host)
            cfg.set(section_name, "username", account.username)
            cfg.set(section_name, "password", account.password)
            cfg.set(section_name, "name", account.replyToAddress.fullName)
            cfg.set(section_name, "address",
                account.replyToAddress.emailAddress)
            cfg.set(section_name, "port", account.port)
            cfg.set(section_name, "security", account.connectionSecurity)
            if account.defaultSMTPAccount:
                cfg.set(section_name, "smtp",
                    account.defaultSMTPAccount.itsUUID)
            if account is currentAccount:
                cfg.set(section_name, "default", "True")
            counter += 1

    # POP accounts
    currentAccount = schema.ns("osaf.pim", rv).currentMailAccount.item
    section_prefix = "pop_account"
    counter = 1

    for account in pim.mail.POPAccount.iterItems(rv):
        if account.isActive and account.host:
            section_name = "%s_%d" % (section_prefix, counter)
            cfg.add_section(section_name)
            cfg.set(section_name, "type", "pop account")
            cfg.set(section_name, "uuid", account.itsUUID)
            cfg.set(section_name, "title", account.displayName)
            cfg.set(section_name, "host", account.host)
            cfg.set(section_name, "username", account.username)
            cfg.set(section_name, "password", account.password)
            cfg.set(section_name, "name", account.replyToAddress.fullName)
            cfg.set(section_name, "address",
                account.replyToAddress.emailAddress)
            cfg.set(section_name, "port", account.port)
            cfg.set(section_name, "security", account.connectionSecurity)
            cfg.set(section_name, "leave", account.leaveOnServer)
            if account.defaultSMTPAccount:
                cfg.set(section_name, "smtp",
                    account.defaultSMTPAccount.itsUUID)
            if account is currentAccount:
                cfg.set(section_name, "default", "True")
            counter += 1

    # Show timezones
    cfg.add_section("timezones")
    showTZ = schema.ns("osaf.app", rv).TimezonePrefs.showUI
    cfg.set("timezones", "type", "show timezones")
    cfg.set("timezones", "show_timezones", showTZ)

    # Visible hours
    cfg.add_section("visible_hours")
    cfg.set("visible_hours", "type", "visible hours")
    calPrefs = schema.ns("osaf.framework.blocks.calendar", rv).calendarPrefs
    cfg.set("visible_hours", "height_mode", calPrefs.hourHeightMode)
    cfg.set("visible_hours", "num_hours", calPrefs.visibleHours)

    # Event Logger
    cfg.add_section("event_logger")
    eventHook = schema.ns("eventLogger", rv).EventLoggingHook
    cfg.set("event_logger", "type", "event logger")
    active = eventHook.logging
    cfg.set("event_logger", "active", active)

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
                freebusy = False
                if cfg.has_option(section, "freebusy"):
                    freebusy = cfg.getboolean(section, "freebusy")
                title = cfg.get(section, "title")

                if cfg.has_option(section, "red"):
                    # Backwards-compatibility fix for bug 6899...
                    # Due to an earlier bug, some people's ini files
                    # still have floats in them, so let's cast just in case:
                    red = int(float(cfg.get(section, "red")))
                    blue = int(float(cfg.get(section, "blue")))
                    green = int(float(cfg.get(section, "green")))
                    alpha = int(float(cfg.get(section, "alpha")))
                    color = ColorType(red, green, blue, alpha)
                else:
                    color = None

                SubscribeCollection.Show(None, view=rv, url=url, name=title,
                                         modal=False, immediate=True,
                                         mine=mine, publisher=publisher,
                                         freebusy=freebusy, color=color)

    # smtp accounts
    for section in cfg.sections():
        section_type = cfg.get(section, "type")
        if section_type == "smtp account":
            if cfg.has_option(section, "uuid"):
                uuid = cfg.get(section, "uuid")
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = pim.mail.SMTPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            else:
                account = pim.mail.SMTPAccount(itsView=rv)

            account.displayName = cfg.get(section, "title")
            account.host = cfg.get(section, "host")
            account.useAuth = cfg.getboolean(section, "auth")
            account.username = cfg.get(section, "username")
            account.password = cfg.get(section, "password")
            account.port = cfg.getint(section, "port")
            account.connectionSecurity = cfg.get(section, "security")
            emailAddress = pim.mail.EmailAddress.getEmailAddress(rv,
                cfg.get(section, "address"), cfg.get(section, "name"))
            account.fromAddress = emailAddress


    # imap accounts
    for section in cfg.sections():
        section_type = cfg.get(section, "type")
        if section_type == "imap account":
            if cfg.has_option(section, "uuid"):
                uuid = cfg.get(section, "uuid")
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = pim.mail.IMAPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            else:
                account = pim.mail.IMAPAccount(itsView=rv)

            account.displayName = cfg.get(section, "title")
            account.host = cfg.get(section, "host")
            account.username = cfg.get(section, "username")
            account.password = cfg.get(section, "password")
            account.port = cfg.getint(section, "port")
            account.connectionSecurity = cfg.get(section, "security")
            emailAddress = pim.mail.EmailAddress.getEmailAddress(rv,
                cfg.get(section, "address"), cfg.get(section, "name"))
            account.replyToAddress = emailAddress

            if (cfg.has_option(section, "default") and
                cfg.get(section, "default")):
                accountRef = schema.ns("osaf.pim", rv).currentMailAccount
                accountRef.item = account

            if cfg.has_option(section, "smtp"):
                uuid = cfg.get(section, "smtp")
                uuid = UUID(uuid)
                smtp = rv.findUUID(uuid)
                account.defaultSMTPAccount = smtp

    # pop accounts
    for section in cfg.sections():
        section_type = cfg.get(section, "type")
        if section_type == "pop account":
            if cfg.has_option(section, "uuid"):
                uuid = cfg.get(section, "uuid")
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = pim.mail.POPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            else:
                account = pim.mail.POPAccount(itsView=rv)

            account.displayName = cfg.get(section, "title")
            account.host = cfg.get(section, "host")
            account.username = cfg.get(section, "username")
            account.password = cfg.get(section, "password")
            account.port = cfg.getint(section, "port")
            account.connectionSecurity = cfg.get(section, "security")
            account.leaveOnServer = cfg.getboolean(section, "leave")
            emailAddress = pim.mail.EmailAddress.getEmailAddress(rv,
                cfg.get(section, "address"), cfg.get(section, "name"))
            account.replyToAddress = emailAddress

            if (cfg.has_option(section, "default") and
                cfg.get(section, "default")):
                accountRef = schema.ns("osaf.pim", rv).currentMailAccount
                accountRef.item = account

            if cfg.has_option(section, "smtp"):
                uuid = cfg.get(section, "smtp")
                uuid = UUID(uuid)
                smtp = rv.findUUID(uuid)
                account.defaultSMTPAccount = smtp


    # timezones
    if cfg.has_section("timezones"):
        if cfg.has_option("timezones", "show_timezones"):
            show = cfg.getboolean("timezones", "show_timezones")
            schema.ns("osaf.app", rv).TimezonePrefs.showUI = show

    # Visible hours
    if cfg.has_section("visible_hours"):
        calPrefs = schema.ns("osaf.framework.blocks.calendar", rv).calendarPrefs
        if cfg.has_option("visible_hours", "height_mode"):
            calPrefs.hourHeightMode = cfg.get("visible_hours", "height_mode")
        if cfg.has_option("visible_hours", "num_hours"):
            calPrefs.visibleHours = cfg.getint("visible_hours", "num_hours")

    # Event Logger
    if cfg.has_section("event_logger"):
        active = cfg.getboolean("event_logger", "active")
        if active:
            eventHook = schema.ns("eventLogger", rv).EventLoggingHook
            eventHook.onToggleLoggingEvent(None)
