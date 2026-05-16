# PipeRDC

> A modern, native RDP Connection Manager for Linux — inspired by Windows Remote Desktop Connection.

![PipeRDC Screenshot](data/icons/piperdc.svg)

## Features

- **Connection Management** — Add, edit, duplicate, and delete RDP connections
- **Group Organization** — Group connections into folders (e.g., Servers, Work, Home)
- **Search & Filter** — Quickly find connections by name, host, or group
- **Launch RDP Sessions** — One-click connection using `xfreerdp3`
- **Script Export** — Generate executable `.sh` scripts for each connection (run from terminal or file manager)
- **.rdp File Import** — Import Microsoft RDP configuration files
- **Credential Storage** — Passwords stored securely in system keyring (SecretService/gnome-keyring)
- **Multi-Monitor Support** — Full multimonitor configuration with selected monitors
- **Audio & Devices** — Audio redirection, microphone support, drive sharing
- **GTK4 + LibAdwaita** — Native look and feel on GNOME, works on Wayland
- **Ships standalone** — Can be packaged as DEB/RPM/Pacman or run from source

## Installation

### From Source (Linux)

```bash
git clone https://github.com/dariusjeleru/piperdc.git
cd piperdc

# Option 1: Run directly
make run

# Option 2: Install system-wide
sudo make install

# Option 3: Install user-local
make install-local

# Option 4: Install with CMake
mkdir -B build
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr
cmake --install build
```

### Arch Linux (AUR)

```bash
yay -S piperdc
# or
paru -S piperdc
```

### Debian/Ubuntu (.deb)

```bash
make build-deb
sudo dpkg -i dist/piperdc_1.0.0_amd64.deb
```

### Fedora/RHEL (.rpm)

```bash
make build-rpm
sudo rpm -i dist/piperdc-1.0.0-1.x86_64.rpm
```

### Arch Linux (Pacman)

```bash
make build-arch
sudo pacman -U dist/piperdc-1.0.0-1-x86_64.pkg.tar.zst
```

## Dependencies

| Dependency | Purpose |
|-----------|---------|
| `python3` (≥ 3.10) | Runtime |
| `gtk4` | GUI toolkit |
| `libadwaita` | Modern GNOME widgets |
| `python-gobject` | GTK4 Python bindings |
| `freerdp` (`xfreerdp3`) | RDP protocol client |
| `python-secretstorage` | Keyring credential storage |

## Usage

1. Launch **PipeRDC** from your application menu or terminal: `piperdc`
2. Click **New Connection** to add your first RDP connection
3. Fill in the connection details (host, port, username, password)
4. Double-click a connection or press the ▶ button to connect
5. Right-click a connection for more options (Edit, Duplicate, Export Script, Delete)
6. Use the **Groups** sidebar to organize connections
7. Use the search bar to quickly filter connections

### Script Export

Each connection can export a standalone `.sh` script that runs `xfreerdp3` with all configured options:

```bash
~/.config/piperdc/scripts/My_Windows_VM.sh
```

These scripts can be launched from PipeRDC, the terminal, or your file manager.

## Building Packages

```bash
make build-pyinstaller   # Standalone binary (all dependencies bundled)
make build-deb           # .deb package
make build-rpm           # .rpm package
make build-arch          # Arch Linux package
```

## Project Structure

```
piperdc/
├── src/                    # Python source code
│   ├── __main__.py         # Entry point
│   ├── main.py             # Application class
│   ├── models/             # Data models
│   │   └── connection.py   # RDPConnection dataclass
│   ├── services/           # Business logic
│   │   ├── config_manager.py    # JSON config persistence
│   │   ├── credential_manager.py # Keyring integration
│   │   └── rdp_launcher.py      # xfreerdp3 subprocess
│   ├── ui/                 # GTK4 UI components
│   │   ├── window.py            # Main window
│   │   └── connection_dialog.py # Add/Edit dialog
│   └── utils/              # Utilities
│       └── rdp_parser.py   # .rdp file parser
├── data/                   # App data
│   ├── icons/piperdc.svg   # App icon
│   └── piperdc.desktop     # Desktop entry
├── packaging/              # Distribution packaging
│   ├── aur/PKGBUILD
│   ├── deb/DEBIAN/control
│   └── rpm/piperdc.spec
├── Makefile                # Build automation
├── pyproject.toml          # Python project config
└── README.md
```

## License

MIT

## Credits

Built with [Python](https://python.org), [GTK4](https://gtk.org), and [LibAdwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/).