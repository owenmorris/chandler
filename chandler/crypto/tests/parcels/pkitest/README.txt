To test, you will need to build OpenSSL, M2Crypto and PyEGADS. Then:

cp ../../../../../m2crypto/demo/ssl/*3.py .
cp ../../../../../m2crypto/demo/ssl/*.pem ../../../../

Now you can launch Chandler, enter 9999 for server port and start server 
(waits only 5 seconds for client to connect).

Then in osaf/chandler/m2crypto/demo/ssl directory run client3.py via HardHat
to connect.

Problems:
  * SSL handshake terminates because server does not see client certificate
