import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import re

THEME = {
    "bg": "#0a0a0a",
    "fg": "#00ff41",
    "warning": "#ff3333",
    "font_main": ("Consolas", 10),
    "font_header": ("Consolas", 14, "bold"),
    "font_mono": ("Consolas", 9),
}


class HackerButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg="black",
            fg=THEME["fg"],
            activebackground=THEME["fg"],
            activeforeground="black",
            font=THEME["font_main"],
            bd=1,
            relief="solid",
        )


class Overlay(tk.Toplevel):
    def __init__(self, master, state, save_config):
        super().__init__(master)
        self.state = state
        self.save_config = save_config
        self.overrideredirect(True)
        self.attributes("-topmost", True, "-alpha", 0.85)
        self.config(bg="black")
        self.lbl_status = tk.Label(
            self,
            text="NET: ONLINE",
            font=("Consolas", 10, "bold"),
            bg="black",
            fg=THEME["fg"],
        )
        self.lbl_status.pack(anchor="w")
        self.lbl_macro = tk.Label(
            self,
            text="",
            font=("Consolas", 10, "bold"),
            bg="black",
            fg=THEME["warning"],
        )
        self.lbl_macro.pack(anchor="w")
        self.geometry(
            f"150x50+{state['config']['overlay_x']}+{state['config']['overlay_y']}"
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
    if not state["overlay_ref"] or not state["overlay_ref"].winfo_exists():
        return
    ov = state["overlay_ref"]
    if state["config"]["overlay_enabled"]:
        ov.deiconify()
        ov.lbl_status.config(
            text="NET: OFFLINE" if state["is_lagging"] else "NET: ONLINE",
            fg=THEME["warning"] if state["is_lagging"] else THEME["fg"],
        )
        macro_text = (
            "MACRO: RUNNING"
            if state["is_running_macro"]
            else (
                "MACRO: OFF" if not state["config"].get("macro_enabled", True) else ""
            )
        )
        ov.lbl_macro.config(
            text=macro_text,
            fg="#888" if macro_text == "MACRO: OFF" else THEME["warning"],
        )
    else:
        ov.withdraw()


class App(tk.Tk):
    def __init__(self, state, save_config, get_active_network_interfaces):
        super().__init__()
        self.state = state
        self.save_config_func = save_config
        self.get_active_network_interfaces = get_active_network_interfaces

        self.title("MACRO CONTROLLER")
        self.geometry("300x950")
        self.configure(bg=THEME["bg"])
        self.attributes("-topmost", True)

        self.canvas = tk.Canvas(self, bg=THEME["bg"], highlightthickness=0)
        self.scrollbar = tk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=THEME["bg"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        tk.Label(
            self.scrollable_frame,
            text="[ TIMELINE MACRO ]",
            font=THEME["font_header"],
            bg=THEME["bg"],
            fg=THEME["fg"],
        ).pack(pady=(20, 10))

        self.frame = tk.Frame(self.scrollable_frame, bg=THEME["bg"])
        self.frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.build_ui()
        self.state["overlay_ref"] = Overlay(self, self.state, self.save_config_func)
        update_overlay(self.state)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def build_ui(self):
        keys = (
            [chr(i) for i in range(97, 123)]
            + [str(i) for i in range(10)]
            + [f"Key.f{i}" for i in range(1, 13)]
        )
        clumsy_keys = [chr(i) for i in range(97, 123)] + [str(i) for i in range(10)]

        def add_section(txt):
            tk.Label(
                self.frame,
                text=txt,
                bg=THEME["bg"],
                fg="#888",
                font=("Consolas", 9, "bold"),
            ).pack(anchor="w", pady=(10, 2), padx=0)

        def add_entry(txt, key):
            f = tk.Frame(self.frame, bg=THEME["bg"])
            f.pack(fill="x", pady=2, padx=0)
            tk.Label(
                f, text=txt, bg=THEME["bg"], fg="white", width=18, anchor="w"
            ).pack(side="left")
            e = tk.Entry(f, bg="#222", fg="white", font=THEME["font_mono"])
            e.insert(0, str(self.state["config"].get(key, "")))
            e.pack(side="left", fill="x", expand=True)
            return e

        tk.Label(
            self.frame,
            text="NETWORK METHOD:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", padx=0)
        self.cb_net_method = ttk.Combobox(
            self.frame, values=["netsh", "Clumsy"], font=THEME["font_mono"]
        )
        self.cb_net_method.set(self.state["config"].get("network_method", "netsh"))
        self.cb_net_method.pack(fill="x", pady=2, padx=0)
        self.cb_net_method.bind("<<ComboboxSelected>>", self.on_method_change)

        self.frame_netsh = tk.Frame(self.frame, bg=THEME["bg"])
        self.frame_clumsy = tk.Frame(self.frame, bg=THEME["bg"])

        self.lbl_iface = tk.Label(
            self.frame_netsh,
            text="NETWORK INTERFACE:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        )
        self.lbl_iface.pack(anchor="w", padx=0)

        active_interfaces = self.get_active_network_interfaces()
        interface_values = []
        for iface in active_interfaces:
            interface_values.append(f"{iface['name']} ({iface['type']})")

        if not interface_values:
            interface_values = ["No active interfaces detected"]

        self.cb_iface = ttk.Combobox(
            self.frame_netsh,
            values=interface_values,
            font=THEME["font_mono"],
            state="readonly",
        )

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

        self.cb_iface.pack(fill="x", pady=2, padx=0)

        self.btn_refresh = HackerButton(
            self.frame_netsh,
            text="REFRESH INTERFACES",
            command=self.refresh_interfaces,
            bg="#003333",
        )
        self.btn_refresh.pack(fill="x", pady=2, padx=0)

        self.lbl_clumsy = tk.Label(
            self.frame_clumsy,
            text="CLUMSY HOTKEY:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        )
        self.lbl_clumsy.pack(anchor="w", padx=0)
        self.cb_clumsy_key = ttk.Combobox(
            self.frame_clumsy, values=clumsy_keys, font=THEME["font_mono"]
        )
        self.cb_clumsy_key.set(self.state["config"].get("clumsy_hotkey", "8"))
        self.cb_clumsy_key.pack(fill="x", pady=2, padx=0)

        self.update_method_display()

        tk.Label(
            self.frame,
            text="TRIGGER KEY:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0), padx=0)
        self.cb_trig = ttk.Combobox(self.frame, values=keys, font=THEME["font_mono"])
        self.cb_trig.set(self.state["config"]["key_macro_trigger"])
        self.cb_trig.pack(fill="x", pady=2, padx=0)

        tk.Label(
            self.frame,
            text="DISCONNECT TIMING:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0), padx=0)
        self.cb_disc_mode = ttk.Combobox(
            self.frame,
            values=["After Click Start", "Before Click Start"],
            font=THEME["font_mono"],
        )
        self.cb_disc_mode.set(
            self.state["config"].get("macro_disconnect_mode", "Before Click Start")
        )
        self.cb_disc_mode.pack(fill="x", pady=2, padx=0)

        tk.Label(
            self.frame,
            text="CLICKS PER SECOND (CPS):",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0), padx=0)
        self.s_cps = tk.Scale(
            self.frame,
            from_=1,
            to=30,
            orient="horizontal",
            bg=THEME["bg"],
            fg="white",
            highlightthickness=0,
            troughcolor="#222",
        )
        self.s_cps.set(self.state["config"]["click_cps"])
        self.s_cps.pack(fill="x", padx=0)

        add_section("--- 1. HOLD CLICK ---")
        self.e_h_st = add_entry("Start Delay (s):", "macro_hold_start")
        self.e_h_ln = add_entry("Duration (s):", "macro_hold_len")

        add_section("--- 2. NETWORK ---")
        self.e_n_st = add_entry("Start Delay (s):", "macro_net_start")
        self.e_n_ln = add_entry("Offline Time (s):", "macro_net_len")

        add_section("--- 3. SPAM CLICK ---")
        self.e_s_st = add_entry("Start Delay (s):", "macro_spam_start")
        self.e_s_ln = add_entry("Duration (s):", "macro_spam_len")

        add_section("--- THROW MACRO SETTINGS ---")
        tk.Label(
            self.frame,
            text="THROW TRIGGER KEY:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0), padx=0)
        self.cb_throw_trig = ttk.Combobox(
            self.frame, values=keys, font=THEME["font_mono"]
        )
        self.cb_throw_trig.set(self.state["config"]["key_throw_trigger"])
        self.cb_throw_trig.pack(fill="x", pady=2, padx=0)

        tk.Label(
            self.frame,
            text="Fixed sequence: <3s total\nClumsy toggle → Drag → Tab → E-spam",
            bg=THEME["bg"],
            fg="#888",
            font=("Consolas", 8),
            justify="left",
        ).pack(anchor="w", pady=2, padx=0)

        add_section("--- RECORDING SETTINGS ---")
        tk.Label(
            self.frame,
            text="RECORD TRIGGER KEY:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0), padx=0)
        self.cb_record_trig = ttk.Combobox(
            self.frame, values=keys, font=THEME["font_mono"]
        )
        self.cb_record_trig.set(self.state["config"]["key_record_trigger"])
        self.cb_record_trig.pack(fill="x", pady=2, padx=0)

        tk.Label(
            self.frame,
            text="PLAYBACK TRIGGER KEY:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(5, 0), padx=0)
        self.cb_playback_trig = ttk.Combobox(
            self.frame, values=keys, font=THEME["font_mono"]
        )
        self.cb_playback_trig.set(self.state["config"]["key_playback_trigger"])
        self.cb_playback_trig.pack(fill="x", pady=2, padx=0)

        tk.Label(
            self.frame,
            text="Press RECORD key to start/stop recording\nPress PLAYBACK key to replay",
            bg=THEME["bg"],
            fg="#888",
            font=("Consolas", 8),
            justify="left",
        ).pack(anchor="w", pady=2, padx=0)

        f_btn = tk.Frame(self.frame, bg=THEME["bg"])
        f_btn.pack(fill="x", pady=20, padx=0)
        self.btn_macro = HackerButton(
            f_btn, text="DISABLE MACRO", command=self.toggle_macro, bg="#003300"
        )
        self.btn_macro.pack(fill="x", pady=2, padx=0)
        self.btn_throw = HackerButton(
            f_btn, text="DISABLE THROW", command=self.toggle_throw, bg="#003300"
        )
        self.btn_throw.pack(fill="x", pady=2, padx=0)
        self.btn_recording = HackerButton(
            f_btn, text="DISABLE RECORDING", command=self.toggle_recording, bg="#003300"
        )
        self.btn_recording.pack(fill="x", pady=2, padx=0)
        HackerButton(f_btn, text="SAVE SETTINGS", command=self.save).pack(
            fill="x", pady=2, padx=0
        )
        self.btn_ov = HackerButton(
            f_btn, text="DISABLE OVERLAY", command=self.toggle_ov
        )
        self.btn_ov.pack(fill="x", pady=2, padx=0)
        HackerButton(
            f_btn,
            text="RELOAD TOOL",
            command=lambda: os.execv(sys.executable, [sys.executable] + sys.argv),
            bg="#330000",
        ).pack(fill="x", pady=2, padx=0)

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

        try:
            c["macro_hold_start"] = float(self.e_h_st.get())
            c["macro_hold_len"] = float(self.e_h_ln.get())
            c["macro_net_start"] = float(self.e_n_st.get())
            c["macro_net_len"] = float(self.e_n_ln.get())
            c["macro_spam_start"] = float(self.e_s_st.get())
            c["macro_spam_len"] = float(self.e_s_ln.get())

            c["key_throw_trigger"] = self.cb_throw_trig.get()

            c["key_record_trigger"] = self.cb_record_trig.get()
            c["key_playback_trigger"] = self.cb_playback_trig.get()
        except Exception:
            pass
        self.save_config_func()
        messagebox.showinfo("Saved", "Settings Updated!")

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
            self.frame_clumsy.pack(after=self.cb_net_method, fill="x", pady=2)
        else:
            self.frame_netsh.pack(after=self.cb_net_method, fill="x", pady=2)

    def on_method_change(self, event=None):
        """Handle network method change"""
        self.update_method_display()

    def toggle_macro(self):
        self.state["config"]["macro_enabled"] = not self.state["config"].get(
            "macro_enabled", True
        )
        enabled = self.state["config"]["macro_enabled"]
        self.btn_macro.config(
            text="DISABLE MACRO" if enabled else "ENABLE MACRO",
            bg="#003300" if enabled else "#330000",
        )
        update_overlay(self.state)
        self.save_config_func()

    def toggle_throw(self):
        self.state["config"]["throw_enabled"] = not self.state["config"].get(
            "throw_enabled", True
        )
        enabled = self.state["config"]["throw_enabled"]
        self.btn_throw.config(
            text="DISABLE THROW" if enabled else "ENABLE THROW",
            bg="#003300" if enabled else "#330000",
        )
        self.save_config_func()

    def toggle_recording(self):
        self.state["config"]["recording_enabled"] = not self.state["config"].get(
            "recording_enabled", True
        )
        enabled = self.state["config"]["recording_enabled"]
        self.btn_recording.config(
            text="DISABLE RECORDING" if enabled else "ENABLE RECORDING",
            bg="#003300" if enabled else "#330000",
        )
        self.save_config_func()

    def toggle_ov(self):
        self.state["config"]["overlay_enabled"] = not self.state["config"][
            "overlay_enabled"
        ]
        self.btn_ov.config(
            text=(
                "DISABLE OVERLAY"
                if self.state["config"]["overlay_enabled"]
                else "ENABLE OVERLAY"
            )
        )
        update_overlay(self.state)
        self.save_config_func()
