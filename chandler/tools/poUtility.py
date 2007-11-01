#   Copyright (c) 2006-2007 Open Source Applications Foundation
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


import re
import sys
import traceback

"""
Utility for parsing and validating po files.
"""

#PARSER STATE TOKENS
IDLE = 0
IN_MSGID = 1
IN_MSGSTR = 2
IN_LOCALIZER_COMMENT = 3
IN_PREVIOUS_MSGID_COMMENT = 4

def cmpPOEntry(e1, e2):
        # Sort entries based on which appeared first in the po
        # file
        if e1.msgidLineNumber > e2.msgidLineNumber:
            return 1
        return -1

class POEntry(object):
    __slots__ = ["msgidLineNumber", "msgstrLineNumber", "msgid", "msgstr", "fuzzy",
                 "localizerComment", "sourceFiles", "previousMsgID"]

    def __init__(self, msgidLineNumber=0, msgstrLineNumber=0, fuzzy=False, msgid='',
                 msgstr='', sourceFiles=None, localizerComment=None, previousMsgID=None):
        """
            All msgid and msgstr values are assumed to be of type str.
        """
        assert(isinstance(msgid, str))
        assert(isinstance(msgstr, str))

        self.msgidLineNumber = msgidLineNumber
        self.msgstrLineNumber = msgstrLineNumber
        self.fuzzy = False
        self.msgid = msgid
        self.msgstr = msgstr

        if sourceFiles:
            self.sourceFiles = sourceFiles
        else:
            self.sourceFiles = []
        self.localizerComment = localizerComment
        self.previousMsgID = previousMsgID


    def __repr__(self):
        buf = ["POEntry(%i, %i, %s, '%s', '%s', %s, "]

        if self.localizerComment is None:
            buf.append("%s, ")
        else:
            buf.append("'%s', ")

        if self.previousMsgID is None:
            buf.append("%s)")
        else:
            buf.append("'%s')")

        return "".join(buf) % \
                (self.msgidLineNumber, self.msgstrLineNumber, self.fuzzy, self.msgid, 
                 self.msgstr, self.sourceFiles, self.localizerComment, self.previousMsgID)

    def __str__(self):
        if isinstance(self.msgstr, unicode):
            return self.msgstr.encode("utf8")

        return self.msgstr

    def __unicode__(self):
        if isinstance(self.msgstr, str):
            return unicode(self.msgstr, "utf8", "ignore")

        return self.msgstr

    def isTranslated(self):
         return self.msgstr and len(self.msgstr)

    def isFuzzy(self):
        return self.fuzzy

    def hasSourceFiles(self):
        return self.sourceFiles and len(self.sourceFiles)

    def hasLocalizerComment(self):
        return self.localizerComment and len(self.localizerComment)

    def hasPreviousMsgID(self):
        return self.previousMsgID and len(self.previousMsgID)


class POFile(object):
    __slots__ = ["poEntries", "poFileName", "poComments"]

    def __init__(self, poFileName=None):
        self.poEntries = {}
        self.poFileName = poFileName
        self.poComments = None

    def getMsgIDs(self):
        return self.poEntries.keys()

    def getMsgIDCount(self):
        return len(self.poEntries.keys())

    def getFuzzyCount(self):
        fuzzyCount = 0

        for msgid, poEntry in self.poEntries.items():
            if poEntry.fuzzy:
                fuzzyCount += 1

        return fuzzyCount

    def getUntranslatedCount(self):
        untranslatedCount = 0

        for msgid, poEntry in self.poEntries.items():
            if not poEntry.isTranslated():
                untranslatedCount += 1

        return untranslatedCount

    def getTranslatedCount(self):
        translatedCount = 0

        for msgid, poEntry in self.poEntries.items():
            if poEntry.isTranslated():
                translatedCount += 1

        return translatedCount

