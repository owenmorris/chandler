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


""" Class used for Items of Kind Task
"""

__all__ = ['TaskStamp', 'Task']

import items, notes
from contacts import Contact
from stamping import Stamp

from application import schema


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

    # Redirections
    @apply
    def summary():
        def fget(self):
            return self.itsItem.displayName
        def fset(self, value):
            self.itsItem.displayName = value
        return schema.Calculated(schema.Text, (items.ContentItem.displayName,),
                                 fget, fset)

    schema.addClouds(
        copying = schema.Cloud(
            requestor, requestee
        )
    )

    def InitOutgoingAttributes (self):
        self.itsItem.InitOutgoingAttributes()

def Task(*args, **kw):
    for key in kw.keys():
        attr = getattr(TaskStamp, key, None)
        if isinstance(attr, schema.Descriptor):
            kw[attr.name] = kw[key]
            del kw[key]
            
    
    note = notes.Note(*args, **kw)
    result = TaskStamp(note)
    result.add()
    
    return result
