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

/*
 * Implementation of UUID spec at
 * http://www.ics.uci.edu/pub/ietf/webdav/uuid-guid/draft-leach-uuids-guids-01.txt
 */


#include "fns.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>

extern int debug;

static unsigned char hTable[] = {
     33,  14, 188, 130,  50,  93, 118, 216,
    108, 146,  27, 236, 111, 191, 131,  52,
    140, 160, 189, 198, 243, 103, 142, 206,
    110, 133, 151,  71,  24, 186,  76,   9,
    173, 141,  94, 155, 226,  38, 229,  31,
     29,  13,  51, 137, 222,   8, 253, 102,
     61,  56, 127,  55,  35,  37, 159, 231,
     36, 192, 149,  96,  85, 185,  78, 177,
    138,  63, 209, 156, 154, 238,  11, 175,
    168, 161,   7, 190, 239,  82, 221, 134,
    143,  46,  72,  92, 197, 215,  10,  70,
    204,  86, 207, 145,  69,  18, 153, 244,
    176,  67, 212, 254, 249, 178, 182, 199,
    114, 214,  19, 162,   4, 120,  62,  21,
    196, 104, 124, 220, 230, 201, 163,   3,
    135, 100, 210, 235, 227, 166, 180, 211,
    164, 203, 219,  49,  54,  64, 101, 167,
    117, 228, 200, 171,   2, 128,  47, 205,
     66, 218, 125,  90,  68,  99, 165,  97,
    179,  77, 255,  59, 172, 109, 224,   6,
     81, 252, 174, 116, 181, 250, 184,  88,
    217, 148,  84, 187, 105, 107, 240,  74,
     58,  17, 139,  30, 152,  40,  39,  43,
     22,  42, 169,  41,  12,  28, 251, 132,
    195, 112, 202,  15, 234, 157,  60, 144,
    119, 213, 237, 245,   5, 126,  98, 223,
    194,  83, 247,  91, 115, 241,  65, 170,
     23, 150, 242, 225, 233,  45, 158,  26,
     80,  53, 193,  16,  87,   0,  48, 121,
    248,  32,  95,  20,  75,  44, 106,  79,
    246,  73, 113, 136,  25, 208, 183,  34,
     89, 129, 232,   1, 147, 123,  57, 122,
};

long hash_bytes(unsigned char *uuid, int len)
{
    unsigned long hash = 0xdeadbeef;
    int i = -1;

    while (++i < len) {
        unsigned char source = uuid[i];
        unsigned char byte = hTable[(unsigned char) ((hash & 0xff) ^ source)];
        unsigned long newHash = byte;

        hash >>= 8;
        byte = hTable[(unsigned char) ((hash & 0xff) ^ (source + 1))];
        newHash = (newHash << 8) | byte;

        hash >>= 8;
        byte = hTable[(unsigned char) ((hash & 0xff) ^ (source + 2))];
        newHash = (newHash << 8) | byte;

        hash >>= 8;
        byte = hTable[(unsigned char) ((hash & 0xff) ^ (source + 3))];
        newHash = (newHash << 8) | byte;

        hash = newHash;
    }

    return hash;
}

static unsigned char chew_long(unsigned long n)
{
    unsigned char hash = hTable[0 ^ (n & 0xff)];

    n >>= 8;
    hash = hTable[hash ^ (n & 0xff)];

    n >>= 8;
    hash = hTable[hash ^ (n & 0xff)];

    n >>= 8;
    hash = hTable[hash ^ (n & 0xff)];

    return hash;
}

static long hash_long(unsigned long n)
{
    unsigned long hash;

    hash = chew_long(n);
    hash |= chew_long(++n) << 8;
    hash |= chew_long(++n) << 16;
    hash |= chew_long(++n) << 24;

    return hash ? hash : hash_long(++n);
}

long combine_longs(unsigned long h0, unsigned long h1)
{
    unsigned long hash;

    while (!(hash = hash_long(h0 + h1)))
        h0 = hash_long(h0);

    return hash;
}


#if defined(__MACH__)

#include <unistd.h>
#include <sys/socket.h>
#include <sys/sysctl.h>
#include <sys/time.h>
#include <net/if.h>
#include <net/if_dl.h>
#include <net/if_types.h>
#include <net/route.h>

#define __int64 long long

/* Ask the kernel for an ethernet card's globally unique node id. If an error
 * occurs, or no ethernet card is found, return -1. Return 0 when successful.
 * Source code for this function is inspired from Mac OS X 10.2.6 ifconfig's.
 */

