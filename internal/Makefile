#-*- Mode: Makefile; -*-
#
# internal
#

include Makefile.inc

SYSTEMS=chandlerdb \
        launchers

.PHONY: binaries $(SYSTEMS)

strips:
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system DEBUG=$(DEBUG) strip; \
	done

binaries: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system DEBUG=$(DEBUG) snap; \
	done

$(SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG)

all: env $(SYSTEMS)

world: all binaries install

clean: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system -k DEBUG=$(DEBUG) clean; \
	done

realclean: env
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system -k realclean; \
	done

# this should only be called by the full tbox client
uploadstaging:
	@for system in $(SYSTEMS); \
	do \
	    $(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done

# convenience
uploads:
	@for system in $(SYSTEMS); \
	do \
	   $(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done

install:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) install; \
	done

drops:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) drop; \
	done

