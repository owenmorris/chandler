
VERSION=0.3-2

include Makefile.inc

SYSTEMS=persistence/db \
        python \
        epydoc \
        persistence/xerces-c \
        persistence/pathan \
        persistence/dbxml \
        persistence/libxml2 \
        persistence/libxslt \
        pyxml \
        egenix-mx \
        jabber-py \
        SOAPpy \
        pychecker

SOURCES=persistence/db/db-4.2.52.tar.gz \
        python/Python-2.3.3.tgz \
        python/bzip2-1.0.2.tar.gz \
        python/zlib-1.2.1.tar.gz \
        epydoc/epydoc-2.0.tar.gz \
        persistence/xerces-c/xerces-c-src2_4_0.tar.gz \
        persistence/pathan/libpathan-1.2-2-src.tar.gz \
        persistence/dbxml/dbxml-1.2.1.tar.gz \
        persistence/libxml2/libxml2-2.6.3.tar.gz \
        persistence/libxslt/libxslt-1.1.2.tar.gz \
        pyxml/PyXML-0.8.3.tar.gz \
        egenix-mx/egenix-mx-base-2.1.0.tar.gz \
        jabber-py/jabberpy0.4-0.tar.gz \
        SOAPpy/SOAPpy-0.10.2.tar.gz \
        pychecker/pychecker-0.8.13.tar.gz

.PHONY: sources expand binaries $(SYSTEMS)

sources:
	tar -cvf sources-$(VERSION).tar $(SOURCES)

sources-$(VERSION).tar:
	curl -O http://builds.o11n.org/external/sources-$(VERSION).tar

expand: env sources-$(VERSION).tar
	tar xvf sources-$(VERSION).tar
	for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system expand; \
	done

binaries: env
	rm -f $(SNAP)-$(VERSION).tar $(SNAP)-$(VERSION).tar.gz
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system DEBUG=$(DEBUG) snap; \
	done
	@for system in $(SYSTEMS); \
	do \
	    echo appending $$system; \
	    gunzip -c $$system/$(SNAP).tar.gz > _tmp.tar; \
            tar -Af $(SNAP)-$(VERSION).tar _tmp.tar; \
	    rm _tmp.tar; \
	done
	gzip $(SNAP)-$(VERSION).tar


$(SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG)

all: env $(SYSTEMS)

clean: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system -k DEBUG=$(DEBUG) clean; \
	done


HOST=http://downloads.osafoundation.org/compilers

ifeq ($(OS),Cygwin)
compilers: mingw-3.1.zip
mingw-3.1.zip:
	curl -O $(HOST)/windows/mingw-3.1.zip
endif

ifeq ($(OS),Darwin)
compilers: gcc-3.4-20040107.tar.bz2
gcc-3.4-20040107.tar.bz2:
	curl -O $(HOST)/osx/gcc-3.4-20040107.tar.bz2
endif

upload:	$(SNAP)-$(VERSION).tar.gz
	scp $(SNAP)-$(VERSION).tar.gz $(UPLOAD)
