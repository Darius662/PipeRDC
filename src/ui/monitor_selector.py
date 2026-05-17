"""Monitor selection widget for RDP multi-monitor settings."""

from gi.repository import Gtk, Adw, Gdk


class MonitorSelectionWidget(Gtk.Box):
    """A selectable monitor chooser built from the local display configuration."""

    def __init__(self, title: str = "Select Monitors"):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_hexpand(True)

        title_label = Gtk.Label(label=title, xalign=0)
        title_label.add_css_class("title")
        self.append(title_label)

        self._monitor_box = Gtk.FlowBox()
        self._monitor_box.set_row_spacing(8)
        self._monitor_box.set_column_spacing(8)
        self._monitor_box.set_min_children_per_line(1)
        self._monitor_box.set_max_children_per_line(4)
        self._monitor_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.append(self._monitor_box)

        self._summary_label = Gtk.Label(label="", xalign=0)
        self._summary_label.add_css_class("dim-label")
        self.append(self._summary_label)

        self._fallback_entry = Adw.EntryRow(title="Monitor IDs")
        self._fallback_entry.set_visible(False)
        self.append(self._fallback_entry)

        self._buttons: list[Gtk.ToggleButton] = []
        self._build_monitor_buttons()
        self._update_summary()

    def _build_monitor_buttons(self):
        display = Gdk.Display.get_default()
        if display is None:
            self._fallback_entry.set_visible(True)
            return

        monitors = display.get_monitors()
        if not monitors:
            self._fallback_entry.set_visible(True)
            return

        monitor_infos = []
        for index, monitor in enumerate(monitors):
            geometry = monitor.get_geometry()
            monitor_infos.append({
                "index": index,
                "monitor": monitor,
                "geometry": geometry,
            })

        monitor_infos.sort(key=lambda info: (info["geometry"].x, info["geometry"].y))

        for info in monitor_infos:
            index = info["index"]
            monitor = info["monitor"]
            geometry = info["geometry"]
            label = monitor.get_model() or f"Monitor {index}"
            manufacturer = monitor.get_manufacturer()
            info_text = f"{geometry.width}×{geometry.height} @ {geometry.x},{geometry.y}"
            if manufacturer:
                label = f"{manufacturer} {label}".strip()

            button = Gtk.ToggleButton()
            button.add_css_class("flat")
            button.add_css_class("action")
            button.set_tooltip_text(f"Use monitor {index}")
            button.set_child(self._build_button_content(label, info_text))
            button._monitor_index = index
            button._geometry = geometry
            button.connect("toggled", self._on_monitor_toggled)
            self._monitor_box.append(button)
            self._buttons.append(button)

    def _build_button_content(self, title, subtitle):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.set_wrap(True)
        subtitle_label = Gtk.Label(label=subtitle, xalign=0)
        subtitle_label.add_css_class("dim-label")
        box.append(title_label)
        box.append(subtitle_label)
        return box

    def _on_monitor_toggled(self, button):
        self._update_summary()

    def _selected_monitor_infos(self):
        selected = []
        for button in self._buttons:
            if not button.get_active():
                continue
            index = getattr(button, "_monitor_index", None)
            geometry = getattr(button, "_geometry", None)
            if index is None or geometry is None:
                continue
            selected.append({"index": index, "geometry": geometry})
        return sorted(selected, key=lambda info: (info["geometry"].x, info["geometry"].y))

    def _has_monitor_gaps(self):
        selected = self._selected_monitor_infos()
        if len(selected) < 2:
            return False

        last_geometry = selected[0]["geometry"]
        for info in selected[1:]:
            geometry = info["geometry"]
            if geometry.x > last_geometry.x + last_geometry.width:
                return True
            last_geometry = geometry
        return False

    def _update_summary(self):
        ids = self.get_selected_ids()
        if self._fallback_entry.get_visible():
            self._summary_label.set_text("Enter monitor IDs manually if monitor detection is unavailable.")
        elif self._has_monitor_gaps():
            self._summary_label.set_text(
                "Selected monitors contain gaps and may be rejected by FreeRDP. "
                "Clear or reselect a contiguous monitor group."
            )
        elif ids:
            self._summary_label.set_text(f"Selected monitors: {ids}")
        else:
            self._summary_label.set_text("No monitors selected.")

    def get_selected_ids_safe(self):
        if self._fallback_entry.get_visible():
            return self.get_selected_ids()
        return "" if self._has_monitor_gaps() else self.get_selected_ids()

    def set_selected_ids(self, ids):
        if self._fallback_entry.get_visible():
            self._fallback_entry.set_text(ids or "")
            self._update_summary()
            return

        selected = self._normalize_ids(ids)
        for button in self._buttons:
            index = getattr(button, "_monitor_index", None)
            button.set_active(index in selected)
        self._update_summary()

    def get_selected_ids(self):
        if self._fallback_entry.get_visible():
            selected = self._normalize_ids(self._fallback_entry.get_text())
            return ",".join(str(i) for i in selected)

        selected = [str(getattr(button, "_monitor_index", ""))
                    for button in self._buttons if button.get_active()]
        if not selected and self._buttons:
            selected = [str(getattr(button, "_monitor_index", "")) for button in self._buttons]
        return ",".join(selected)

    @staticmethod
    def _normalize_ids(ids):
        if ids is None:
            return []
        if isinstance(ids, str):
            ids = ids.split(",")
        selected = []
        for value in ids:
            try:
                selected.append(int(str(value).strip()))
            except (TypeError, ValueError):
                continue
        return sorted(set(selected))
