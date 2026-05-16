"""Parser for Microsoft .rdp connection files."""

from pathlib import Path
from src.models.connection import RDPConnection


def parse_rdp_file(filepath: str) -> RDPConnection:
    """
    Parse a Microsoft .rdp file into an RDPConnection object.
    
    .rdp files are simple key=value text files.
    """
    conn = RDPConnection()
    path = Path(filepath)
    conn.name = path.stem

    if not path.exists():
        return conn

    try:
        content = path.read_text(encoding="utf-16-le")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        if ":" not in line:
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        _apply_rdp_setting(conn, key, value)

    return conn


def _apply_rdp_setting(conn: RDPConnection, key: str, value: str):
    """Apply a single .rdp setting to the connection."""
    try:
        if key == "full address":
            # Value can be "host:port" or just "host"
            if ":" in value:
                host, port = value.rsplit(":", 1)
                conn.host = host
                try:
                    conn.port = int(port)
                except ValueError:
                    conn.port = 3389
            else:
                conn.host = value
                conn.port = 3389

        elif key == "username":
            conn.username = value
        elif key == "domain":
            conn.domain = value
        elif key == "desktopwidth":
            try:
                conn.custom_width = int(value)
                if conn.resolution == "fullscreen":
                    conn.resolution = "custom"
            except ValueError:
                pass
        elif key == "desktopheight":
            try:
                conn.custom_height = int(value)
                if conn.resolution == "fullscreen":
                    conn.resolution = "custom"
            except ValueError:
                pass
        elif key == "session bpp":
            try:
                conn.bpp = int(value)
            except ValueError:
                pass
        elif key == "audiomode":
            # 0: redirect, 1: play, 2: none
            audio_map = {"0": "redirect", "1": "play", "2": "none"}
            conn.audio_mode = audio_map.get(value, "redirect")
        elif key == "redirectmicrophone":
            conn.enable_mic = value.lower() in ("1", "true", "on")
        elif key == "drivestoredirect":
            conn.enable_drive = bool(value.strip())
            if value.strip():
                conn.drive_path = f"home,{value}"
        elif key == "networkautodetect":
            if value.lower() in ("1", "true", "on"):
                conn.network_type = "auto"
        elif key == "use multimon":
            conn.use_multimon = value.lower() in ("1", "true", "on")
        elif key == "selectedmonitors":
            conn.monitors = value

    except (ValueError, TypeError):
        pass


def export_to_rdp(conn: RDPConnection) -> str:
    """Export a connection to .rdp file format."""
    lines = [
        "screen mode id:i:2",
        f"full address:s:{conn.host}:{conn.port}",
    ]

    if conn.username:
        lines.append(f"username:s:{conn.username}")
    if conn.domain:
        lines.append(f"domain:s:{conn.domain}")

    lines.append(f"session bpp:i:{conn.bpp}")
    lines.append(f"desktopwidth:i:{conn.custom_width}")
    lines.append(f"desktopheight:i:{conn.custom_height}")

    audio_map = {"redirect": "0", "play": "1", "record": "0", "none": "2"}
    lines.append(f"audiomode:i:{audio_map.get(conn.audio_mode, '0')}")

    if conn.enable_mic:
        lines.append("redirectmicrophone:i:1")

    if conn.use_multimon:
        lines.append("use multimon:i:1")
        lines.append(f"selectedmonitors:s:{conn.monitors}")

    lines.append("networkautodetect:i:1")
    lines.append("autoreconnection enabled:i:1")

    return "\r\n".join(lines)