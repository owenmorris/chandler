
VERSION=0.3-0

ifeq ($(DEBUG),1)
SNAP=debug
else
SNAP=release
DEBUG=0
endif

SYSTEMS=persistence/db \
        python \
        epydoc \
        wx \
        persistence/xerces-c \
        persistence/pathan \
        persistence/dbxml \
        persistence/libxml2 \
        persistence/libxslt \
        persistence/PyLucene \
        pyxml \
        egenix-mx \
        jabber-py \
        SOAPpy \
        pychecker

SOURCES=persistence/db/db-4.2.52.tar.gz \
        python/Python-2.3.3.tgz \
        python/bzip2-1.0.2.tar.gz \
        epydoc/epydoc-2.0.tar.gz \
        wx/wxpython.tar.gz \
        persistence/xerces-c/xerces-c-src2_4_0.tar.gz \
        persistence/pathan/libpathan-1.2-2-src.tar.gz \
        persistence/dbxml/dbxml-1.2.1.tar.gz \
        persistence/libxml2/libxml2-2.6.3.tar.gz \
        persistence/libxslt/libxslt-1.1.2.tar.gz \
        persistence/PyLucene/lucene-1.3-final-src.tar.gz \
        pyxml/PyXML-0.8.3.tar.gz \
        egenix-mx/egenix-mx-base-2.1.0.tar.gz \
        jabber-py/jabberpy0.4-0.tar.gz \
        SOAPpy/SOAPpy-0.10.2.tar.gz \
        pychecker/pychecker-0.8.13.tar.gz

.PHONY: default env sources expand binaries clean all $(SYSTEMS)

default: all

env:
ifeq ($(BUILD_ROOT),)
	echo BUILD_ROOT is not set && false
endif
ifeq ($(GCJ_HOME),)
	echo GCJ_HOME is not set && false
endif

sources:
	tar -cvf sources-$(VERSION).tar $(SOURCES)

sources-$(VERSION).tar:
	curl http://builds.osafoundation.org/external/sources-$(VERSION).tar > sources-$(VERSION).tar

expand: sources-$(VERSION).tar
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
