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

from application import schema
from i18n import MessageFactory
from osaf import sharing, startup, pim
import wx, datetime
from osaf.pim.calendar.TimeZone import convertToICUtzinfo
from dateutil.parser import parse as dateutilparser
from application.dialogs.AccountPreferences import AccountPanel
from osaf.framework.twisted import waitForDeferred
import urllib2



from osaf.framework.blocks import (BlockEvent, NewBlockWindowEvent, MenuItem,
    Menu)
from osaf.framework.blocks.Block import Block

import twitter

_ = MessageFactory("Chandler-TwitterPlugin")


import logging
logger = logging.getLogger(__name__)




class TwitterPeriodicTask(startup.PeriodicTask):
    def fork(self):
        return startup.fork_item(self, name="Twitter", pruneSize=500,
            notify=False, mergeFn=sharing.mergeFunction)




def installParcel(parcel, oldVersion=None):

    TwitterPeriodicTask.update(parcel, "twitterTask",
        invoke="chandler_twitter.Handler",
        run_at_startup=True,
        active=True,
        interval=datetime.timedelta(seconds=2*60)
    )


    AccountPanel.update(parcel, "TwitterAccountPanel",
        accountClass = TwitterAccount,
        key = "SHARING_TWITTER",
        info = {
            "fields" : {
                "TWITTERSHARING_DESCRIPTION" : {
                    "attr" : "displayName",
                    "type" : "string",
                    "required" : True,
                    "default": _(u"New Twitter Account"),
                },
                "TWITTERSHARING_USERNAME" : {
                    "attr" : "username",
                    "type" : "string",
                },
                "TWITTERSHARING_PASSWORD" : {
                    "attr" : "password",
                    "type" : "password",
                },
            },
            "id" : "TWITTERSHARINGPanel",
            "order": 100, # after OOTB accounts
            "displayName" : "TWITTERSHARING_DESCRIPTION",
            "description" : _(u"Twitter"),
            "protocol" : "TWITTER",
        },
        xrc = """<?xml version="1.0" encoding="ISO-8859-15"?>
<resource>
  <object class="wxPanel" name="TWITTERSHARINGPanel">
    <object class="wxBoxSizer">
      <orient>wxVERTICAL</orient>
      <object class="sizeritem">
        <flag>wxALIGN_CENTER|wxALL</flag>
        <border>5</border>
        <object class="wxFlexGridSizer">
          <cols>2</cols>
          <rows>0</rows>
          <vgap>0</vgap>
          <hgap>0</hgap>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <style>wxALIGN_RIGHT</style>
              <label>Account type:</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER_VERTICAL|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <size>300,-1</size>
              <label>Twitter Sharing</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <style>wxALIGN_RIGHT</style>
              <label>Descr&amp;iption:</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER_VERTICAL|wxALL</flag>
            <border>5</border>
            <object class="wxTextCtrl" name="TWITTERSHARING_DESCRIPTION">
              <size>300,-1</size>
              <value></value>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <style>wxALIGN_RIGHT</style>
              <label>User &amp;name:</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER_VERTICAL|wxALL</flag>
            <border>5</border>
            <object class="wxTextCtrl" name="TWITTERSHARING_USERNAME">
              <size>300,-1</size>
              <value></value>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER|wxALL</flag>
            <border>5</border>
            <object class="wxStaticText" name="ID_TEXT">
              <style>wxALIGN_RIGHT</style>
              <label>Pass&amp;word:</label>
            </object>
          </object>
          <object class="sizeritem">
            <flag>wxALIGN_CENTER_VERTICAL|wxALL</flag>
            <border>5</border>
            <object class="wxTextCtrl" name="TWITTERSHARING_PASSWORD">
              <size>300,-1</size>
              <style>wxTE_PASSWORD</style>
              <value></value>
            </object>
          </object>
        </object>
      </object>
    </object>
  </object>
</resource>
"""
    )



class Handler:

    def __init__(self, item):
        self.rv = item.itsView

    def run(self, *args, **kwds):

        # This method must return True -- no raising exceptions!

        try:
            self.rv.refresh()
            uuids = [account.itsUUID for account in
                TwitterAccount.iterItems(self.rv)]
            for uuid in uuids:
                account = self.rv.findUUID(uuid)
                if account is not None and account.username:
                    update(account)

        except:
            logger.exception("Error during Twitter run()")

        return True




def update(account):
    rv = account.itsView

    collection = getCollection(rv)
    if collection is None:
        return

    username = account.username
    password = waitForDeferred(account.password.decryptPassword())

    lastFetch = getattr(account, 'lastFetch',
        convertToICUtzinfo(rv,
            datetime.datetime.now() -
            datetime.timedelta(days=7)).astimezone(rv.tzinfo.default))


    api = twitter.Api(username=username, password=password)

    fmt = "%a %b %d %H:%M:%S +0000 %Y"
    since = lastFetch.astimezone(rv.tzinfo.UTC).strftime(fmt)

    logger.info("Twitter fetch for %s's friends", username)

    try:
        statuses = api.GetFriendsTimeline(since=since)

    except urllib2.HTTPError, e:
        logger.info("Twitter HTTP error: %s", e)
        return

    except Exception, e:
        logger.exception("Twitter error")
        return

    logger.info("Twitter fetch received %d items", len(statuses))

    account.lastFetch = convertToICUtzinfo(rv,
        datetime.datetime.now()).astimezone(rv.tzinfo.default)

    for status in statuses:
        timestamp = convertToICUtzinfo(rv, dateutilparser(status.created_at))
        timestamp = timestamp.astimezone(rv.tzinfo.default)

        fromMe = status.user.screen_name == username
        toMe = "@%s" % username in status.text

        # Create an event
        event = pim.CalendarEvent(itsView=rv,
            displayName = "%s: %s" % (status.user.name, status.text),
            body = "%s: %s" % (status.user.name, status.text),
            startTime = timestamp,
            duration = datetime.timedelta(minutes=30),
            anyTime = False,
            transparency = ('tentative' if fromMe else
                            'confirmed' if toMe else 'fyi')
        )

        # Also stamp as mail so I can set originator:
        pim.mail.MailStamp(event.itsItem).add()
        message = pim.mail.MailStamp(event.itsItem)
        message.originators.add(pim.EmailAddress.getEmailAddress(rv,
            "%s <%s>" % (status.user.name, status.user.screen_name)))

        collection.add(event.itsItem)

    rv.commit()



def getCollection(rv):
    # for now, just look for a collection named "Twitter"
    for collection in pim.SmartCollection.iterItems(rv):
        if collection.displayName == "Twitter":
            return collection

    collection = pim.SmartCollection(itsView=rv, displayName="Twitter")
    schema.ns('osaf.app', rv).sidebarCollection.add(collection)

    return collection






class TwitterAccount(sharing.SharingAccount):
    accountProtocol = schema.One(initialValue = 'Twitter')
    accountType = schema.One(initialValue = 'SHARING_TWITTER')
    lastFetch = schema.One(schema.DateTimeTZ)

    def publish(self, collection, activity=None, filters=None, overwrite=False):
        # Not implemented
        raise sharing.SharingError("Publishing to Twitter not yet supported")




