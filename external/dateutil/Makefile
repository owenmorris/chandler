include ../Makefile.inc

VERSION=0.9
RELVER=$(VERSION)-1
DATEUTIL=$(BUILD_ROOT)/dateutil
MANIFEST=$(SNAP)/$(SITE)/dateutil
BUILD=build_$(SNAP)
SRC=python-dateutil-$(VERSION)

$(SRC).tar.bz2:
	$(CURL) http://builds.o11n.org/external/$(SRC).tar.bz2
	$(CURL) http://builds.o11n.org/external/$(SRC).tar.bz2.md5

sources: python-dateutil-$(VERSION).tar.bz2

$(SRC)-expanded: $(SRC).tar.bz2
	tar xvjf $(SRC).tar.bz2
	touch $(SRC)-expanded

expand: $(SRC)-expanded

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok


build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force


snap: 
	cd $(BUILD_ROOT); \
	find $(MANIFEST) -name "*.pyc" | xargs rm -f; \
	find $(MANIFEST) -name "*.pyo" | xargs rm -f
	tar -C $(BUILD_ROOT) -cvzf $(DATEUTIL)/dateutil-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)
	$(MD5) dateutil-$(SNAP)-$(RELVER).tar.gz > dateutil-$(SNAP)-$(RELVER).tar.gz.md5

upload: dateutil-$(SNAP)-$(RELVER).tar.gz
	scp dateutil-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp dateutil-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

clean:
	rm -rf $(BUILD)
	rm -rf $(SRC)
	rm $(SRC)-expanded

realclean: clean
	rm -rf build_debug build_release
	rm -f dateutil-debug-*.tar.gz* dateutil-release-*.tar.gz*
