
include ../Makefile.inc

RELVER=0.3-1
UUIDEXT=$(INTERNAL)/UUIDext

BUILD=build_$(SNAP)


build:
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(UUIDEXT)/UUIDext-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/UUIDext*

clean:
	rm -rf $(BUILD)

upload: UUIDext-$(SNAP)-$(RELVER).tar.gz
	scp UUIDext-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)
