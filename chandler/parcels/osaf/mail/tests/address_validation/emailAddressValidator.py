#!/usr/bin/python
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


import re as re
from string import *
import email.Utils as Utils

validEmailAddresses   = ["morgen@o11.org", "John Test <john@test.com>", "bill+73@home.test.com", "fred&barney@example.com", "matt@[127.0.0.1]"]
invalidEmailAddresses = ["e@a.c", "", "ted.jone#!(@notreal.com", "", "*", "69@@teset.com"]

def main():
    print "\nTesting Valid Email Addresses:"
    print "------------------------------\n"
    testEmailAddresses(validEmailAddresses)

    print "\nTesting Invalid Email Addresses:"
    print "----------------------------------\n"
    testEmailAddresses(invalidEmailAddresses)

def testEmailAddresses(arr):
    for email in arr:
        print "\tEmail Address: ", email
        print "\t---------------------------------"

        #Strip any name information from email address
        email = Utils.parseaddr(email)[1]

        if isvalidEmailOne(email):
            print "\t\tisvalidEmailOne PASSED"
        else:
            print "\t\tisvalidEmailOne FAILED"

        if isvalidEmailTwo(email):
            print "\t\tisvalidEmailTwo PASSED"
        else:
            print "\t\tisvalidateEmailTwo FAILED"

        if isvalidEmailThree(email):
            print "\t\tisvalidateEmailThree PASSED"
        else:
            print "\t\tisvalidateEmailThree FAILED"

        if isvalidEmailFour(email):
            print "\t\tisvalidateEmailFour PASSED"
        else:
            print "\t\tisvalidateEmailFour FAILED"

        if isvalidEmailFive(email):
            print "\t\tisvalidateEmailFive PASSED"
        else:
            print "\t\tisvalidateEmailFive FAILED"

        print "\n"


def isvalidEmailOne(s):
    return re.match("\w+((-\w+)|(\.\w+)|(\_\w+))*\@[A-Za-z0-9]+((\.|-)[A-Za-z0-9]+)*\.[A-Za-z]{2,5}", s) is not None


def isvalidEmailTwo(s):
    return re.match("^.+\\@(\\[?)[a-zA-Z1-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", s) is not None

def isvalidEmailThree(s):
    # First we validate the name portion (name@domain)
    rfc822_specials = '()<>@,;:\\"[]'

    c = 0
    while c < len(s):
        if s[c] == '"' and (not c or s[c - 1] == '.' or s[c - 1] == '"'):
            c = c + 1
            while c < len(s):
                if s[c] == '"': break
                if s[c] == '\\' and s[c + 1] == ' ':
                    c = c + 2
                    continue
                if ord(s[c]) < 32 or ord(s[c]) >= 127: return 0
                c = c + 1
            else: return 0
            if s[c] == '@': break
            if s[c] != '.': return 0
            c = c + 1
            continue
        if s[c] == '@': break
        if ord(s[c]) <= 32 or ord(s[c]) >= 127: return 0
        if s[c] in rfc822_specials: return 0
        c = c + 1
    if not c or s[c - 1] == '.': return 0

    # Next we validate the domain portion (name@domain)
    domain = c = c + 1
    if domain >= len(s): return 0
    count = 0
    while c < len(s):
        if s[c] == '.':
            if c == domain or s[c - 1] == '.': return 0
            count = count + 1
        if ord(s[c]) <= 32 or ord(s[c]) >= 127: return 0
        if s[c] in rfc822_specials: return 0
        c = c + 1

    return count >= 1

def isvalidEmailFour(s):
    """Verify that the an email address isn't grossly evil."""

    _badchars = re.compile(r'[][()<>|;^,/\200-\377]')

    # Pretty minimal, cheesy check.  We could do better...
    if not s or s.count(' ') > 0:
        return False
    if _badchars.search(s) or s[0] == '-':
        return False
    user, domain_parts = _ParseEmail(s)
    # This means local, unqualified addresses, are no allowed
    if not domain_parts:
        return False
    if len(domain_parts) < 2:
        return False

    return True

def isvalidEmailFive(s):
    return re.match("^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$", s) is not None


def _ParseEmail(email):
    user = None
    domain = None
    email = email.lower()
    at_sign = email.find('@')
    if at_sign < 1:
        return email, None
    user = email[:at_sign]
    rest = email[at_sign+1:]
    domain = rest.split('.')
    return user, domain

main()
