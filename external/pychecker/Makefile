
VERSION=0.8.13
RELVER=$(VERSION)-3
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


build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

pychecker-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/pychecker-$(VERSION).tar.gz
	$(CURL) http://builds.o11n.org/external/pychecker-$(VERSION).tar.gz.md5

sources: pychecker-$(VERSION).tar.gz

pychecker-$(VERSION)-expanded: pychecker-$(VERSION).tar.gz
	tar xvzf pychecker-$(VERSION).tar.gz
	touch pychecker-$(VERSION)-expanded

expand: pychecker-$(VERSION)-expanded

snap: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/pychecker -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/pychecker -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(PYCHECKER)/pychecker-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/pychecker \
                  $(SNAP)/$(BIN)/pychecker*; \
	$(MD5) $(PYCHECKER)/pychecker-$(SNAP)-$(RELVER).tar.gz > $(PYCHECKER)/pychecker-$(SNAP)-$(RELVER).tar.gz.md5

install: pychecker-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf pychecker-$(SNAP)-$(RELVER).tar.gz

upload: pychecker-$(SNAP)-$(RELVER).tar.gz
	scp pychecker-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp pychecker-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

clean:
	rm -rf $(SRC)/$(BUILD)
