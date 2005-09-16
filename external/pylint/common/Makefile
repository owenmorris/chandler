
VERSION=0.12.0
RELVER=$(VERSION)-1
COMMON=$(BUILD_ROOT)/pylint/common
SRC=$(COMMON)/common-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

common-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/common-$(VERSION).tar.gz
	$(CURL) http://builds.osafoundation.org/external/common-$(VERSION).tar.gz.md5

sources: common-$(VERSION).tar.gz

common-$(VERSION)-expanded: common-$(VERSION).tar.gz
	tar xvzf common-$(VERSION).tar.gz
	chmod u+w -R common-$(VERSION)
	touch common-$(VERSION)-expanded

expand: common-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/logilab -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/logilab -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(COMMON)/common-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/logilab \
                  --exclude test; \
	$(MD5) $(COMMON)/common-$(SNAP)-$(RELVER).tar.gz > $(COMMON)/common-$(SNAP)-$(RELVER).tar.gz.md5

install: common-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf common-$(SNAP)-$(RELVER).tar.gz

clean:
	@if [ -f $(PYTHON) ]; then \
            cd $(SRC); \
            $(PYTHON) setup.py clean --all; \
        fi

upload: common-$(SNAP)-$(RELVER).tar.gz
	scp common-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp common-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)
