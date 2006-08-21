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


__parcel__ = "eventLogger"

from application import schema
from application import Globals
from osaf.framework.blocks import DispatchHook, BlockEvent
from osaf.framework.blocks.MenusAndToolbars import MenuItem
from osaf.startup import PeriodicTask
from osaf.sharing.WebDAV import ChandlerServerHandle
from zanshin.http import Request
from string import joinfields
from datetime import timedelta
from datetime import datetime
import socket
import re
import logging
import logging.handlers
import os


logger = logging.getLogger(__name__)

logDir = os.path.join(Globals.options.profileDir, 'eventLogger')
logFile = os.path.join(logDir, 'event.log')
logFileMaxSize = 250000 #Bytes
logFileMaxCount = 10    #Max logfiles to keep
logFileVersion = "1.0"  #Version of the logfile

class EventLoggingDispatchHook (DispatchHook):
    """
    Class to handle event dispatches
    """
    logging = schema.One(schema.Boolean, initialValue=False)

    def dispatchEvent (self, event, depth):
        """
        Actual handler which instantiates the logger and 'logs' the event
        """
        if not event.arguments.has_key ('UpdateUI') and depth == 1:
            logger = getattr (self, "logger", None)
            if logger is None:
                ## cache the logger for future use
                self.logger = self.createLogger()
            self.logEvent(event)

    def onToggleLoggingEvent (self, event):
        self.logging = not self.logging

        hooksListItem = schema.ns ('osaf.framework.blocks', self.itsView).BlockDispatchHookList
        dispatchHook = schema.ns (__name__, self.itsView).EventLoggingHook
        if self.logging:
            hooksListItem.hooks.insertItem (dispatchHook, None)
        else:
            hooksListItem.hooks.remove (dispatchHook)

    def onToggleLoggingEventUpdateUI (self, event):
        event.arguments['Check'] = self.logging

    def createLogger(self):   
        if not os.path.isdir(logDir):
            os.mkdir(logDir)

        handler = logging.handlers.RotatingFileHandler(logFile,'a', \
                                                       logFileMaxSize, \
                                                       logFileMaxCount)
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        logger = logging.getLogger('eventLogger')
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger


    def logEvent(self, event):
        items = event.arguments.get('items', None)
        if items is not None and len(items) > 0:
            item_name = items[0].getItemDisplayName()
        else:
            item_name = ""

        collection = event.arguments.get('collection', None)
        if collection is not None and len(collection) > 0:
            collection_name = collection.getItemDisplayName()
        else:
            collection_name = ""

        self.logger.debug("%s - %s - %s - %s" % (event.blockName, event.arguments, item_name, collection_name))


class UploadTask(object):
    """
    PeriodicTasks require that we use a non-persistent Python object
    """
    def __init__(self, item):
        self.rv = item.itsView
        logger.info("eventLogger - Installing Parcel")

    def run(self):
        logger.info("eventLogger - receiveWakeupCall()")

        dirList = os.listdir(logDir)
        for file in dirList:
            if re.search("event\.log\.\d+", file):

                fname = os.path.join(logDir, file)

                logger.info("eventLogger.Uploader: Trying to upload %s", fname)
                self.uploadFile(fname)
        return True


    def uploadFile(self, filename):
        """
        You can view via https://feedback.osafoundation.org/manage/usage/
        """
        
        path = '/desktop/usage/post/submit'
        host = 'feedback.osafoundation.org'
        port = 443
        useSSL = True

        timestamp = datetime.now()

        f = open(filename, 'rb')
        fdata = f.read()
        f.close()

        data = []
        data.append("username=%s" % os.getlogin())
        data.append("hostname=%s" % socket.gethostname())
        data.append("lversion=%s" % logFileVersion)
        data.append("uploaded=%s" % timestamp)
        data.append("\n%s" % fdata)

        datastring = joinfields(data,"\n")

        request = Request('POST', path, None, datastring)
        handle = ChandlerServerHandle(host=host, 
                                      port=port,
                                      useSSL=useSSL, 
                                      repositoryView=self.rv)
        defferedObject = handle.addRequest(request)
        defferedObject.addCallback(self.uploadSuccess, filename).addErrback(self.uploadFailure, filename) 
       

    def uploadSuccess(self, response, fname):
        if response.status == 200:
            os.remove(fname)          
            logger.info("Successfully uploaded %s", fname)
        else:
            logger.info("Failed up upload %s - %s:%s", fname, response.status, response.message)

    def uploadFailure(self, fobject, fname):
        logger.info("Failed to upload %s\n%s", fname, fobject)

def installParcel(parcel, old_version=None):
    mainView = schema.ns('osaf.views.main', parcel.itsView)

    dispatchHook = EventLoggingDispatchHook.update(
        parcel, 'EventLoggingHook',
        blockName = 'EventLoggingHook')

    # Event to toggle logging
    ToggleLogging = BlockEvent.update(
        parcel, 'ToggleLogging',
        blockName = 'ToggleLogging',
        dispatchEnum = 'SendToBlockByReference',
        destinationBlockReference = dispatchHook)

    # Add menu item to Chandler
    MenuItem.update(
        parcel, 'StartLogging',
        blockName = 'StartLoggingMenuItem',
        menuItemKind = 'Check',
        title = u'Start Logging',
        helpString = u'Turn on logging and send result to OSAF',
        event = ToggleLogging,
        eventsForNamedLookup = [ToggleLogging],
        location = "TestMenu",
        operation = 'InsertBefore',
        itemLocation = "SearchWindowItem",
        parentBlock = mainView.MainView)

    # The periodic task that uploads logfiles in the background  
    PeriodicTask.update(
        parcel, 'eventLoggerUploadTask',
        invoke = 'eventLogger.UploadTask',
        run_at_startup = True,
        active = True,
        interval = timedelta(minutes=20))

