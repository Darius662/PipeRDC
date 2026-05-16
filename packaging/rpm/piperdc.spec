Name:       piperdc
Version:    1.0.0
Release:    1%{?dist}
Summary:    A modern RDP Connection Manager for Linux

License:    MIT
URL:        https://github.com/dariusjeleru/piperdc
Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools

Requires:   python3
Requires:   python3-gobject
Requires:   gtk4
Requires:   libadwaita
Requires:   freerdp
Requires:   python3-secretstorage

%description
PipeRDC is a modern, native RDP connection manager for Linux.
It provides a clean GTK4 interface to manage and launch
Remote Desktop connections using xfreerdp3.

Features:
  - Connection management with groups/folders
  - Search and filter connections
  - Secure credential storage via keyring
  - .rdp file import
  - Export launchable shell scripts
  - Multi-monitor support
  - Audio redirection and microphone support

%prep
%setup -q

%build
python3 -m build --wheel

%install
python3 -m installer --destdir=%{buildroot} dist/*.whl
install -Dm644 data/piperdc.desktop %{buildroot}%{_datadir}/applications/piperdc.desktop
install -Dm644 data/icons/piperdc.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/piperdc.svg

%files
%{_bindir}/piperdc
%{_datadir}/applications/piperdc.desktop
%{_datadir}/icons/hicolor/scalable/apps/piperdc.svg
%{python3_sitelib}/src/**

%changelog
* Sat May 16 2026 Your Name <your.email@example.com> - 1.0.0-1
- Initial release