include ../Makefile.inc

VERSION=0.1.3
RELVER=$(VERSION)-1
VOBJECT=$(BUILD_ROOT)/vobject
MANIFEST=$(SNAP)/$(SITE)/vobject
BUILD=build_$(SNAP)
SRC=vobject-$(VERSION)

$(SRC).tar.gz:
	$(CURL) http://builds.o11n.org/external/$(SRC).tar.gz
	$(CURL) http://builds.o11n.org/external/$(SRC).tar.gz.md5

sources: vobject-$(VERSION).tar.gz

$(SRC)-expanded: $(SRC).tar.gz
	tar xzf $(SRC).tar.gz
	touch $(SRC)-expanded

expand: $(SRC)-expanded

apply: patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok
	patch -Nup0 < patches2-$(VERSION); echo ok

build: expand
	cd $(SRC); \
	MACOSX_DEPLOYMENT_TARGET=$(MACOSX_DEPLOYMENT_TARGET) $(PYTHON) setup.py \
          build --build-base=$(BUILD) $(DIST_OPT) \
          install --force


snap: 
	cd $(BUILD_ROOT); \
	find $(MANIFEST) -name "*.pyc" | xargs rm -f; \
	find $(MANIFEST) -name "*.pyo" | xargs rm -f
	tar -C $(BUILD_ROOT) -cvzf $(VOBJECT)/vobject-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)
	$(MD5) vobject-$(SNAP)-$(RELVER).tar.gz > vobject-$(SNAP)-$(RELVER).tar.gz.md5

upload: vobject-$(SNAP)-$(RELVER).tar.gz
	scp vobject-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp vobject-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -

clean:
	rm -rf $(BUILD)
	rm -rf $(SRC)
	rm $(SRC)-expanded

realclean: clean
	rm -rf build_debug build_release
	rm -f vobject-debug-*.tar.gz* vobject-release-*.tar.gz*
