#   Copyright (c) 2003-2007 Open Source Applications Foundation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

include Makefile.inc

BUILD_ONLY_SYSTEMS=config \
                   swig

SYSTEMS=db \
        $(ICU_BUILD) \
        $(OPENSSL_BUILD) \
        $(OPENJDK_BUILD) \
        $(READLINE_BUILD) \
        $(PYTHON_BUILD) \
        $(SETUPTOOLS_BUILD) \
        epydoc \
        PyLucene \
        PyICU \
        $(ZOPE_BUILD) \
        twisted \
        vobject \
        dateutil \
        m2crypto \
        zanshin \
	$(GETTEXT_BUILD) \
        eggtranslations \
        pylint \
        parsedatetime \
        $(CONFIGOBJ_BUILD) \
        $(DOCUTILS_BUILD) \
        wx

SYS_TESTS=dateutil \
          m2crypto \
          $(OPENSSL_BUILD) \
          parsedatetime \
          vobject \
          zanshin \
          PyLucene \
          PyICU


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

$(addprefix test-, $(SYS_TESTS)):
	$(MAKE) -C $(subst test-,,$@) test

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

test: $(addprefix test-, $(SYS_TESTS))

tests: test

clean: $(addprefix clean-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS))

realclean: $(addprefix realclean-, $(BUILD_ONLY_SYSTEMS) $(SYSTEMS))
	rm -rf release debug

all: env sources $(BUILD_ONLY_SYSTEMS) $(SYSTEMS)

world: all binaries install
	$(MAKE) -C ../internal DEBUG=$(DEBUG) world
	$(MAKE) -C $(CHANDLERBIN) DEBUG=$(DEBUG) install

cleanworld: clean
	$(MAKE) -C ../internal DEBUG=$(DEBUG) clean
	$(MAKE) -C ../chandler DEBUG=$(DEBUG) clean

realcleanworld: realclean
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
