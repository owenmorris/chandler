
VERSION=0.8.13
PYCHECKER=$(BUILD_ROOT)/pychecker
SRC=$(PYCHECKER)/pychecker-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)
BIN=bin/Scripts
else
ifeq ($(OS),Darwin)
BIN=$(FRAMEWORK)/bin
else
BIN=bin
endif
endif

BUILD=build_$(SNAP)


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
                  $(SNAP)/$(BIN)/pychecker*

clean:
	cd $(SRC); rm -rf $(BUILD)