static int get_ethernet_node_id(unsigned char *node_id, int node_len)
{
    int mib[] = { CTL_NET, PF_ROUTE, 0, AF_LINK, NET_RT_IFLIST, 0 };
    size_t info_len;

    if (sysctl(mib, 6, NULL, &info_len, NULL, 0) < 0)
        return -1;
    else
    {
        void *buf = alloca(info_len);

	if (sysctl(mib, 6, buf, &info_len, NULL, 0) < 0)
            return -1;
        else
        {
            char *lim = buf + info_len;
            char *next = buf;

            while (next < lim) {
                struct if_msghdr *ifm = (struct if_msghdr *) next;

		if (ifm->ifm_type == RTM_IFINFO)
                {
                    struct sockaddr_dl *sdl = (struct sockaddr_dl *)(ifm + 1);
                    char *name = alloca(sdl->sdl_nlen + 1);

                    memcpy(name, sdl->sdl_data, sdl->sdl_nlen);
                    name[sdl->sdl_nlen] = '\0';

                    next += ifm->ifm_msglen;

                    while (next < lim) {
			struct if_msghdr *nextifm = (struct if_msghdr *) next;

			if (nextifm->ifm_type != RTM_NEWADDR)
                            break;

			next += nextifm->ifm_msglen;
                    }

                    if (sdl->sdl_type == IFT_ETHER &&
                        sdl->sdl_alen == node_len)
                    {
                        unsigned char *id = (unsigned char *) LLADDR(sdl);
                        int i = -1;

                        /* ensure non-zero */
                        while (++i < node_len) if (id[i]) break;

                        if (i < node_len)
                        {
                            if (node_id)
                                memcpy(node_id, id, node_len);

                            return 0;
                        }
                    }
		}
                else
                    return -1;
            }
        }
    }

    return -1;
}


/* see man 4 random for rationale behind using /dev/random */

static int get_random_fd(void)
{
    static int fd = -2;

    if (fd == -2)
        fd = open("/dev/random", O_RDONLY);

    return fd;
}

#elif defined(linux)

#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <net/if.h>
#include <netinet/in.h>

#define __int64 long long

/* Ask the kernel for an ethernet card's globally unique node id. If an error
 * occurs, or no ethernet card is found, return -1. Return 0 when successful.
 * Source code for this function is inspired from e2fsprogs 1.33 uuidgen's.
 */

static int get_ethernet_node_id(unsigned char *node_id, size_t node_len)
{
    int sd = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
	
    if (sd >= 0)
    {
        struct ifreq ifr, *ifrp;
        struct ifconf ifc;
        char buf[1024];

        memset(buf, 0, sizeof(buf));
        ifc.ifc_len = sizeof(buf);
        ifc.ifc_buf = buf;

        if (ioctl(sd, SIOCGIFCONF, (char *) &ifc) >= 0)
        {
            int n = ifc.ifc_len;
            int ifn;

            for (ifn = 0; ifn < n; ifn += sizeof(struct ifreq)) {
                struct ifreq *ifrp = (struct ifreq *)
                    ((char *) ifc.ifc_buf + ifn);

                strncpy(ifr.ifr_name, ifrp->ifr_name, IFNAMSIZ);

                if (ioctl(sd, SIOCGIFHWADDR, &ifr) < 0)
                    continue;
                else
                {
                    unsigned char *id = (unsigned char *)
                        &ifr.ifr_hwaddr.sa_data;
                    int i = -1;

                    /* ensure non-zero */
                    while (++i < node_len) if (id[i]) break;

                    if (i < node_len)
                    {
                        if (node_id)
                            memcpy(node_id, id, node_len);
                        close(sd);

                        return 0;
                    }
                }
            }
        }

        close(sd);
    }

    return -1;
}

static int get_random_fd(void)
{
    static int fd = -2;

    if (fd == -2)
    {
        fd = open("/dev/urandom", O_RDONLY);
        if (fd == -1)
            fd = open("/dev/random", O_RDONLY | O_NONBLOCK);
    }

    return fd;
}

#elif defined(winnt) || defined(_MSC_VER)

#ifdef _MSC_VER

#pragma comment(lib, "iphlpapi")
#pragma comment(lib, "advapi32")
#pragma comment(lib, "ws2_32")

#include <windows.h>
#include <iphlpapi.h>
#include <wincrypt.h>
#include <malloc.h>

#else

