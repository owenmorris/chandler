
VERSION=0.4-0
JABBERPY=$(BUILD_ROOT)/jabber-py
SRC=$(JABBERPY)/jabberpy$(VERSION)
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

apply: patches
	patch -Nup0 < patches; echo ok

build: apply
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: jabberpy$(VERSION).tar.gz
	tar xvzf jabberpy$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(JABBERPY)/$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/jabber.py* \
                  $(SNAP)/$(SITE)/xmlstream.py*

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
