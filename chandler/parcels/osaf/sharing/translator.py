from application import schema
from osaf import pim
from osaf.sharing import eim, model
from PyICU import ICUtzinfo
import decimal



class PIMTranslator(eim.Translator):

    URI = "cid:pim-translator@osaf.us"
    version = 1
    description = u"Translator for Chandler PIM items"


    # ItemRecord -------------

    # TODO: last_modified_by
    # TODO: remind_on

    @model.ItemRecord.importer
    def import_item(self, record):

        # This assumes the created_on field has no timezone:
        inUTC = record.created_on.replace(tzinfo=ICUtzinfo.getInstance('UTC'))
        # Convert to user's tz:
        createdOn = inUTC.astimezone(ICUtzinfo.default)

        self.loadItemByUUID(
            record.uuid,
            pim.ContentItem,
            displayName=record.title,
            triageStatus=record.triage_status,
            triageStatusChanged=float(record.triage_status_changed),
            createdOn=createdOn
        ) # incomplete


    @sharing.exporter(pim.ContentItem)
    def export_item(self, item):
        yield model.ItemRecord(
            item.itsUUID,                               # uuid
            item.displayName,                           # title
            item.triageStatus,                          # triage_status
            decimal.Decimal("%.2f" % item.triageStatusChanged), # t_s_changed
            None,                                       # last_modified_by
            item.createdOn.astimezone(ICUtzinfo.getInstance('UTC')), # created
            None                                        # remind_on
        )



    # NoteRecord -------------

    # TODO: icaluid

    @model.NoteRecord.importer
    def import_note(self, r):
        self.loadItemByUUID(
            record.uuid,
            pim.Note,
            body=record.body
        ) # incomplete

    @sharing.exporter(pim.Note)
    def export_note(self, item):
        yield model.NoteRecord(
            item.itsUUID,                               # uuid
            item.body,                                  # body
            None                                        # icaluid
        )



    # TaskRecord -------------

    @model.TaskRecord.importer
    def import_task(self, r):
        self.loadItemByUUID(
            record.uuid,
            pim.TaskStamp
        )

    @sharing.exporter(pim.TaskStamp)
    def export_task(self, item):
        yield model.TaskRecord(
            item.itsUUID                                # uuid
        )



    # EventRecord -------------

    # TODO: EventRecord fields need work, for example: rfc3339 date strings

    @model.EventRecord.importer
    def import_event(self, r):
        self.loadItemByUUID(
            record.uuid,
            pim.EventStamp
        ) # incomplete


    @sharing.exporter(pim.EventStamp)
    def export_event(self, item):
        event = pim.EventStamp(item)
        yield model.EventRecord(
            item.itsUUID,                               # uuid
            str(event.startTime),                       # dstart
            None,                                       # dtend
            None,                                       # location
            None,                                       # rrule
            None,                                       # exrule
            None,                                       # rdate
            None,                                       # exdate
            None,                                       # recurrenceid
            None,                                       # status
            None                                        # trigger
        )

