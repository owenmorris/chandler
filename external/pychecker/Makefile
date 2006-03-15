
VERSION=0.8.13
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)4
PYCHECKER=$(BUILD_ROOT)/pychecker
SRC=$(PYCHECKER)/pychecker-$(VERSION)
TARBALL=pychecker-$(SNAP)-$(RELVER).tar.gz

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
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build \
          --build-base=$(BUILD) $(DIST_OPT) \
          install --force

pychecker-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/pychecker-$(VERSION).tar.gz

sources: pychecker-$(VERSION).tar.gz

pychecker-$(VERSION)-expanded: pychecker-$(VERSION).tar.gz
	tar xvzf pychecker-$(VERSION).tar.gz
	touch pychecker-$(VERSION)-expanded

expand: pychecker-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
      find $(SNAP)/$(SITE)/pychecker -name "*.pyc" | xargs rm -f; \
      find $(SNAP)/$(SITE)/pychecker -name "*.pyo" | xargs rm -f; \
      tar -cvzf $(PYCHECKER)/$(TARBALL) \
          $(SNAP)/$(SITE)/pychecker \
          $(SNAP)/$(BIN)/pychecker*

install: $(TARBALL)
	cp $(TARBALL) $(CHANDLERARCHIVES)

upload: $(TARBALL)
	scp $(TARBALL) $(UPLOAD)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
