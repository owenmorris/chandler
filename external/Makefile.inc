#-*- Mode: Makefile; -*-
#
# external
#

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

OS=$(shell uname)
OS_VER=$(shell uname -r)
OS_MAJOR_VER=$(firstword $(subst ., ,$(OS_VER)))

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
CURL=curl -f -L -O $(CHANDLER_CURL_OPTIONS)
endif

PYTHON_VER=2.5

ifeq ($(OS),Cygwin)
    PYTHON_BINDIR:=bin
    PYTHON:=$(PREFIX)/$(PYTHON_BINDIR)/$(PYTHON).exe
    SITE=bin/Lib/site-packages
    PLATFORM=windows
    SWIG=$(PREFIX)/bin/swig/swig.exe
    UPLOAD=builder@builds.osafoundation.org:/www/docs/external/$(PLATFORM)
    READLINE_BUILD=readline
    OPENSSL_BUILD=openssl
    OPENJDK_BUILD=openjdk
    PYTHON_BUILD=python
    ICU_BUILD=icu
    PYICU_BUILD=pyicu
endif

ifeq ($(OS),Darwin)
    PLATFORM=macosx
    SWIG=$(PREFIX)/bin/swig
    ARCH=$(shell arch)
    ifeq ($(ARCH),i386)
        UPLOAD=builder@builds.osafoundation.org:/www/docs/external/maciosx
    else
        UPLOAD=builder@builds.osafoundation.org:/www/docs/external/macosx
    endif
    ifeq ($(OS_MAJOR_VER),9)
        MACOSX_DEPLOYMENT_TARGET=10.5
        FRAMEWORK=/System/Library/Frameworks/Python.framework/Versions/$(PYTHON_VER)
        SITE=site-packages
        PYTHON_BINDIR:=$(FRAMEWORK)/bin
        PYTHON:=PYTHONPATH=$(BUILD_ROOT)/$(SNAP)/$(SITE) $(PYTHON_BINDIR)/python
        UPLOAD:=$(UPLOAD)/10.5
    else
        ifeq ($(MACOSX_DEPLOYMENT_TARGET),)
            ifeq ($(ARCH),ppc)
                MACOSX_DEPLOYMENT_TARGET=10.3
            else
                MACOSX_DEPLOYMENT_TARGET=10.4
            endif
        endif
        FRAMEWORK=Library/Frameworks/Python.framework/Versions/$(PYTHON_VER)
        SITE=$(FRAMEWORK)/lib/python$(PYTHON_VER)/site-packages
        PYTHON_BINDIR:=$(FRAMEWORK)/bin
        PYTHON:=$(PREFIX)/$(PYTHON_BINDIR)/$(PYTHON)
    endif
    PYTHON:=MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON)
    OPENSSL_BUILD=openssl
    OPENJDK_BUILD=
    ifeq ($(OS_MAJOR_VER),9)
        READLINE_BUILD=
        PYTHON_BUILD=
    else
        READLINE_BUILD=readline
        PYTHON_BUILD=python
    endif
    ICU_BUILD=icu
    PYICU_BUILD=PyICU
endif

ifeq ($(OS),Linux)
    PLATFORM=linux
    ARCH=$(shell uname -m)
    DISTRIB_CODENAME=$(subst DISTRIB_CODENAME=,,$(shell cat /etc/lsb-release | grep DISTRIB_CODENAME))
    SWIG=$(PREFIX)/bin/swig
    UPLOAD=builder@builds.osafoundation.org:/www/docs/external/$(PLATFORM)
    OPENJDK_BUILD=openjdk
    ifneq ($(findstring $(DISTRIB_CODENAME),feisty gutsy hardy intrepid jaunty),)
        SITE=site-packages
        PYTHON_BINDIR:=/usr/bin
        PYTHON:=PYTHONPATH=$(BUILD_ROOT)/$(SNAP)/$(SITE) $(PYTHON_BINDIR)/python
        UPLOAD:=$(UPLOAD)/$(DISTRIB_CODENAME)
        ifeq ($(DISTRIB_CODENAME),feisty)
            OPENSSL_BUILD=openssl
        else
            OPENSSL_BUILD=
            OPENJDK_BUILD=
        endif
        PYTHON_BUILD=
        ICU_BUILD=
        ifneq ($(findstring $(DISTRIB_CODENAME),feisty gutsy),)
            PYICU_BUILD=PyICU
        else
            PYICU_BUILD=
        endif
    else
        PYTHON_BINDIR:=bin
        PYTHON:=$(PREFIX)/$(PYTHON_BINDIR)/$(PYTHON)
        SITE=lib/python$(PYTHON_VER)/site-packages
        OPENSSL_BUILD=openssl
        PYTHON_BUILD=python
        ICU_BUILD=icu
        PYICU_BUILD=PyICU
    endif
    READLINE_BUILD=
    ifeq ($(ARCH),x86_64)
        UPLOAD:=$(UPLOAD)/$(ARCH)
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
	@echo UPLOAD is $(UPLOAD)
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
endif

all: build

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
	elif [ "$(SRC)" = "none" ]; then \
	    true; \
	else \
	    rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded; \
	    rm -rf $(SRC)*;  \
	fi
