
include ../Makefile.inc

RELVER=0.3-2
UUIDEXT=$(INTERNAL)/UUIDext

BUILD=build_$(SNAP)

MANIFEST=$(SNAP)/$(SITE)/UUIDext*


build:
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

clean:
	rm -rf $(BUILD)

upload: UUIDext-$(SNAP)-$(RELVER).tar.gz
	scp UUIDext-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(UUIDEXT)/UUIDext-$(SNAP)-$(RELVER).tar.gz $(MANIFEST)

install:
	cd $(BUILD_ROOT); \
        tar -cf - $(MANIFEST) | tar -C $(CHANDLERBIN) -xvf -
