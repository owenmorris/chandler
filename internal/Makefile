
include Makefile.inc

SYSTEMS=PyLucene \
        UUIDext \
        wx

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
