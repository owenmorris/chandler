
include Makefile.inc

SYSTEMS=persistence/db \
        swig \
        icu \
        readline \
        python \
        epydoc \
        PyLucene \
        PyICU \
        persistence/libxml2 \
        openssl \
        jabber-py \
        SOAPpy \
        zope \
        twisted \
        pychecker \
        yapps \
        vobject \
        dateutil \
        m2crypto \
        zanshin

.PHONY: systems env binaries sources expand install clean $(SYSTEMS)

$(SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG) all

$(addprefix binaries-, $(SYSTEMS)):
	$(MAKE) -C $(subst binaries-,,$@) binaries

$(addprefix sources-, $(SYSTEMS)):
	$(MAKE) -C $(subst sources-,,$@) sources

$(addprefix expand-, $(SYSTEMS)):
	$(MAKE) -C $(subst expand-,,$@) expand

$(addprefix install-, $(SYSTEMS)):
	$(MAKE) -C $(subst install-,,$@) install

$(addprefix clean-, $(SYSTEMS)):
	$(MAKE) -C $(subst clean-,,$@) clean

$(addprefix realclean-, $(SYSTEMS)):
	$(MAKE) -C $(subst realclean-,,$@) _realclean

# to start build from a given system instead of from the beginning
# for example: make from-PyLucene
# builds PyLucene and all systems from PyLucene onwards

$(addprefix from-, $(SYSTEMS)):
	$(MAKE) $(shell echo $(SYSTEMS) | sed "s=.*\($(subst from-,,$@).*\)=\1=")

# to do a build up to a given system instead of until the end
# for example: make to-PyICU
# builds all systems up to and including PyICU

$(addprefix to-, $(SYSTEMS)):
	$(MAKE) $(shell echo $(SYSTEMS) | sed "s=\(.*$(subst to-,,$@)\).*=\1=")

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
	find release -name "*.so" | xargs strip $(STRIP_OPTIONS)
endif
endif

env::
	mkdir -p $(PREFIX)/bin $(PREFIX)/lib $(PREFIX)/include

systems: $(SYSTEMS)

binaries: $(addprefix binaries-, $(SYSTEMS))

sources: $(addprefix sources-, $(SYSTEMS))

expand: $(addprefix expand-, $(SYSTEMS))

install: $(addprefix install-, $(SYSTEMS))

clean: $(addprefix clean-, $(SYSTEMS))

realclean: $(addprefix realclean-, $(SYSTEMS))
	rm -rf release debug

all: env sources $(SYSTEMS)

world: all binaries install
	$(MAKE) -C ../internal DEBUG=$(DEBUG) world

cleanworld: $(addprefix clean-, $(SYSTEMS))
	$(MAKE) -C ../internal DEBUG=$(DEBUG) clean
	$(MAKE) -C ../chandler DEBUG=$(DEBUG) clean

realcleanworld: $(addprefix realclean-, $(SYSTEMS))
	$(MAKE) -C ../internal DEBUG=$(DEBUG) realclean
	$(MAKE) -C ../chandler DEBUG=$(DEBUG) realclean

# this is the only one still using a for loop
# it should only be called by the full tbox client
uploadstaging:
	@for system in $(SYSTEMS); \
	do \
		$(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done