class ParserError(Exception):
    __slots__ = ["exception", "tracebk", "lineNumber", "parserState", "poEntry", "poFileName"]

    def __init__(self, exception, tracebk, lineNumber, parserState, poEntry, poFileName):
        super(ParserError, self).__init__(str(exception))
        self.exception = exception
        self.tracebk = tracebk
        self.lineNumber = lineNumber
        self.parserState = parserState
        self.poEntry = poEntry
        self.poFileName = poFileName

    def __str__(self):
        buf = ["PO File Name: %s" % self.poFileName]
        buf.append("PO Line Number: %s" % self.lineNumber)
        buf.append("Error: %s" % str(self.exception))
        buf.append("Traceback: %s" % self.tracebk)

        return "\n".join(buf)

def checkAccelerators(poFile):
    assert(isinstance(poFile, POFile))
    results = []

    # This is a basic regex and could
    # be refined.
    exp   = r"&\S+"
    regex = re.compile(exp)

    for msgid, poEntry in poFile.poEntries.items():
        if isEmpty(poEntry.msgstr):
            continue

        if len(regex.findall(msgid)):
            amsgstr = len(regex.findall(poEntry.msgstr))

            if not amsgstr:
                results.append(poEntry)

    # Sort by line number
    results.sort(cmpPOEntry)
    return results


def checkPrintValues(poFile, field="msgid"):
    """
        The field argument can either be 'msgid' or
        'msgstr'. The method will search the requested
        field for Python print replace values such
        as %s and %3i etc.
    """
    assert(isinstance(poFile, POFile))
    assert(field=='msgid' or field == 'msgstr')

    results = []

    # Match Python print tokens such as %s %3i %3.3d etc.
    # in field specified in the method arguments
    exp = r"(%(c|s|\d*i|\d*\.*\d*(d|f)))"
    regex = re.compile(exp)

    for msgid, poEntry in poFile.poEntries.items():
        if field == 'msgid':
            text = msgid
        else:
            text = poEntry.msgstr

        if isEmpty(text):
            continue

        tokens = regex.findall(text)

        if len(tokens) == 0:
            continue

        values = []

        for token in tokens:
            values.append(token[0])

        results.append((poEntry, values))

    def _cmp(e1, e2):
        # Sort entries based on which appeared first in the po
        # file
        if e1[0].msgidLineNumber > e2[0].msgidLineNumber:
            return 1
        return -1

    # Sort by line number
    results.sort(_cmp)

    return results


def checkReplaceableValues(poFile):
    assert(isinstance(poFile, POFile))
    results = []

    # Match replaceable dictionary tokens to confirm that
    # the msgstr contains the same values as the msgid.
    exp = r"(%\([A-Z,a-z,\d]*\)(c|s|\d*i|\d*\.*\d*(d|f)))"
    regex = re.compile(exp)

    for msgid, poEntry in poFile.poEntries.items():
        if isEmpty(poEntry.msgstr):
            continue
        msgidTokens = regex.findall(msgid)

        if len(msgidTokens) == 0:
            continue

        msgstrTokens = regex.findall(poEntry.msgstr)

        error = False
        tokens = []

        for token in msgidTokens:
            # confirm that the token is in the msgstrTokens list.
            # Replaceable dictionary value ordering will change
            # on a locale by locale basis. But all of the values
            # must be in the string.

            if token not in msgstrTokens:
                error = True
                tokens.append(token[0])

        if error:
            results.append((poEntry, tokens))

    def _cmp(e1, e2):
        # Sort entries based on which appeared first in the po
        # file
        if e1[0].msgidLineNumber > e2[0].msgidLineNumber:
            return 1
        return -1

    # Sort by line number
    results.sort(_cmp)

    return results


def checkNewLines(poFile):
    assert(isinstance(poFile, POFile))

    results = []

    for msgid, poEntry in poFile.poEntries.items():
        if msgid.endswith("\\n") and not \
           isEmpty(poEntry.msgstr) and not \
           poEntry.msgstr.endswith("\\n"):
            results.append(poEntry)


    # Sort by line number
    results.sort(cmpPOEntry)

    return results


