
VERSION=4.2.52
DB=$(BUILD_ROOT)/persistence/db
SRC=$(DB)/db-$(VERSION)

include $(BUILD_ROOT)/Makefile.inc

ifeq ($(OS),Cygwin)

BUILD=build_win32
BINDIR=$(SRC)/$(BUILD)/$(Snap)

$(SRC)/$(BUILD)/Berkeley_DB.sln:
	(cd win32; tar -cf - *.sln *.vcproj) | (cd $(SRC)/$(BUILD); tar -xf -)

build: compile install

compile: $(SRC)/$(BUILD)/Berkeley_DB.sln
	cd $(SRC)/$(BUILD); \
        devenv.com Berkeley_DB.sln /project build_all /build $(Snap)

install:
	mkdir -p $(PREFIX)/bin/db $(PREFIX)/include/db $(PREFIX)/lib
	(cd $(SRC)/dbinc; tar cf - cxx_*.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(SRC)/$(BUILD); tar cf - *.h) | (cd $(PREFIX)/include/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.dll) | (cd $(PREFIX)/bin; tar xvf -)
	(cd $(BINDIR); tar cf - *.exe) | (cd $(PREFIX)/bin/db; tar xvf -)
	(cd $(BINDIR); tar cf - *.lib *.exp) | (cd $(PREFIX)/lib; tar xvf -)

clean:
	cd $(SRC)/$(BUILD); \
        devenv.com Berkeley_DB.sln /project build_all /clean $(Snap); \
        rm Berkeley_DB.sln

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(DB)/$(SNAP).tar.gz \
                  $(SNAP)/bin/libdb*.dll \
                  $(SNAP)/bin/db/db_*.exe

else

ifeq ($(DEBUG),1)
CONF_DBG=--enable-debug
else
CONF_DBG=
endif


BUILD=build_$(SNAP)

$(SRC)/$(BUILD)/Makefile: patches
	patch -Nup0 < patches; echo ok; \
	cd $(SRC); mkdir -p $(BUILD); cd $(BUILD); \
	../dist/configure --prefix=$(PREFIX)/db \
                          --enable-cxx $(CONF_DBG)

build: $(SRC)/$(BUILD)/Makefile
	cd $(SRC)/$(BUILD); $(MAKE); $(MAKE) install

expand: db-$(VERSION).tar.gz
	tar xvzf db-$(VERSION).tar.gz

clean:
	cd $(SRC); rm -rf $(BUILD)

snap: 
	cd $(BUILD_ROOT); \
        tar -cvzf $(DB)/$(SNAP).tar.gz $(SNAP)/db/bin $(SNAP)/db/lib

endif

all: build
