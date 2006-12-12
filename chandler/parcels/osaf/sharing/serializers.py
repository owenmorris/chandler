from application import schema

class Serializer(schema.Item):

    def serialize(recordSets):
        raise NotImplementedError()

    def deserialize(text):
        raise NotImplementedError()
