#!/usr/bin/env python

"""Demonstration of M2Crypto.xmlrpclib2.

Copyright (c) 1999-2003 Ng Pheng Siong. All rights reserved."""

RCS_id='$Id$'

from M2Crypto import Rand, SSL
from M2Crypto.m2xmlrpclib import Server, SSL_Transport

def ZServerSSL():
    # Server is Zope-2.6.1 on ZServerSSL/0.12.
    ctx = SSL.Context('sslv3')
    ctx.load_cert_chain('client.pem')
    ctx.load_verify_locations('ca.pem')
    ctx.set_verify(SSL.verify_peer, 10)
    zs = Server('https://127.0.0.1:9443/', SSL_Transport(ctx))
    print zs.manage_listObjects()

if __name__ == '__main__':
    Rand.load_file('../randpool.dat', -1)
    ZServerSSL()
    Rand.save_file('../randpool.dat')

