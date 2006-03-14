include ../Makefile.inc

VERSION=0.6a10-py2.4
SETUPTOOLS=$(BUILD_ROOT)/setuptools
BUILD=build_$(SNAP)
SRC=setuptools-$(VERSION).egg

ifeq ($(DEBUG),1)
DEBUG_SUFFIX=_d
else
DEBUG_SUFFIX=
endif

SETUPTOOLS_EGG=$(CHANDLERBIN)/$(SNAP)/$(SRC)
SETUPTOOLS_ABS=$(SETUPTOOLS_EGG)
SETUPTOOLS_BIN=$(CHANDLERBIN)/$(SNAP)
PYTHONEGG_BIN=$(CHANDLERBIN)/$(SNAP)/bin/python$(DEBUG_SUFFIX)

ifeq ($(OS),Cygwin)
SETUPTOOLS_ABS:=`cygpath -wa $(SETUPTOOLS_EGG)`
SETUPTOOLS_BIN:=`cygpath -wa $(SETUPTOOLS_BIN)`
endif

ifeq ($(OS),Darwin)
PYTHONEGG_BIN:=$(SETUPTOOLS_BIN)/RunPython
endif

$(SRC):
	$(CURL) http://builds.osafoundation.org/external/$(SRC)

sources: $(SRC)

expand: $(SRC)

build: expand

all: build

binaries:

install: build
	cp $(SRC) $(SETUPTOOLS_ABS)
	MACOSX_DEPLOYMENT_TARGET= CHANDLERHOME=$(CHANDLERBIN) $(PYTHONEGG_BIN) \
        -c "import sys; sys.path.insert(0,r'$(SETUPTOOLS_ABS)'); from setuptools.command.easy_install import main; main()" \
        --script-dir=$(SETUPTOOLS_BIN) $(SETUPTOOLS_ABS)
