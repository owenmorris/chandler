"""This is the Hello World parcel.  It doesn't actually do anything."""

def installParcel(parcel, oldVersion=None):

    import logging
    logger = logging.getLogger(__name__)

    if oldVersion is None:
        logger.info("installing %s", parcel)
    else:
        logger.info(
            "upgrading %s from %s to %s", parcel, oldVersion, parcel.version
        )

