from application import schema
import repository.schema.Types as Types

class String(schema.Item):
    
    schema.kindInfo(displayName="Container for string attribute tests")
    
    uString = schema.One(schema.UString)
                
    bString = schema.One(schema.BString)
                
    localizableString = schema.One(schema.LocalizableString)

    text = schema.One(schema.Text)


