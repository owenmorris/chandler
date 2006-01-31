
VERSION=1.5
RELVER=$(VERSION)-$(BRANCH_REV_PREFIX)2
OPTIK=$(BUILD_ROOT)/pylint/optik
SRC=$(OPTIK)/optik-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

BUILD=build_$(SNAP)


build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

optik-$(VERSION).tar.gz:
	$(CURL) http://builds.osafoundation.org/external/optik-$(VERSION).tar.gz

sources: optik-$(VERSION).tar.gz

optik-$(VERSION)-expanded: optik-$(VERSION).tar.gz
	tar xvzf optik-$(VERSION).tar.gz
	touch optik-$(VERSION)-expanded

expand: optik-$(VERSION)-expanded

binaries: 
	cd $(BUILD_ROOT); \
	find $(SNAP)/$(SITE)/optik -name "*.pyc" | xargs rm -f; \
	find $(SNAP)/$(SITE)/optik -name "*.pyo" | xargs rm -f; \
        tar -cvzf $(OPTIK)/optik-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/optik

install: optik-$(SNAP)-$(RELVER).tar.gz
	tar -C $(CHANDLERBIN) -xvzf optik-$(SNAP)-$(RELVER).tar.gz

ifneq (/,$(SRC)/$(BUILD))
clean:
	rm -rf $(SRC)/$(BUILD)
endif

_realclean::
	rm -f $(SRC)/../*-release-* $(SRC)/../*-debug-* $(SRC)/../*-expanded
	rm -rf $(SRC)*

upload: optik-$(SNAP)-$(RELVER).tar.gz
	scp optik-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
