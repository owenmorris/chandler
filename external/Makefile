
ifeq ($(DEBUG),1)

SNAP=debug

else

SNAP=release

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
        epydoc/epydoc-2.0.tar.gz \
        wx/wxpython.tar.gz \
        persistence/xerces-c/xerces-c-src2_4_0.tar.gz \
        persistence/pathan/libpathan-1.2-2-src.tar.gz \
        persistence/dbxml/dbxml-1.2.1.tar.gz \
        persistence/libxml2/libxml2-2.6.3.tar.gz \
        persistence/libxslt/libxslt-1.1.2.tar.gz \
        persistence/PyLucene/lucene-1.3-final-src.tar.gz \
        pyxml/PyXML-0.8.3.tar.gz \
        egenix-mx/egenix-mx-base-2.0.4.tar.gz \
        jabber-py/jabberpy0.4-0.tar.gz \
        SOAPpy/SOAPpy-0.10.2.tar.gz \
        pychecker/pychecker-0.8.13.tar.gz

default: all

env:
	@if [ "$(BUILD_ROOT)" = "" ]; then \
	    echo BUILD_ROOT is not set; \
	    false; \
        fi; \
	if [ "$(GCJ_HOME)" = "" ]; then \
	    echo GCJ_HOME is not set; \
	    false; \
        fi

sources:
	tar -cvf sources.tar $(SOURCES)

sources.tar:
	curl http://builds.osafoundation.org/external/sources.tar > sources.tar

expand: sources.tar
	tar xvf sources.tar; \
	for system in $(SYSTEMS); \
	do \
	    (cd $$system; $(MAKE) expand); \
	done

binaries: env
	@rm -f $(SNAP).tar $(SNAP).tar.gz; \
	for system in $(SYSTEMS); \
	do \
	    (cd $$system; $(MAKE) DEBUG=$(DEBUG) snap); \
	done; \
	for system in $(SYSTEMS); \
	do \
	    echo appending $$system; \
	    gunzip -c $$system/$(SNAP).tar.gz > _tmp.tar; \
            tar -Af $(SNAP).tar _tmp.tar; \
	    rm _tmp.tar; \
	done; \
	echo compressing $(SNAP).tar; \
        gzip $(SNAP).tar;

all: env
	@for system in $(SYSTEMS); \
	do \
	    (cd $$system; $(MAKE) DEBUG=$(DEBUG) all); \
	done

clean: env
	@for system in $(SYSTEMS); \
	do \
	    (cd $$system; $(MAKE) -k DEBUG=$(DEBUG) clean); \
	done
