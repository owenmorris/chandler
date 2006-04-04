
include Makefile.inc

SYSTEMS=db \
        swig \
        icu \
        readline \
        openssl \
        python \
        epydoc \
        PyLucene \
        PyICU \
        zope \
        twisted \
        pychecker \
        vobject \
        dateutil \
        m2crypto \
        zanshin \
        elementtree \
        pylint

.PHONY: systems env binaries sources expand install clean $(SYSTEMS)

$(SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG) all

$(addprefix binaries-, $(SYSTEMS)):
	$(MAKE) -C $(subst binaries-,,$@) binaries

$(addprefix strip-, $(SYSTEMS)):
	$(MAKE) -C $(subst strip-,,$@) strip

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

env::
	mkdir -p $(PREFIX)/bin $(PREFIX)/lib $(PREFIX)/include $(CHANDLERARCHIVES)

systems: $(SYSTEMS)

binaries: $(addprefix binaries-, $(SYSTEMS))

strips: $(addprefix strip-, $(SYSTEMS))

sources: $(addprefix sources-, $(SYSTEMS))

expand: $(addprefix expand-, $(SYSTEMS))

install: $(addprefix install-, $(SYSTEMS))

clean: $(addprefix clean-, $(SYSTEMS))

realclean: $(addprefix realclean-, $(SYSTEMS))
	rm -rf release debug

all: env sources $(SYSTEMS)

world: all binaries install
	$(MAKE) -C ../internal DEBUG=$(DEBUG) world
	$(MAKE) -C $(CHANDLERBIN) DEBUG=$(DEBUG) install
	$(MAKE) -C $(CHANDLERBIN) DEBUG=$(DEBUG) build-plugins
	$(MAKE) -C $(CHANDLERBIN) DEBUG=$(DEBUG) bundled-plugins

cleanworld: $(addprefix clean-, $(SYSTEMS))
	$(MAKE) -C ../internal DEBUG=$(DEBUG) clean
	$(MAKE) -C ../chandler DEBUG=$(DEBUG) clean

realcleanworld: $(addprefix realclean-, $(SYSTEMS))
	$(MAKE) -C ../internal DEBUG=$(DEBUG) realclean
	$(MAKE) -C ../chandler DEBUG=$(DEBUG) realclean

# only called by the full tbox client
uploadstaging:
	@for system in $(SYSTEMS); \
	do \
	   $(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done
	$(MAKE) -C ../internal DEBUG=$(DEBUG) uploadstaging

# convenience
uploads:
	@for system in $(SYSTEMS); \
	do \
	   $(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done

# convenience
drops:
	@for system in $(SYSTEMS); \
	do \
	   echo $$system ; \
	   $(MAKE) -C $$system DEBUG=$(DEBUG) drop; \
	done
