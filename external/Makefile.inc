
OS=$(shell uname)

ifeq ($(findstring CYGWIN,$(OS)),CYGWIN)
OS=Cygwin
endif

ifeq ($(DEBUG),1)
SNAP=debug
Snap=Debug
else
SNAP=release
Snap=Release
DEBUG=0
endif

PREFIX=$(BUILD_ROOT)/$(SNAP)

default: all

.PHONY: default all build compile install clean env

env:
	@echo Operating system is $(OS)
ifeq ($(BUILD_ROOT),)
	@echo BUILD_ROOT is not set && false
else
	@echo BUILD_ROOT is $(BUILD_ROOT)
endif
ifeq ($(GCJ_HOME),)
	@echo GCJ_HOME is not set && false
else
	@echo GCJ_HOME is $(GCJ_HOME)
endif
