/* Copyright (c) 2000 Ng Pheng Siong. All rights reserved.  */
/* 
** Open Source Applications Foundation (OSAF) has extended the functionality
** to make it possible to create and verify certificates programmatically.
**
** OSAF Changes copyright (c) 2004 Open Source Applications Foundation.
** Author: Heikki Toivonen
*/
/* $Id$ */

%{
#include <openssl/asn1.h>
%}

%apply Pointer NONNULL { ASN1_INTEGER * };
%apply Pointer NONNULL { ASN1_UTCTIME * };
%apply Pointer NONNULL { BIO * };

%name(asn1_integer_get) extern long ASN1_INTEGER_get(ASN1_INTEGER *);
%name(asn1_integer_set) extern int ASN1_INTEGER_set(ASN1_INTEGER *, long);
%name(asn1_utctime_print) extern int ASN1_UTCTIME_print(BIO *, ASN1_UTCTIME *);

%inline %{
/* nothing */
%}
