
include ../Makefile.inc

RELVER=0.3-3
UUIDEXT=$(INTERNAL)/UUIDext

BUILD=build_$(SNAP)

MANIFEST=$(SNAP)/$(SITE)/UUIDext*


build:
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

clean:
	rm -rf $(BUILD)

realclean: 
	rm -fr build_debug build_release
	rm -f UUIDext-debug-*.tar.gz* UUIDext-release-*.tar.gz*

upload: UUIDext-$(SNAP)-$(RELVER).tar.gz
	scp UUIDext-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
	scp UUIDext-$(SNAP)-$(RELVER).tar.gz.md5 $(UPLOAD)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(UUIDEXT)/UUIDext-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)
	$(MD5) UUIDext-$(SNAP)-$(RELVER).tar.gz > UUIDext-$(SNAP)-$(RELVER).tar.gz.md5

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -
