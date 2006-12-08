
include ../../Makefile

ifeq ($(PLATFORM),maciosx)
DIST_PLATFORM=mac
endif

ifeq ($(PLATFORM),macosx)
DIST_PLATFORM=mac
endif

ifeq ($(PLATFORM),linux)
DIST_PLATFORM=linux
endif

ifeq ($(PLATFORM),windows)
DIST_PLATFORM=windows
endif

DIST_HOME=$(DSTDIR)/chandler/chandler
DIST_BIN=$(DSTDIR)/chandler/$(DIST_PLATFORM)

.PHONY: deploy distro archive


deploy:
	mkdir -p $(DSTDIR)/chandler/mac/archives
	mkdir -p $(DSTDIR)/chandler/linux/archives
	mkdir -p $(DSTDIR)/chandler/windows/archives
	mkdir -p $(DSTDIR)/chandler/profile
	cd $(DSTDIR)/chandler; svn co $(SVNURL) chandler
	$(MAKE) -f $(DSTDIR)/chandler/chandler/Makefile -e \
                CHANDLERBIN="$(DSTDIR)/chandler/mac" \
                CHANDLERARCHIVES="$(DSTDIR)/chandler/mac/archives" \
                PLATFORM=maciosx \
                archives
	$(MAKE) -f $(DSTDIR)/chandler/chandler/Makefile -e \
                CHANDLERBIN="$(DSTDIR)/chandler/linux" \
                CHANDLERARCHIVES="$(DSTDIR)/chandler/linux/archives" \
                PLATFORM=linux \
                archives
	$(MAKE) -f $(DSTDIR)/chandler/chandler/Makefile -e \
                CHANDLERBIN="$(DSTDIR)/chandler/windows" \
                CHANDLERARCHIVES="$(DSTDIR)/chandler/windows/archives" \
                PLATFORM=windows \
                archives
	$(MAKE) -C "$(DIST_HOME)" -f $(DSTDIR)/chandler/chandler/Makefile -e \
                CHANDLERBIN="$(DIST_BIN)" \
                CHANDLERHOME="$(DIST_HOME)" \
                install-plugin-core distrib-plugins


starters:
	tar -cf - --exclude .svn \
                Chandler.app chandler.sh chandler.bat | \
        tar -C $(DSTDIR)/chandler -xvf -


archive:
	tar -C $(DSTDIR) -cvjf $(DSTDIR)/chandler.tar.bz2 \
                         --ignore-failed-read \
                         --exclude .svn \
                         --exclude archives \
                         --exclude distrib \
                         --exclude '*.inst' \
                         chandler


distro: deploy starters archive
