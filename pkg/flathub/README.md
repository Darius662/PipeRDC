# Flathub packaging for PipeRDC

This directory contains the Flathub packaging files for `PipeRDC`.

Files:
- `org.piperdc.PipeRDC.yml` — Flatpak manifest for building the app on Flathub.
- `org.piperdc.PipeRDC.appdata.xml` — AppStream metadata used by Flathub.

To use locally:

```bash
cd pkg/flathub
flatpak-builder --force-clean build-dir org.piperdc.PipeRDC.yml
flatpak install --user build-dir org.piperdc.PipeRDC -y
```

For Flathub submission, copy these files into a fork of `flathub/flathub` under `apps/org.piperdc.PipeRDC/` and open a PR.
