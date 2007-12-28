#   Copyright (c) 2005-2007 Open Source Applications Foundation
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

from __future__ import with_statement
from chandlerdb.persistence.Repository import RepositoryWorker
from chandlerdb.persistence.RepositoryView import otherViewWins
import twisted.internet.reactor as reactor
import logging

#Chandler mail imports
import constants
from utils import setStatusMessage, trace, alert, alertMailError
import message

"""
NEXT:
===============
1. Turn off observers in Mail Worker and EIM Translator layers
2. If good performance in step one then enable processing logic:
   processMail ever 100 messages commit every 500.

Performance Ideas Post-Preview:
==================================
1. Add in reactor.callLater throttling and higher timeout
   numbers that are caculated
2. Add back delete logic
3. Add tickets that are passed to worker. The worker posts
   the ticket number back to the caller when the action
   is complete. This is a good way to handle
   the delete mail case.
4. Try switching inline from WAIT_ON_COMMIT False to True on
   bottle necks.
5. Set the POP account type in an ini or dump file (MAIL vs.
   CHANDLER_HEADERS)
6. Feed Mail Objects to the worker every 100 messages,
   commit every 500.
7. Refactor POP seenMessageUIDs for faster lookup
8. Need a way to turn off observers and do calculations more
   efficiently in bulk instead of per item per attribute which
   is slow.

Performance Profiling Post-Preview:
========================================
1. previewQuickConvert and previewQuickParse
2. MailStamp.incomingMessage
3. ics and eimml profile calls
4. Test with empty_request and watch perf and memory
5. Use the chandler_perf account for testing eimml,
   ics, mail, task, and event conversion.
"""

MAIL_REQUEST = "MAIL"
DONE_REQUEST = "DONE"
ERROR_REQUEST = "ERROR"
UID_REQUEST = "UID"

# These two request types are used for
# debugging.
EMPTY_REQUEST = "EMPTY"
COMMIT_REQUEST = "COMMIT"

COMMANDS = {
    MAIL_REQUEST: "processMail",
    UID_REQUEST: "processUIDS",
    DONE_REQUEST: "processDone",
    ERROR_REQUEST: "processError",
    EMPTY_REQUEST: "processEmpty",
    COMMIT_REQUEST: "processCommit",
}

class DownloadTracker(object):
    def __init__(self):
        self.totalDownloaded = 0
        self.totalNewDownloaded = 0
        self.totalUpdateDownloaded = 0
        self.totalIgnoreDownloaded = 0
        self.totalErrorDownloaded = 0

        # Tracks the total number of downloaded
        # messages at the time of last commit
        self.lastTotalDownloaded = 0

