from application import schema
from osaf import pim
from osaf.sharing import eim, model
from PyICU import ICUtzinfo
import time
from datetime import datetime
from decimal import Decimal


class PIMTranslator(eim.Translator):

    URI = "cid:pim-translator@osaf.us"
    version = 1
    description = u"Translator for Chandler PIM items"


    # ItemRecord -------------

    # TODO: lastModifiedBy

    @model.ItemRecord.importer
    def import_item(self, record):

        utc = ICUtzinfo.getInstance('UTC')

        if record.createdOn is not eim.NoChange:
            # createdOn is a Decimal we need to change to datetime
            naive = datetime.utcfromtimestamp(float(record.createdOn))
            inUTC = naive.replace(tzinfo=utc)
            # Convert to user's tz:
            createdOn = inUTC.astimezone(ICUtzinfo.default)

        if record.triageStatus is not eim.NoChange:
            # @@@MOR -- is this the right way to get an enum?  (it works)
            triageStatus = getattr(pim.TriageEnum, record.triageStatus)

        self.loadItemByUUID(
            record.uuid,
            pim.ContentItem,
            displayName=record.title,
            triageStatus=triageStatus,
            triageStatusChanged=float(record.triageStatusChanged),
            createdOn=createdOn
        ) # incomplete


    @eim.exporter(pim.ContentItem)
    def export_item(self, item):
        utc = ICUtzinfo.getInstance('UTC')
        yield model.ItemRecord(
            item.itsUUID,                               # uuid
            item.displayName,                           # title
            str(item.triageStatus),                     # triageStatus
            Decimal("%.2f" % item.triageStatusChanged), # t_s_changed
            None,                                       # lastModifiedBy
            Decimal(int(time.mktime(item.createdOn.timetuple()))) # createdOn
        )



    # NoteRecord -------------

    # TODO: icaluid (Grant is moving it to Note)

    @model.NoteRecord.importer
    def import_note(self, record):
        self.loadItemByUUID(
            record.uuid,
            pim.Note,
            body=record.body
        ) # incomplete

    @eim.exporter(pim.Note)
    def export_note(self, item):
        yield model.NoteRecord(
            item.itsUUID,                               # uuid
            item.body,                                  # body
            None                                        # icaluid
        )



    # TaskRecord -------------

    @model.TaskRecord.importer
    def import_task(self, record):
        self.loadItemByUUID(
            record.uuid,
            pim.TaskStamp
        )

    @eim.exporter(pim.TaskStamp)
    def export_task(self, task):
        yield model.TaskRecord(
            task.itsItem.itsUUID                   # uuid
        )



    # EventRecord -------------

    # TODO: EventRecord fields need work, for example: rfc3339 date strings

    @model.EventRecord.importer
    def import_event(self, record):
        self.loadItemByUUID(
            record.uuid,
            pim.EventStamp
        ) # incomplete


    @eim.exporter(pim.EventStamp)
    def export_event(self, event):
        yield model.EventRecord(
            event.itsItem.itsUUID,                      # uuid
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









def test_suite():
    import doctest
    return doctest.DocFileSuite(
        'Translator.txt',
        optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE,
    )

