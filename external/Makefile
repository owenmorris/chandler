
VERSION=0.3-5

include Makefile.inc

SYSTEMS=persistence/db \
        python \
        swig \
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
        swig/swig-1.3.21.tar.gz \
        swig/swigwin-1.3.21.zip \
        epydoc/epydoc-2.1.tar.gz \
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
            cp $$system/$(SNAP).tar.gz _tmp.tar.gz; \
            gunzip -f _tmp.tar.gz; \
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

upload:	$(SNAP)-$(VERSION).tar.gz
	scp $(SNAP)-$(VERSION).tar.gz $(UPLOAD)

install: $(SNAP)-$(VERSION).tar.gz
	tar -C .. -xvzf $(SNAP)-$(VERSION).tar.gz