class MailWorker(RepositoryWorker):
    def __init__(self, name, repository):
        super(MailWorker, self).__init__(name, repository)
        self.CACHE = {}
        self.shuttingDown = False

    def shutdown(self):
        self.shuttingDown = True
        self.terminate()

    def isEmpty(self):
        return self._requests.empty()

    def getQueueSize(self):
        return self._requests.qsize()

    def processRequest(self, view, request):
        if __debug__:
            trace("processRequest")

        if self.shuttingDown:
            return None

        if view is None:
            view = self._repository.createView(self.getName(),
                                               notify=False,
                                               mergeFn=otherViewWins,
                                               pruneSize=constants.MAILWORKER_PRUNE_SIZE)
            view.setBackgroundIndexed(True)
        else:
            view.refresh()

        cmd = account = client = protocol = None

        try:
            # request
            #    0: cmd
            #    1: Mail Client
            #    2: accountUUID
            cmd = request[0]
            client = request[1]
            account = view.findUUID(request[2])
            protocol = account.accountProtocol

            method = COMMANDS[cmd]
            callable = getattr(self, method)

            callable(view, protocol, client, account, request)

        except Exception, e:
            # This is a non-recoverable exception
            # which will result in an error dialog
            # being displayd in the UI
            if __debug__:
                logging.exception(e)

            self.handleError(view, client, account, e)

        return view

    def processMail(self, view, protocol, client, 
                    account, request):
        if __debug__:
            trace("processMail")

        # request
        #    0: cmd
        #    1: Mail Client
        #    2: accountUUID
        #    3: a tuple containing:
        #        0: message requests
        #        1: any protocol specific server UID info
        #    4. Status bar message to display on commit
        #    5: Reserved for Protocol specific info
        #        IMAP = tuple containing
        #            0: imap folder UID
        #            1: last UID of downloaded messages
        #
        #        Pop = None
        #


        if self.shuttingDown:
            return None

        assert(len(request) == 6)

        dt = self.getDownloadTracker(account)

        mRequests = request[3]

        # The status bar message to display on commit 
        msg = request[4]

        numToProcess = len(mRequests)
        numError = 0

        if protocol == "IMAP":
            # This is the IMAPFolder item
            args = view.findUUID(request[5][0])

        elif protocol == "POP":
            args = None

        for mRequest in mRequests:
            try:
                if self.shuttingDown:
                    try:
                        view.cancel()
                    except:
                        pass
                    return None

                self.processMessage(view, protocol, client, account,
                                    mRequest, dt, args)
            except Exception, e:
                # This is a recoverable exception related to conversion of
                # the mail message to an Item. Any processing errors
                # should be logged however it should not terminate
                # mail download
                logging.exception(e)

                # This is used to track the total number of messages
                # that failed to be converted to Items.
                numError += 1

        if numToProcess != numError:
            # If all the messages failed to be converted to Items then
            # there is a bug in the mail code or some other major error.
            # In this case we don't want to save the lastMessageUID since
            # this will prevent the messages from being downloaded and
            # processed again once the error or bug is resolved.
            if protocol == "IMAP":
                args.lastMessageUID = request[5][1]

            setStatusMessage(msg)
            view.commit()

            dt.lastTotalDownloaded = dt.totalDownloaded

        else:
            # Unable to process any messages so cancel the view
            view.cancel()

        if constants.WAIT_FOR_COMMIT:
            reactor.callFromThread(client.nextAction)

    def processMessage(self, view, protocol, client,
                       account, mRequest, dt, args):
        if __debug__:
            trace("processMessage")

        # mRequest
        #     0: Mail Request Tuple
        #         0: headers of the email decoded and converted to Unicode
        #         1: body of the message as displayed in the ContentItem.body attribute or None
        #         2. decoded and carriage return stripped eimml attachment or None
        #         3: decoded and carriage return stripped ics attachment or None
        #     1: Protocol specific UID

        headers, body, eimml, ics = mRequest[0]

        statusCode, repMessage = message.previewQuickConvert(view, headers,
                                                             body, eimml, ics)

        if statusCode == 1:
            # If the message contained an eimml attachment
            # that was older then the current state or
            # contained bogus data then repMessage will be
            # None and the Mail Service will ingore the message.

            if repMessage.isAnUpdate():
                # This is an update to an existing Chandler item
                # so increment the updatecounter
                dt.totalUpdateDownloaded += 1

            else:
                # This is a new Chandler item so increment the
                # new counter
                dt.totalNewDownloaded += 1

            ignoreMe = False

            if protocol == "IMAP":
                # If this is an IMAP request then check the
                # folder type. If the type is EVENT then
                # stamp the Item with an EventStamp and
                # parse the subject and body for
                # date time info. If the type is
                # TASK then stamp the Item with a TaskStamp.

                # The args variable is an IMAPFolder item instance
                if args.folderType == "EVENT":
                    message.parseEventInfo(repMessage)

                elif args.folderType == "TASK":
                    message.parseTaskInfo(repMessage)


                if args.displayName.lower() != u"inbox":
                    # In this case do not assign mail as
                    # toMe if the from address is a 'me' address.
                    # The use case is a person dropping a draft
                    # or sent message in to a Chandler Folder.
                    # The design team asks that when this happens
                    # the message not appear in the 'In Collection'
                    ignoreMe = True

            repMessage.incomingMessage(ignoreMe)
        elif statusCode == 0:
            # The eimml was a duplicate or ignored
            dt.totalIgnoreDownloaded += 1

        else:
            # There was an error raised while parsing the
            # eimml
            dt.totalErrorDownloaded += 1

        if protocol == "IMAP":
            # IMAP folders can have max download
            # limits set in the Chandler Mail Service.
            # This value is used to track the total
            # downloaded for the Folder. If the total
            # equals the max allowable then
            # don't download anymore. This a configurable
            # option. The IMAP Folders do not
            # have download limits by default.
            args.downloaded += 1

        elif protocol == "POP":
            # POP accounts can have max download
            # limits set in the Chandler Mail Service.
            # This value is used to track the total
            # downloaded for the account. If the total
            # equals the max allowable then
            # don't download anymore. This a configurable
            # option. POP Accounts do not
            # have download limits by default.
            account.downloaded += 1
            account.seenMessageUIDS[mRequest[1]] = "True"

        dt.totalDownloaded += 1


    def processUIDS(self, view, protocol, client, 
                    account, request):
        if __debug__:
            trace("processUIDS")

        # request =
        #   0: cmd
        #   1: Mail Client
        #   2: accountUUID
        #   3: proocol specific info
        #       IMAP = tuple containing
        #           0: imap folder UUID
        #           1: UID of last message
        #
        #       POP =  List of UIDS of seen messages

        if self.shuttingDown:
            return None

        if protocol == "IMAP":
            imapFolderUUID = request[3][0]
            imapFolder = view.findUUID(imapFolderUUID)

            # Store the last message UID for the IMAPFolder
            imapFolder.lastMessageUID = request[3][1]

        elif protocol == "POP":
            uids = request[3]

            for uid in uids:
                account.seenMessageUIDS[uid] = "True"

        view.commit()


    def processDone(self, view, protocol, client,
                    account, request):
        if __debug__:
            trace("processDone")

        if self.shuttingDown:
            return None

        # request
        #     0: cmd
        #     1: client
        #     2: accountUUID
        dt = self.getDownloadTracker(account)

        if dt.totalDownloaded > 0:
            # This is a PyICU.ChoiceFormat class
            txt = constants.DOWNLOAD_CHANDLER_MESSAGES.format(dt.totalDownloaded)

            setStatusMessage(txt % \
                             {'accountName': account.displayName,
                              'numberTotal': dt.totalDownloaded,
                              'numberNew': dt.totalNewDownloaded,
                              'numberUpdates': dt.totalUpdateDownloaded,
                              'numberDuplicates': dt.totalIgnoreDownloaded,
                              'numberErrors': dt.totalErrorDownloaded})
        else:
            setStatusMessage(constants.DOWNLOAD_NO_MESSAGES % \
                            {'accountName': account.displayName})

        self._resetWorker(account)

        # Post a notification to the Mail Protocol Client
        # That the requested actions are finished.
        reactor.callFromThread(client.requestsComplete)


    def processEmpty(self, view, protocol, client,
                     account, request):
        if __debug__:
            trace("processEmpty")

        if self.shuttingDown:
            return None
        return

    def processCommit(self, view, protocol, client,
                      account, request):
        if __debug__:
            trace("processCommit")

        if self.shutttingDown:
            return None

        try:
            dt = self.getDownloadTracker(account)
            view.commit()
            dt.lastTotalDownloaded = dt.totalDownloaded

            if constants.WAIT_FOR_COMMIT:
                reactor.callFromThread(client.nextAction)

        except Exception, e:
            if __debug__:
                logging.exception(e)

            self.handleError(view, client, account, e)


    def processError(self, view, protocol, client,
                     account, request):
        if __debug__:
            trace("processError")

        if self.shuttingDown:
            return None

        #Clear the status bar message
        setStatusMessage(u"")
        self._resetWorker(account)

    def _resetWorker(self, account):
        if __debug__:
            trace("_resetWorker")

        dt = self.getDownloadTracker(account)

        dt.totalDownloaded = 0
        dt.totalNewDownloaded = 0
        dt.totalUpdateDownloaded = 0
        dt.totalIgnoreDownloaded = 0
        dt.totalErrorDownloaded = 0
        dt.lastTotalDownloaded = 0

    def handleError(self, view, client, account, err):
        if __debug__:
            trace("handleError")

        if self.shuttingDown:
            return None

        if client is None:
            errText = unicode(err.__str__(), 'utf8', 'ignore')

            if account is None:
                alert(constants.MAIL_GENERIC_ERROR % {'errText': errText})

            else:
                alertMailError(constants.MAIL_PROTOCOL_ERROR, account, \
                               {'hostName': account.host, 'errText': errText})
        else:
            reactor.callFromThread(client.catchErrors, err)

        view.cancel()

        if account:
            self._resetWorker(account)

    def getDownloadTracker(self, account):
        if not self.CACHE.has_key(account.itsUUID):
            self.CACHE[account.itsUUID] = DownloadTracker()

        return self.CACHE[account.itsUUID]
