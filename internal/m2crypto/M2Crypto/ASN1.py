"""Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

RCS_id='$Id$'

import BIO
import m2

class ASN1_UTCTIME:
    def __init__(self, asn1):
        self.asn1 = asn1

    def __str__(self):
        buf = BIO.MemoryBuffer()
        m2.asn1_utctime_print(buf.bio_ptr(), self.asn1)
        return buf.read_all()


