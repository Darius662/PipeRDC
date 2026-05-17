"""Main application window for PipeRDC - Windows RDC style with tabs."""

import os
import subprocess
from pathlib import Path
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, Pango

from src.ui.monitor_selector import MonitorSelectionWidget
from src.models.connection import RDPConnection
from src.services.config_manager import (
    load_connections, save_connections, save_script, delete_connection_script,
    SCRIPTS_DIR
)
from src.services.credential_manager import CredentialManager
from src.services.rdp_launcher import RDPLauncher, RDPSession


class SettingsTab:
    """Holds references to all settings widgets for a connection."""

    def __init__(self):
        # General
        self.entry_name = None
        self.entry_host = None
        self.spin_port = None
        self.entry_username = None
        self.entry_password = None
        self.entry_domain = None

        # Display
        self.combo_resolution = None
        self.spin_width = None
        self.spin_height = None
        self.switch_multimon = None
        self.entry_monitors = None
        self.monitors_selector = None
        self.spin_bpp = None

        # Security
        self.combo_cert = None
        self.entry_cert_name = None
        self.entry_cert_fingerprint = None
        self.combo_sec_protocol = None
        self.entry_encryption = None
        self.switch_auth_only = None
        self.entry_pth = None
        self.switch_no_encrypt = None
        self.switch_no_nego = None

        # Devices
        self.switch_clipboard = None
        self.combo_clipboard_dir = None
        self.switch_mic = None
        self.switch_drive = None
        self.entry_drive = None
        self.entry_printer = None
        self.entry_printer_driver = None
        self.switch_smartcard = None
        self.entry_smartcard = None
        self.switch_usb = None
        self.entry_usb = None
        self.entry_serial = None
        self.entry_parallel = None
        self.switch_grab_kbd = None
        self.switch_grab_mouse = None
        self.combo_audio = None
        self.switch_floatbar = None

        # Experience
        self.combo_network = None
        self.switch_gfx = None
        self.switch_h264 = None

        # Advanced
        self.entry_flags = None
        self.entry_client = None


