
VERSION=2.0
EPYDOC=$(BUILD_ROOT)/epydoc
SRC=$(EPYDOC)/epydoc-$(VERSION)
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
SITE=Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages

else

PYTHON:=$(PREFIX)/bin/$(PYTHON)
SITE=lib/python2.3/site-packages

endif

BUILD=build_$(SNAP)


default: all

build:
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: epydoc-$(VERSION).tar.gz
	tar xvzf epydoc-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(EPYDOC)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/epydoc

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
