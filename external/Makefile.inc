
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
ifeq ($(GCJ_HOME),)
	@echo GCJ_HOME is not set && false
else
	@echo GCJ_HOME is $(GCJ_HOME)
ifeq ($(OS),Cygwin)
	@if [ ! -f $(GCJ_HOME)/bin/gcj.exe ]; then \
            echo GCJ_HOME is incorrect; \
            echo it needs to be set to the absolute gcc installation path; \
            false; \
        fi
else
	@if [ ! -f $(GCJ_HOME)/bin/gcj ]; then \
            echo GCJ_HOME is incorrect; \
            echo it needs to be set to the absolute gcc installation path; \
            false; \
        fi
endif
endif

all: build