def parse(poFileName):
    assert(isinstance(poFileName, str))

    PARSER_STATE = IDLE
    FIRST_MSGID = True
    poFileObject = POFile(poFileName)
    poEntry = POEntry()
    lineNumber = 0

    # Raise any file opening related exceptions
    # outside the try except ParserException
    # block.
    poFileHandle = open(poFileName)

    try:
        for line in poFileHandle:
            lineNumber += 1

            if isComment(line):
                if PARSER_STATE == IN_MSGSTR:
                    if FIRST_MSGID:
                        FIRST_MSGID = False
                        # The first POEntry in the PO File contains
                        # meta data such as the translator and file encoding.
                        poFileObject.poComments = poEntry.msgstr
                    else:
                        poFileObject.poEntries[poEntry.msgid] = poEntry

                    #create a new entry
                    poEntry = POEntry()
                    PARSER_STATE = IDLE

                if isFuzzyComment(line):
                    poEntry.fuzzy = True
                    PARSER_STATE = IDLE

                elif isSourceComment(line):
                    map(poEntry.sourceFiles.append, line.split()[1:])
                    PARSER_STATE = IDLE

                elif isPreviousComment(line):
                    if PARSER_STATE == IN_PREVIOUS_MSGID_COMMENT:
                        poEntry.previousMsgID += "\n%s" % " ".join(line.split()[1:])[1:-1]
                    else:
                        line = " ".join(line.split()[2:])[1:-1]

                        poEntry.previousMsgID = line
                        PARSER_STATE = IN_PREVIOUS_MSGID_COMMENT

                elif isLocalizerComment(line):
                    if PARSER_STATE == IN_LOCALIZER_COMMENT:
                        poEntry.localizerComment += "\n%s" % " ".join(line.split()[1:])

                    else:
                        poEntry.localizerComment = " ".join(line.split()[1:])
                        PARSER_STATE = IN_LOCALIZER_COMMENT

                # Move to the next line in the po file
                continue

            if line.find("msgid") == 0:
                if PARSER_STATE == IN_MSGSTR:
                    if FIRST_MSGID:
                        FIRST_MSGID = False
                        # The first POEntry in the PO File contains
                        # meta data such as the translator and file encoding.
                        poFileObject.poComments = poEntry.msgstr
                    else:
                        poFileObject.poEntries[poEntry.msgid] = poEntry

                    #create a new entry
                    poEntry = POEntry()

                if FIRST_MSGID and line != 'msgid ""\n':
                    raise Exception("Invalid format. The first msgid in a po file must be empty.")

                poEntry.msgidLineNumber = lineNumber
                line = line[5:]
                PARSER_STATE = IN_MSGID

            elif line.find("msgstr") == 0:
                poEntry.msgstrLineNumber = lineNumber
                line = line[6:]
                PARSER_STATE = IN_MSGSTR

            if isEmpty(line):
                # Skip blank lines
                continue

            # Is the line properly formatted?
            eval(line)

            #Strip off opening and closing double quotes
            line = line.strip()[1:-1]

            if PARSER_STATE == IN_MSGID:
                poEntry.msgid += line
            elif PARSER_STATE == IN_MSGSTR:
                poEntry.msgstr += line
            else:
                raise Exception("Syntax error found in po file.")

        if PARSER_STATE == IN_MSGSTR:
            #We are at the end of the file so add the last poEntry
            poFileObject.poEntries[poEntry.msgid] = poEntry

        poFileHandle.close()
        return  poFileObject

    except Exception, e:
        cls, exc, tb = sys.exc_info()
        stack = traceback.format_tb(tb, 5)
        tracebk = []
        map(tracebk.append, stack)

        tracebk = "\n".join(tracebk)

        # Capture as much information as possible about where the exception occurred.
        raise ParserError(e, tracebk, lineNumber,
                          PARSER_STATE, poEntry, poFileName)


def isEmpty(line):
    return len(line.strip()) == 0

def isComment(line):
    return line.startswith("#")

def isFuzzyComment(line):
    return line.startswith("#,") and "fuzzy" in line

def isSourceComment(line):
    return line.startswith("#:")

def isPreviousComment(line):
    return line.startswith("#|")

def isLocalizerComment(line):
    return line.startswith("#.")

def unEscapeNewline(line):
    # Newlined with in a msgid or msgstr block are
    # escaped so convert \\n to \n.
    return "\n".join(line.split("\\n"))

