
VERSION=2.1
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)6
EPYDOC=$(BUILD_ROOT)/epydoc
SRC=$(EPYDOC)/epydoc-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

.PHONY: patches-$(VERSION)

apply: patches-$(VERSION)
	if [ -f patches-$(VERSION) ]; then \
            patch -Nup0 < patches-$(VERSION); echo ok; \
        fi

build: expand apply
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

epydoc-$(VERSION).tar.gz:
	$(CURL) http://builds.o11n.org/external/epydoc-$(VERSION).tar.gz

sources: epydoc-$(VERSION).tar.gz

epydoc-$(VERSION)-expanded: epydoc-$(VERSION).tar.gz
	tar xvzf epydoc-$(VERSION).tar.gz
	touch epydoc-$(VERSION)-expanded

expand: epydoc-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
      find $(SNAP)/$(SITE)/epydoc -name "*.pyc" | xargs rm -f; \
      find $(SNAP)/$(SITE)/epydoc -name "*.pyo" | xargs rm -f; \
      tar -cvzf $(EPYDOC)/epydoc-$(SNAP)-$(RELVER).tar.gz \
          --exclude test \
          $(SNAP)/$(SITE)/epydoc

install: epydoc-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf epydoc-$(SNAP)-$(RELVER).tar.gz

upload: epydoc-$(SNAP)-$(RELVER).tar.gz
	scp epydoc-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif
