#!/usr/bin/env python
"""
client3 from the book 'Network Security with OpenSSL', but modified to
Python/M2Crypto from the original C implementation.

Copyright (c) 2004 Open Source Applications Foundation.
Author: Heikki Toivonen
"""
import sys
from M2Crypto import SSL, Rand

verbose_debug = 1

def verify_callback(ok, store):
    print '***Is this ever called?' # XXX
    if not ok:
        print "***Verify Not ok"
    return ok

def setup_client_ctx():
    ctx = SSL.Context('sslv23')
    if ctx.load_verify_locations('ca.pem') != 1:
        print "***No CA file"
    #if ctx.set_default_verify_paths() != 1:
    #    print "***No default verify paths"
    ctx.load_cert_chain('client.pem')
    ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert,
                   10, verify_callback)
    ctx.set_options(SSL.op_all | SSL.op_no_sslv2)
    if ctx.set_cipher_list('ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH') != 1:
        print "***No valid ciphers"
    if verbose_debug:
        ctx.set_info_callback()
    return ctx

def post_connection_check(conn):
    cert = conn.get_peer_cert()
    if cert is None:
        print "***No peer certificate"
    # Not sure if we can do any other checks

def do_client_loop(conn):
    while 1:
        buf = sys.stdin.readline()
        if not buf: 
            break
        if conn.write(buf) <= 0:
            return 0
    return 1

if __name__=='__main__':
    print 'press enter' # XXX hack to get later readline() working
    sys.stdin.readline()# XXX
    Rand.load_file('../randpool.dat', -1)
    ctx = setup_client_ctx()
    conn = SSL.Connection(ctx)
    if conn.connect(('127.0.0.1', 9999)) < 0:
        print "***Connection error"
    post_connection_check(conn)

    print 'SSL Connection opened'
    if do_client_loop(conn):
        conn.close()
    else:
        conn.clear()
    print 'SSL Connection closed'