#include <w32api/windows.h>
#include <w32api/iphlpapi.h>
#include <w32api/wincrypt.h>
#include <sys/time.h>

#endif

static int get_ethernet_node_id(unsigned char *node_id, size_t node_len)
{
    IP_ADAPTER_INFO *info = NULL;
    ULONG size = 0L;

    GetAdaptersInfo(info, &size);
    info = (IP_ADAPTER_INFO *) alloca(size);

    if (GetAdaptersInfo(info, &size) == ERROR_SUCCESS)
    {
        int count = size / sizeof(IP_ADAPTER_INFO);
        int i = -1;

        while (++i < count) {
            IP_ADAPTER_INFO *adapter = info + i;

            if (adapter->AddressLength == node_len)
            {
                memcpy(node_id, adapter->Address, node_len);
                return 0;
            }
        }
    }

    return -1;
}

static int get_random_fd(void)
{
    static HCRYPTPROV prov = 0;

    /* Why PROV_DSS ? Hopefully it's commonly installed, PROV_RSA_SIG isn't */
    if (!prov && !CryptAcquireContext(&prov, NULL, NULL,
                                      PROV_DSS, CRYPT_VERIFYCONTEXT))
        prov = -1;

    return prov;
}

#else

#error system is not linux, os x or winnt

#endif


static void get_random_bytes(unsigned char *buf, size_t buf_len)
{
    int fd = get_random_fd();

#if defined(winnt) || defined(_MSC_VER)
    if (fd != -1 && CryptGenRandom((HCRYPTPROV) fd, buf_len, buf))
        buf_len = 0;
#else
    if (fd >= 0)
    {
        int cursor = 0;

        while (buf_len > 0) {
            int read_len = read(fd, buf + cursor, buf_len);

            if (read_len < 0)
                break;

            buf_len -= read_len;
            cursor += read_len;
        }
    }
#endif

    if (buf_len > 0)
    {
        while (buf_len-- > 0)
            buf[buf_len] = (rand() >> 7) & 0xFF;
    }
}

int generate_uuid(unsigned char *uuid)
{
    static unsigned char node_id[6];
    static unsigned short clock_seq;
    static int was_initialized = 0;
    static __int64 last_time = 0L;

    __int64 current_time;
    unsigned short time_mid, time_hi;
    unsigned int time_low;

    if (!was_initialized)
    {
        if (!debug || get_ethernet_node_id(node_id, sizeof(node_id)) < 0)
        {
            get_random_bytes(node_id, sizeof(node_id));

            /* Set multicast bit, to prevent conflicts
             * with IEEE 802 addresses obtained from
             * network cards
             */

            node_id[0] |= 0x80;
        }

        get_random_bytes((unsigned char *) &clock_seq, sizeof(clock_seq));
        was_initialized = 1;
    }

#ifdef _MSC_VER
    {
        /* microseconds * 10 from January 1, 1601 to October 15, 1582. */
        static const __int64 gregorian_cutover =
            (__int64) -5748192 * 1000000000;
        ULARGE_INTEGER system_time;

        GetSystemTimeAsFileTime((FILETIME *) &system_time);
        current_time = system_time.QuadPart - gregorian_cutover;
    }
#else
    {
        /* microseconds * 10 from January 1, 1970 to October 15, 1582. */
        static const __int64 gregorian_cutover =
            (__int64) -122192928 * 1000000000;
        struct timeval tv;

        gettimeofday(&tv, NULL);
        current_time = (__int64) tv.tv_sec * 10000000 + tv.tv_usec * 10;
        current_time -= gregorian_cutover;
    }
#endif

    if (current_time == last_time)
        clock_seq += 1;
    last_time = current_time;

    time_low = (unsigned int) (current_time & 0xffffffff);
    time_mid = (unsigned short) ((current_time >> 32) & 0xffff);
    time_hi = (unsigned short) ((current_time >> 48) & 0xffff);

    uuid[0] = (unsigned char) ((time_low >> 24) & 0xff);
    uuid[1] = (unsigned char) ((time_low >> 16) & 0xff);
    uuid[2] = (unsigned char) ((time_low >> 8) & 0xff);
    uuid[3] = (unsigned char) (time_low & 0xff);

    uuid[4] = (unsigned char) ((time_mid >> 8) & 0xff);
    uuid[5] = (unsigned char) (time_mid & 0xff);

    uuid[6] = (unsigned char) ((time_hi >> 8) & 0xff);
    uuid[7] = (unsigned char) (time_hi & 0xff);

    uuid[8] = (clock_seq >> 8) & 0xff;
    uuid[9] = (clock_seq & 0xff);

    uuid[10] = node_id[0];
    uuid[11] = node_id[1];
    uuid[12] = node_id[2];
    uuid[13] = node_id[3];
    uuid[14] = node_id[4];
    uuid[15] = node_id[5];

    uuid[6] = 0x10 | (uuid[6] & 0x0f);
    uuid[8] |= 0x80;

    return 0;
}

