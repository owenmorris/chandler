/* Copyright (c) 2000 Ng Pheng Siong. All rights reserved.  */
/* $Id$ */

%{
#include <openssl/asn1.h>
%}

%apply Pointer NONNULL { ASN1_INTEGER * };
%apply Pointer NONNULL { ASN1_UTCTIME * };
%apply Pointer NONNULL { BIO * };

%name(asn1_integer_get) extern long ASN1_INTEGER_get(ASN1_INTEGER *);
%name(asn1_utctime_print) extern int ASN1_UTCTIME_print(BIO *, ASN1_UTCTIME *);

%inline %{
/* nothing */
%}
