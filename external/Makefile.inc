
OS=$(shell uname)

ifeq ($(findstring CYGWIN,$(OS)),CYGWIN)
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

ifeq ($(OS),Cygwin)
PYTHON:=$(PREFIX)/bin/$(PYTHON).exe
SITE=bin/Lib/site-packages
PLATFORM=windows
else
ifeq ($(OS),Darwin)
FRAMEWORK=Library/Frameworks/Python.framework/Versions/2.3
PYTHON:=$(PREFIX)/$(FRAMEWORK)/bin/$(PYTHON)
SITE=$(FRAMEWORK)/lib/python2.3/site-packages
PLATFORM=macosx
else
PYTHON:=$(PREFIX)/bin/$(PYTHON)
SITE=lib/python2.3/site-packages
PLATFORM=linux
endif
endif

ifeq ($(GCJ_HOME),)
ifeq ($(OS),Cygwin)
GCJ_HOME=$(compiler)
endif
ifeq ($(OS),Darwin)
GCJ_HOME=$(compiler)/install
endif
ifeq ($(OS),Linux)
GCJ_HOME=/usr
endif
endif

UPLOAD=builder@builds.osafoundation.org:/www/docs/external/$(PLATFORM)

.PHONY: default all build compile install clean env

default: all

env::
	@echo Operating system is $(OS)
ifeq ($(BUILD_ROOT),)
	@echo BUILD_ROOT is not set && false
else
	@echo BUILD_ROOT is $(BUILD_ROOT)
	@if [ ! -f $(BUILD_ROOT)/build_root ]; then \
            echo BUILD_ROOT is incorrect; \
            echo it needs to be set to the absolute path including 'external'; \
            false; \
        fi
endif
	@echo GCJ_HOME is $(GCJ_HOME)
ifeq ($(OS),Cygwin)
	@if [ ! -f $(GCJ_HOME)/bin/gcj.exe ]; then \
            echo GCJ_HOME is incorrect; \
            echo it needs to be set to the absolute gcc with gcj installation path; \
            echo or unset it and run 'make compilers' to install gcc with gcj into $(BUILD_ROOT)/mingw-3.1; \
            false; \
        fi
else
	@if [ ! -f $(GCJ_HOME)/bin/gcj ]; then \
            echo GCJ_HOME is incorrect; \
            echo it needs to be set to the absolute gcc with gcj installation path; \
            echo or unset it and run 'make compilers' to install gcc with gcj into $(BUILD_ROOT)/gcc-3.4; \
            false; \
        fi
endif

all: build


COMPILERS=http://downloads.osafoundation.org/compilers

ifeq ($(OS),Cygwin)

compiler=$(BUILD_ROOT)/mingw-3.1

$(compiler): mingw-3.1.zip
	cd $(BUILD_ROOT); \
	gunzip mingw-3.1.zip

mingw-3.1.zip:
	cd $(BUILD_ROOT); \
	curl -O $(COMPILERS)/windows/mingw-3.1.zip

endif

ifeq ($(OS),Darwin)

compiler=$(BUILD_ROOT)/gcc-3.4

$(compiler): gcc-3.4-20040407.tar.bz2
	cd $(BUILD_ROOT); \
	bunzip2 -c gcc-3.4-20040407.tar.bz2 | tar -xvf -

$(BUILD_ROOT)/gcc-3.4-20040407.tar.bz2:
	cd $(BUILD_ROOT); \
	curl -O $(COMPILERS)/osx/gcc-3.4-20040407.tar.bz2

endif

compilers: $(compiler)

