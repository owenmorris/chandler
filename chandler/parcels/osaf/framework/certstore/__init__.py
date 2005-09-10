from certificate import Certificate, CertificateStore

def installParcel(parcel, oldVersion=None):
    # load our subparcels
    from application import schema
    schema.synchronize(parcel.itsView, "osaf.framework.certstore.data")
    schema.synchronize(parcel.itsView, "osaf.framework.certstore.blocks")

