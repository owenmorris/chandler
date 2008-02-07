#   Copyright (c) 2007 Open Source Applications Foundation
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

from osaf.pim.stamping import has_stamp
from osaf.pim.mail  import MailStamp, EmailAddress
from osaf.pim.tasks import TaskStamp
from osaf.pim.notes import Note
from osaf.pim.calendar.Calendar import parseText, setEventDateTime, EventStamp

from osaf.quickentry import QuickEntryState, QuickEntryCommand

from i18n import ChandlerMessageFactory as _

__all__ = ['NoteCommand', 'TaskCommand', 'EventCommand', 'MailCommand',
           'RequestCommand', 'InviteCommand', 'stamp_to_command']

class ItemState(QuickEntryState):
    """
    State for creating and processing an item
    """
    def __init__(self, view, text):
        self.view = view
        self.text = text
        self.item = Note(itsView = view)
        self.item.InitOutgoingAttributes()

        self.parse_tuple = parseText(view, text)
        self.handled_event = False
        self.handled_reminder = False

    def finalize(self):
        """Add item to the selected sidebar collection, set displayName on item.

	If the selected sidebar collection can't be added to, instead add to the
	Dashboard.

	"""
        self.item.displayName = self.text

    def set_event_attributes(self):
        if not has_stamp(self.item, EventStamp):
            EventStamp(self.item).add()

        startTime, endTime, countFlag, typeFlag = self.parse_tuple
        setEventDateTime(self.item, startTime, endTime, typeFlag)    

    def parse_for_event(self):
        if not self.handled_event:
            startTime, endTime, countFlag, typeFlag = self.parse_tuple
            # If there is a date/time range, treat the message as an event
            if startTime != endTime and not has_stamp(self.item, EventStamp):
                self.set_event_attributes()
            self.handled_event = True

    def parse_for_reminder(self):
        if not self.handled_reminder:
            startTime, endTime, countFlag, typeFlag = self.parse_tuple
            # If there is a date/time range, treat the message as an event
            if not has_stamp(self.item, EventStamp) and typeFlag != 0 :
                self.item.userReminderTime = startTime
            self.handled_reminder = True

#### finding contacts helpers ##################################################
email_pattern = u'[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}'
find_contact_re = re.compile(u'\s?((%s)\s?(,|;)?\s?)+\s?:' % email_pattern, re.UNICODE | re.LOCALE)

contacts_pattern = u"""
                 \s*                      # ignore whitespace
                 (?P<contact> ([^,;\s]+)) # any intervening non-whitespace is the contact
                 \s*                      # ignore whitespace
                 (,|;)?                   # gobble contact separators
                 \s*                      # ignore whitespace
                 """
many_contacts_re = re.compile(contacts_pattern, re.UNICODE | re.VERBOSE | re.LOCALE)

def getAddress(view, match):
    """Get an EmailAddress from a many_contacts_re match."""
    return EmailAddress.getEmailAddress(view, match.group('contact'))
################################################################################

class NoteCommand(QuickEntryCommand):
    """Don't add any stamps, leave the item as a Note."""
    single_command = False
    stamp_types = []
    # L10N: A comma separated list of names for commands to create a note
    command_names = _(u"note").split(',')
    state_class = ItemState

    @classmethod
    def process(cls, state):
        for stamp in cls.stamp_types:
            if not has_stamp(state.item, stamp):
                stamp(state.item).add()

        cls.process_stamp(state)

    @classmethod
    def process_stamp(cls, state):
        """Add event or reminder details if they can be found."""
        state.parse_for_event()
        state.parse_for_reminder()

class TaskCommand(NoteCommand):
    stamp_types = [TaskStamp]
    # L10N: A comma separated list of names for commands to create a task
    command_names = _(u"task,starred").split(',')

class EventCommand(NoteCommand):
    stamp_types = [EventStamp]
    # L10N: A comma separated list of names for commands to create an event
    command_names = _(u"event").split(',')

    @classmethod
    def process_stamp(cls, state):
        """Add event stamp with details parsed from text."""
        state.set_event_attributes()

class MailCommand(NoteCommand):
    stamp_types = [MailStamp]
    # L10N: A comma separated list of names for commands to create a message
    command_names = _(u"message,msg").split(',')

    @classmethod
    def process_stamp(cls, state):
        """Add event stamp with details parsed from text."""
        # add EventStamp or a reminder if times are found
        state.parse_for_event()
        state.parse_for_reminder()

        email = MailStamp(state.item)

        # Search for contacts and seperate them
        text = state.text
        if find_contact_re.match(text) and text.find(':') > -1:
            contacts, sep, text = text.partition(':')
            email.toAddress = [getAddress(state.view, match) for match in
                               many_contacts_re.finditer(contacts)]
            state.text = text.strip()

class RequestCommand(MailCommand):
    stamp_types = [TaskStamp, MailStamp]
    # L10N: A comma separated list of names for commands to add both the Mail
    # stamp and the Task stamp, which should be rendered in the UI as meaning
    # the task is assigned to the To: address
    command_names = _(u"assign,request").split(',')

class InviteCommand(MailCommand):
    stamp_types = [EventStamp, MailStamp]
    # L10N: A comma separated list of names for commands to add the Event stamp
    # and the Mail stamp to an item
    command_names = _(u"invite").split(',')

    @classmethod
    def process_stamp(cls, state):
        EventCommand.process_stamp(state)
        MailCommand.process_stamp(state)

stamp_to_command = {None       : NoteCommand,
                    TaskStamp  : TaskCommand,
                    EventStamp : EventCommand,
                    MailStamp  : MailCommand}
