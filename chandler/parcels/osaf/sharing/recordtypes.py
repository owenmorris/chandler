from osaf import sharing
from application import schema

# These may eventually live elsewhere, but checking them in here so we can
# collaborate on them

class ItemRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)
    title = sharing.field(sharing.TextType(size=256))
    triage_status = sharing.field(sharing.TextType(size=256))
    triage_status_changed = sharing.field(sharing.DecimalType(digits=11,
        decimal_places=2))
    last_modified_by = sharing.field(sharing.TextType(size=256)) # storing an email address
    created_on = sharing.field(sharing.DateType)

class NoteRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)
    body = sharing.field(sharing.LobType())
    icaluid = sharing.field(sharing.TextType(size=256))

class TaskRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)

class EventRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)
    dtstart = sharing.field(sharing.DateType)
    dtend = sharing.field(sharing.DateType)
    location = sharing.field(sharing.TextType(size=256))
    rrule = sharing.field(sharing.TextType(size=1024))
    exrule = sharing.field(sharing.TextType(size=1024))
    rdate = sharing.field(sharing.DateType)
    exdate = sharing.field(sharing.DateType)
    recurrenceid = sharing.field(sharing.DateType)
    status = sharing.field(sharing.TextType(size=256))
    # anyTime -- may need for Apple iCal?
    # allDay


class MailMessageRecord(sharing.Record):
    uuid = sharing.key(schema.UUID)
    subject = sharing.field(sharing.TextType(size=256))
    to = sharing.field(sharing.TextType(size=256))
    cc = sharing.field(sharing.TextType(size=256))
    bcc = sharing.field(sharing.TextType(size=256))
    # other headers?

