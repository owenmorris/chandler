__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2003 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from OSAF.framework.agents.schema.Action import Action
from OSAF.examples.zaobao.RSSData import ZaoBaoParcel
from repository.item.Query import KindQuery
import socket
import logging

def MainThreadCommit():
    Globals.repository.commit()

class UpdateAction(Action):
    def Execute(self, agent, notification):
        repository = self.getRepository()

        repository.commit()
        #print 'Updating feeds...'
        chanKind = ZaoBaoParcel.getRSSChannelKind()
        for item in KindQuery().run([chanKind]):
            try:
                item.Update()
            except socket.timeout:
                logging.debug('zaobao - socked timed out')
        repository.commit()
        #print 'Updated feeds'

        Globals.wxApplication.PostAsyncEvent(MainThreadCommit)
