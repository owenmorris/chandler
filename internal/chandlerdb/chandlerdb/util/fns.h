/*
 *  Copyright (c) 2003-2006 Open Source Applications Foundation
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */


int generate_uuid(unsigned char *uuid);
int make_uuid(unsigned char *uuid, char *text, int len);
void format16_uuid(unsigned char *uuid, char *buf);
void format64_uuid(unsigned char *uuid, char *buf);
long hash_bytes(unsigned char *uuid, int len);
long combine_longs(unsigned long h0, unsigned long h1);

