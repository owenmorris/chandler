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


"""
Calendar Domain Model

Kinds and Attributes related to Calendar functionality. This schema is still a
strawman schema, a starting point.

Issues:
 - We have not yet fully addressed dates, times, timezones, etc.
 - Recurrence is still a placeholder, and might be general enough to live
   with PimSchema.
 - The calendar schema depends heavily on people/contacts/users/groups/etc,
   we have yet to adequately model them.
 - Consider using the icalendar terminology, generally
 - Consider using the common icalendar task attributes (i.e.
   percentComplete)
"""
from Calendar import EventStamp as __EventStamp
from Calendar import EventStamp, Location, RecurrencePattern, EventComparator

from TimeZone import TimeZoneInfo, formatTime, shortTZ
