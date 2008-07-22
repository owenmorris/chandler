#   Copyright (c) 2003-2008 Open Source Applications Foundation
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

import logging, wx
from binascii import hexlify, unhexlify
from configobj import ConfigObj
from application import schema
from osaf import pim, sharing, usercollections
from osaf.framework.twisted import waitForDeferred
from osaf.pim.structs import ColorType
from application.dialogs import SubscribeCollection
from i18n import ChandlerMessageFactory as _
from chandlerdb.util.c import UUID
from osaf.framework import password, MasterPassword


logger = logging.getLogger(__name__)


def save(rv, filename):
    """
    Save selected settings information, including all sharing accounts
    and shares (whether published or subscribed), to an INI file.

    @param rv:       Repository view
    @param filename: File to save settings into
    """

    cfg = ConfigObj()
    cfg.encoding = "UTF8"
    cfg.filename = filename

    # Sharing accounts
    counter = 1
    for account in sharing.SharingAccount.iterItems(rv):
        if account.username: # skip account if not configured
            section_name = u"sharing_account_%d" % counter
            cfg[section_name] = {}
            if isinstance(account, sharing.HubAccount):
                cfg[section_name][u"type"] = u"hub account"
            elif isinstance(account, sharing.CosmoAccount):
                cfg[section_name][u"type"] = u"cosmo account"
            else:
                cfg[section_name][u"type"] = u"webdav account"
            cfg[section_name][u"uuid"] = account.itsUUID
            cfg[section_name][u"title"] = account.displayName
            cfg[section_name][u"host"] = account.host
            cfg[section_name][u"path"] = account.path
            cfg[section_name][u"username"] = account.username
            savePassword(cfg[section_name], account.password)
            cfg[section_name][u"port"] = account.port
            cfg[section_name][u"usessl"] = account.useSSL
            counter += 1
            
    # Subscriptions
    mine = schema.ns("osaf.pim", rv).mine
    counter = 1
    sidebar = schema.ns("osaf.app", rv).sidebarCollection
    for col in sidebar:
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
                if isinstance(share.conduit, sharing.CosmoConduit):
                    c = share.conduit
                    cfg[section_name][u"url"] = c.getLocation(morsecode=True)
                else:
                    cfg[section_name][u"url"] = share.getLocation()
            else:
                cfg[section_name][u"publisher"] = u"False"
                url = share.getLocation()
                cfg[section_name][u"url"] = url
                if url != urls[0]:
                    cfg[section_name][u"ticket"] = urls[0]
            if isinstance(share.conduit, sharing.RecordSetConduit):
                c = share.conduit
                cfg[section_name][u"filters"] = ",".join(c.filters)
            counter += 1

    # SMTP accounts
    counter = 1
    currentAccount = getattr(schema.ns("osaf.pim", rv).currentOutgoingAccount,
                             "item", None)

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
            savePassword(cfg[section_name], account.password)

            if currentAccount and account is currentAccount:
                cfg[section_name][u"default"] = u"True"

            if account.fromAddress:
                cfg[section_name][u"name"] = account.fromAddress.fullName
                cfg[section_name][u"address"] = account.fromAddress.emailAddress

            cfg[section_name][u"port"] = account.port
            cfg[section_name][u"security"] = account.connectionSecurity
            counter += 1

    # IMAP accounts
    currentAccount = getattr(schema.ns("osaf.pim", rv).currentIncomingAccount,
                             "item", None)
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
            savePassword(cfg[section_name], account.password)

            if account.replyToAddress:
                cfg[section_name][u"name"] = account.replyToAddress.fullName
                cfg[section_name][u"address"] = account.replyToAddress.emailAddress

            cfg[section_name][u"port"] = account.port
            cfg[section_name][u"security"] = account.connectionSecurity

            if currentAccount and account is currentAccount:
                cfg[section_name][u"default"] = u"True"

            folderNum = len(account.folders)

            if folderNum:
                cfg[section_name]["imap_folder_num"] = folderNum

                fCounter = 0

                for folder in account.folders:
                    fname = "imap_folder_%d" % fCounter
                    cfg[section_name][fname] = {}
                    cfg[section_name][fname][u"type"] = u"imap folder"
                    cfg[section_name][fname][u"uuid"] = folder.itsUUID
                    cfg[section_name][fname][u"title"] = folder.displayName
                    cfg[section_name][fname][u"name"] = folder.folderName
                    cfg[section_name][fname][u"type"] = folder.folderType
                    # Commented out for 1.0. These features are not
                    # supported in the Chandler UI. So leave them out
                    # of the ini files as well.
                    #cfg[section_name][fname][u"max"] = folder.downloadMax
                    #cfg[section_name][fname][u"del"] = folder.deleteOnDownload
                    fCounter += 1

            counter += 1

    # POP accounts
    currentAccount = getattr(schema.ns("osaf.pim", rv).currentIncomingAccount,
                             "item", None)


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
            savePassword(cfg[section_name], account.password)

            if account.replyToAddress:
                cfg[section_name][u"name"] = account.replyToAddress.fullName
                cfg[section_name][u"address"] = account.replyToAddress.emailAddress

            cfg[section_name][u"port"] = account.port
            cfg[section_name][u"security"] = account.connectionSecurity
            cfg[section_name][u"del"] = account.deleteOnDownload

            if currentAccount and account is currentAccount:
                cfg[section_name][u"default"] = u"True"
            counter += 1

    # Show timezones
    cfg[u"timezones"] = {}
    showTZ = schema.ns("osaf.pim", rv).TimezonePrefs.showUI
    cfg[u"timezones"][u"type"] = u"show timezones"
    cfg[u"timezones"][u"show_timezones"] = showTZ

    # Visible hours
    cfg[u"visible_hours"] = {}
    cfg[u"visible_hours"][u"type"] = u"visible hours"
    calPrefs = schema.ns("osaf.framework.blocks.calendar", rv).calendarPrefs
    cfg[u"visible_hours"][u"height_mode"] = calPrefs.hourHeightMode
    cfg[u"visible_hours"][u"num_hours"] = calPrefs.visibleHours

    # Master password
    prefs = schema.ns("osaf.framework.MasterPassword", rv).masterPasswordPrefs
    cfg[u"master_password"] = {}
    cfg[u"master_password"][u"masterPassword"] = prefs.masterPassword
    cfg[u"master_password"][u"timeout"] = prefs.timeout
    if hasattr(prefs, "protect"):
        cfg[u"master_password"][u"protect"] = prefs.protect

    # password, we'll just use the master password section as they are tied
    dummy = schema.ns("osaf.framework.password", rv).passwordPrefs.dummyPassword
    savePassword(cfg[u"master_password"], dummy, sectionName=u"dummyPassword")

    cfg.write()


