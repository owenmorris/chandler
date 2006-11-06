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


""" Class used for Items of Kind Task
"""

__all__ = ['TaskStamp', 'Task']

import items, notes
from contacts import Contact
from stamping import Stamp

from datetime import datetime, timedelta
from application import schema

from PyICU import ICUtzinfo


class TaskStamp(Stamp):
    """
    TaskStamp is the bag of Task-specific attributes.
    """

    schema.kindInfo(annotates = notes.Note)

    __use_collection__ = True
    
    requestor = schema.One(
        Contact,
        description =
            "Issues:\n"
            '   Type could be Contact, EmailAddress or String\n'
            '   Think about using the icalendar terminology\n',
        inverse = Contact.requestedTasks,
    )
    requestee = schema.Sequence(
        Contact,
        description =
            "Issues:\n"
            '   Type could be Contact, EmailAddress or String\n'
            '   Think about using the icalendar terminology\n',
        inverse = Contact.taskRequests,
    )

    dueDate = schema.One(schema.DateTimeTZ)

    # Redirections
    summary = schema.One(redirectTo="displayName")

    schema.addClouds(
        copying = schema.Cloud(
            requestor, requestee
        )
    )

    def InitOutgoingAttributes (self):
        self.itsItem.InitOutgoingAttributes()

    def add(self):
        """
          Set up the attributes specific to this mixin.
        Called when stamping adds these attributes.
        """
        
        super(TaskStamp, self).add()
        
        # default due date is 1 hour hence
        # (?) Grant
        if not hasattr(self, 'dueDate'):
            self.dueDate = datetime.now(ICUtzinfo.default) + timedelta(hours=1)

def Task(*args, **keywds):
    note = notes.Note(*args, **keywds)
    result = TaskStamp(note)

    result.add()
    
    return result # Set some keywords? Could filter out all the attribut names
                  # that don't apply to the Note kind
