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

import logging
from configobj import ConfigObj
from application import schema
from osaf import pim, sharing, usercollections
from osaf.pim.structs import ColorType
from application.dialogs import SubscribeCollection
from chandlerdb.util.c import UUID

logger = logging.getLogger(__name__)


def save(rv, filename):
    """Save selected settings information, including all sharing accounts
    and shares (whether published or subscribed), to an INI file"""
    
    cfg = ConfigObj()
    cfg.encoding = "UTF8"
    cfg.filename = filename
    
    # Sharing accounts
    currentAccount = schema.ns("osaf.sharing", rv).currentWebDAVAccount.item
    counter = 1
    for account in sharing.WebDAVAccount.iterItems(rv):
        if account.username: # skip account if not configured
            section_name = u"sharing_account_%d" % counter
            cfg[section_name] = {}
            cfg[section_name][u"type"] = u"webdav account"
            cfg[section_name][u"uuid"] = account.itsUUID
            cfg[section_name][u"title"] = account.displayName
            cfg[section_name][u"host"] = account.host
            cfg[section_name][u"path"] = account.path
            cfg[section_name][u"username"] = account.username
            cfg[section_name][u"password"] = account.password
            cfg[section_name][u"port"] = account.port
            cfg[section_name][u"usessl"] = account.useSSL
            if account is currentAccount:
                cfg[section_name][u"default"] = u"True"
            counter += 1
            
    # Subscriptions
    mine = schema.ns("osaf.pim", rv).mine
    counter = 1
    for col in pim.ContentCollection.iterItems(rv):
        share = sharing.getShare(col)
        if share:
            section_name = u"share_%d" % counter
            cfg[section_name] = {}
            cfg[section_name][u"type"] = u"share"
            cfg[section_name][u"title"] = share.contents.displayName
            cfg[section_name][u"mine"] = col in mine.sources
            uc = usercollections.UserCollection(col)
            if getattr(uc, "color", False):
                color = uc.color
                cfg[section_name][u"red"] = color.red
                cfg[section_name][u"green"] = color.green
                cfg[section_name][u"blue"] = color.blue
                cfg[section_name][u"alpha"] = color.alpha
            urls = sharing.getUrls(share)
            if sharing.isSharedByMe(share):
                cfg[section_name][u"publisher"] = u"True"
                cfg[section_name][u"url"] = share.getLocation()
            else:
                cfg[section_name][u"publisher"] = u"False"
                url = share.getLocation()
                cfg[section_name][u"url"] = url
                if url != urls[0]:
                    cfg[section_name][u"ticket"] = urls[0]
                ticketFreeBusy = getattr(share.conduit, "ticketFreeBusy", None)
                if ticketFreeBusy:
                    cfg[section_name][u"freebusy"] = u"True"
            counter += 1
            
    # SMTP accounts
    counter = 1
    for account in pim.mail.SMTPAccount.iterItems(rv):
        if account.isActive and account.host:
            section_name = u"smtp_account_%d" % counter
            cfg[section_name] = {}
            cfg[section_name][u"type"] = u"smtp account"
            cfg[section_name][u"uuid"] = account.itsUUID
            cfg[section_name][u"title"] = account.displayName
            cfg[section_name][u"host"] = account.host
            cfg[section_name][u"auth"] = account.useAuth
            cfg[section_name][u"username"] = account.username
            cfg[section_name][u"password"] = account.password
            cfg[section_name][u"name"] = account.fromAddress.fullName
            cfg[section_name][u"address"] = account.fromAddress.emailAddress
            cfg[section_name][u"port"] = account.port
            cfg[section_name][u"security"] = account.connectionSecurity
            counter += 1
            
    # IMAP accounts
    currentAccount = schema.ns("osaf.pim", rv).currentMailAccount.item
    counter = 1
    for account in pim.mail.IMAPAccount.iterItems(rv):
        if account.isActive and account.host:
            section_name = u"imap_account_%d" % counter
            cfg[section_name] = {}
            cfg[section_name][u"type"] = u"imap account"
            cfg[section_name][u"uuid"] = account.itsUUID
            cfg[section_name][u"title"] = account.displayName
            cfg[section_name][u"host"] = account.host
            cfg[section_name][u"username"] = account.username
            cfg[section_name][u"password"] = account.password
            cfg[section_name][u"name"] = account.replyToAddress.fullName
            cfg[section_name][u"address"] = account.replyToAddress.emailAddress
            cfg[section_name][u"port"] = account.port
            cfg[section_name][u"security"] = account.connectionSecurity
            if account.defaultSMTPAccount:
                cfg[section_name][u"smtp"] = account.defaultSMTPAccount.itsUUID
            if account is currentAccount:
                cfg[section_name][u"default"] = u"True"
            counter += 1
            
    # POP accounts
    currentAccount = schema.ns("osaf.pim", rv).currentMailAccount.item
    counter = 1
    for account in pim.mail.POPAccount.iterItems(rv):
        if account.isActive and account.host:
            section_name = u"pop_account_%d" % counter
            cfg[section_name] = {}
            cfg[section_name][u"type"] = u"pop account"
            cfg[section_name][u"uuid"] = account.itsUUID
            cfg[section_name][u"title"] = account.displayName
            cfg[section_name][u"host"] = account.host
            cfg[section_name][u"username"] = account.username
            cfg[section_name][u"password"] = account.password
            cfg[section_name][u"name"] = account.replyToAddress.fullName
            cfg[section_name][u"address"] = account.replyToAddress.emailAddress
            cfg[section_name][u"port"] = account.port
            cfg[section_name][u"security"] = account.connectionSecurity
            cfg[section_name][u"leave"] = account.leaveOnServer
            if account.defaultSMTPAccount:
                cfg[section_name][u"smtp"] = account.defaultSMTPAccount.itsUUID
            if account is currentAccount:
                cfg[section_name][u"default"] = u"True"
            counter += 1
            
    # Show timezones
    cfg[u"timezones"] = {}
    showTZ = schema.ns("osaf.app", rv).TimezonePrefs.showUI
    cfg[u"timezones"][u"type"] = u"show timezones"
    cfg[u"timezones"][u"show_timezones"] = showTZ
    
    # Visible hours
    cfg[u"visible_hours"] = {}
    cfg[u"visible_hours"][u"type"] = u"visible hours"
    calPrefs = schema.ns("osaf.framework.blocks.calendar", rv).calendarPrefs
    cfg[u"visible_hours"][u"height_mode"] = calPrefs.hourHeightMode
    cfg[u"visible_hours"][u"num_hours"] = calPrefs.visibleHours
    
    # Event Logger
    cfg[u"event_logger"] = {}
    eventHook = schema.ns("eventLogger", rv).EventLoggingHook
    cfg[u"event_logger"][u"type"] = u"event logger"
    active = eventHook.logging
    cfg[u"event_logger"][u"active"] = active
    
    cfg.write()


