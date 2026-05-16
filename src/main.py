"""PipeRDC main application entry point."""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gio
from src.ui.window import PipeRDCWindow


class PipeRDCApplication(Adw.Application):
    """PipeRDC GTK Application."""

    def __init__(self):
        super().__init__(
            application_id="com.piperdc.app",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.window = None

    def do_activate(self):
        """Called when the application is activated."""
        if not self.window:
            self.window = PipeRDCWindow(application=self)
        self.window.present()

    def do_shutdown(self):
        """Clean up on shutdown."""
        if self.window:
            self.window.cleanup()
        Adw.Application.do_shutdown(self)

    def do_startup(self):
        """Called when the application starts."""
        Adw.Application.do_startup(self)
        # Set up dark mode preference
        self.get_style_manager().set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)


def main() -> int:
    """Main entry point."""
    settings = Gtk.Settings.get_default()
    if settings is not None and settings.find_property("gtk-application-prefer-dark-theme"):
        settings.set_property("gtk-application-prefer-dark-theme", False)
    app = PipeRDCApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())