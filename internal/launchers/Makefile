
include ../Makefile.inc

RELVER=0.1-1
LAUNCHERS=$(INTERNAL)/launchers

BUILD=build_$(SNAP)

ifeq ($(DEBUG),1)
    DEBUG=$DEBUG
else
    undef DEBUG
endif

ifeq ($(OS),Darwin)

else
ARCHIVE: $(LAUNCHERS)/linux/$(BUILD)/chandler \
         $(LAUNCHERS)/linux/$(BUILD)/chandler_bin \
         $(LAUNCHERS)/win/

build:
	cd $(LAUNCHERS)/linux; \
	make; \
	cd $(LAUNCHERS)/win;
	make

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(LAUNCHERS)/LAUNCHERS-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/LAUNCHERS*

clean:
	rm -rf $(BUILD)

upload: LAUNCHERS-$(SNAP)-$(RELVER).tar.gz
	scp LAUNCHERS-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

endif