def restore(rv, filename, testmode=False):
    """Restore accounts and shares from an INI file"""
    
    cfg = ConfigObj(filename, encoding="UTF8")
    
    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # sharing accounts
        if sectiontype == u"webdav account":
            if section.has_key(u"uuid"):
                uuid = section[u"uuid"]
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = sharing.WebDAVAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            else:
                account = sharing.WebDAVAccount(itsView=rv)

            account.displayName = section[u"title"]
            account.host = section[u"host"]
            account.path = section[u"path"]
            account.username = section[u"username"]
            account.password = section[u"password"]
            account.port = section.as_int(u"port")
            account.useSSL = section.as_bool(u"usessl")

            if section.has_key(u"default") and section.as_bool(u"default"):
                accountRef = schema.ns("osaf.sharing", rv).currentWebDAVAccount
                accountRef.item = account
                
    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # shares
        if sectiontype == u"share":
            url = section[u"url"]

            mine = False
            if section.has_key(u"mine"):
                # Add to my items
                mine = section.as_bool(u"mine")

            publisher = False
            if section.has_key(u"publisher"):
                # make me the publisher
                publisher = section.as_bool(u"publisher")

            subscribed = False
            for share in sharing.Share.iterItems(rv):
                if url == share.getLocation():
                    subscribed = True

            if not subscribed:
                if section.has_key(u"ticket"):
                    url = section[u"ticket"]
                freebusy = False
                if section.has_key(u"freebusy"):
                    freebusy = section.as_bool(u"freebusy")
                title = section[u"title"]

                if section.has_key(u"red"):
                    # Backwards-compatibility fix for bug 6899...
                    # Due to an earlier bug, some people's ini files
                    # still have floats in them, so let's cast just in case:
                    red = int(float(section.as_float(u"red")))
                    blue = int(float(section.as_float(u"blue")))
                    green = int(float(section.as_float(u"green")))
                    alpha = int(float(section.as_float(u"alpha")))
                    color = ColorType(red, green, blue, alpha)
                else:
                    color = None

                if testmode:
                    # Fake the subscribes so unit tests don't have to
                    # access the network
                    collection = pim.SmartCollection(itsView=rv)
                    collection.displayName = title
                    if mine:
                        schema.ns('osaf.pim', rv).mine.addSource(collection)
                    usercollections.UserCollection(collection).color = color
                else:
                    SubscribeCollection.Show(None, view=rv, url=url,
                                             name=title, modal=False,
                                             immediate=True, mine=mine,
                                             publisher=publisher,
                                             freebusy=freebusy, color=color)
        
    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # smtp accounts
        if sectiontype == u"smtp account":
            if section.has_key(u"uuid"):
                uuid = section[u"uuid"]
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = pim.mail.SMTPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            else:
                account = pim.mail.SMTPAccount(itsView=rv)

            account.displayName = section[u"title"]
            account.host = section[u"host"]
            account.useAuth = section.as_bool(u"auth")
            account.username = section[u"username"]
            account.password = section[u"password"]
            account.port = section.as_int(u"port")
            account.connectionSecurity = section[u"security"]
            emailAddress = pim.mail.EmailAddress.getEmailAddress(rv,
                section[u"address"], section[u"name"])
            account.fromAddress = emailAddress
        
    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # imap accounts
        if sectiontype == u"imap account":
            if section.has_key(u"uuid"):
                uuid = section[u"uuid"]
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = pim.mail.IMAPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            else:
                account = pim.mail.IMAPAccount(itsView=rv)

            account.displayName = section[u"title"]
            account.host = section[u"host"]
            account.username = section[u"username"]
            account.password = section[u"password"]
            account.port = section.as_int(u"port")
            account.connectionSecurity = section[u"security"]
            emailAddress = pim.mail.EmailAddress.getEmailAddress(rv,
                section[u"address"], section[u"name"])
            account.replyToAddress = emailAddress

            if section.has_key(u"default") and section[u"default"]:
                accountRef = schema.ns("osaf.pim", rv).currentMailAccount
                accountRef.item = account

            if section.has_key(u"smtp"):
                uuid = section[u"smtp"]
                uuid = UUID(uuid)
                smtp = rv.findUUID(uuid)
                account.defaultSMTPAccount = smtp
        
    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # pop accounts
        if sectiontype == u"pop account":
            if section.has_key(u"uuid"):
                uuid = section[u"uuid"]
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = pim.mail.POPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            else:
                account = pim.mail.POPAccount(itsView=rv)

            account.displayName = section[u"title"]
            account.host = section[u"host"]
            account.username = section[u"username"]
            account.password = section[u"password"]
            account.port = section.as_int(u"port")
            account.connectionSecurity = section[u"security"]
            account.leaveOnServer = section.as_bool(u"leave")
            emailAddress = pim.mail.EmailAddress.getEmailAddress(rv,
                section[u"address"], section[u"name"])
            account.replyToAddress = emailAddress

            if section.has_key(u"default") and section[u"default"]:
                accountRef = schema.ns("osaf.pim", rv).currentMailAccount
                accountRef.item = account

            if section.has_key(u"smtp"):
                uuid = section[u"smtp"]
                uuid = UUID(uuid)
                smtp = rv.findUUID(uuid)
                account.defaultSMTPAccount = smtp
        
    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # timezones
        if sectionname == u"timezones":
            if section.has_key(u"show_timezones"):
                show = section.as_bool(u"show_timezones")
                schema.ns("osaf.app", rv).TimezonePrefs.showUI = show
        
        # Visible hours
        elif sectionname == u"visible_hours":
            calPrefs = schema.ns("osaf.framework.blocks.calendar", rv).calendarPrefs
            if section.has_key(u"height_mode"):
                calPrefs.hourHeightMode = section[u"height_mode"]
            if section.has_key(u"num_hours"):
                calPrefs.visibleHours = section.as_int(u"num_hours")
        
        # Event Logger        
        elif sectionname == u"event_logger":
            if section.has_key(u"active"):
                active = section.as_bool(u"active")
                if active:
                    eventHook = schema.ns("eventLogger", rv).EventLoggingHook
                    eventHook.onToggleLoggingEvent(None)

