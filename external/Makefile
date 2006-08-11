
include Makefile.inc

BUILD_ONLY_SYSTEMS=swig

SYSTEMS=db \
        icu \
        openssl \
        $(READLINE_OSX) \
        python \
        setuptools \
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
        pylint \
        parsedatetime \
        wx

.PHONY: systems env binaries sources expand install clean \
        $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)

$(BUILD_ONLY_SYSTEMS) $(SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG) all

$(addprefix binaries-, $(SYSTEMS)):
	$(MAKE) -C $(subst binaries-,,$@) binaries

$(addprefix strip-, $(SYSTEMS)):
	$(MAKE) -C $(subst strip-,,$@) strip

$(addprefix sources-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)):
	$(MAKE) -C $(subst sources-,,$@) sources

$(addprefix expand-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)):
	$(MAKE) -C $(subst expand-,,$@) expand

$(addprefix install-, $(SYSTEMS)):
	$(MAKE) -C $(subst install-,,$@) install

$(addprefix clean-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)):
	$(MAKE) -C $(subst clean-,,$@) clean

$(addprefix realclean-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)):
	$(MAKE) -C $(subst realclean-,,$@) _realclean

# to start build from a given system instead of from the beginning
# for example: make from-PyLucene
# builds PyLucene and all systems from PyLucene onwards

$(addprefix from-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)):
	$(MAKE) $(shell echo $(BUILD_ONLY_SYSTEMS) $(SYSTEMS) | sed "s=.*\($(subst from-,,$@).*\)=\1=")

# to do a build up to a given system instead of until the end
# for example: make to-PyICU
# builds all systems up to and including PyICU

$(addprefix to-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)):
	$(MAKE) $(shell echo $(BUILD_ONLY_SYSTEMS) $(SYSTEMS) | sed "s=\(.*$(subst to-,,$@)\).*=\1=")

env::
	mkdir -p $(PREFIX)/bin $(PREFIX)/lib $(PREFIX)/include $(CHANDLERARCHIVES)

systems: $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)

binaries: $(addprefix binaries-, $(SYSTEMS))

strips: $(addprefix strip-, $(SYSTEMS))

sources: $(addprefix sources-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS))

expand: $(addprefix expand-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS))

install: $(addprefix install-, $(SYSTEMS))

clean: $(addprefix clean-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS))

realclean: $(addprefix realclean-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS))
	rm -rf release debug

all: env sources $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)

world: all binaries install
	$(MAKE) -C ../internal DEBUG=$(DEBUG) world
	$(MAKE) -C $(CHANDLERBIN) DEBUG=$(DEBUG) install

cleanworld: $(addprefix clean-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS))
	$(MAKE) -C ../internal DEBUG=$(DEBUG) clean
	$(MAKE) -C ../chandler DEBUG=$(DEBUG) clean

realcleanworld: $(addprefix realclean-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS))
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
