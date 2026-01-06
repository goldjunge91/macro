import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import re
from settings_window import SettingsWindow

# Modern Color Theme
THEME = {
    "bg": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_card": "#0f3460",
    "accent": "#00d4ff",
    "accent_hover": "#00b8e6",
    "success": "#00ff88",
    "warning": "#ff6b6b",
    "text": "#e4e4e4",
    "text_dim": "#a0a0a0",
    "border": "#2a2a4e",
    "font_main": ("Segoe UI", 10),
    "font_header": ("Segoe UI", 16, "bold"),
    "font_subheader": ("Segoe UI", 12, "bold"),
    "font_mono": ("Consolas", 9),
}


class ModernButton(tk.Button):
    """Modern styled button with hover effects"""

    def __init__(self, master, **kwargs):
        style = kwargs.pop("style", "primary")
        super().__init__(master, **kwargs)

        if style == "primary":
            bg_color = THEME["accent"]
            hover_color = THEME["accent_hover"]
            fg_color = THEME["bg"]
        elif style == "success":
            bg_color = THEME["success"]
            hover_color = "#00e67a"
            fg_color = THEME["bg"]
        elif style == "danger":
            bg_color = THEME["warning"]
            hover_color = "#ff5252"
            fg_color = "white"
        else:
            bg_color = THEME["bg_card"]
            hover_color = THEME["border"]
            fg_color = THEME["text"]

        self.bg_color = bg_color
        self.hover_color = hover_color

        self.config(
            bg=bg_color,
            fg=fg_color,
            activebackground=hover_color,
            activeforeground=fg_color,
            font=THEME["font_main"],
            bd=0,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
        )

        self.bind("<Enter>", lambda e: self.config(bg=self.hover_color))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_color))


