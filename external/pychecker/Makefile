
VERSION=0.8.13
PYCHECKER=$(BUILD_ROOT)/pychecker
SRC=$(PYCHECKER)/pychecker-$(VERSION)
OS=$(shell uname)

ifeq ($(DEBUG),1)

DIST_OPT=--debug
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug
PYTHON=python_d

else

DIST_OPT=
PREFIX=$(BUILD_ROOT)/release
SNAP=release
PYTHON=python

endif

ifeq ($(OS),Darwin)

PYTHON:=$(PREFIX)/Library/Frameworks/Python.framework/Versions/2.3/bin/$(PYTHON)
FRAMEWORK=Library/Frameworks/Python.framework/Versions/2.3
SITE=$(FRAMEWORK)/lib/python2.3/site-packages
BIN=$(FRAMEWORK)/bin

else

PYTHON:=$(PREFIX)/bin/$(PYTHON)
SITE=lib/python2.3/site-packages
BIN=bin

endif

BUILD=build_$(SNAP)


default: all

build:
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: pychecker-$(VERSION).tar.gz
	tar xvzf pychecker-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYCHECKER)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/pychecker \
                  $(SNAP)/$(BIN)/pychecker

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
