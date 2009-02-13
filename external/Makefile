#   Copyright (c) 2003-2009 Open Source Applications Foundation
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

#
# These are eggs we install if not present, once we have
# built a working python 2.5
#
BUILD_ONLY_PY_SYSTEMS = \
    setuptools \
    zope.interface

INSTALL_DIR=$(BUILD_ROOT)/$(SNAP)/$(SITE)
ifeq ($(OS),Cygwin)
    INSTALL_DIR := $(shell cygpath -aw $(INSTALL_DIR))
endif

ifeq ($(PYTHON_BUILD),)
EASY_INSTALL_ARGS = -m easy_install
else
EASY_INSTALL = $(CHANDLERARCHIVES)/ez_setup.py
EASY_INSTALL_ARGS = $(EASY_INSTALL)
$(EASY_INSTALL):
	cd $(CHANDLERARCHIVES) && $(CURL) http://peak.telecommunity.com/dist/ez_setup.py
endif


setuptools: $(EASY_INSTALL)
	$(PYTHON) -c 'from pkg_resources import require; require("setuptools>=0.6c9")' || \
	$(PYTHON) $(EASY_INSTALL_ARGS) -x --install '$(INSTALL_DIR)' setuptools'>=0.6c9'

zope.interface:
	$(PYTHON) -c 'from pkg_resources import require; require("zope.interface>=3.3.0b2")' || \
	$(PYTHON) $(EASY_INSTALL_ARGS) -x --install '$(INSTALL_DIR)' http://builds.osafoundation.org/external/zope.interface-3.3.0b2-r71371.tar.bz2

BINARY_SYSTEMS = \
        db \
        $(ICU_BUILD) \
        $(OPENSSL_BUILD) \
        $(OPENJDK_BUILD) \
        $(READLINE_BUILD) \
        $(PYTHON_BUILD) \

PY_SYSTEMS = \
        PyLucene \
        $(PYICU_BUILD) \
        $(ZOPE_BUILD) \
        twisted \
        m2crypto \
        wx

ALL_SYSTEMS = $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(BUILD_ONLY_PY_SYSTEMS) \
              $(PY_SYSTEMS)

SYS_TESTS=dateutil \
          m2crypto \
          $(OPENSSL_BUILD) \
          parsedatetime \
          vobject \
          zanshin \
          PyLucene \
          PyICU

.PHONY: systems env binaries sources expand install clean $(ALL_SYSTEMS)
        

$(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS):
	$(MAKE) -C $@ DEBUG=$(DEBUG) all

$(addprefix binaries-, $(BINARY_SYSTEMS) $(PY_SYSTEMS)):
	$(MAKE) -C $(subst binaries-,,$@) binaries

$(addprefix strip-, $(BINARY_SYSTEMS) $(PY_SYSTEMS)):
	$(MAKE) -C $(subst strip-,,$@) strip

$(addprefix sources-, $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS)):
	$(MAKE) -C $(subst sources-,,$@) sources

$(addprefix expand-, $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS)):
	$(MAKE) -C $(subst expand-,,$@) expand

$(addprefix install-, $(BINARY_SYSTEMS) $(PY_SYSTEMS)):
	$(MAKE) -C $(subst install-,,$@) install

$(addprefix test-, $(SYS_TESTS)):
	$(MAKE) -C $(subst test-,,$@) test

$(addprefix clean-, $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS)):
	$(MAKE) -C $(subst clean-,,$@) clean

$(addprefix realclean-, $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS)):
	$(MAKE) -C $(subst realclean-,,$@) _realclean

# to start build from a given system instead of from the beginning
# for example: make from-PyLucene
# builds PyLucene and all systems from PyLucene onwards

$(addprefix from-, $(ALL_SYSTEMS)):
	$(MAKE) $(shell echo $(ALL_SYSTEMS) | sed "s=.*\($(subst from-,,$@).*\)=\1=")

# to do a build up to a given system instead of until the end
# for example: make to-PyICU
# builds all systems up to and including PyICU

$(addprefix to-, $(ALL_SYSTEMS)):
	$(MAKE) $(shell echo $(ALL_SYSTEMS) | sed "s=\(.*$(subst to-,,$@)\).*=\1=")

env::
	mkdir -p $(PREFIX)/bin $(PREFIX)/lib $(PREFIX)/include $(CHANDLERARCHIVES)

systems: $(ALL_SYSTEMS)

binaries: $(addprefix binaries-, $(BINARY_SYSTEMS) $(PY_SYSTEMS))

strips: $(addprefix strip-, $(BINARY_SYSTEMS) $(PY_SYSTEMS))

sources: $(addprefix sources-, $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS))

expand: $(addprefix expand-, $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS))

install: $(addprefix install-, $(BINARY_SYSTEMS) $(PY_SYSTEMS))

test: $(addprefix test-, $(SYS_TESTS))

tests: test

clean: $(addprefix clean-, $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS))

realclean: $(addprefix realclean-, $(BUILD_ONLY_SYSTEMS) $(BINARY_SYSTEMS) $(PY_SYSTEMS))
	rm -rf release debug

all: env sources $(ALL_SYSTEMS)

world: all binaries install
	$(MAKE) -C ../internal DEBUG=$(DEBUG) world
	$(MAKE) -C $(CHANDLERBIN) DEBUG=$(DEBUG) install

world-no-plugins: all binaries install
	$(MAKE) -C ../internal DEBUG=$(DEBUG) world
	$(MAKE) -C $(CHANDLERBIN) DEBUG=$(DEBUG) install-no-plugins

cleanworld: clean
	$(MAKE) -C ../internal DEBUG=$(DEBUG) clean
	$(MAKE) -C ../chandler DEBUG=$(DEBUG) clean

realcleanworld: realclean
	$(MAKE) -C ../internal DEBUG=$(DEBUG) realclean
	$(MAKE) -C ../chandler DEBUG=$(DEBUG) realclean

# only called by the full tbox client
uploadstaging:
	@for system in $(BINARY_SYSTEMS) $(PY_SYSTEMS); \
	do \
	   $(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done
	$(MAKE) -C ../internal DEBUG=$(DEBUG) uploadstaging

# convenience
uploads:
	@for system in $(BINARY_SYSTEMS) $(PY_SYSTEMS); \
	do \
	   $(MAKE) -C $$system DEBUG=$(DEBUG) upload; \
	done

# convenience
drops:
	@for system in $(BINARY_SYSTEMS) $(PY_SYSTEMS); \
	do \
	   echo $$system ; \
	   $(MAKE) -C $$system DEBUG=$(DEBUG) drop; \
	done
