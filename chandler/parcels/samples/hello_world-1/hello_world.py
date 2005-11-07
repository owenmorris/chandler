from osaf.pim.notes import Note
from application import schema

class MP3(Note):
    audio = schema.One (schema.Lob)


