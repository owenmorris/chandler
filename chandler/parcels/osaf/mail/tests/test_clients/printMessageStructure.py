#!/usr/bin/python
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

import email
from email import Utils
import sys, os
import mimetypes

FLAG = True

class Counter:
    def __init__(self, val=0):
        self.counter = val

    def nextValue(self):
        self.counter += 1
        return self.counter

class MailMessage:
    def __init__(self):
        self.subject = None
        self.body = []
        self.attachments = []

    def __str__(self):
        buffer = ["MailMessage:\n------------\n\n"]
        self.subject and buffer.append("Subject: %s" % self.subject)

        if len(self.body):
            buffer.append("Body:\n---------------\n")

            for part in self.body:
                buffer.append("%s\n" % part)

        if len(self.attachments):
            buffer.append("Attachments:\n---------------\n")

            for attachment in self.attachments:
                buffer.append("%s\n" % str(attachment))

        return '\n'.join(buffer)

    def save(self):
        for attachment in self.attachments:
            attachment.save()

class Attachment:
    def __init__(self, filename, body, size, mimetype, mimedesc, encoding=None):
        self.filename = filename
        self.body = body
        self.size = size
        self.mimetype = mimetype
        self.encoding = encoding

    def __str__(self):
        buffer = []

        self.filename and buffer.append("Filename: %s" % self.filename)
        self.size and buffer.append(" size: %s" % self.size)
        self.mimetype and buffer.append(" mimetype: %s" % self.mimetype)
        self.encoding and buffer.append(" encoding: %s" % self.encoding)

        return ''.join(buffer)

    def save(self):
        out = open("attachments/%s" % self.filename, "w")
        out.write(self.body)
        out.close()

def parse(m, mes, counter, level=1):
    #XXX: For now just log the defects, it also may not be an actual message
    checkDefects(m)

    if len(m.keys()) == 0:
        print "Not a RFC 2822 Compliant Message"
        return

    if level == 1:
        trace(level, "\n\nMESSAGE STRUCTURE\n------------------------------")

    multipart = m.is_multipart()
    maintype  = m.get_content_maintype()
    contype   = m.get_content_type()
    subtype   = m.get_content_subtype()

    """If the message is multipart then pass decode=False to get_poyload otherwise pass True"""
    payload = m.get_payload(decode=not multipart)

    if payload is None:
        #XXX: Throw an exception
        trace(level, "Something wrong payload is still None")
        return

    if maintype == "message":
        """Get the required headers and append to the body then append any text parts"""

        if subtype == "rfc822":
            if multipart:
                """record the subject and from, date, to, subject"""
                sub = m.get_payload()[0]
                #XXX: handle the reply-to / sender case and decode the headers
                mes.body.append(u'\nFrom: %s' % sub.get('From'))
                mes.body.append(u'Date: %s' % sub.get('Date'))
                mes.body.append(u'To: %s' % sub.get('To'))
                mes.body.append(u'Subject: %s\n' % sub.get('Subject'))
            else:
                #XXX Log the object structure error
                print "rfc822 part is not Multipart"

        elif subtype == "delivery-status":
            #XXX: The email 3.0 is messed up need to add a hack later
            #XXX: This is will need i18n decoding
            """Add the delivery status info to the message body """
            mes.body.append(m.as_string())
            return

        elif subtype == "disposition-notification-to":
            """Add the disposition-notification-to info to the message body"""
            #XXX: This is will need i18n decoding
            mes.body.append(unicode(m.as_string()))
            return

        elif subtype == "external-body":
            return

        elif subtype == "http":
            return

        elif subtype == "partial":
            return

        if multipart:
            trace(level, "%s" % contype)

            for part in payload:
                parse(part, mes, counter, level+1)

        else:
            trace(level, "Message: %s %s" % (contype, payload))
            mes.body.append(payload)

    elif maintype == "multipart":
        if subtype == "alternative":
            trace(level, "multipart/alternative")

            if len(payload) > 0:
                foundText = False

                for part in payload:
                    if part.get_content_type() == "text/plain":
                        #XXX: This needs i18n decoding
                        mes.body.append(part.get_payload(decode=1))
                        foundText = True
                        break

                if not foundText:
                    for part in payload:
                        """A multipart/alternative container should have
                           at least one part that is not multipart and
                           is text based (plain, html, rtf) for display
                        """
                        if not part.is_multipart():
                            addPart(part, part.get_payload(decode=1), \
                                          mes, counter, level)
                            break

        elif subtype == "byteranges":
            print "Ignore me: %s" % contype
            return

        elif subtype == "form-data":
            print "Ignore me: %s" % contype
            return

        elif subtype == "signed":
            print "Ignore me: %s" % contype
            return

        elif subtype == "encrypted":
            print "Ignore me: %s" % contype
            return

        else:
            trace(level, contype)
            for part in payload:
                parse(part, mes, counter, level+1)

    # It is an attachement or text part
    else:
        addPart(m, payload, mes, counter, level)


def addPart(m, payload, mes, counter, level):
        # skip AppleDouble resource files per RFC1740
        if m.get_content_type() == "application/applefile":
            return

        contype   = m.get_content_type()
        maintype  = m.get_content_maintype()
        subtype   = m.get_content_subtype()

        trace(level, contype)

        # Get the size of the attachment or text part
        size = len(payload)

        #XXX: Perform 18n decoding
        if maintype == "text":
            pass

        if subtype == "plain" or subtype == "rfc822-headers":
            """Plain text and rfc-headers are the only supported types"""
            #XXX: this requires i18n decoding
            size > 0 and mes.body.append("%s\n" % payload)

        else:
            mes.attachments.append(Attachment(getFileName(m, counter), payload, size, \
                                              contype, None))

def getFileName(mimePart, counter):
    """
        This should handle all Unicode decoding of filename as well
    """
    filename = mimePart.get_filename()

    if filename:
        return filename

    """No Filename need to create an arbitrary namei and guess extension"""
    ext = mimetypes.guess_extension(mimePart.get_content_type())

    if not ext:
       ext = '.bin'

    #XXX: Mime type will be application/octet-stream
    return u'Attachment-%s%s' % (counter.nextValue(), ext)

def checkDefects(m):
    if len(m.defects) > 0:
        for defect in m.defects:
            print "***** WARNING ********* Found defect: %s" % str(defect.__class__).split(".").pop()

def trace(level, str):
    if not FLAG:
       return

    if level:
        print "%s %s" % (level * "   ", str)
    else:
        print str

def parseFile(file):
    messageObject = email.message_from_file(open(file))
    mailMessage = MailMessage()
    counter = Counter()

    parse(messageObject, mailMessage, counter)
    print "\n"

    if not FLAG:
        #print "Parsing File ", file
        print mailMessage
        #mailMessage.save()


def parseDir(dir):
    files = os.listdir(dir)
    files.sort()

    for file in files:
        if not file.startswith('test_'):
            continue

        parseFile("%s/%s" % (dir, file))

parseFile(sys.argv[1])
#parseDir(sys.argv[1])




