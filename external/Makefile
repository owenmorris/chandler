
include Makefile.inc

SYSTEMS=persistence/db \
        swig \
        readline \
        python \
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
        yapps \
	vobject \
	dateutil \
	m2crypto

.PHONY: sources expand binaries $(SYSTEMS)

env::
	mkdir -p $(PREFIX)/bin $(PREFIX)/lib $(PREFIX)/include

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
	$(MAKE) -C $@ DEBUG=$(DEBUG) all

all: env sources $(SYSTEMS)

ifeq ($(OS),Cygwin)
strip:
else
ifeq ($(DEBUG),1)
strip:
else
ifeq ($(OS),Darwin)
STRIP_OPTIONS=-S
else
STRIP_OPTIONS=
endif
strip:
	find release -name "*.so" |xargs strip $(STRIP_OPTIONS)
endif
endif

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

cleanworld: clean
	make -C ../internal DEBUG=$(DEBUG) clean
	make -C ../chandler DEBUG=$(DEBUG) clean

realcleanworld: realclean
	make -C ../internal realclean
	make -C ../chandler realclean

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
