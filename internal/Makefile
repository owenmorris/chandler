
include Makefile.inc

SYSTEMS=chandlerdb \
        wx \
        launchers

.PHONY: binaries $(SYSTEMS)

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

install:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) install; \
	done