class PipeRDCWindow(Adw.ApplicationWindow):
    """Main window of PipeRDC - Windows RDC style with tabs."""

    def __init__(self, application):
        super().__init__(application=application)
        self.set_title("PipeRDC - Remote Desktop Connection")
        self.set_default_size(950, 700)
        self.set_resizable(True)

        self.connections: dict[str, RDPConnection] = {}
        self.filtered_connections: dict[str, RDPConnection] = {}
        self.credential_manager = CredentialManager()
        self.launcher = RDPLauncher()
        self._search_text = ""
        self._selected_conn_id = None
        self._settings = SettingsTab()

        self._build_ui()
        self._load_connections()

    def _build_ui(self):
        """Build the main window UI."""
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(main_vbox)

        header = Adw.HeaderBar()
        main_vbox.append(header)
        header.set_title_widget(Gtk.Label(label="PipeRDC - Remote Desktop Connection"))

        menu_model = Gio.Menu()
        menu_model.append("Export All Scripts", "win.export_scripts")
        menu_model.append("About PipeRDC", "win.about")
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_menu_model(menu_model)
        header.pack_end(menu_btn)
        self._setup_actions()
        self._load_css()

        # === Quick Connect Bar ===
        qc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6,
                         margin_start=12, margin_end=12, margin_top=8, margin_bottom=4)
        main_vbox.append(qc_box)
        qc_box.append(Gtk.Label(label="Computer:"))
        self.qc_host = Gtk.Entry(placeholder_text="10.10.0.66:3389", hexpand=True)
        self.qc_host.connect("activate", self._on_quick_connect)
        qc_box.append(self.qc_host)
        qc_btn = Gtk.Button(label="Connect")
        qc_btn.add_css_class("suggested-action")
        qc_btn.connect("clicked", self._on_quick_connect)
        qc_box.append(qc_btn)
        self.qc_options_btn = Gtk.Button(label="Show Options ∨")
        self.qc_options_btn.connect("clicked", self._on_toggle_qc)
        qc_box.append(self.qc_options_btn)

        self.qc_revealer = Gtk.Revealer()
        self.qc_revealer.set_reveal_child(False)
        main_vbox.append(self.qc_revealer)
        qc_opts = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6,
                          margin_start=12, margin_end=12, margin_top=2, margin_bottom=2)
        self.qc_revealer.set_child(qc_opts)
        qc_opts.append(Gtk.Label(label="User:"))
        self.qc_user = Gtk.Entry(placeholder_text="admin", width_chars=12)
        qc_opts.append(self.qc_user)
        qc_opts.append(Gtk.Label(label="Pass:"))
        self.qc_pass = Gtk.Entry(placeholder_text="password", visibility=False, width_chars=12)
        qc_opts.append(self.qc_pass)
        qc_opts.append(Gtk.Label(label="Resolution:"))
        self.qc_res = Gtk.ComboBoxText()
        for val, lbl in [("fullscreen", "Fullscreen"), ("widescreen", "1920x1080"),
                         ("quadhd", "2560x1440"), ("ultrahd", "3840x2160")]:
            self.qc_res.append(val, lbl)
        self.qc_res.set_active_id("fullscreen")
        qc_opts.append(self.qc_res)

        # === Main Content: HSplit ===
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=True)
        main_vbox.append(hpaned)

        # Left: Connection List
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        left_box.set_size_request(250, -1)
        search_new_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4,
                                 margin_start=6, margin_end=6, margin_top=6)
        left_box.append(search_new_box)
        self.search_entry = Gtk.SearchEntry(placeholder_text="Search...", hexpand=True)
        self.search_entry.connect("search-changed", self._on_search)
        search_new_box.append(self.search_entry)
        new_btn = Gtk.Button(label="+")
        new_btn.set_tooltip_text("New Connection")
        new_btn.connect("clicked", self._on_new_connection)
        search_new_box.append(new_btn)

        self.conn_list = Gtk.ListBox(css_classes=["boxed-list"], selection_mode=Gtk.SelectionMode.SINGLE)
        self.conn_list.connect("row-activated", self._on_connect_double)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(self.conn_list)
        left_box.append(scroll)
        hpaned.set_start_child(left_box)

        # Right: Tabbed Settings
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hpaned.set_end_child(right_box)
        hpaned.set_position(280)

        self.empty_page = Adw.StatusPage(
            title="Select a connection",
            description="Choose a connection from the list or use Quick Connect above.",
            icon_name="network-server-symbolic", vexpand=True,
        )
        # Tab bar + tab view
        self.tab_bar = Adw.TabBar()
        self.tab_view = Adw.TabView()
        self.tab_view.set_vexpand(True)
        self.tab_bar.set_view(self.tab_view)

        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tab_box.append(self.tab_bar)
        tab_box.append(self.tab_view)

        right_box.append(self.empty_page)
        right_box.append(tab_box)
        self.empty_page.set_visible(True)
        tab_box.set_visible(False)
        self._tab_box = tab_box

        self._build_tabs()

    def _load_css(self):
        css = b"""
        button.tab-close-button {
            opacity: 0;
            min-width: 0;
            min-height: 0;
            padding: 0;
            margin: 0;
            border: none;
            background: transparent;
        }
        button.tab-close-button image {
            opacity: 0;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _setup_actions(self):
        actions = [
            ("export_scripts", self._on_export_all_scripts),
            ("about", self._on_about),
        ]
        for name, callback in actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

    def _build_tabs(self):
        """Build all settings tabs, each wrapped in a scrolled window."""
        tabs = [
            ("General", self._build_general_tab),
            ("Display", self._build_display_tab),
            ("Security", self._build_security_tab),
            ("Devices", self._build_devices_tab),
            ("Experience", self._build_experience_tab),
            ("Advanced", self._build_advanced_tab),
        ]
        for title, builder in tabs:
            # Wrap each tab in a ScrolledWindow so content scrolls instead of stretching
            content = builder()
            scroll = Gtk.ScrolledWindow()
            scroll.set_child(content)
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            page = self.tab_view.add_page(scroll)
            page.set_title(title)

    def _make_group(self, title):
        return Adw.PreferencesGroup(title=title)

    def _add_entry(self, group, title):
        row = Adw.EntryRow(title=title)
        group.add(row)
        return row

    def _add_password(self, group, title):
        row = Adw.PasswordEntryRow(title=title)
        group.add(row)
        return row

    def _add_spin(self, group, title, val, min_v, max_v, step=1):
        row = Adw.SpinRow.new_with_range(min_v, max_v, step)
        row.set_title(title)
        row.set_value(val)
        group.add(row)
        return row

    def _add_switch(self, group, title, default=False):
        row = Adw.SwitchRow(title=title)
        row.set_active(default)
        group.add(row)
        return row

    def _add_combo(self, group, title, options):
        row = Adw.ComboRow(title=title)
        model = Gtk.StringList.new(options)
        row.set_model(model)
        row.set_selected(0)
        group.add(row)
        return row

    def _add_monitor_selector(self, group, title):
        selector = MonitorSelectionWidget(title=title)
        group.add(selector)
        return selector

    # ---- Tab Builders ----

    def _build_general_tab(self):
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        clamp.set_child(box)

        g = self._make_group("Connection Settings")
        box.append(g)
        s = self._settings
        s.entry_name = self._add_entry(g, "Name")
        s.entry_host = self._add_entry(g, "Computer")
        s.spin_port = self._add_spin(g, "Port", 3389, 1, 65535)
        s.entry_username = self._add_entry(g, "Username")
        s.entry_password = self._add_password(g, "Password")
        s.entry_domain = self._add_entry(g, "Domain")

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                          margin_top=12, homogeneous=True)
        box.append(btn_box)
        save_btn = Gtk.Button(label="Save Connection")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save_settings)
        btn_box.append(save_btn)
        connect_btn = Gtk.Button(label="Connect")
        connect_btn.connect("clicked", self._on_connect_from_tab)
        btn_box.append(connect_btn)
        delete_btn = Gtk.Button(label="Delete")
        delete_btn.add_css_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete_selected)
        btn_box.append(delete_btn)

        return clamp

    def _build_display_tab(self):
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        clamp.set_child(box)

        g = self._make_group("Display Settings")
        box.append(g)
        s = self._settings
        s.combo_resolution = self._add_combo(g, "Resolution",
            ["fullscreen", "widescreen (1920x1080)", "quadhd (2560x1440)",
             "ultrahd (3840x2160)", "custom"])
        s.spin_width = self._add_spin(g, "Custom Width", 1920, 640, 7680)
        s.spin_height = self._add_spin(g, "Custom Height", 1080, 480, 4320)
        s.switch_multimon = self._add_switch(g, "Use Multiple Monitors")
        s.monitors_selector = self._add_monitor_selector(g, "Select Monitors")
        s.switch_multimon.connect(
            "notify::active",
            lambda switch, ps: s.monitors_selector.set_sensitive(switch.get_active()),
        )

        g2 = self._make_group("Color")
        box.append(g2)
        s.spin_bpp = self._add_spin(g2, "Color Depth (bpp)", 32, 8, 32, step=8)

        return clamp

    def _build_security_tab(self):
        """Security tab: Certificate, protocol, encryption."""
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        clamp.set_child(box)

        s = self._settings

        g1 = self._make_group("Certificate Verification")
        box.append(g1)
        s.combo_cert = self._add_combo(g1, "Certificate Behavior",
            ["tofu (trust on first use)", "ignore", "deny", "name", "fingerprint"])
        s.entry_cert_name = self._add_entry(g1, "Expected Certificate Name")
        s.entry_cert_fingerprint = self._add_entry(g1, "Certificate Fingerprint")

        g2 = self._make_group("Authentication Protocol")
        box.append(g2)
        s.combo_sec_protocol = self._add_combo(g2, "Security Protocol",
            ["nla (NLA/credSSP)", "tls (TLS)", "rdp (RDP)", "ext (Extended)", "aad (Azure AD)"])
        s.entry_encryption = self._add_entry(g2, "Encryption Methods")
        s.switch_auth_only = self._add_switch(g2, "Authentication Only (no session)")
        s.entry_pth = self._add_entry(g2, "Pass-the-Hash")

        g3 = self._make_group("Advanced Security")
        box.append(g3)
        s.switch_no_encrypt = self._add_switch(g3, "Disable Encryption (experimental)")
        s.switch_no_nego = self._add_switch(g3, "Disable Protocol Negotiation")

        return clamp

    def _build_devices_tab(self):
        """Devices tab: Clipboard, audio, drives, printers, USB, etc."""
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        clamp.set_child(box)

        s = self._settings

        g1 = self._make_group("Clipboard")
        box.append(g1)
        s.switch_clipboard = self._add_switch(g1, "Enable Clipboard Redirection", default=True)
        s.combo_clipboard_dir = self._add_combo(g1, "Clipboard Direction",
            ["both", "to client only", "from client only"])

        g2 = self._make_group("Audio")
        box.append(g2)
        s.combo_audio = self._add_combo(g2, "Audio Mode", ["redirect", "play", "record", "none"])
        s.switch_mic = self._add_switch(g2, "Redirect Microphone")

        g3 = self._make_group("Drives")
        box.append(g3)
        s.switch_drive = self._add_switch(g3, "Enable Drive Redirection", default=True)
        s.entry_drive = self._add_entry(g3, "Drive Path")

        g4 = self._make_group("Printers")
        box.append(g4)
        s.entry_printer = self._add_entry(g4, "Printer Name")
        s.entry_printer_driver = self._add_entry(g4, "Printer Driver")

        g5 = self._make_group("Other Devices")
        box.append(g5)
        s.switch_smartcard = self._add_switch(g5, "Redirect Smartcard")
        s.entry_smartcard = self._add_entry(g5, "Smartcard Filter")
        s.switch_usb = self._add_switch(g5, "Redirect USB Devices")
        s.entry_usb = self._add_entry(g5, "USB Filter (vid:pid)")
        s.entry_serial = self._add_entry(g5, "Serial Device")
        s.entry_parallel = self._add_entry(g5, "Parallel Device")

        g6 = self._make_group("Input")
        box.append(g6)
        s.switch_grab_kbd = self._add_switch(g6, "Grab Keyboard", default=True)
        s.switch_grab_mouse = self._add_switch(g6, "Grab Mouse", default=True)

        g7 = self._make_group("Interface")
        box.append(g7)
        s.switch_floatbar = self._add_switch(g7, "Show Floating Toolbar", default=True)

        return clamp

    def _build_experience_tab(self):
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        clamp.set_child(box)

        g = self._make_group("Performance")
        box.append(g)
        s = self._settings
        s.combo_network = self._add_combo(g, "Network Type", ["auto", "modem", "broadband", "wan"])
        s.switch_gfx = self._add_switch(g, "Use GFX Acceleration", default=True)
        s.switch_h264 = self._add_switch(g, "Use H264 Codec", default=True)

        return clamp

    def _build_advanced_tab(self):
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        clamp.set_child(box)

        g = self._make_group("Advanced")
        box.append(g)
        s = self._settings
        s.entry_flags = self._add_entry(g, "Additional FreeRDP Flags")
        s.entry_client = self._add_entry(g, "Client Executable")

        g2 = self._make_group("Script Export")
        box.append(g2)
        script_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, margin_top=8)
        g2.add(script_btn_box)
        export_btn = Gtk.Button(label="Export .sh Script")
        export_btn.connect("clicked", self._on_export_script)
        script_btn_box.append(export_btn)
        edit_btn = Gtk.Button(label="Edit Script in Editor")
        edit_btn.connect("clicked", self._on_edit_script)
        script_btn_box.append(edit_btn)
        run_btn = Gtk.Button(label="Run Script")
        run_btn.add_css_class("suggested-action")
        run_btn.connect("clicked", self._on_run_script)
        script_btn_box.append(run_btn)

        self.script_buffer = Gtk.TextBuffer()
        self.script_view = Gtk.TextView(
            buffer=self.script_buffer, editable=False, monospace=True,
            wrap_mode=Gtk.WrapMode.WORD, height_request=200,
        )
        self.script_view.add_css_class("monospace")
        script_scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True, margin_top=8)
        script_scroll.set_child(self.script_view)
        g2.add(script_scroll)

        return clamp

    # --- Quick Connect ---

    def _on_toggle_qc(self, btn):
        reveal = not self.qc_revealer.get_reveal_child()
        self.qc_revealer.set_reveal_child(reveal)
        btn.set_label("Show Options ∧" if reveal else "Show Options ∨")

    def _on_quick_connect(self, widget):
        text = self.qc_host.get_text().strip()
        if not text:
            return
        host = text
        port = 3389
        if ":" in text:
            host, ps = text.rsplit(":", 1)
            try: port = int(ps)
            except ValueError: pass

        conn = RDPConnection(
            name=host, host=host, port=port,
            username=self.qc_user.get_text().strip() if self.qc_revealer.get_reveal_child() else "",
            password=self.qc_pass.get_text() if self.qc_revealer.get_reveal_child() else "",
            resolution=self.qc_res.get_active_id() or "fullscreen",
            enable_drive=False, audio_mode="none", floatbar=True,
            use_gfx=False, use_h264=False, enable_clipboard=False,
        )
        try:
            self.launcher.launch(conn)
        except Exception as e:
            self._error_dialog(str(e))

    # --- Search ---

    def _on_search(self, entry):
        self._search_text = entry.get_text().strip().lower()
        self._apply_filter()

    def _apply_filter(self):
        self.filtered_connections = {}
        for cid, c in self.connections.items():
            if self._search_text:
                if self._search_text not in f"{c.name} {c.host} {c.group} {c.username}".lower():
                    continue
            self.filtered_connections[cid] = c
        self._refresh_list()

    def _refresh_list(self):
        for child in list(self.conn_list):
            self.conn_list.remove(child)
        for cid, c in self.filtered_connections.items():
            row = Adw.ActionRow(title=c.name, subtitle=f"{c.host}:{c.port}")
            row._conn = c; row._conn_id = cid
            btn = Gtk.Button(icon_name="media-playback-start-symbolic")
            btn.add_css_class("flat"); btn.set_tooltip_text("Connect")
            btn.connect("clicked", lambda b, co=c: self._connect(co))
            row.add_suffix(btn)
            click = Gtk.GestureClick()
            click.connect("pressed", self._on_row_click, cid)
            row.add_controller(click)
            menu_g = Gtk.GestureClick(button=Gdk.BUTTON_SECONDARY)
            menu_g.connect("pressed", self._on_row_right, cid)
            row.add_controller(menu_g)
            self.conn_list.append(row)

    def _on_row_click(self, g, n, x, y, cid):
        if n == 1: self._select_connection(cid)
        elif n == 2:
            conn = self.connections.get(cid)
            if conn: self._connect(conn)

    def _on_row_right(self, g, n, x, y, cid):
        p = Gtk.Popover()
        vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, margin_top=6, margin_bottom=6)
        def mkbtn(lbl, cb):
            b = Gtk.Button(label=lbl, css_classes=["flat", "menu-button"])
            b.connect("clicked", lambda x: self._pop_close(p, cb))
            vb.append(b); return b
        mkbtn("Duplicate", lambda: self._duplicate(cid))
        mkbtn("Delete", lambda: self._delete_confirm(cid))
        p.set_child(vb); p.set_parent(self); p.popup()

    def _pop_close(self, pop, cb): pop.popdown(); cb()

    def _on_connect_double(self, lb, row):
        conn = getattr(row, "_conn", None)
        if conn: self._connect(conn)

    # --- Select connection → populate tabs ---

    def _select_connection(self, cid):
        self._selected_conn_id = cid
        conn = self.connections.get(cid)
        if not conn: return

        self.empty_page.set_visible(False)
        self._tab_box.set_visible(True)

        s = self._settings
        # General
        s.entry_name.set_text(conn.name)
        s.entry_host.set_text(conn.host)
        s.spin_port.set_value(conn.port)
        s.entry_username.set_text(conn.username)
        if conn.password: s.entry_password.set_text(conn.password)
        s.entry_domain.set_text(conn.domain)

        # Display
        res_map = {"fullscreen": 0, "widescreen": 1, "quadhd": 2, "ultrahd": 3, "custom": 4}
        if conn.resolution in res_map: s.combo_resolution.set_selected(res_map[conn.resolution])
        s.spin_width.set_value(conn.custom_width)
        s.spin_height.set_value(conn.custom_height)
        s.switch_multimon.set_active(conn.use_multimon)
        if s.monitors_selector:
            s.monitors_selector.set_selected_ids(conn.monitors)
            s.monitors_selector.set_sensitive(conn.use_multimon)
        s.spin_bpp.set_value(conn.bpp)

        # Security
        cert_map = {"tofu": 0, "ignore": 1, "deny": 2, "name": 3, "fingerprint": 4}
        if conn.cert_behavior in cert_map: s.combo_cert.set_selected(cert_map[conn.cert_behavior])
        s.entry_cert_name.set_text(conn.cert_name)
        s.entry_cert_fingerprint.set_text(conn.cert_fingerprint)
        sec_map = {"nla": 0, "tls": 1, "rdp": 2, "ext": 3, "aad": 4}
        if conn.sec_protocol in sec_map: s.combo_sec_protocol.set_selected(sec_map[conn.sec_protocol])
        s.entry_encryption.set_text(conn.encryption_methods)
        s.switch_auth_only.set_active(conn.auth_only)
        s.entry_pth.set_text(conn.pass_the_hash)
        s.switch_no_encrypt.set_active(conn.disable_encryption)
        s.switch_no_nego.set_active(conn.disable_nego)

        # Devices
        s.switch_clipboard.set_active(conn.enable_clipboard)
        clip_map = {"both": 0, "to-client": 1, "from-client": 2}
        if conn.clipboard_direction in clip_map: s.combo_clipboard_dir.set_selected(clip_map[conn.clipboard_direction])
        audio_map = {"redirect": 0, "play": 1, "record": 2, "none": 3}
        if conn.audio_mode in audio_map: s.combo_audio.set_selected(audio_map[conn.audio_mode])
        s.switch_mic.set_active(conn.enable_mic)
        s.switch_drive.set_active(conn.enable_drive)
        s.entry_drive.set_text(conn.drive_path)
        s.entry_printer.set_text(conn.printer_name)
        s.entry_printer_driver.set_text(conn.printer_driver)
        s.switch_smartcard.set_active(conn.enable_smartcard)
        s.entry_smartcard.set_text(conn.smartcard_info)
        s.switch_usb.set_active(conn.enable_usb)
        s.entry_usb.set_text(conn.usb_filter)
        s.entry_serial.set_text(conn.serial_device)
        s.entry_parallel.set_text(conn.parallel_device)
        s.switch_grab_kbd.set_active(conn.grab_keyboard)
        s.switch_grab_mouse.set_active(conn.grab_mouse)
        s.switch_floatbar.set_active(conn.floatbar)

        # Experience
        net_map = {"auto": 0, "modem": 1, "broadband": 2, "wan": 3}
        if conn.network_type in net_map: s.combo_network.set_selected(net_map[conn.network_type])
        s.switch_gfx.set_active(conn.use_gfx)
        s.switch_h264.set_active(conn.use_h264)

        # Advanced
        s.entry_flags.set_text(conn.additional_flags)
        s.entry_client.set_text(conn.client)

        # Script preview
        script = conn.generate_script()
        self.script_buffer.set_text(script)
        self._saved_script_path = save_script(conn)

    # --- Read settings → connection ---

    def _read_settings(self) -> RDPConnection:
        s = self._settings
        res_ops = ["fullscreen", "widescreen", "quadhd", "ultrahd", "custom"]
        cert_ops = ["tofu", "ignore", "deny", "name", "fingerprint"]
        sec_ops = ["nla", "tls", "rdp", "ext", "aad"]
        clip_ops = ["both", "to-client", "from-client"]
        audio_ops = ["redirect", "play", "record", "none"]
        net_ops = ["auto", "modem", "broadband", "wan"]

        return RDPConnection(
            id=self._selected_conn_id or "",
            # General
            name=s.entry_name.get_text().strip(),
            host=s.entry_host.get_text().strip(),
            port=int(s.spin_port.get_value()),
            username=s.entry_username.get_text().strip(),
            password=s.entry_password.get_text(),
            domain=s.entry_domain.get_text().strip(),
            # Display
            resolution=res_ops[s.combo_resolution.get_selected()],
            custom_width=int(s.spin_width.get_value()),
            custom_height=int(s.spin_height.get_value()),
            use_multimon=s.switch_multimon.get_active(),
            monitors=(s.monitors_selector.get_selected_ids_safe() if s.monitors_selector
                      else s.entry_monitors.get_text().strip()),
            bpp=int(s.spin_bpp.get_value()),
            # Security
            cert_behavior=cert_ops[s.combo_cert.get_selected()],
            cert_name=s.entry_cert_name.get_text().strip(),
            cert_fingerprint=s.entry_cert_fingerprint.get_text().strip(),
            sec_protocol=sec_ops[s.combo_sec_protocol.get_selected()],
            encryption_methods=s.entry_encryption.get_text().strip(),
            auth_only=s.switch_auth_only.get_active(),
            pass_the_hash=s.entry_pth.get_text().strip(),
            disable_encryption=s.switch_no_encrypt.get_active(),
            disable_nego=s.switch_no_nego.get_active(),
            # Devices
            enable_clipboard=s.switch_clipboard.get_active(),
            clipboard_direction=clip_ops[s.combo_clipboard_dir.get_selected()],
            audio_mode=audio_ops[s.combo_audio.get_selected()],
            enable_mic=s.switch_mic.get_active(),
            enable_drive=s.switch_drive.get_active(),
            drive_path=s.entry_drive.get_text().strip(),
            printer_name=s.entry_printer.get_text().strip(),
            printer_driver=s.entry_printer_driver.get_text().strip(),
            enable_smartcard=s.switch_smartcard.get_active(),
            smartcard_info=s.entry_smartcard.get_text().strip(),
            enable_usb=s.switch_usb.get_active(),
            usb_filter=s.entry_usb.get_text().strip(),
            serial_device=s.entry_serial.get_text().strip(),
            parallel_device=s.entry_parallel.get_text().strip(),
            grab_keyboard=s.switch_grab_kbd.get_active(),
            grab_mouse=s.switch_grab_mouse.get_active(),
            floatbar=s.switch_floatbar.get_active(),
            # Experience
            network_type=net_ops[s.combo_network.get_selected()],
            use_gfx=s.switch_gfx.get_active(),
            use_h264=s.switch_h264.get_active(),
            # Advanced
            additional_flags=s.entry_flags.get_text().strip(),
            client=s.entry_client.get_text().strip(),
        )

    def _on_save_settings(self, btn):
        conn = self._read_settings()
        if not conn.name or not conn.host: return
        if self._selected_conn_id:
            self.connections[self._selected_conn_id] = conn
        else:
            self.connections[conn.id] = conn
            self._selected_conn_id = conn.id
        self._save_and_refresh()
        self._select_connection(self._selected_conn_id)

    def _on_connect_from_tab(self, btn):
        conn = self._read_settings()
        self._connect(conn)

    def _on_export_script(self, btn):
        if not self._selected_conn_id: return
        conn = self.connections.get(self._selected_conn_id)
        if not conn: return
        path = save_script(conn)
        self._send_toast(f"Script saved: {path}")

    def _on_edit_script(self, btn):
        if not self._selected_conn_id: return
        conn = self.connections.get(self._selected_conn_id)
        if not conn: return
        path = save_script(conn)
        editors = ["gedit", "xed", "kate", "code", "nano", "vim"]
        for e in editors:
            if subprocess.run(["which", e], capture_output=True).returncode == 0:
                subprocess.Popen([e, str(path)], start_new_session=True); return
        self._send_toast("No editor found")

    def _on_run_script(self, btn):
        if not self._selected_conn_id: return
        conn = self.connections.get(self._selected_conn_id)
        if not conn: return
        path = save_script(conn)
        if path.exists(): subprocess.Popen([str(path)], start_new_session=True)

    def _on_delete_selected(self, btn):
        if self._selected_conn_id: self._delete_confirm(self._selected_conn_id)

    def _on_new_connection(self, btn):
        conn = RDPConnection(name="New Connection", host="10.0.0.1")
        self.connections[conn.id] = conn
        self._save_and_refresh()
        self._select_connection(conn.id)

    def _duplicate(self, cid):
        if cid not in self.connections: return
        from copy import deepcopy
        orig = self.connections[cid]
        new = deepcopy(orig); new.id = ""; new.name = f"{orig.name} (Copy)"
        self.connections[new.id] = new
        self._save_and_refresh()

    def _delete_confirm(self, cid):
        if cid not in self.connections: return
        conn = self.connections[cid]
        d = Adw.MessageDialog(transient_for=self, heading=f"Delete '{conn.name}'?",
                              body="This will permanently delete this connection.", close_response="cancel")
        d.add_response("cancel", "Cancel"); d.add_response("delete", "Delete")
        d.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        def on_resp(dlg, resp):
            if resp == "delete":
                self.credential_manager.delete_password(cid)
                delete_connection_script(conn)
                del self.connections[cid]
                if self._selected_conn_id == cid:
                    self._selected_conn_id = None
                    self.empty_page.set_visible(True); self._tab_box.set_visible(False)
                self._save_and_refresh()
        d.connect("response", on_resp); d.present()

    def _connect(self, conn):
        """Connect by saving and executing the .sh script."""
        if conn.password:
            self.credential_manager.store_password(conn.id, conn.password)
            conn.password = self.credential_manager.get_password(conn.id) or conn.password
        try:
            script_path = save_script(conn)
            subprocess.Popen(["bash", str(script_path)], start_new_session=True)
            self._send_toast(f"Connecting to {conn.name}...")
        except Exception as e:
            self._error_dialog(f"Connection failed: {e}")

    def _error_dialog(self, msg):
        d = Adw.MessageDialog(transient_for=self, heading="Error", body=msg, close_response="ok")
        d.add_response("ok", "OK"); d.present()

    def _send_toast(self, msg):
        toast = Adw.Toast(title=msg, timeout=3)
        if hasattr(self, '_toast_overlay') and self._toast_overlay:
            self._toast_overlay.add_toast(toast)

    def _on_export_all_scripts(self, a, p):
        count = 0
        for conn in self.connections.values(): save_script(conn); count += 1
        self._send_toast(f"Exported {count} scripts")

    def _on_about(self, a, p):
        about = Adw.AboutDialog(
            application_name="PipeRDC", application_icon="network-server-symbolic",
            version="1.0.0", developer_name="PipeRDC Team",
            comments="A modern RDP Connection Manager for Linux",
            website="https://github.com/dariusjeleru/piperdc",
            license_type=Gtk.License.MIT_X11,
        )
        about.add_credit_section("Built with", ["Python", "GTK4", "LibAdwaita", "FreeRDP"])
        about.present(self)

    def _load_connections(self):
        self.connections = load_connections()
        for cid, c in self.connections.items():
            if not c.password:
                pw = self.credential_manager.get_password(cid)
                if pw: c.password = pw
        self._apply_filter()

    def _save_and_refresh(self):
        save_connections(self.connections)
        self._apply_filter()

    def cleanup(self):
        self.launcher.close_all()