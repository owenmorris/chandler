
include ../Makefile.inc

VERSION=0.9.7d
RELVER=$(VERSION)-1
OPENSSL=$(BUILD_ROOT)/openssl
SRC=$(OPENSSL)/openssl-$(VERSION)

BUILD=build_$(SNAP)

.PHONY: openssl

ifeq ($(OS),Cygwin)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(SRC)/openssl-$(SNAP)-$(RELVER).zip \
                  $(SNAP)/$(SITE)/openssl

clean:
	cd $(SRC); devenv.com build/msw/msw.sln /clean $(Snap)
	cd $(SRC)/openssl; rm -rf $(SRC)/openssl/$(BUILD)

upload: openssl-$(SNAP)-$(RELVER).zip
	scp openssl-$(SNAP)-$(RELVER).zip $(UPLOAD)

build:
	@echo openssl build not yet implemented

snap:
	@echo openssl snap not yet implemented

clean:
	@echo openssl clean not yet implemented


else

$(SRC)/Makefile:
	cd $(SRC); \
	./config --prefix=$(PREFIX) --openssldir=$(PREFIX) $(CONF_OPT)
# 	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
# 	../config --prefix=$(PREFIX) $(CONF_OPT) 

openssl:   $(SRC)/Makefile
	cd $(SRC); \
        $(MAKE) ; $(MAKE) install 

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(SRC)/openssl-$(SNAP)-$(RELVER).tar.gz \
                  $(SNAP)/$(SITE)/openssl 

apply: $(SRC)/Makefile.ssl patches
	patch -Nup0 < patches; echo ok

expand: openssl-$(VERSION).tar.gz
	tar xvzf openssl-$(VERSION).tar.gz
	rm -f openssl-$(VERSION)/Makefile

clean:
	cd $(SRC); make clean; rm -f Makefile

upload: openssl-$(SNAP)-$(RELVER).tar.gz
	scp openssl-$(SNAP)-$(RELVER).tar.gz $(UPLOAD)

endif

build: apply openssl
