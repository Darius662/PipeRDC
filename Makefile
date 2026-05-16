# PipeRDC Build System
#
# Targets:
#   make install        - Install locally from source
#   make run            - Run directly from source
#   make build-pyinstaller - Build standalone binary with PyInstaller
#   make build-deb      - Build .deb package (requires dpkg-deb)
#   make build-rpm      - Build .rpm package (requires rpmbuild)
#   make build-arch     - Build Arch Linux package (requires makepkg)
#   make clean          - Remove build artifacts

PACKAGE_NAME = piperdc
VERSION = 1.0.0

# Local install paths
PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share
APPDIR ?= $(DATADIR)/applications
ICONDIR ?= $(DATADIR)/icons/hicolor/scalable/apps

.PHONY: all install run clean build-pyinstaller build-deb build-rpm build-arch

all: install

# Run directly from source
run:
	python3 -m src

# Install system-wide from source
install:
	install -Dm755 src/__main__.py $(DESTDIR)$(BINDIR)/piperdc
	install -Dm644 data/piperdc.desktop $(DESTDIR)$(APPDIR)/piperdc.desktop
	install -Dm644 data/icons/piperdc.svg $(DESTDIR)$(ICONDIR)/piperdc.svg
	# Install Python package
	cp -r src $(DESTDIR)$(DATADIR)/piperdc/
	# Create wrapper script
	printf '#!/bin/bash\nexec python3 $(DATADIR)/piperdc/__main__.py "$$@"' > $(DESTDIR)$(BINDIR)/piperdc
	chmod +x $(DESTDIR)$(BINDIR)/piperdc

# Install user-local
install-local:
	install -Dm755 src/__main__.py ~/.local/bin/piperdc
	install -Dm644 data/piperdc.desktop ~/.local/share/applications/piperdc.desktop
	install -Dm644 data/icons/piperdc.svg ~/.local/share/icons/hicolor/scalable/apps/piperdc.svg
	cp -r src ~/.local/share/piperdc/
	mkdir -p ~/.local/bin
	printf '#!/bin/bash\nexec python3 ~/.local/share/piperdc/__main__.py "$$@"' > ~/.local/bin/piperdc
	chmod +x ~/.local/bin/piperdc

# Build standalone binary with PyInstaller (all dependencies bundled)
build-pyinstaller:
	pip install pyinstaller
	pyinstaller --onefile \
		--name piperdc \
		--hidden-import gi \
		--hidden-import gi.repository.Gtk \
		--hidden-import gi.repository.Adw \
		--hidden-import gi.repository.GLib \
		--hidden-import gi.repository.Gio \
		--hidden-import secretstorage \
		--add-data "src:src" \
		--add-data "data/icons/piperdc.svg:." \
		src/__main__.py
	@echo "Binary built: dist/piperdc"
	@ls -lh dist/piperdc

# Build .deb package (uses PyInstaller binary)
build-deb:
	make build-pyinstaller
	mkdir -p packaging/deb/usr/bin
	mkdir -p packaging/deb/usr/share/applications
	mkdir -p packaging/deb/usr/share/icons/hicolor/scalable/apps
	cp dist/piperdc packaging/deb/usr/bin/
	cp data/piperdc.desktop packaging/deb/usr/share/applications/
	cp data/icons/piperdc.svg packaging/deb/usr/share/icons/hicolor/scalable/apps/
	dpkg-deb --build packaging/deb dist/piperdc_$(VERSION)_amd64.deb
	@echo "DEB package built: dist/piperdc_$(VERSION)_amd64.deb"

# Build .rpm package (uses PyInstaller binary)
build-rpm:
	make build-pyinstaller
	mkdir -p ~/rpmbuild/SOURCES
	mkdir -p ~/rpmbuild/BUILD/piperdc-$(VERSION)/usr/bin
	mkdir -p ~/rpmbuild/BUILD/piperdc-$(VERSION)/usr/share/applications
	mkdir -p ~/rpmbuild/BUILD/piperdc-$(VERSION)/usr/share/icons/hicolor/scalable/apps
	cp dist/piperdc ~/rpmbuild/BUILD/piperdc-$(VERSION)/usr/bin/
	cp data/piperdc.desktop ~/rpmbuild/BUILD/piperdc-$(VERSION)/usr/share/applications/
	cp data/icons/piperdc.svg ~/rpmbuild/BUILD/piperdc-$(VERSION)/usr/share/icons/hicolor/scalable/apps/
	cd ~/rpmbuild && tar czf SOURCES/piperdc-$(VERSION).tar.gz BUILD/piperdc-$(VERSION)/
	rpmbuild -bb --define "_topdir $(HOME)/rpmbuild" packaging/rpm/piperdc.spec
	@echo "RPM package built"

# Build Arch Linux package (for pacman -U)
build-arch:
	cd packaging/archlinux && makepkg -f
	cp packaging/archlinux/piperdc-*.pkg.tar.zst dist/
	@echo "Arch package built"

# Clean build artifacts
clean:
	rm -rf build/ dist/ __pycache__/
	rm -rf src/__pycache__/ src/*/__pycache__/
	rm -rf packaging/deb/usr/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned build artifacts"