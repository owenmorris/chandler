from M2Crypto import SSL, Rand, threading
import thread
from socket import *

verbose_debug = 1

def verify_callback(ok, store):
    if not ok:
        print "***Verify Not ok"
    return ok

dh1024 = None

def init_dhparams():
    dh1024 = DH.load_params('dh1024.pem')

def tmp_dh_callback(ssl, is_export, keylength):
    if not dh1024:
        init_dhparams()
    return dh1024

def setup_server_ctx():
    ctx = SSL.Context('sslv23')
    #if ctx.load_verify_locations('ca.pem') != 1:
    #    print "***No CA file"
    #if ctx.load_cert_chain('server.pem') != 1:
    #    print '***No server cert'
    #ctx.set_verify(SSL.verify_peer | SSL.verify_fail_if_no_peer_cert,
    #               10)#, verify_callback) # XXX Crash with callback
    #ctx.set_options(SSL.op_all | SSL.op_no_sslv2)
    #ctx.set_tmp_dh_callback(tmp_dh_callback)# XXX This causes crash
    #ctx.set_tmp_dh('dh1024.pem')
    #if ctx.set_cipher_list('ALL:!ADH:!LOW:!EXP:!MD5:@STRENGTH') != 1:
    #    print "***No valid ciphers"
    if verbose_debug:
        ctx.set_info_callback()
    return ctx

def post_connection_check(conn):
    cert = conn.get_peer_cert()
    if cert is None:
        print "***No peer certificate"
    # Not sure if we can do any other checks

def do_server_loop(conn):
    while 1:
        try:
            buf = conn.read()
            if not buf:
                break
            print buf
        except SSL.SSLError, what:
            if str(what) == 'unexpected eof':
                break
            else:
                raise
        except:
            break
            
    if conn.get_shutdown():
        return 1
    return 0

def server_thread(ctx, sock, addr):
    conn = SSL.Connection(ctx, sock)
    conn.setup_addr(addr)
    conn.set_accept_state()
    conn.setup_ssl()
    conn.accept_ssl()
    
    post_connection_check(conn)

    print 'SSL Connection opened'
    if do_server_loop(conn):
        conn.close()
    else:
        conn.clear()
    print 'SSL Connection closed'        
