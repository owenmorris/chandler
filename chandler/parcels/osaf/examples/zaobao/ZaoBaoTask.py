__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import application.Globals as Globals
from osaf.framework.tasks.Action import Action
from osaf.examples.zaobao.RSSData import ZaoBaoParcel
from repository.item.Query import KindQuery, TextQuery
import socket
import logging
from xml.sax import SAXParseException

def MainThreadCommit():
    Globals.repository.commit()

    #for item,attr in TextQuery('PyCon').run(Globals.repository):
    #    print item.getAttributeValue(attr).getReader().read()
    #    print '---------'

class UpdateAction(Action):
    def Execute(self, task):
        repository = self.itsView

        repository.commit()

        #print 'Updating feeds...'
        chanKind = ZaoBaoParcel.getRSSChannelKind()
        for item in KindQuery().run([chanKind]):
            try:
                item.Update()
            except socket.timeout:
                logging.exception('zaobao - socked timed out')
            except SAXParseException, e:
                #print 'failed to parse %s' % item.url
                #print e
                logging.exception('zaobao failed to parse %s' % item.url)
            except UnicodeDecodeError, e:
                #print 'failed to parse %s' % item.url
                #print e
                logging.exception('zaobao failed to parse %s' % item.url)
            except UnicodeEncodeError, e:
                #print 'failed to parse %s' % item.url
                #print e
                logging.exception('zaobao failed to parse %s' % item.url)

        repository.commit()
        #print 'Updated feeds'

        Globals.wxApplication.PostAsyncEvent(MainThreadCommit)
