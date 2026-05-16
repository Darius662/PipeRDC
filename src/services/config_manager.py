"""Configuration management for PipeRDC."""

import json
import os
import shutil
from pathlib import Path
from typing import Optional
from src.models.connection import RDPConnection


CONFIG_DIR = Path.home() / ".config" / "piperdc"
CONFIG_FILE = CONFIG_DIR / "connections.json"
SCRIPTS_DIR = CONFIG_DIR / "scripts"


def ensure_dirs():
    """Create config directories if they don't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


def load_connections() -> dict[str, RDPConnection]:
    """Load all connections from config file."""
    ensure_dirs()
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

    connections = {}
    for conn_id, conn_data in data.items():
        try:
            connections[conn_id] = RDPConnection.from_dict(conn_data, conn_id)
        except (KeyError, TypeError):
            continue
    return connections


def save_connections(connections: dict[str, RDPConnection]):
    """Save all connections to config file."""
    ensure_dirs()
    data = {}
    for conn_id, conn in connections.items():
        data[conn_id] = conn.to_dict()

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_script(connection: RDPConnection) -> Path:
    """Generate and save a shell script for this connection."""
    ensure_dirs()
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in connection.name)
    safe_name = safe_name.strip().replace(" ", "_")
    script_path = SCRIPTS_DIR / f"{safe_name}.sh"

    script_content = connection.generate_script()
    with open(script_path, "w") as f:
        f.write(script_content)

    # Make executable
    os.chmod(script_path, 0o755)
    return script_path


def delete_connection_script(connection: RDPConnection):
    """Delete the saved script for a connection."""
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in connection.name)
    safe_name = safe_name.strip().replace(" ", "_")
    script_path = SCRIPTS_DIR / f"{safe_name}.sh"
    if script_path.exists():
        script_path.unlink()