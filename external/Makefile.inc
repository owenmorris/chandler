#-*- Mode: Makefile; -*-
#
# external
#

#   Copyright (c) 2003-2006 Open Source Applications Foundation
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

OS=$(shell uname)
OS_VER=$(shell uname -r)
OS_MAJOR_VER=$(firstword $(subst ., ,$(OS_VER)))
ARCH=$(shell arch)

ifeq ($(findstring CYGWIN,$(OS)),CYGWIN)
OS=Cygwin
endif

ifeq ($(findstring WINNT,$(OS)),WINNT)
OS=Cygwin
endif

ifeq ($(DEBUG),1)
SNAP=debug
Snap=Debug
DIST_OPT=--debug
PYTHON=python_d
else
SNAP=release
Snap=Release
DEBUG=0
DIST_OPT=
PYTHON=python
endif

BRANCH_REV_PREFIX=
PREFIX=$(BUILD_ROOT)/$(SNAP)

# We download some pretty big files, which can clog your network. You can now
# control the download options (well, any options) for curl. For example:
#   CHANDLER_CURL_OPTIONS="--limit-rate 200K"
#
# You can also replace curl with something else, for example wget:
#   CURL=wget
ifeq ($(CURL),)
CURL=curl -f -O $(CHANDLER_CURL_OPTIONS)
endif

PYTHON_VER=2.5

ifeq ($(OS),Cygwin)
PYTHON:=$(PREFIX)/bin/$(PYTHON).exe
SITE=bin/Lib/site-packages
PLATFORM=windows
SWIG=$(PREFIX)/bin/swig/swig.exe
UPLOAD=builder@builds.osafoundation.org:/www/docs/external/$(PLATFORM)
READLINE_WIN=readline
else
ifeq ($(OS),Darwin)
FRAMEWORK=Library/Frameworks/Python.framework/Versions/$(PYTHON_VER)
ifeq ($(MACOSX_DEPLOYMENT_TARGET),)
ifeq ($(ARCH),ppc)
MACOSX_DEPLOYMENT_TARGET=10.3
else
MACOSX_DEPLOYMENT_TARGET=10.4
endif
endif
READLINE_OSX=readline
PYTHON:=$(PREFIX)/$(FRAMEWORK)/bin/$(PYTHON)
SITE=$(FRAMEWORK)/lib/python$(PYTHON_VER)/site-packages
PLATFORM=macosx
SWIG=$(PREFIX)/bin/swig
ifeq ($(ARCH),i386)
UPLOAD=builder@builds.osafoundation.org:/www/docs/external/maciosx
else
UPLOAD=builder@builds.osafoundation.org:/www/docs/external/macosx
endif
else
PYTHON:=$(PREFIX)/bin/$(PYTHON)
SITE=lib/python$(PYTHON_VER)/site-packages
PLATFORM=linux
SWIG=$(PREFIX)/bin/swig
UPLOAD=builder@builds.osafoundation.org:/www/docs/external/$(PLATFORM)
endif
endif

# GCJ_VER should be set to 3, if using gcj 3.4.x
# GCJ_VER should be set to 4, if using gcj 4.x.y

ifndef GCJ_HOME
ifeq ($(OS),Cygwin)
GCJ_HOME=$(BUILD_ROOT)/mingw-5.0-3.4.6
GCJ_VER=3
endif
ifeq ($(OS),Darwin)
ifeq ($(ARCH),ppc)
GCJ_HOME=$(BUILD_ROOT)/gcc-3.4.4
GCJ_VER=3
else
GCJ_HOME=$(BUILD_ROOT)/gcc-4.0.2
GCJ_VER=4
endif
endif
ifeq ($(OS),Linux)
GCJ_HOME=$(BUILD_ROOT)/gcc-3.4.5
GCJ_VER=3
endif
else
ifndef GCJ_VER
GCJ_VER=3
endif
endif

ifeq ($(CHANDLERHOME),)
CHANDLERHOME=$(BUILD_ROOT)/../chandler
endif

ifeq ($(CHANDLERPLUGINS),)
CHANDLERPLUGINS=$(BUILD_ROOT)/../chandler/projects
endif

ifeq ($(CHANDLERBIN),)
CHANDLERBIN=$(CHANDLERHOME)
endif

ifeq ($(CHANDLERARCHIVES),)
CHANDLERARCHIVES=$(BUILD_ROOT)/../downloads
endif

ifeq ($(OS),Cygwin)
ifdef VS71COMNTOOLS

MSVC_ROOT:=$(shell cygpath -u $$VS71COMNTOOLS\\..\\..)
MSVC_DIR:=$(MSVC_ROOT)/Vc7

export PATH:=$(MSVC_ROOT)/Common7/IDE:$(MSVC_DIR)/BIN:$(MSVC_ROOT)/Common7/Tools:$(MSVC_ROOT)/Common7/Tools/bin/prerelease:$(MSVC_ROOT)/Common7/Tools/bin:$(PATH)

export INCLUDE:=$(shell cygpath -awp $(MSVC_DIR)/atlmfc/include:$(MSVC_DIR)/PlatformSDK/include/prerelease:$(MSVC_DIR)/PlatformSDK/include:$(MSVC_DIR)/include)

