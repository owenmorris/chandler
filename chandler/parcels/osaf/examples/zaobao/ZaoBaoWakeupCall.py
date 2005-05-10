__revision__  = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004 Open Source Applications Foundation"
__license__   = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import osaf.framework.wakeup.WakeupCaller as WakeupCaller
import osaf.examples.zaobao.RSSData as RSSData
from repository.item.Query import KindQuery, TextQuery
import socket
import logging
from xml.sax import SAXParseException

class WakeupCall(WakeupCaller.WakeupCall):

    def receiveWakeupCall(self, wakeupCallItem):

        view = wakeupCallItem.itsView
        view.refresh()

        chanKind = RSSData.RSSChannel.getKind(view)

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
            except Exception, e:
                logging.exception('zaobao failed to parse %s' % item.url)

            try:
                view.commit()
            except Exception, e:
                logging.exception('zaobao failed to commit %s' % item.url)