static int c16Value(char c)
{
    if (c >= '0' && c <= '9')
        return c - '0';

    if (c >= 'a' && c <= 'f')
        return c - 'a' + 10;

    if (c >= 'A' && c <= 'F')
        return c - 'A' + 10;

    return -1;
}

static int read16Bytes(char *text, int from,
                       unsigned char *uuid, int to, int length)
{
    int i = 0;

    while (i++ < length) {
        int c1 = c16Value(text[from++]);
        int c2 = c16Value(text[from++]);

        if (c1 < 0 || c2 < 0)
            return -1;

        uuid[to++] = (unsigned char) ((c1 << 4) + c2);
    }

    return 0;
}

static int c64Value(char c)
{
    if (c >= '0' && c <= '9')
        return c - '0';

    if (c >= 'a' && c <= 'z')
        return c - 'a' + 10;

    if (c >= 'A' && c <= 'Z')
        return c - 'A' + 10 + 26;

    if (c == '_')
        return 62;

    if (c == '$')
        return 63;

    return -1;
}

static int read64Bytes(char *text, int from, unsigned char *uuid, int to)
{
    unsigned __int64 l = 0L;
    int i = 0;

    while (i++ < 11) {
        int c64 = c64Value(text[from++]);

        if (c64 < 0)
            return -1;

        l = (l << 6) + c64;
    }

    for (i = 8; i > 0; l >>= 8)
        uuid[to + --i] = (unsigned char) (l & 0xff);

    return 0;
}

int make_uuid(unsigned char *uuid, char *text, int len)
{
    switch (len) {
      case 16:
        memcpy(uuid, text, len);
        return 0;

      case 22:
        if (read64Bytes(text, 0, uuid, 0) ||
            read64Bytes(text, 11, uuid, 8))
            return -1;
        return 0;

      case 36:
        if (read16Bytes(text, 0, uuid, 0, 4) ||
            read16Bytes(text, 9, uuid, 4, 2) ||
            read16Bytes(text, 14, uuid, 6, 2) ||
            read16Bytes(text, 19, uuid, 8, 2) ||
            read16Bytes(text, 24, uuid, 10, 6))
            return -1;
        return 0;

      default:
        return -1;
    }
}

static void get16Bytes(unsigned char *src, char *buf,
                       int dst, int from, int to)
{
    static const char *digits = "0123456789abcdef";
    int i = from - 1;

    while (++i < to) {
        buf[dst++] = digits[(src[i] >> 4) & 0x0f];
        buf[dst++] = digits[src[i] & 0x0f];
    }
}

static void get64Bytes(unsigned char *src, char *buf,
                       int dst, unsigned __int64 n)
{
    static const char *digits = 
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$";
    int i, charPos;

    for (i = 0, charPos = dst + 10; i < 11; i++, charPos--, n >>= 6)
        buf[charPos] = digits[n & 0x3f];
}

void format16_uuid(unsigned char *uuid, char *buf)
{
    get16Bytes(uuid, buf, 0, 0, 4);
    buf[8] = '-';
    get16Bytes(uuid, buf, 9, 4, 6);
    buf[13] = '-';
    get16Bytes(uuid, buf, 14, 6, 8);
    buf[18] = '-';
    get16Bytes(uuid, buf, 19, 8, 10);
    buf[23] = '-';
    get16Bytes(uuid, buf, 24, 10, 16);
}

void format64_uuid(unsigned char *uuid, char *buf)
{
    unsigned __int64 l;

    l = ((unsigned __int64) ntohl(*(unsigned long *) uuid)) << 32 |
        (unsigned __int64) (ntohl(*(unsigned long *) (uuid + 4)) &
                            0xffffffff);
    get64Bytes(uuid, buf, 0, l);

    l = ((unsigned __int64) ntohl(*(unsigned long *) (uuid + 8))) << 32 |
        (unsigned __int64) (ntohl(*(unsigned long *) (uuid + 12)) &
                            0xffffffff);
    get64Bytes(uuid, buf, 11, l);
}
