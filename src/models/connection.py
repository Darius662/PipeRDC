"""Connection model for RDP connections."""

from __future__ import annotations
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class RDPConnection:
    """Represents a single RDP connection configuration."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    group: str = ""
    host: str = ""
    port: int = 3389
    username: str = ""
    password: str = ""
    domain: str = ""
    resolution: str = "fullscreen"
    custom_width: int = 1920
    custom_height: int = 1080
    use_multimon: bool = False
    monitors: str = ""
    audio_mode: str = "redirect"
    enable_mic: bool = False
    enable_drive: bool = True
    drive_path: str = "home,$HOME"
    bpp: int = 32
    network_type: str = "auto"
    floatbar: bool = True
    use_gfx: bool = True
    use_h264: bool = True
    additional_flags: str = ""
    client: str = "xfreerdp3"

    # Security settings
    cert_behavior: str = "tofu"  # deny, ignore, name, tofu, fingerprint
    cert_name: str = ""
    cert_fingerprint: str = ""
    sec_protocol: str = "nla"    # rdp, tls, nla, ext, aad
    encryption_methods: str = "128"
    auth_only: bool = False
    pass_the_hash: str = ""
    disable_encryption: bool = False
    disable_nego: bool = False

    # Device redirection
    enable_clipboard: bool = True
    clipboard_direction: str = "both"  # both, to-client, from-client
    printer_name: str = ""
    printer_driver: str = ""
    enable_smartcard: bool = False
    smartcard_info: str = ""
    enable_usb: bool = False
    usb_filter: str = ""
    enable_serial: bool = False
    serial_device: str = ""
    enable_parallel: bool = False
    parallel_device: str = ""
    grab_keyboard: bool = True
    grab_mouse: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d.pop("id", None)
        return d

    @classmethod
    def from_dict(cls, data: dict, conn_id: str) -> "RDPConnection":
        """Create from dictionary with ID."""
        return cls(id=conn_id, **data)

    def _normalize_monitors(self) -> str:
        """Normalize a monitor index list into a clean comma-separated string."""
        if not self.monitors:
            return ""
        normalized = []
        for part in str(self.monitors).split(","):
            part = part.strip()
            if not part:
                continue
            try:
                normalized.append(str(int(part)))
            except ValueError:
                continue
        return ",".join(sorted(set(normalized), key=int))

    def build_xfreerdp_args(self) -> list[str]:
        """Build xfreerdp3 command-line arguments."""
        args = [self.client, f"/v:{self.host}:{self.port}"]

        if self.username:
            args.append(f"/u:{self.username}")
        if self.password:
            args.append(f"/p:{self.password}")
        if self.domain:
            args.append(f"/d:{self.domain}")

        # Resolution
        if self.resolution == "fullscreen":
            args.append("/f")
        elif self.resolution == "custom":
            args.append(f"/size:{self.custom_width}x{self.custom_height}")
        elif self.resolution == "widescreen":
            args.append("/size:1920x1080")
        elif self.resolution == "quadhd":
            args.append("/size:2560x1440")
        elif self.resolution == "ultrahd":
            args.append("/size:3840x2160")

        # Multimonitor
        if self.use_multimon:
            args.append("/multimon")
            monitors = self._normalize_monitors()
            if monitors:
                args.append(f"/monitors:{monitors}")

        # Floatbar
        if self.floatbar:
            args.append("/floatbar:sticky:on,default:visible,show:always")

        # Audio
        if self.audio_mode:
            args.append(f"/audio-mode:{self.audio_mode}")

        # Microphone
        if self.enable_mic:
            args.append("/mic")

        # Security: certificate handling
        if self.cert_behavior == "ignore":
            args.append("/cert:ignore")
        elif self.cert_behavior == "tofu":
            args.append("/cert:tofu")
        elif self.cert_behavior == "name" and self.cert_name:
            args.append(f"/cert:name:{self.cert_name}")
        elif self.cert_behavior == "fingerprint" and self.cert_fingerprint:
            args.append(f"/cert:fingerprint:{self.cert_fingerprint}")

        # Security: protocol
        if self.sec_protocol in ("rdp", "tls", "nla", "ext", "aad"):
            args.append(f"/sec:{self.sec_protocol}")

        # Security: encryption
        if self.encryption_methods:
            args.append(f"/encryption-methods:{self.encryption_methods}")

        # Security: auth only
        if self.auth_only:
            args.append("+auth-only")

        # Security: pass-the-hash
        if self.pass_the_hash:
            args.append(f"/pth:{self.pass_the_hash}")

        # Security: disable
        if self.disable_encryption:
            args.append("-encryption")
        if self.disable_nego:
            args.append("-nego")

        # Devices: clipboard
        if self.enable_clipboard:
            if self.clipboard_direction == "to-client":
                args.append("/clipboard:direction-to:client")
            elif self.clipboard_direction == "from-client":
                args.append("/clipboard:direction-to:server")
            else:
                args.append("/clipboard")
        else:
            args.append("-clipboard")

        # Devices: printer
        if self.printer_name:
            if self.printer_driver:
                args.append(f"/printer:{self.printer_name},{self.printer_driver}")
            else:
                args.append(f"/printer:{self.printer_name}")

        # Devices: smartcard
        if self.enable_smartcard and self.smartcard_info:
            args.append(f"/smartcard:{self.smartcard_info}")
        elif self.enable_smartcard:
            args.append("/smartcard")

        # Devices: USB
        if self.enable_usb and self.usb_filter:
            args.append(f"/usb:{self.usb_filter}")
        elif self.enable_usb:
            args.append("/usb")

        # Devices: serial
        if self.enable_serial and self.serial_device:
            args.append(f"/serial:{self.serial_device}")

        # Devices: parallel
        if self.enable_parallel and self.parallel_device:
            args.append(f"/parallel:{self.parallel_device}")

        # Keyboard/mouse grab
        if not self.grab_keyboard:
            args.append("-grab-keyboard")
        if not self.grab_mouse:
            args.append("-grab-mouse")

        # Drive redirection - expand $HOME for non-shell execution
        if self.enable_drive and self.drive_path:
            drive_arg = self.drive_path.replace("$HOME", os.environ.get("HOME", ""))
            args.append(f"/drive:{drive_arg}")

        # Performance
        args.append(f"/bpp:{self.bpp}")
        args.append(f"/network:{self.network_type}")

        # GFX/H264
        if self.use_gfx:
            if self.use_h264:
                args.append("/gfx:AVC444")
            else:
                args.append("/gfx")

        # Additional flags
        if self.additional_flags:
            for flag in self.additional_flags.split():
                args.append(flag)

        return args

    def generate_script(self) -> str:
        """Generate a shell script for this connection."""
        flag_lines = []

        if self.username:
            flag_lines.append(f"/u:{self.username}")
        if self.password:
            flag_lines.append(f"/p:{self.password}")
        if self.domain:
            flag_lines.append(f"/d:{self.domain}")

        if self.resolution == "fullscreen":
            flag_lines.append("/f")
        elif self.resolution == "custom":
            flag_lines.append(f"/size:{self.custom_width}x{self.custom_height}")
        elif self.resolution == "widescreen":
            flag_lines.append("/size:1920x1080")
        elif self.resolution == "quadhd":
            flag_lines.append("/size:2560x1440")
        elif self.resolution == "ultrahd":
            flag_lines.append("/size:3840x2160")

        if self.use_multimon:
            flag_lines.append("/multimon")
            monitors = self._normalize_monitors()
            if monitors:
                flag_lines.append(f"/monitors:{monitors}")

        if self.floatbar:
            flag_lines.append("/floatbar:sticky:on,default:visible,show:always")

        if self.audio_mode:
            flag_lines.append(f"/audio-mode:{self.audio_mode}")

        if self.enable_mic:
            flag_lines.append("/mic")

        # Security: certificate
        if self.cert_behavior == "ignore":
            flag_lines.append("/cert:ignore")
        elif self.cert_behavior == "tofu":
            flag_lines.append("/cert:tofu")
        elif self.cert_behavior == "name" and self.cert_name:
            flag_lines.append(f"/cert:name:{self.cert_name}")
        elif self.cert_behavior == "fingerprint" and self.cert_fingerprint:
            flag_lines.append(f"/cert:fingerprint:{self.cert_fingerprint}")

        if self.sec_protocol in ("rdp", "tls", "nla", "ext", "aad"):
            flag_lines.append(f"/sec:{self.sec_protocol}")
        if self.encryption_methods:
            flag_lines.append(f"/encryption-methods:{self.encryption_methods}")
        if self.auth_only:
            flag_lines.append("+auth-only")
        if self.pass_the_hash:
            flag_lines.append(f"/pth:{self.pass_the_hash}")
        if self.disable_encryption:
            flag_lines.append("-encryption")
        if self.disable_nego:
            flag_lines.append("-nego")

        # Devices
        if self.enable_clipboard:
            if self.clipboard_direction == "to-client":
                flag_lines.append("/clipboard:direction-to:client")
            elif self.clipboard_direction == "from-client":
                flag_lines.append("/clipboard:direction-to:server")
            else:
                flag_lines.append("/clipboard")
        else:
            flag_lines.append("-clipboard")

        if self.printer_name:
            if self.printer_driver:
                flag_lines.append(f"/printer:{self.printer_name},{self.printer_driver}")
            else:
                flag_lines.append(f"/printer:{self.printer_name}")

        if self.enable_smartcard and self.smartcard_info:
            flag_lines.append(f"/smartcard:{self.smartcard_info}")
        elif self.enable_smartcard:
            flag_lines.append("/smartcard")

        if self.enable_usb and self.usb_filter:
            flag_lines.append(f"/usb:{self.usb_filter}")
        elif self.enable_usb:
            flag_lines.append("/usb")

        if self.enable_serial and self.serial_device:
            flag_lines.append(f"/serial:{self.serial_device}")
        if self.enable_parallel and self.parallel_device:
            flag_lines.append(f"/parallel:{self.parallel_device}")

        if not self.grab_keyboard:
            flag_lines.append("-grab-keyboard")
        if not self.grab_mouse:
            flag_lines.append("-grab-mouse")

        if self.enable_drive and self.drive_path:
            flag_lines.append(f"/drive:{self.drive_path}")

        flag_lines.append(f"/bpp:{self.bpp}")
        flag_lines.append(f"/network:{self.network_type}")

        if self.use_gfx:
            if self.use_h264:
                flag_lines.append("/gfx:AVC444")
            else:
                flag_lines.append("/gfx")

        if self.additional_flags:
            for flag in self.additional_flags.split():
                flag_lines.append(flag)

        lines = [
            "#!/bin/bash",
            f'SERVER="${{1:-{self.host}}}"',
            f'PORT="${{2:-{self.port}}}"',
            f'CLIENT="${{3:-{self.client}}}"',
            "",
            f"$CLIENT /v:\"$SERVER\":\"$PORT\" \\",
        ]

        for i, flag in enumerate(flag_lines):
            if i < len(flag_lines) - 1:
                lines.append(f"  {flag} \\")
            else:
                lines.append(f"  {flag}")

        lines.append("")
        return "\n".join(lines)