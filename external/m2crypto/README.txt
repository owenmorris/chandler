Commands to re-create source tarball:

svn co -r<revision> http://svn.osafoundation.org/m2crypto/trunk M2Crypto-r<revision> 

tar --exclude=.svn -czvf M2Crypto-r<revision>.tar.gz M2Crypto-r<revision>

where <revision> is the svn revision you are interested in, for
example 255.
