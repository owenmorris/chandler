# Make file for new chandler

VERSION=0.3-2

include ../external/Makefile.inc

DEPS =../external/persistence/db/db-4.2.52.tar.gz \
	  ../external/python/Python-2.3.3.tgz \
	  ../external/python/bzip2-1.0.2.tar.gz \
	  ../external/python/zlib-1.2.1.tar.gz \
	  ../external/epydoc/epydoc-2.0.tar.gz \
	  ../external/persistence/xerces-c/xerces-c-src2_4_0.tar.gz \
	  ../external/persistence/pathan/libpathan-1.2-2-src.tar.gz \
	  ../external/persistence/dbxml/dbxml-1.2.1.tar.gz \
	  ../external/persistence/libxml2/libxml2-2.6.3.tar.gz \
	  ../external/persistence/libxslt/libxslt-1.1.2.tar.gz \
	  ../external/pyxml/PyXML-0.8.3.tar.gz \
	  ../external/egenix-mx/egenix-mx-base-2.1.0.tar.gz \
	  ../external/jabber-py/jabberpy0.4-0.tar.gz \
	  ../external/SOAPpy/SOAPpy-0.10.2.tar.gz \
	  ../external/pychecker/pychecker-0.8.13.tar.gz

.PHONY: $(DEPS)

all: env $(DEPS) ../external/sources-$(VERSION).tar
	cd ../external; \
	make expand; \
	make
	cd ../internal; \
	make

