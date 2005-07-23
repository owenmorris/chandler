"""Calendar Content Model

Kinds and Attributes related to Calendar functionality. This schema is still a
strawman schema, a starting point.

Issues:
    * We have not yet fully addressed dates, times, timezones, etc.
    * Recurrence is still a placeholder, and might be general enough to live
      with PimSchema.
    * reminderTime is also a trial balloon.
    * The calendar schema depends heavily on people/contacts/users/groups/etc,
      we have yet to adequately model them.
    * Consider using the icalendar terminology, generally
    * Consider using the common icalendar task attributes (i.e.
      percentComplete)
"""
from Calendar import Calendar as __Calendar
from Calendar import CalendarEvent, CalendarEventMixin, Location, RecurrencePattern

