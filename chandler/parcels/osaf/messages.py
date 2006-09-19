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


from i18n import ChandlerMessageFactory as _

#XXX: Relook at how to leverage wxstd translations

UNTITLED = _(u"Untitled")
ME = _(u"me")

"""Common GUI Stuff. This might come directly from WxWidgets"""
UNDO   = _(u"Undo")
REDO   = _(u"Redo")
CUT    = _(u"Cut")
COPY   = _(u"Copy")
PASTE  = _(u"Paste")
CLEAR  = _(u"Clear")
SELECT_ALL = _(u"Select All")
ERROR = _(u"Error")

"""Menu Item / Markup bar button Titles"""
SEND = _(u"Send")
REPLY = _(u"Reply")
REPLY_ALL = _(u"Reply All")
FORWARD = _(u"Forward")
STAMP_MAIL = _(u"Prepare as Message")
STAMP_TASK = _(u"Put on Task list")
STAMP_CALENDAR = _(u"Put on Calendar")
PRIVATE = _(u"Never share this item")
NOT_PRIVATE = _(u"Allow sharing this item")
READONLY = _(u"Read only")

STAMP_MAIL_HELP = _(u"Address this item")
STAMP_TASK_HELP = _(u"Add to task list")
STAMP_CALENDAR_HELP = _(u"Add to Calendar")

"""Server Account Settings"""
USERNAME = _(u"Username")
PASSWORD = _(u"Password")
HOST = _(u"Host")
PORT = _(u"Port")
PATH = _(u"Path")

"""Account Configuration"""
NEW_ACCOUNT = _(u"New %(accountType)s Account")
ACCOUNT_PREFERENCES = _(u"Account Preferences")
ACCOUNT = _(u"%(accountName)s Account")

# SSL
SSL_HOST_MISMATCH = _(u'Peer certificate does not match host, expected %(expectedHost)s, got %(actualHost)s')

