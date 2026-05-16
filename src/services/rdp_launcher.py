"""RDP session launcher - spawns xfreerdp3 as a subprocess."""

import subprocess
import signal
import os
from typing import Optional
from gi.repository import GLib

from src.models.connection import RDPConnection


class RDPSession:
    """Represents a running RDP session."""

    def __init__(self, connection: RDPConnection, process: subprocess.Popen):
        self.connection = connection
        self.process = process
        self._watch_id: Optional[int] = None

    @property
    def is_running(self) -> bool:
        """Check if the process is still running."""
        return self.process.poll() is None

    def terminate(self):
        """Terminate the RDP session gracefully."""
        if self.is_running:
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class RDPLauncher:
    """Manages launching and tracking RDP sessions."""

    def __init__(self):
        self.sessions: list[RDPSession] = []

    def launch(self, connection: RDPConnection) -> Optional[RDPSession]:
        """
        Launch an RDP connection using xfreerdp3.
        Returns an RDPSession or None if launch failed.
        """
        args = connection.build_xfreerdp_args()

        # Check if client exists
        client_path = connection.client
        if not os.path.exists(client_path) and not any(
            os.access(f"{p}/{client_path}", os.X_OK)
            for p in os.environ.get("PATH", "").split(":")
            if os.path.exists(f"{p}/{client_path}")
        ):
            # Try without path resolution - subprocess will handle it
            pass

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            session = RDPSession(connection, process)
            self.sessions.append(session)
            return session
        except FileNotFoundError:
            raise RuntimeError(
                f"Could not find '{connection.client}'. "
                f"Please install FreeRDP: sudo apt install freerdp3 (Debian) "
                f"or sudo pacman -S freerdp (Arch)"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to launch RDP session: {e}")

    def launch_script(self, script_path: str) -> Optional[subprocess.Popen]:
        """Launch a saved script file."""
        try:
            process = subprocess.Popen(
                [script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return process
        except Exception as e:
            raise RuntimeError(f"Failed to launch script: {e}")

    def close_session(self, session: RDPSession):
        """Close and remove a session."""
        session.terminate()
        if session in self.sessions:
            self.sessions.remove(session)

    def close_all(self):
        """Terminate all active sessions."""
        for session in self.sessions[:]:
            self.close_session(session)