def restore(rv, filename, testmode=False, newMaster=''):
    """
    Restore accounts and shares from an INI file.

    @param rv:        repository view
    @param filename:  Path to INI file to load.
    @param testmode:  Are we running a test or not
    @param newMaster: Used in testmode only
    """
    subscribes = []

    if not testmode:
        oldMaster = waitForDeferred(MasterPassword.get(rv))
    else:
        oldMaster = ''

    cfg = ConfigObj(filename, encoding="UTF8")

    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # sharing accounts
        if sectiontype in (u"webdav account", u"cosmo account", u"hub account"):

            if sectiontype == u"webdav account":
                klass = sharing.WebDAVAccount
            elif sectiontype == u"hub account":
                klass = sharing.HubAccount
            else:
                klass = sharing.CosmoAccount

            if section.has_key(u"uuid"):
                uuid = section[u"uuid"]
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = klass.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
                    account.password = password.Password(itsView=rv,
                                                         itsParent=account)

            account.displayName = section[u"title"]
            account.host = section[u"host"]
            account.path = section[u"path"]
            account.username = section[u"username"]
            restorePassword(account, section)
            account.port = section.as_int(u"port")
            account.useSSL = section.as_bool(u"usessl")


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

            filters = None
            if section.has_key(u"filters"):
                filterStr = section[u"filters"]
                if filterStr:
                    filters = set(filterStr.split(","))

            if not subscribed:
                if section.has_key(u"ticket"):
                    url = section[u"ticket"]
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

                subscribes.append((url, title, mine, publisher, color, filters))

    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # smtp accounts
        if sectiontype == u"smtp account":
            account = None
            current = getattr(schema.ns("osaf.pim", rv).currentOutgoingAccount,
                              "item", None)

            isEmpty = current is None or len(current.host.strip()) == 0

            makeCurrent = False

            if isEmpty:
                if current:
                    current.isActive = False
                makeCurrent = True

            if section.has_key(u"uuid") and account is None:
                uuid = section[u"uuid"]
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = pim.mail.SMTPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            elif account is None:
                account = pim.mail.SMTPAccount(itsView=rv)

            if makeCurrent or (section.has_key(u"default") and \
               section[u"default"]):
                schema.ns("osaf.pim", rv).currentOutgoingAccount.item = account

            account.displayName = section[u"title"]
            account.host = section[u"host"]
            account.useAuth = section.as_bool(u"auth")
            account.username = section[u"username"]
            restorePassword(account, section)
            account.port = section.as_int(u"port")
            account.connectionSecurity = section[u"security"]

            if section.has_key(u"address"):
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
            account = None

            current = getattr(schema.ns("osaf.pim", rv).currentIncomingAccount,
                              "item", None)

            isEmpty = current is None or \
                      (len(current.host.strip()) == 0 and \
                       not hasattr(current.password, 'ciphertext') and \
                       len(current.username.strip()) == 0)

            makeCurrent = False

            if isEmpty:
                if current:
                    current.isActive = False
                makeCurrent = True

            if section.has_key(u"uuid") and account is None:
                uuid = section[u"uuid"]
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                   #XXX overwrite the default account info
                    kind = pim.mail.IMAPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                                                   withInitialValues=True)

            if account is None:
                account = pim.mail.IMAPAccount(itsView=rv)

            # Remove any existing folders since the
            # account will be repopulated with the
            # folders in the ini file
            for folder in account.folders:
                account.folders.remove(folder)
                #The folders are not deleted because it
                # will cause the IMAP accounts folders to go stale
                # if the MailService is currently downloading.
                #folder.delete()

            account.displayName = section[u"title"]
            account.host = section[u"host"]
            account.username = section[u"username"]
            restorePassword(account, section)
            account.port = section.as_int(u"port")
            account.connectionSecurity = section[u"security"]
            account.isActive = True

            if section.has_key(u"address"):
                emailAddress = pim.mail.EmailAddress.getEmailAddress(rv,
                                    section[u"address"], section[u"name"])
                account.replyToAddress = emailAddress

            if makeCurrent or (section.has_key(u"default") and \
               section[u"default"]):
                schema.ns("osaf.pim", rv).currentIncomingAccount.item = account

            if section.has_key(u"imap_folder_num"):
                fnum = section.as_int("imap_folder_num")

                for i in xrange(0, fnum):
                    fcfg = section['imap_folder_%d' % i]

                    if fcfg.has_key(u"uuid"):
                        uuid = fcfg[u"uuid"]
                        uuid = UUID(uuid)
                        folder = rv.findUUID(uuid)
                        if folder is None:
                            kind = pim.mail.IMAPFolder.getKind(rv)
                            parent = schema.Item.getDefaultParent(rv)
                            folder = kind.instantiateItem(None, parent, uuid,
                                                 withInitialValues=True)
                    else:
                        folder = pim.mail.IMAPFolder(itsView=rv)

                    folder.displayName = fcfg['title']
                    folder.folderName = fcfg['name']
                    folder.folderType = fcfg['type']
                    # Since better performance has been established
                    # for 1.0 the max download feature is disabled
                    #folder.downloadMax = fcfg.as_int('max')

                    # To enable better performance for 1.0 the
                    # delete on download feature was temporarily disabled
                    #folder.deleteOnDownload = fcfg.as_bool('del')

                    account.folders.append(folder)
            else:
                # This is an Alpha 4 ini file which predates the 1.0 IMAP
                # foldering logic
                account._addInbox()

    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # pop accounts
        if sectiontype == u"pop account":
            account = None

            current = getattr(schema.ns("osaf.pim", rv).currentIncomingAccount,
                              "item", None)

            isEmpty = current is None or \
                      (len(current.host.strip()) == 0 and \
                       not hasattr(current.password, 'ciphertext') and \
                       len(current.username.strip()) == 0)

            makeCurrent = False

            if isEmpty:
                if current:
                    current.isActive = False
                makeCurrent = True

            if section.has_key(u"uuid") and account is None:
                uuid = section[u"uuid"]
                uuid = UUID(uuid)
                account = rv.findUUID(uuid)
                if account is None:
                    kind = pim.mail.POPAccount.getKind(rv)
                    parent = schema.Item.getDefaultParent(rv)
                    account = kind.instantiateItem(None, parent, uuid,
                        withInitialValues=True)
            elif account is None:
                account = pim.mail.POPAccount(itsView=rv)

            account.displayName = section[u"title"]
            account.host = section[u"host"]
            account.username = section[u"username"]
            restorePassword(account, section)
            account.port = section.as_int(u"port")
            account.connectionSecurity = section[u"security"]
            account.isActive = True

            # To enable better performance for 1.0 the
            # delete on download feature was temporarily disabled
            #if section.has_key(u"del"):
            #    account.deleteOnDownload = section.as_bool(u"del")

            if section.has_key(u"address"):
                emailAddress = pim.mail.EmailAddress.getEmailAddress(rv,
                                    section[u"address"], section[u"name"])
                account.replyToAddress = emailAddress

            if makeCurrent or (section.has_key(u"default") and \
               section[u"default"]):
                schema.ns("osaf.pim", rv).currentIncomingAccount.item = account

    for sectionname, section in cfg.iteritems():
        if section.has_key(u"type"):
            sectiontype = section[u"type"]
        else:
            sectiontype = ""
        # timezones
        if sectionname == u"timezones":
            if section.has_key(u"show_timezones"):
                show = section.as_bool(u"show_timezones")
                schema.ns("osaf.pim", rv).TimezonePrefs.showUI = show
        
        # Visible hours
        elif sectionname == u"visible_hours":
            calPrefs = schema.ns("osaf.framework.blocks.calendar", rv).calendarPrefs
            if section.has_key(u"height_mode"):
                calPrefs.hourHeightMode = section[u"height_mode"]
            if section.has_key(u"num_hours"):
                calPrefs.visibleHours = section.as_int(u"num_hours")

    # Master password, must be done after accounts have been handled
    restoreMasterPassword(rv, cfg, testmode, oldMaster, newMaster)

    # Subscribe
    for url, title, mine, publisher, color, filters in subscribes:
        if testmode:
            # Fake the subscribes so unit tests don't have to
            # access the network
            collection = pim.SmartCollection(itsView=rv)
            collection.displayName = title
            if mine:
                schema.ns('osaf.pim', rv).mine.addSource(collection)
            usercollections.UserCollection(collection).color = color
        else:
            SubscribeCollection.Show(view=rv, url=url,
                                     name=title, modal=True,
                                     immediate=True, mine=mine,
                                     publisher=publisher,
                                     color=color,
                                     filters=filters)


