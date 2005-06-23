from application import schema

class AttributeEditor(schema.Item):
    className = schema.One(schema.String)

del schema  # clean up after ourselves