export LIB:=$(shell cygpath -awp $(MSVC_DIR)/atlmfc/lib:$(MSVC_DIR)/LIB:$(MSVC_DIR)/PlatformSDK/lib/prerelease:$(MSVC_DIR)/PlatformSDK/lib)

endif
endif

.PHONY: default all build compile install clean env realclean _realclean

default: all

env::
	@echo Operating system is $(OS)
ifndef BUILD_ROOT
	@echo BUILD_ROOT is not set && false
else
	@echo BUILD_ROOT is $(BUILD_ROOT)
	@if [ ! -f $(BUILD_ROOT)/build_root ]; then \
            echo BUILD_ROOT is incorrect; \
            echo it needs to be set to the absolute path including 'external'; \
            false; \
        fi
endif
	@echo CHANDLERBIN is $(CHANDLERBIN)
	@echo GCJ_HOME is $(GCJ_HOME)
ifeq ($(OS),Darwin)
	@if [ "$(ARCH)" = "ppc" ]; then \
            echo ARCH is $(ARCH); \
         elif [ "$(ARCH)" = "i386" ]; then \
            echo ARCH is $(ARCH); \
         else \
            echo unsupported ARCH is $(ARCH); \
            false; \
        fi
endif
ifeq ($(OS),Cygwin)
	@if [ ! -f $(GCJ_HOME)/bin/gcj.exe ]; then \
            echo GCJ_HOME is incorrect; \
            echo it needs to be set to the absolute gcc with gcj installation path; \
            echo or unset it and run 'make compilers' to install gcc with gcj into $(BUILD_ROOT)/mingw-5.0-3.4.6; \
            false; \
        else \
            $(GCJ_HOME)/bin/gcj.exe --v; \
        fi
ifndef VS71COMNTOOLS
	@echo VS71COMNTOOLS is not set, you do not have MSVC 7.1 installed
	@false
else
	@if [ ! -d "$(shell cygpath -u $$VS71COMNTOOLS)" ]; then \
            echo VS71COMNTOOLS is not set properly; \
            false; \
        else \
            echo INCLUDE for MSVC is `echo $$INCLUDE`; \
            echo LIB for MSVC is `echo $$LIB`; \
	fi
endif
else
	@if [ ! -f $(GCJ_HOME)/bin/gcj ]; then \
            echo GCJ_HOME is incorrect; \
            echo it needs to be set to the absolute gcc with gcj installation path; \
            echo or unset it and run 'make compilers' to install gcc with gcj into $(BUILD_ROOT)/$(GCC_VERSION); \
            false; \
        else \
            $(GCJ_HOME)/bin/gcj --v; \
        fi
endif

all: build


COMPILERS=http://builds.osafoundation.org/compilers

ifeq ($(OS),Cygwin)

MINGW_VERSION=5.0-3.4.6

$(GCJ_HOME): $(notdir $(GCJ_HOME).tar.bz2)
	cd $(BUILD_ROOT); tar -xvjf $<

$(notdir $(GCJ_HOME).tar.bz2):
	cd $(BUILD_ROOT); \
	$(CURL) -O $(COMPILERS)/windows/$@

endif

ifeq ($(OS),Darwin)

ifeq ($(ARCH),ppc)
$(GCJ_HOME): $(notdir $(GCJ_HOME).tar.gz)
	cd $(BUILD_ROOT); \
	tar xvzf $<

$(notdir $(GCJ_HOME).tar.gz):
	cd $(BUILD_ROOT);
	$(CURL) $(COMPILERS)/osx/$(ARCH)/$@
else
$(GCJ_HOME): $(notdir $(GCJ_HOME).tar.bz2)
	cd $(BUILD_ROOT); tar xvjf $<

$(notdir $(GCJ_HOME).tar.bz2):
	cd $(BUILD_ROOT);
	$(CURL) $(COMPILERS)/osx/$(ARCH)/$@
endif

endif

ifeq ($(OS),Linux)

$(GCJ_HOME): $(notdir $(GCJ_HOME).tar.gz)
	cd $(BUILD_ROOT); tar xvzf $<

$(notdir $(GCJ_HOME).tar.gz):
	cd $(BUILD_ROOT); \
	$(CURL) $(COMPILERS)/linux/$@

endif

ifeq ($(OS),Cygwin)
strip:
else
ifeq ($(DEBUG),1)
strip:
else
ifeq ($(OS),Darwin)
STRIP_OPTIONS=-S -x
STRIP_OP=\( -name '*.dylib' -o -name '*.so' \)
else
STRIP_OPTIONS=
STRIP_OP=-name '*.so'
endif
strip:
	for item in `find $(SRC)/$(BUILD) $(STRIP_OP)` ; do \
        chmod +w $$item; \
        strip $(STRIP_OPTIONS) $$item; \
    done
endif
endif

compilers: $(GCJ_HOME)/

print-%:
	@echo $* = $($*)

upload: $(TARBALL)
	scp $(TARBALL) $(UPLOAD)

drop: $(TARBALL)
	tar -C $(CHANDLERBIN) -xvzf $(TARBALL)

_realclean::
	@if [ "$(SRC)" = "" ]; then \
	    echo SRC is not set; false; \
	elif [ "$(SRC)" = "/" ]; then \
	    echo SRC is set to $(SRC); false; \
	else \
	    rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded; \
	    rm -rf $(SRC)*;  \
	fi
