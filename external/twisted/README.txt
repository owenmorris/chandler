Commands to re-create Twisted source tarball:

svn co -r<revision> svn://svn.twistedmatrix.com/svn/Twisted/trunk Twisted-r<revision>  

tar --exclude=doc --exclude=sandbox --exclude=.svn -czvf Twisted-r<revision>.tar.gz Twisted-r<revision>

where <revision> is the Twisted svn revision you are interested in, for
example 12000.
