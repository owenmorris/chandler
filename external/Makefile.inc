#-*- Mode: Makefile; -*-
OS=$(shell uname)

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

ifeq ($(OS),Cygwin)
PYTHON:=$(PREFIX)/bin/$(PYTHON).exe
SITE=bin/Lib/site-packages
PLATFORM=windows
SWIG=$(PREFIX)/bin/swig.exe
MD5=md5sum.exe
else
ifeq ($(OS),Darwin)
FRAMEWORK=Library/Frameworks/Python.framework/Versions/2.3
PYTHON:=$(PREFIX)/$(FRAMEWORK)/bin/$(PYTHON)
SITE=$(FRAMEWORK)/lib/python2.3/site-packages
PLATFORM=macosx
SWIG=$(PREFIX)/bin/swig
MD5=md5
else
PYTHON:=$(PREFIX)/bin/$(PYTHON)
SITE=lib/python2.3/site-packages
PLATFORM=linux
SWIG=$(PREFIX)/bin/swig
MD5=md5sum
endif
endif

ifndef GCJ_HOME
ifeq ($(OS),Cygwin)
GCJ_HOME=$(compiler)
endif
ifeq ($(OS),Darwin)
GCJ_HOME=$(compiler)
endif
ifeq ($(OS),Linux)
GCJ_HOME=/usr
endif
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

UPLOAD=builder@builds.o11n.org:/www/docs/external/$(PLATFORM)

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
            echo or unset it and run 'make compilers' to install gcc with gcj into $(BUILD_ROOT)/mingw-3.1; \
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
            echo or unset it and run 'make compilers' to install gcc with gcj into $(BUILD_ROOT)/gcc-3.4; \
            false; \
        else \
            $(GCJ_HOME)/bin/gcj --v; \
        fi
endif

all: build


COMPILERS=http://downloads.osafoundation.org/compilers

ifeq ($(OS),Cygwin)

compiler=$(BUILD_ROOT)/mingw-3.1

$(compiler): $(BUILD_ROOT)/mingw-3.1.zip
	cd $(BUILD_ROOT); \
	unzip mingw-3.1.zip

$(BUILD_ROOT)/mingw-3.1.zip:
	cd $(BUILD_ROOT); \
	$(CURL) $(COMPILERS)/windows/mingw-3.1.zip
	$(CURL) $(COMPILERS)/windows/mingw-3.1.zip.md5
	$(MD5) --check mingw-3.1.zip.md5

endif

ifeq ($(OS),Darwin)

compiler=$(BUILD_ROOT)/gcc-3.4.1

$(compiler): $(BUILD_ROOT)/gcc-3.4.1.tar.bz2
	cd $(BUILD_ROOT); \
	bunzip2 -c gcc-3.4.1.tar.bz2 | tar -xvf -

$(BUILD_ROOT)/gcc-3.4.1.tar.bz2:
	cd $(BUILD_ROOT); \
	$(CURL) $(COMPILERS)/osx/gcc-3.4.1.tar.bz2
	$(CURL) $(COMPILERS)/osx/gcc-3.4.1.tar.bz2.md5
	$(MD5) --check gcc-3.4.1.tar.bz2.md5

endif

ifeq ($(OS),Linux)

.PHONY: compiler

compiler=compiler

$(compiler):
	@echo you need to install a gcc 3.4.x distribution for your Linux distribution that includes gcj and set GCJ_HOME to point at its installation directory

endif

compilers: $(compiler)

_realclean::
	@if [ "$(SRC)" = "" ]; then \
	    echo SRC is not set; false; \
	elif [ "$(SRC)" = "/" ]; then \
	    echo SRC is set to $(SRC); false; \
	else \
	    rm -rf $(SRC); \
	fi
