
include ../Makefile.inc

VERSION=0.9.7d
OPENSSL=$(BUILD_ROOT)/openssl
SRC=$(OPENSSL)/openssl-$(VERSION)

BUILD=build_$(SNAP)

.PHONY: openssl

ifeq ($(OS),Darwin)
PLATFORM='darwin-ppc-cc'
endif
ifeq ($(OS),Linux)
# XXX fix later, just for now
PLATFORM='linux-pentium'
endif

REAL_OS=unknown

ifeq ($(OS),Cygwin)
  REAL_OS=WINNT
endif

ifeq ($(OS),WINNT)
  REAL_OS=WINNT
endif

ifeq ($(REAL_OS),WINNT)
# Build using Visual C++ compiler

ifeq ($(DEBUG),1)
MK1MF=sed -e "s/mk1mf\.pl/mk1mf\.pl debug/" ms/do_masm.bat > ms/do_masm_debug.bat
OUT32DLL=out32dll.dbg
DOMASM=do_masm_debug.bat
else
MK1MF=echo "Defaults work"
OUT32DLL=out32dll
DOMASM=do_masm.bat
endif

$(SRC)/$(BUILD)/ms/$(DOMASM): $(SRC)/Configure
	cd $(SRC); mkdir $(BUILD); cp Makefile.org *.h $(BUILD)/; \
	cp -r crypto ssl apps certs tools util ms include test $(BUILD)/;cd $(BUILD);\
	$(MK1MF);\
	chmod a+x ms/$(DOMASM);

openssl: $(SRC)/$(BUILD)/ms/$(DOMASM)
	cd $(SRC)/$(BUILD); \
	MAKEFLAGS=; \
	perl ../Configure --openssldir=$(PREFIX) --install_prefix=$(PREFIX) $(CONF_OPT) VC-WIN32; \
	ms/$(DOMASM); \
	nmake -f ms/ntdll.mak;\
	cd $(OUT32DLL); \
	../ms/test.bat; \
	echo 'Installing...';\
	cp -f ssleay32.dll $(PREFIX)/bin/; \
	cp -f libeay32.dll $(PREFIX)/bin/; \
	cp -f ssleay32.lib $(PREFIX)/lib/; \
	cp -f libeay32.lib $(PREFIX)/lib/; \
	cp -fr ../inc32/openssl $(PREFIX)/Include;\
	echo 'Installation done.'

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(OPENSSL)/$(SNAP).tar.gz \
			   $(SNAP)/bin/ssleay32.dll \
			   $(SNAP)/bin/libeay32.dll

endif

ifeq ($(OS),Darwin)

openssl:   $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); \
	$(MAKE) -f Makefile.ssl; \
	mkdir -p $(PREFIX)/lib; \
	$(MAKE) -f Makefile.ssl install 

$(SRC)/$(BUILD)/Makefile: $(SRC)/Configure
	cd $(SRC); mkdir $(BUILD); cp Makefile.org *.h $(BUILD)/; \
	cp -r crypto ssl apps certs tools util doc include $(BUILD)/;cd $(BUILD);\
	perl ../Configure -shared --openssldir=$(PREFIX) $(CONF_OPT) $(PLATFORM)

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(OPENSSL)/$(SNAP).tar.gz \
		   $(SNAP)/lib/libcrypto.0.9.7.dylib \
		   $(SNAP)/lib/libcrypto.0.dylib \
		   $(SNAP)/lib/libcrypto.a \
		   $(SNAP)/lib/libcrypto.dylib \
		   $(SNAP)/lib/libssl.0.9.7.dylib \
		   $(SNAP)/lib/libssl.0.dylib \
		   $(SNAP)/lib/libssl.a \
		   $(SNAP)/lib/libssl.dylib

else

openssl:   $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); \
	$(MAKE) -f Makefile.ssl; \
	mkdir -p $(PREFIX)/lib; \
	$(MAKE) -f Makefile.ssl install

$(SRC)/$(BUILD)/Makefile: $(SRC)/Configure
	cd $(SRC); mkdir $(BUILD); cp Makefile.org *.h $(BUILD)/; \
	cp -r crypto ssl apps certs tools util doc include $(BUILD)/;cd $(BUILD);\
	perl ../Configure --openssldir=$(PREFIX) $(CONF_OPT) $(PLATFORM)

snap: 
	cd $(BUILD_ROOT); \
	tar -cvzf $(OPENSSL)/$(SNAP).tar.gz \
		   $(SNAP)/lib/libcrypto.a \
		   $(SNAP)/lib/libssl.a

endif

$(SRC)/Configure: apply

expand: openssl-$(VERSION).tar.gz
	tar xvzf openssl-$(VERSION).tar.gz

apply: expand patches-$(VERSION)
	patch -Nup0 < patches-$(VERSION); echo ok

clean:
	rm -rf $(SRC)

build: openssl
