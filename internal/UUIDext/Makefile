
include ../Makefile.inc

UUIDEXT=$(INTERNAL)/UUIDext

BUILD=build_$(SNAP)


build:
	$(PYTHON) setup.py build --build-base=$(BUILD) $(DIST_OPT) \
                           install --force

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(UUIDEXT)/UUIDext-$(SNAP).tar.gz \
                  $(SNAP)/$(SITE)/UUIDext*

clean:
	rm -rf $(BUILD)
