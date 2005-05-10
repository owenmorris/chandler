#-*- Mode: Makefile; -*-
OS=$(shell uname)
OS_VERSION=$(shell uname -r) 

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

PREFIX=$(BUILD_ROOT)/$(SNAP)

# We download some pretty big files, which can clog your network. You can now
# control the download options (well, any options) for curl. For example:
#   CHANDLER_CURL_OPTIONS="--limit-rate 200K"
#
# You can also replace curl with something else, for example wget:
#   CURL=wget
ifeq ($(CURL),)
CURL=curl -O $(CHANDLER_CURL_OPTIONS)
endif

PYTHON_VER=2.4

ifeq ($(OS),Cygwin)
PYTHON:=$(PREFIX)/bin/$(PYTHON).exe
SITE=bin/Lib/site-packages
PLATFORM=windows
SWIG=$(PREFIX)/bin/swig/swig.exe
MD5=md5sum.exe
MD5CHECK=$(MD5) -c
else
ifeq ($(OS),Darwin)
FRAMEWORK=Library/Frameworks/Python.framework/Versions/$(PYTHON_VER)
MACOSX_DEPLOYMENT_TARGET=10.3
PYTHON:=$(PREFIX)/$(FRAMEWORK)/bin/$(PYTHON)
SITE=$(FRAMEWORK)/lib/python$(PYTHON_VER)/site-packages
PLATFORM=macosx
SWIG=$(PREFIX)/bin/swig
MD5=md5
MD5CHECK=$(MD5) --check
else
PYTHON:=$(PREFIX)/bin/$(PYTHON)
SITE=lib/python$(PYTHON_VER)/site-packages
PLATFORM=linux
SWIG=$(PREFIX)/bin/swig
MD5=md5sum
MD5CHECK=$(MD5) -c
endif
endif

# GCJ_VER should be set to 3, if using gcj 3.4.x
# GCJ_VER should be set to 4, if using gcj 4.x.y

ifndef GCJ_HOME
ifeq ($(OS),Cygwin)
GCJ_HOME=$(compiler)
GCJ_VER=3
endif
ifeq ($(OS),Darwin)
GCJ_HOME=$(compiler)
GCJ_VER=3
endif
ifeq ($(OS),Linux)
GCJ_HOME=$(compiler)
GCJ_VER=3
endif
else
GCJ_VER=3
endif

ifeq ($(CHANDLERHOME),)
CHANDLERHOME=$(BUILD_ROOT)/../chandler
endif

ifeq ($(CHANDLERBIN),)
CHANDLERBIN=$(CHANDLERHOME)
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

UPLOAD=builder@builds.osafoundation.org:/www/docs/external/$(PLATFORM)

.PHONY: default all build compile install clean env realclean

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
	echo CHANDLERBIN is $(CHANDLERBIN)
	@echo GCJ_HOME is $(GCJ_HOME)
ifeq ($(OS),Cygwin)
	@if [ ! -f $(GCJ_HOME)/bin/gcj.exe ]; then \
            echo GCJ_HOME is incorrect; \
            echo it needs to be set to the absolute gcc with gcj installation path; \
            echo or unset it and run 'make compilers' to install gcc with gcj into $(BUILD_ROOT)/mingw-3.1-3.4.2; \
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


COMPILERS=http://downloads.osafoundation.org/compilers

ifeq ($(OS),Cygwin)

MINGW_VERSION=3.1-3.4.2

compiler=$(BUILD_ROOT)/mingw-$(MINGW_VERSION)

$(compiler): $(BUILD_ROOT)/mingw-$(MINGW_VERSION).tar.gz
	cd $(BUILD_ROOT); \
	tar -xvzf mingw-$(MINGW_VERSION).tar.gz

$(BUILD_ROOT)/mingw-$(MINGW_VERSION).tar.gz:
	cd $(BUILD_ROOT); \
	$(CURL) -O $(COMPILERS)/windows/mingw-$(MINGW_VERSION).tar.gz
	$(CURL) -O $(COMPILERS)/windows/mingw-$(MINGW_VERSION).tar.gz.md5

#	$(MD5CHECK) mingw-$(MINGW_VERSION).tar.gz.md5

endif

ifeq ($(OS),Darwin)

ifeq ($(strip $(OS_VERSION)),8.0.0)
GCC_VERSION=4.1-20050501
GCJ_VER=4
else
GCC_VERSION=3.4.3
GCJ_VER=3
endif

compiler=$(BUILD_ROOT)/gcc-$(GCC_VERSION)

$(compiler): $(BUILD_ROOT)/gcc-$(GCC_VERSION).tar.gz
	cd $(BUILD_ROOT); \
	tar xvzf gcc-$(GCC_VERSION).tar.gz

$(BUILD_ROOT)/gcc-$(GCC_VERSION).tar.gz:
	cd $(BUILD_ROOT);
	$(CURL) $(COMPILERS)/osx/gcc-$(GCC_VERSION).tar.gz
	$(CURL) $(COMPILERS)/osx/gcc-$(GCC_VERSION).tar.gz.md5

#	$(MD5CHECK) gcc-$(GCC_VERSION).tar.gz.md5

endif

ifeq ($(OS),Linux)

GCC_VERSION=3.4.3

compiler=$(BUILD_ROOT)/gcc-$(GCC_VERSION)/install

$(compiler): $(BUILD_ROOT)/gcc-$(GCC_VERSION).tar.gz
	cd $(BUILD_ROOT); \
	tar xvzf gcc-$(GCC_VERSION).tar.gz

$(BUILD_ROOT)/gcc-$(GCC_VERSION).tar.gz:
	cd $(BUILD_ROOT); \
	$(CURL) $(COMPILERS)/linux/gcc-$(GCC_VERSION).tar.gz
	$(CURL) $(COMPILERS)/linux/gcc-$(GCC_VERSION).tar.gz.md5

#	$(MD5CHECK) gcc-$(GCC_VERSION).tar.gz.md5

endif

compilers: $(compiler)

_realclean::
	@if [ "$(SRC)" = "" ]; then \
	    echo SRC is not set; false; \
	elif [ "$(SRC)" = "/" ]; then \
	    echo SRC is set to $(SRC); false; \
	else \
	    rm -rf $(SRC)* $(SRC)/../*-expanded; \
	    rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC); \
	fi
