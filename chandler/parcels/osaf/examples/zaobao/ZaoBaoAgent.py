__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from repository.item.Item import Item
from repository.item.Query import KindQuery
from OSAF.framework.agents.schema.Action import Action
from OSAF.examples.zaobao.RSSData import ZaoBaoParcel, RSSChannel

import feedparser

def UpdateChannel(chan):
    try:
        etag = chan.getAttributeValue('etag', default=None)
        lastModified = chan.getAttributeValue('lastModified', default=None)
        if lastModified:
            modified = lastModified.tuple()
        else:
            modified = None
        data = feedparser.parse(chan.url, etag, modified)

        if data['status'] == 404:
            return

        chan.Update(data)
    except:
        pass

def MainThreadCommit():
    Globals.repository.commit()

class UpdateAction(Action):
    def Execute(self, agent, notification):
        repository = self.getRepository()

        repository.commit()
        #print 'Updating feeds...'
        chanKind = ZaoBaoParcel.getRSSChannelKind()
        for item in KindQuery().run([chanKind]):
            UpdateChannel(item)
        repository.commit()
        #print 'Updated feeds'

        Globals.application.PostAsyncEvent(MainThreadCommit)
