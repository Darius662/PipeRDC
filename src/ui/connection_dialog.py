"""Connection add/edit dialog for PipeRDC."""

from gi.repository import Gtk, Adw, GLib, GObject


class ConnectionDialog(Adw.Dialog):
    """Dialog for adding or editing an RDP connection."""

    def __init__(self, parent, connection=None, connection_id=None):
        super().__init__()
        self.set_title("Edit Connection" if connection else "New Connection")
        self.set_content_width(600)
        self.set_content_height(700)

        self.parent = parent
        self.connection = connection
        self.connection_id = connection_id
        self.saved_connection = None

        self._build_ui()

        if connection:
            self._populate_from_connection(connection)

    def _build_ui(self):
        """Build the dialog UI."""
        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        # Save button
        save_btn = Gtk.Button(label="Save", css_classes=["suggested-action"])
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)

        # Cancel button
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_btn)

        # Main content
        clamp = Adw.Clamp()
        clamp.set_maximum_size(500)
        toolbar_view.set_content(clamp)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        clamp.set_child(box)

        # --- General Section ---
        group1 = Adw.PreferencesGroup(title="General")
        box.append(group1)

        self.entry_name = self._add_entry_row(group1, "Name", "My Windows VM")
        self.entry_host = self._add_entry_row(group1, "Host", "10.10.0.66")
        self.spin_port = self._add_spin_row(group1, "Port", 3389, 1, 65535)
        self.entry_group = self._add_entry_row(group1, "Group", "Servers")

        # --- Authentication Section ---
        group2 = Adw.PreferencesGroup(title="Authentication")
        box.append(group2)

        self.entry_username = self._add_entry_row(group2, "Username", "admin")
        self.entry_password = self._add_password_row(group2, "Password")
        self.entry_domain = self._add_entry_row(group2, "Domain", "")

        # --- Display Section ---
        group3 = Adw.PreferencesGroup(title="Display")
        box.append(group3)

        self.combo_resolution = self._add_combo_row(
            group3, "Resolution",
            ["fullscreen", "widescreen", "quadhd", "ultrahd", "custom"]
        )
        self.spin_width = self._add_spin_row(group3, "Custom Width", 1920, 640, 7680)
        self.spin_height = self._add_spin_row(group3, "Custom Height", 1080, 480, 4320)
        self.switch_multimon = self._add_switch_row(group3, "Multi-monitor")
        self.entry_monitors = self._add_entry_row(group3, "Monitors", "0,1,2")

        # --- Audio Section ---
        group4 = Adw.PreferencesGroup(title="Audio & Devices")
        box.append(group4)

        self.combo_audio = self._add_combo_row(
            group4, "Audio Mode",
            ["redirect", "play", "record", "none"]
        )
        self.switch_mic = self._add_switch_row(group4, "Enable Microphone")
        self.switch_drive = self._add_switch_row(group4, "Enable Drive Redirection", default_active=True)
        self.entry_drive_path = self._add_entry_row(group4, "Drive Path", "home,$HOME")

        # --- Performance Section ---
        group5 = Adw.PreferencesGroup(title="Performance")
        box.append(group5)

        self.spin_bpp = self._add_spin_row(group5, "Color Depth (bpp)", 32, 8, 32, step=8)
        self.combo_network = self._add_combo_row(
            group5, "Network Type",
            ["auto", "modem", "broadband", "wan"]
        )
        self.switch_gfx = self._add_switch_row(group5, "Use GFX Acceleration", default_active=True)
        self.switch_h264 = self._add_switch_row(group5, "Use H264 Codec", default_active=True)
        self.switch_floatbar = self._add_switch_row(group5, "Show Floatbar", default_active=True)

        # --- Advanced Section ---
        group6 = Adw.PreferencesGroup(title="Advanced")
        box.append(group6)

        self.entry_flags = self._add_entry_row(group6, "Additional Flags", "")
        self.entry_client = self._add_entry_row(group6, "Client Path", "xfreerdp3")

    def _add_entry_row(self, group, title, placeholder=""):
        """Add an entry row to a preferences group."""
        row = Adw.EntryRow(title=title)
        row.set_placeholder_text(placeholder)
        group.add(row)
        return row

    def _add_password_row(self, group, title):
        """Add a password entry row."""
        row = Adw.PasswordEntryRow(title=title)
        group.add(row)
        return row

    def _add_spin_row(self, group, title, value, min_val, max_val, step=1):
        """Add a spin button row."""
        row = Adw.SpinRow.new_with_range(min_val, max_val, step)
        row.set_title(title)
        row.set_value(value)
        group.add(row)
        return row

    def _add_switch_row(self, group, title, default_active=False):
        """Add a switch row."""
        row = Adw.SwitchRow(title=title)
        row.set_active(default_active)
        group.add(row)
        return row

    def _add_combo_row(self, group, title, options):
        """Add a combo row."""
        row = Adw.ComboRow(title=title)
        model = Gtk.StringList.new(options)
        row.set_model(model)
        row.set_selected(0)
        group.add(row)
        return row

    def _populate_from_connection(self, conn):
        """Populate dialog fields from an existing connection."""
        self.entry_name.set_text(conn.name)
        self.entry_host.set_text(conn.host)
        self.spin_port.set_value(conn.port)
        self.entry_group.set_text(conn.group)
        self.entry_username.set_text(conn.username)
        if conn.password:
            self.entry_password.set_text(conn.password)
        self.entry_domain.set_text(conn.domain)

        res_options = ["fullscreen", "widescreen", "quadhd", "ultrahd", "custom"]
        if conn.resolution in res_options:
            self.combo_resolution.set_selected(res_options.index(conn.resolution))

        self.spin_width.set_value(conn.custom_width)
        self.spin_height.set_value(conn.custom_height)
        self.switch_multimon.set_active(conn.use_multimon)
        self.entry_monitors.set_text(conn.monitors)

        audio_options = ["redirect", "play", "record", "none"]
        if conn.audio_mode in audio_options:
            self.combo_audio.set_selected(audio_options.index(conn.audio_mode))

        self.switch_mic.set_active(conn.enable_mic)
        self.switch_drive.set_active(conn.enable_drive)
        self.entry_drive_path.set_text(conn.drive_path)

        self.spin_bpp.set_value(conn.bpp)
        net_options = ["auto", "modem", "broadband", "wan"]
        if conn.network_type in net_options:
            self.combo_network.set_selected(net_options.index(conn.network_type))

        self.switch_gfx.set_active(conn.use_gfx)
        self.switch_h264.set_active(conn.use_h264)
        self.switch_floatbar.set_active(conn.floatbar)
        self.entry_flags.set_text(conn.additional_flags)
        self.entry_client.set_text(conn.client)

    def _on_save(self, button):
        """Handle save button click."""
        from src.models.connection import RDPConnection

        name = self.entry_name.get_text().strip()
        host = self.entry_host.get_text().strip()

        if not name:
            self.entry_name.add_css_class("error")
            return
        if not host:
            self.entry_host.add_css_class("error")
            return

        res_options = ["fullscreen", "widescreen", "quadhd", "ultrahd", "custom"]
        audio_options = ["redirect", "play", "record", "none"]
        net_options = ["auto", "modem", "broadband", "wan"]

        conn = RDPConnection(
            id=self.connection_id or "",
            name=name,
            host=host,
            port=int(self.spin_port.get_value()),
            group=self.entry_group.get_text().strip(),
            username=self.entry_username.get_text().strip(),
            password=self.entry_password.get_text(),
            domain=self.entry_domain.get_text().strip(),
            resolution=res_options[self.combo_resolution.get_selected()],
            custom_width=int(self.spin_width.get_value()),
            custom_height=int(self.spin_height.get_value()),
            use_multimon=self.switch_multimon.get_active(),
            monitors=self.entry_monitors.get_text().strip(),
            audio_mode=audio_options[self.combo_audio.get_selected()],
            enable_mic=self.switch_mic.get_active(),
            enable_drive=self.switch_drive.get_active(),
            drive_path=self.entry_drive_path.get_text().strip(),
            bpp=int(self.spin_bpp.get_value()),
            network_type=net_options[self.combo_network.get_selected()],
            use_gfx=self.switch_gfx.get_active(),
            use_h264=self.switch_h264.get_active(),
            floatbar=self.switch_floatbar.get_active(),
            additional_flags=self.entry_flags.get_text().strip(),
            client=self.entry_client.get_text().strip(),
        )

        self.saved_connection = conn
        self.close()