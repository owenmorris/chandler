
include Makefile.inc

SYSTEMS=UUIDext \
        wxPython-2.5 \
        m2crypto \
        launchers \
        queryparser

.PHONY: binaries $(SYSTEMS)

binaries: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system DEBUG=$(DEBUG) snap; \
	done


$(SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG)

all: env $(SYSTEMS)

clean: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system -k DEBUG=$(DEBUG) clean; \
	done

upload:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done

install:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) install; \
	done

build:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) ; \
	done

