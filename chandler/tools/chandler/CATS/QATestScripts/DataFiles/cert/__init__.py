import application.schema as schema

def installParcel(parcel, oldVersion=None):
    app = schema.ns('osaf.app', parcel)
    
    from osaf.framework.certstore.data import loadCerts
    loadCerts(parcel,__name__, "certs.pem") 