class Overlay(tk.Toplevel):
    """Status overlay window"""

    def __init__(self, master, state, save_config):
        super().__init__(master)
        self.state = state
        self.save_config = save_config
        self.overrideredirect(True)
        self.attributes("-topmost", True, "-alpha", 0.92)
        self.config(bg=THEME["bg_secondary"])

        container = tk.Frame(self, bg=THEME["bg_secondary"], padx=15, pady=10)
        container.pack(fill="both", expand=True)

        self.lbl_status = tk.Label(
            container,
            text="● ONLINE",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["bg_secondary"],
            fg=THEME["success"],
        )
        self.lbl_status.pack(anchor="w")

        self.lbl_macro = tk.Label(
            container,
            text="",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["bg_secondary"],
            fg=THEME["warning"],
        )
        self.lbl_macro.pack(anchor="w")

        self.geometry(
            f"160x60+{state['config']['overlay_x']}+{state['config']['overlay_y']}"
        )
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        self.bind("<ButtonRelease-1>", self.stop_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = self.winfo_x() + (event.x - self.x)
        y = self.winfo_y() + (event.y - self.y)
        self.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        self.state["config"]["overlay_x"] = self.winfo_x()
        self.state["config"]["overlay_y"] = self.winfo_y()
        self.save_config()


def update_overlay(state):
    """Update overlay text and visibility"""
    if not state["overlay_ref"] or not state["overlay_ref"].winfo_exists():
        return
    ov = state["overlay_ref"]
    if state["config"]["overlay_enabled"]:
        ov.deiconify()
        ov.lbl_status.config(
            text="● OFFLINE" if state["is_lagging"] else "● ONLINE",
            fg=THEME["warning"] if state["is_lagging"] else THEME["success"],
        )
        macro_text = (
            "▶ RUNNING"
            if state["is_running_macro"]
            else (
                "■ DISABLED" if not state["config"].get("macro_enabled", True) else ""
            )
        )
        ov.lbl_macro.config(
            text=macro_text,
            fg=THEME["text_dim"] if macro_text == "■ DISABLED" else THEME["accent"],
        )
    else:
        ov.withdraw()


class App(tk.Tk):
    """Main application window"""

    def __init__(self, state, save_config, get_active_network_interfaces):
        super().__init__()
        self.state = state
        self.save_config_func = save_config
        self.get_active_network_interfaces = get_active_network_interfaces

        self.title("Macro Controller")
        self.geometry("400x800")
        self.configure(bg=THEME["bg"])
        self.attributes("-topmost", True)

        # Configure combobox style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Modern.TCombobox",
            fieldbackground=THEME["bg_card"],
            background=THEME["bg_card"],
            foreground=THEME["text"],
            bordercolor=THEME["border"],
            arrowcolor=THEME["accent"],
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", THEME["bg_card"])],
            selectbackground=[("readonly", THEME["accent"])],
            selectforeground=[("readonly", THEME["bg"])],
        )

        # Scrollable canvas
        self.canvas = tk.Canvas(self, bg=THEME["bg"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
            bg=THEME["bg_secondary"],
            troughcolor=THEME["bg"],
            activebackground=THEME["accent"],
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=THEME["bg"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self._on_configure(),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Header
        header_frame = tk.Frame(self.scrollable_frame, bg=THEME["bg"])
        header_frame.pack(pady=(25, 5), fill="x", padx=25)

        title_label = tk.Label(
            header_frame,
            text="Macro Controller",
            font=THEME["font_header"],
            bg=THEME["bg"],
            fg=THEME["accent"],
        )
        title_label.pack(side="left")

        settings_btn = tk.Button(
            header_frame,
            text="⚙",
            font=("Segoe UI", 18),
            bg=THEME["bg"],
            fg=THEME["accent"],
            bd=0,
            cursor="hand2",
            command=self.open_settings,
            activebackground=THEME["bg"],
            activeforeground=THEME["accent_hover"],
        )
        settings_btn.pack(side="right", padx=5)

        subtitle = tk.Label(
            self.scrollable_frame,
            text="Configure and control your macros",
            font=("Segoe UI", 9),
            bg=THEME["bg"],
            fg=THEME["text_dim"],
        )
        subtitle.pack(pady=(0, 20), padx=25)

        self.frame = tk.Frame(self.scrollable_frame, bg=THEME["bg"])
        self.frame.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        self.build_ui()
        self.state["overlay_ref"] = Overlay(self, self.state, self.save_config_func)
        update_overlay(self.state)

    def _on_configure(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Hide scrollbar if content fits
        if self.canvas.bbox("all")[3] <= self.canvas.winfo_height():
            self.scrollbar.pack_forget()
        else:
            self.scrollbar.pack(side="right", fill="y")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def open_settings(self):
        SettingsWindow(self, self.state, self.save_config_func)

    def build_ui(self):
        keys = (
            [chr(i) for i in range(97, 123)]
            + [str(i) for i in range(10)]
            + [f"Key.f{i}" for i in range(1, 13)]
        )
        clumsy_keys = [chr(i) for i in range(97, 123)] + [str(i) for i in range(10)]

        def create_card(title, icon=""):
            card = tk.Frame(self.frame, bg=THEME["bg_card"], padx=18, pady=15)
            card.pack(fill="x", pady=(0, 15))

            header = tk.Frame(card, bg=THEME["bg_card"])
            header.pack(fill="x", pady=(0, 12))

            if icon:
                tk.Label(
                    header,
                    text=icon,
                    font=("Segoe UI", 14),
                    bg=THEME["bg_card"],
                    fg=THEME["accent"],
                ).pack(side="left", padx=(0, 10))

            tk.Label(
                header,
                text=title,
                font=THEME["font_subheader"],
                bg=THEME["bg_card"],
                fg=THEME["text"],
            ).pack(side="left")

            return card

        def add_label(parent, text):
            tk.Label(
                parent,
                text=text,
                bg=THEME["bg_card"],
                fg=THEME["text"],
                font=THEME["font_main"],
                anchor="w",
            ).pack(fill="x", pady=(8, 3))

        def add_combobox(parent, values, default):
            cb = ttk.Combobox(
                parent,
                values=values,
                font=THEME["font_mono"],
                style="Modern.TCombobox",
                state="readonly",
            )
            cb.set(default)
            cb.pack(fill="x", pady=(0, 8))
            return cb

        # Network Card
        net_card = create_card("Network Configuration", "🌐")

        add_label(net_card, "Network Method")
        self.cb_net_method = add_combobox(
            net_card,
            ["netsh", "Clumsy"],
            self.state["config"].get("network_method", "netsh"),
        )
        self.cb_net_method.bind("<<ComboboxSelected>>", self.on_method_change)

        self.frame_netsh = tk.Frame(net_card, bg=THEME["bg_card"])
        self.frame_clumsy = tk.Frame(net_card, bg=THEME["bg_card"])

        add_label(self.frame_netsh, "Network Interface")
        active_interfaces = self.get_active_network_interfaces()
        interface_values = []
        for iface in active_interfaces:
            interface_values.append(f"{iface['name']} ({iface['type']})")

        if not interface_values:
            interface_values = ["No active interfaces detected"]

        self.cb_iface = add_combobox(self.frame_netsh, interface_values, "")

        current_iface = self.state["config"].get("net_interface", "")
        current_type = self.state["config"].get("net_interface_type", "Unknown")

        selected = False
        if current_iface:
            for iface_display in interface_values:
                if current_iface in iface_display:
                    self.cb_iface.set(iface_display)
                    selected = True
                    break

        if not selected:
            if (
                interface_values
                and interface_values[0] != "No active interfaces detected"
            ):
                self.cb_iface.set(interface_values[0])
            elif current_iface:
                self.cb_iface.set(f"{current_iface} ({current_type})")

        self.btn_refresh = ModernButton(
            self.frame_netsh,
            text="↻ Refresh Interfaces",
            command=self.refresh_interfaces,
            style="secondary",
        )
        self.btn_refresh.pack(fill="x", pady=(8, 0))

        add_label(self.frame_clumsy, "Clumsy Hotkey")
        self.cb_clumsy_key = add_combobox(
            self.frame_clumsy,
            clumsy_keys,
            self.state["config"].get("clumsy_hotkey", "8"),
        )

        self.update_method_display()

        # Timeline Macro Card
        macro_card = create_card("Timeline Macro", "⚡")

        add_label(macro_card, "Trigger Key")
        self.cb_trig = add_combobox(
            macro_card, keys, self.state["config"]["key_macro_trigger"]
        )
        self.cb_trig.bind("<<ComboboxSelected>>", lambda e: self.save())

        add_label(macro_card, "Disconnect Timing")
        self.cb_disc_mode = add_combobox(
            macro_card,
            ["After Click Start", "Before Click Start"],
            self.state["config"].get("macro_disconnect_mode", "Before Click Start"),
        )
        self.cb_disc_mode.bind("<<ComboboxSelected>>", lambda e: self.save())

        add_label(macro_card, f"Clicks Per Second: {self.state['config']['click_cps']}")
        slider_frame = tk.Frame(macro_card, bg=THEME["bg_card"])
        slider_frame.pack(fill="x", pady=(0, 8))

        self.s_cps = tk.Scale(
            slider_frame,
            from_=1,
            to=30,
            orient="horizontal",
            bg=THEME["bg_card"],
            fg=THEME["text"],
            highlightthickness=0,
            troughcolor=THEME["bg_secondary"],
            activebackground=THEME["accent"],
            sliderrelief="flat",
            bd=0,
            command=lambda v: self.save(),
        )
        self.s_cps.set(self.state["config"]["click_cps"])
        self.s_cps.pack(fill="x")

        # Throw Macros Card
        throw_card = create_card("Throw Macros", "🎯")

        add_label(throw_card, "Throw V1 Trigger (pynput)")
        self.cb_throw_trig = add_combobox(
            throw_card, keys, self.state["config"]["key_throw_trigger"]
        )
        self.cb_throw_trig.bind("<<ComboboxSelected>>", lambda e: self.save())

        tk.Label(
            throw_card,
            text="Clumsy toggle → Drag → Tab → E-spam",
            bg=THEME["bg_card"],
            fg=THEME["text_dim"],
            font=("Segoe UI", 8),
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        add_label(throw_card, "Throw V2 Trigger (SendInput)")
        self.cb_throw_v2_trig = add_combobox(
            throw_card, keys, self.state["config"].get("key_throw_v2_trigger", "Key.f7")
        )
        self.cb_throw_v2_trig.bind("<<ComboboxSelected>>", lambda e: self.save())

        tk.Label(
            throw_card,
            text="Robust input • Same sequence as V1",
            bg=THEME["bg_card"],
            fg=THEME["text_dim"],
            font=("Segoe UI", 8),
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        # Recording Card
        recording_card = create_card("Recording", "⏺")

        add_label(recording_card, "Record Trigger")
        self.cb_record_trig = add_combobox(
            recording_card, keys, self.state["config"]["key_record_trigger"]
        )
        self.cb_record_trig.bind("<<ComboboxSelected>>", lambda e: self.save())

        add_label(recording_card, "Playback Trigger")
        self.cb_playback_trig = add_combobox(
            recording_card, keys, self.state["config"]["key_playback_trigger"]
        )
        self.cb_playback_trig.bind("<<ComboboxSelected>>", lambda e: self.save())

        tk.Label(
            recording_card,
            text="Press RECORD to start/stop • Press PLAYBACK to replay",
            bg=THEME["bg_card"],
            fg=THEME["text_dim"],
            font=("Segoe UI", 8),
            justify="left",
        ).pack(anchor="w")

        # Control Card
        control_card = create_card("Controls", "🎮")

        self.btn_macro = ModernButton(
            control_card,
            text="✓ Macro Enabled",
            command=self.toggle_macro,
            style="success",
        )
        self.btn_macro.pack(fill="x", pady=3)

        self.btn_throw = ModernButton(
            control_card,
            text="✓ Throw Enabled",
            command=self.toggle_throw,
            style="success",
        )
        self.btn_throw.pack(fill="x", pady=3)

        self.btn_recording = ModernButton(
            control_card,
            text="✓ Recording Enabled",
            command=self.toggle_recording,
            style="success",
        )
        self.btn_recording.pack(fill="x", pady=3)

        self.btn_ov = ModernButton(
            control_card,
            text="✓ Overlay Enabled",
            command=self.toggle_ov,
            style="success",
        )
        self.btn_ov.pack(fill="x", pady=3)

        ModernButton(
            control_card,
            text="↻ Reload Application",
            command=lambda: os.execv(sys.executable, [sys.executable] + sys.argv),
            style="danger",
        ).pack(fill="x", pady=(12, 3))

    def save(self):
        c = self.state["config"]
        c["key_macro_trigger"] = self.cb_trig.get()
        c["macro_disconnect_mode"] = self.cb_disc_mode.get()
        c["click_cps"] = self.s_cps.get()
        c["network_method"] = self.cb_net_method.get()
        c["clumsy_hotkey"] = self.cb_clumsy_key.get()

        iface_selection = self.cb_iface.get()
        if iface_selection and iface_selection != "No active interfaces detected":
            match = re.match(r"^(.+?)\s*\((.+?)\)$", iface_selection)
            if match:
                c["net_interface"] = match.group(1).strip()
                c["net_interface_type"] = match.group(2).strip()
            else:
                c["net_interface"] = iface_selection
                c["net_interface_type"] = "Unknown"

        c["key_throw_trigger"] = self.cb_throw_trig.get()
        c["key_throw_v2_trigger"] = self.cb_throw_v2_trig.get()
        c["key_record_trigger"] = self.cb_record_trig.get()
        c["key_playback_trigger"] = self.cb_playback_trig.get()

        self.save_config_func()
        # Settings auto-save on every change, so no popup needed

    def refresh_interfaces(self):
        """Refresh the list of active network interfaces"""
        active_interfaces = self.get_active_network_interfaces()
        interface_values = []
        for iface in active_interfaces:
            interface_values.append(f"{iface['name']} ({iface['type']})")

        if not interface_values:
            interface_values = ["No active interfaces detected"]

        self.cb_iface["values"] = interface_values
        if interface_values and interface_values[0] != "No active interfaces detected":
            self.cb_iface.set(interface_values[0])

        messagebox.showinfo(
            "Refresh", f"Found {len(active_interfaces)} active interface(s)"
        )

    def update_method_display(self):
        """Show/hide interface or clumsy settings based on selected method"""
        method = self.cb_net_method.get()

        self.frame_netsh.pack_forget()
        self.frame_clumsy.pack_forget()

        if method == "Clumsy":
            self.frame_clumsy.pack(fill="x", pady=(0, 8))
        else:
            self.frame_netsh.pack(fill="x", pady=(0, 8))

    def on_method_change(self, event=None):
        """Handle network method change"""
        self.update_method_display()

    def toggle_macro(self):
        self.state["config"]["macro_enabled"] = not self.state["config"].get(
            "macro_enabled", True
        )
        enabled = self.state["config"]["macro_enabled"]
        self.btn_macro.config(
            text="✓ Macro Enabled" if enabled else "✗ Macro Disabled",
        )
        self.btn_macro.bg_color = THEME["success"] if enabled else THEME["warning"]
        self.btn_macro.hover_color = "#00e67a" if enabled else "#ff5252"
        self.btn_macro.config(bg=self.btn_macro.bg_color)
        update_overlay(self.state)
        self.save_config_func()

    def toggle_throw(self):
        self.state["config"]["throw_enabled"] = not self.state["config"].get(
            "throw_enabled", True
        )
        enabled = self.state["config"]["throw_enabled"]
        self.btn_throw.config(
            text="✓ Throw Enabled" if enabled else "✗ Throw Disabled",
        )
        self.btn_throw.bg_color = THEME["success"] if enabled else THEME["warning"]
        self.btn_throw.hover_color = "#00e67a" if enabled else "#ff5252"
        self.btn_throw.config(bg=self.btn_throw.bg_color)
        self.save_config_func()

    def toggle_recording(self):
        self.state["config"]["recording_enabled"] = not self.state["config"].get(
            "recording_enabled", True
        )
        enabled = self.state["config"]["recording_enabled"]
        self.btn_recording.config(
            text="✓ Recording Enabled" if enabled else "✗ Recording Disabled",
        )
        self.btn_recording.bg_color = THEME["success"] if enabled else THEME["warning"]
        self.btn_recording.hover_color = "#00e67a" if enabled else "#ff5252"
        self.btn_recording.config(bg=self.btn_recording.bg_color)
        self.save_config_func()

    def toggle_ov(self):
        self.state["config"]["overlay_enabled"] = not self.state["config"][
            "overlay_enabled"
        ]
        enabled = self.state["config"]["overlay_enabled"]
        self.btn_ov.config(
            text="✓ Overlay Enabled" if enabled else "✗ Overlay Disabled",
        )
        self.btn_ov.bg_color = THEME["success"] if enabled else THEME["warning"]
        self.btn_ov.hover_color = "#00e67a" if enabled else "#ff5252"
        self.btn_ov.config(bg=self.btn_ov.bg_color)
        update_overlay(self.state)
        self.save_config_func()
