#   Copyright (c) 2004-2006 Open Source Applications Foundation
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

"""
 A tokenizer module that wraps the PyICU.BreakIterator class.

 The SentenceTokenizer will divide large text blocks in to locale aware
 sentences.
"""

from PyICU import BreakIterator, Locale
from types import UnicodeType, StringType
import sys


class SentenceTokenizer(object):
    def __init__(self, txt, locale, stripEndOfLine=True):
        if type(txt) == StringType:
           txt = unicode(txt)

        assert(type(txt) == UnicodeType)

        self.txt = txt.replace(u"\t", u" ").strip()

        #XXX The decision of whether to replace returns with spaces
        #    is still up for debate. It helps the BreakIterator which
        #    will otherwise assume sentences end at the '\n' even if
        #    it really continues on the next line.
        #    However, if the BreakIterator is not able to find sentences
        #    with returns stripped the entire body of self.txt will be returned.
        if stripEndOfLine:
            self.txt = self.txt.replace(u"\r", u"").replace(u"\n", u" ")

        if type(locale) == UnicodeType:
           locale = str(locale)

        assert(type(locale) == StringType)

        #XXX This could be an invalid PyICU Locale.
        #    The i18n.i18nmanager.isValidPyICULocale
        #    could be used to check the value.
        pyLocale = Locale(locale)

        self.iterator = BreakIterator.createSentenceInstance(pyLocale)
        self.iterator.setText(self.txt)

    def nextToken(self):
        pos = []

        for n in self.iterator:
            pos.append(n)

        l = len(pos)

        if l:
            #Return the first sentence
            yield(self.txt[0:pos[0]]).strip()

            for c in xrange(0, l):
                if c + 1 < l:
                    yield(self.txt[pos[c]:(pos[c+1])]).strip()

if __name__ == "__main__":
    fp = open(sys.argv[1])
    txt = fp.read()
    fp.close()

    strip = True

    if len(sys.argv) > 2 and \
        sys.argv[2].lower() == "false":
        strip = False

    s = SentenceTokenizer(unicode(txt, "utf8", "ignore"), "en", stripEndOfLine=strip)

    for tok in s.nextToken():
        print '"%s"' % tok.encode("utf8")