def savePassword(section, password, sectionName=u"password"):
    try:
        section[sectionName] = u"%s|%s|%s" % (hexlify(password.iv), hexlify(password.salt), hexlify(password.ciphertext))
    except AttributeError:
        section[sectionName] = u''


def restorePassword(account, section, sectionName=u"password"):
    if not hasattr(account, 'password'):
        account.password = password.Password(itsView=account.itsView,
                                             itsParent=account)
    
    try:
        iv, salt, ciphertext = section[sectionName].split('|')
    except ValueError:
        # Backwards compatibility
        waitForDeferred(account.password.encryptPassword(section[sectionName]))
    else:
        if iv and salt and ciphertext:
            try:
                account.password.iv = unhexlify(iv)
                account.password.salt = unhexlify(salt)
                account.password.ciphertext = unhexlify(ciphertext)
            except TypeError:
                # Backwards compatibility, somebody had a long password!
                waitForDeferred(account.password.encryptPassword(section[sectionName]))
        else:
            # Backwards compatibility
            waitForDeferred(account.password.encryptPassword(section[sectionName]))


def restoreMasterPassword(rv, cfg, testmode, oldMaster, newMaster):
    for sectionname, section in cfg.iteritems():
        if sectionname == u"master_password":
            prefs = schema.ns("osaf.framework.MasterPassword", rv).masterPasswordPrefs
            if section.has_key(u"masterPassword"):
                prefs.masterPassword = section.as_bool(u"masterPassword")
            if section.has_key(u"timeout"):
                prefs.timeout = section.as_int(u"timeout")
            if section.has_key(u"protect"):
                prefs.protect = section.as_bool(u"protect")
            dummy = schema.ns("osaf.framework.password", rv).passwordPrefs.dummyPassword
            try:
                iv, salt, ciphertext = section[u"dummyPassword"].split('|')
                dummy.iv = unhexlify(iv)
                dummy.salt = unhexlify(salt)
                dummy.ciphertext = unhexlify(ciphertext)
            except:
                # Oops, we are in trouble, can't really do much but reset()
                # to avoid further problems.
                logger.exception('settings had master_password section but no dummyPassword; clearing passwords')
                MasterPassword.reset(rv)
                break
            else:
                # Now let's try to re-encrypt all passwords with the new master
                # password.
                waitForDeferred(MasterPassword.clear())
                if not testmode:
                    if prefs.masterPassword:
                        wx.MessageBox(_(u'Please enter the master password you used to protect this file to reload account passwords.'),
                                      _(u'Protect Passwords'),
                                      parent = wx.GetApp().mainFrame)                    
                    while True:
                        try:
                            newMaster = waitForDeferred(MasterPassword.get(rv, testPassword=dummy))
                            break
                        except password.NoMasterPassword:
                            if wx.MessageBox(_(u'If you do not remember your master password, all account passwords will be deleted. Delete account passwords?'),
                                             _(u'Reset Master Password'),
                                             style = wx.YES_NO,
                                             parent = wx.GetApp().mainFrame) == wx.YES:
                                MasterPassword.reset(rv)
                                break
                            
                    if newMaster == '':
                        break
                
                for item in password.Password.iterItems(rv):
                    if not waitForDeferred(item.initialized()):
                        # Don't need to re-encrypt uninitialized passwords
                        continue
                    
                    try:
                        pw = waitForDeferred(item.decryptPassword(masterPassword=oldMaster))
                    except password.DecryptionError:
                        # Maybe this was one of the new passwords loaded from
                        # settings, so let's try the new master password
                        try:
                            waitForDeferred(item.decryptPassword(masterPassword=newMaster))
                        except password.DecryptionError:
                            # Oops, we are in trouble, can't really do much but
                            # reset() to avoid further problems.
                            logger.exception('found passwords that could not be decrypted; clearing passwords')
                            MasterPassword.reset(rv)
                            break
                        # Since this is already encrypted with the new
                        # master password we don't need to re-encrypt
                        continue

                    waitForDeferred(item.encryptPassword(pw, masterPassword=newMaster))
