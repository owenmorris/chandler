
VERSION=0.3-14

include Makefile.inc

SYSTEMS=persistence/db \
        python \
        swig \
        epydoc \
        PyLucene \
        persistence/xerces-c \
        persistence/pathan \
        persistence/dbxml \
        persistence/libxml2 \
        persistence/libxslt \
        openssl \
        egenix-mx \
        jabber-py \
        SOAPpy \
        zope \
        twisted \
        pychecker \
        yapps

SOURCES=persistence/db/db-4.2.52.tar.gz \
        python/Python-2.3.3.tgz \
        python/bzip2-1.0.2.tar.gz \
        python/zlib-1.2.1.tar.gz \
        swig/SWIG-20Feb04.tar.gz \
        epydoc/epydoc-2.1.tar.gz \
        PyLucene/PyLucene-0.5.1.tar.gz \
        persistence/xerces-c/xerces-c-src2_4_0.tar.gz \
        persistence/pathan/libpathan-1.2-2-src.tar.gz \
        persistence/dbxml/dbxml-1.2.1.tar.gz \
        persistence/libxml2/libxml2-2.6.10.tar.gz \
        persistence/libxslt/libxslt-1.1.2.tar.gz \
        openssl/openssl-0.9.7d.tar.gz \
        egenix-mx/egenix-mx-base-2.1.0.tar.gz \
        jabber-py/jabberpy0.4-0.tar.gz \
        SOAPpy/SOAPpy-0.10.2.tar.gz \
        zope/ZopeInterface-3.0.0b1.tgz \
        twisted/Twisted-r11303.tar.gz \
        pychecker/pychecker-0.8.13.tar.gz \
        yapps/yapps2.1.1.zip

.PHONY: sources expand binaries $(SYSTEMS)

sources:
	tar -cvf sources-$(VERSION).tar $(SOURCES)

sources-$(VERSION).tar:
	curl -O http://builds.o11n.org/external/sources-$(VERSION).tar

sources-$(VERSION)-expanded: sources-$(VERSION).tar
	tar xvf sources-$(VERSION).tar
	for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system expand; \
	done
	touch sources-$(VERSION)-expanded

expand: env sources-$(VERSION)-expanded

binaries:
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

$(SNAP)-$(VERSION).tar.gz: binaries

$(SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG)

all: env sources-$(VERSION)-expanded $(SYSTEMS)

clean: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system -k DEBUG=$(DEBUG) clean; \
	done

realclean:
	rm -rf release debug sources-$(VERSION)-expanded
	@for system in $(SYSTEMS); \
	do \
	    echo making _realclean in $$system; \
	    $(MAKE) -C $$system -k _realclean; \
	done

upload:	$(SNAP)-$(VERSION).tar.gz
	scp $(SNAP)-$(VERSION).tar.gz $(UPLOAD)

install: $(SNAP)-$(VERSION).tar.gz
	tar -C ../chandler -xvzf $(SNAP)-$(VERSION).tar.gz

checkout:
	cd ..; \
	rm -f cvsco.log;\
	cvs co chandler-all 2>&1 | tee -a cvsco.log; \
	echo 'Do |grep "^C " ../cvsco.log| to check for potential conflicts'
