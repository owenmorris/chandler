
VERSION=0.8.3
PYXML=$(BUILD_ROOT)/pyxml
SRC=$(PYXML)/PyXML-$(VERSION)

ifeq ($(DEBUG),1)

DIST_OPT=--debug
PREFIX=$(BUILD_ROOT)/debug
SNAP=debug
PYTHON=$(PREFIX)/Library/Frameworks/Python.framework/Versions/2.3/bin/python_d

else

DIST_OPT=
PREFIX=$(BUILD_ROOT)/release
SNAP=release
PYTHON=$(PREFIX)/Library/Frameworks/Python.framework/Versions/2.3/bin/python

endif

BUILD=build_$(SNAP)


default: all

build:
	cd $(SRC); \
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

expand: PyXML-$(VERSION).tar.gz
	tar xvzf PyXML-$(VERSION).tar.gz

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(PYXML)/$(SNAP).tar.gz \
                  $(SNAP)/Library/Frameworks/Python.framework/Versions/2.3/lib/python2.3/site-packages/_xmlplus

clean:
	cd $(SRC); rm -rf $(BUILD)

all: build
