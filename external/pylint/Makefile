
VERSION=0.7.0
RELVER=$(VERSION)-1
PYLINT=$(BUILD_ROOT)/pylint
SRC=$(PYLINT)/pylint-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)

build-common:
	$(MAKE) -C common DEBUG=$(DEBUG) all

build-optik:
	$(MAKE) -C optik DEBUG=$(DEBUG) all

build: build-common build-optik expand
	cd $(SRC); \
      MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force

pylint-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/pylint-$(VERSION).tar.gz
#	$(CURL) http://builds.osafoundation.org/external/pylint-$(VERSION).tar.gz.md5

sources-common:
	$(MAKE) -C common DEBUG=$(DEBUG) sources

sources-optik:
	$(MAKE) -C optik DEBUG=$(DEBUG) sources

sources: sources-common sources-optik pylint-$(VERSION).tar.gz

pylint-$(VERSION)-expanded: pylint-$(VERSION).tar.gz
	tar xvzf pylint-$(VERSION).tar.gz
	chmod -R u+w pylint-$(VERSION)
	touch pylint-$(VERSION)-expanded

expand-common:
	$(MAKE) -C common DEBUG=$(DEBUG) expand

expand-optik:
	$(MAKE) -C optik DEBUG=$(DEBUG) expand

expand: expand-common expand-optik pylint-$(VERSION)-expanded

binaries-common:
	$(MAKE) -C common DEBUG=$(DEBUG) binaries

binaries-optik:
	$(MAKE) -C optik DEBUG=$(DEBUG) binaries

binaries: binaries-common binaries-optik
	cd $(BUILD_ROOT); \
    find $(SNAP)/$(SITE)/pylint -name "*.pyc" | xargs rm -f; \
    find $(SNAP)/$(SITE)/pylint -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(PYLINT)/pylint-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/pylint \
                  --exclude test
	$(MD5) $(PYLINT)/pylint-$(SNAP)-$(RELVER).tar.gz > $(PYLINT)/pylint-$(SNAP)-$(RELVER).tar.gz.md5

install-common:
	$(MAKE) -C common DEBUG=$(DEBUG) install

install-optik:
	$(MAKE) -C optik DEBUG=$(DEBUG) install

install: install-common install-optik pylint-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf pylint-$(SNAP)-$(RELVER).tar.gz

clean-common:
	$(MAKE) -C common DEBUG=$(DEBUG) clean

clean-optik:
	$(MAKE) -C optik DEBUG=$(DEBUG) clean

clean: clean-common clean-optik
	@if [ -f $(PYTHON) ]; then \
            cd $(SRC); \
            $(PYTHON) setup.py clean --all; \
        fi

upload-common:
	$(MAKE) -C common DEBUG=$(DEBUG) upload

upload-optik:
	$(MAKE) -C optik DEBUG=$(DEBUG) upload

upload: upload-common upload-optik pylint-$(SNAP)-$(RELVER).tar.gz
	scp pylint-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp pylint-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

_realclean::
	rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded
	rm -rf $(SRC)*
	$(MAKE) -C common DEBUG=$(DEBUG) _realclean
	$(MAKE) -C optik DEBUG=$(DEBUG) _realclean
