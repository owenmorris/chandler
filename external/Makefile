
include Makefile.inc

SYSTEMS=persistence/db \
        python \
        swig \
        epydoc \
        PyLucene \
        persistence/libxml2 \
        openssl \
        egenix-mx \
        jabber-py \
        SOAPpy \
        zope \
        twisted \
        pychecker \
        yapps

.PHONY: sources expand binaries $(SYSTEMS)

sources: env
	for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system sources; \
	done

expand: env
	for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system expand; \
	done

binaries: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system DEBUG=$(DEBUG) snap; \
	done

$(SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG)

all: env sources $(SYSTEMS)

world: all binaries install
	make -C ../internal DEBUG=$(DEBUG) world

clean: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system -k DEBUG=$(DEBUG) clean; \
	done

realclean:
	rm -rf release debug
	@for system in $(SYSTEMS); \
	do \
	    echo making _realclean in $$system; \
	    $(MAKE) -C $$system -k _realclean; \
	done

upload:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done

uploadworld: upload
	make -C ../internal DEBUG=$(DEBUG) upload

install:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) install; \
	done

checkout:
	cd ..; \
	rm -f cvsco.log;\
	cvs co chandler-all 2>&1 | tee -a cvsco.log; \
	echo 'Do |grep "^C " ../cvsco.log| to check for potential conflicts'
