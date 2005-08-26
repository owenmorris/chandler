
/*
 * Copyright (c) 2003-2005 Open Source Applications Foundation
 * License at http://osafoundation.org/Chandler_0.1_license_terms.htm
 */

int generate_uuid(unsigned char *uuid);
int make_uuid(unsigned char *uuid, char *text, int len);
void format16_uuid(unsigned char *uuid, char *buf);
void format64_uuid(unsigned char *uuid, char *buf);
long hash_bytes(unsigned char *uuid, int len);
long combine_longs(unsigned long h0, unsigned long h1);

