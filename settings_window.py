import tkinter as tk
from tkinter import ttk, messagebox

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
    def __init__(self, master, **kwargs):
        style = kwargs.pop('style', 'primary')
        super().__init__(master, **kwargs)
        
        if style == 'primary':
            bg_color = THEME["accent"]
            hover_color = THEME["accent_hover"]
            fg_color = THEME["bg"]
        elif style == 'success':
            bg_color = THEME["success"]
            hover_color = "#00e67a"
            fg_color = THEME["bg"]
        elif style == 'danger':
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
            cursor="hand2"
        )
        
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_color))
        self.bind("<Leave>", lambda e: self.config(bg=self.bg_color))


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, state, save_config):
        super().__init__(master)
        self.state = state
        self.save_config_func = save_config
        
        self.title("Macro Settings")
        self.geometry("550x650")
        self.configure(bg=THEME["bg"])
        self.attributes("-topmost", True)
        
        # Header
        header = tk.Frame(self, bg=THEME["bg"])
        header.pack(fill="x", padx=25, pady=(20, 10))
        
        tk.Label(
            header,
            text="⚙ Macro Timings",
            font=THEME["font_header"],
            bg=THEME["bg"],
            fg=THEME["accent"],
        ).pack(side="left")
        
        tk.Label(
            self,
            text="Fine-tune timing parameters for your macros",
            font=("Segoe UI", 9),
            bg=THEME["bg"],
            fg=THEME["text_dim"],
        ).pack(padx=25, pady=(0, 15))
        
        # Configure notebook style
        style = ttk.Style()
        style.configure("Modern.TNotebook",
                       background=THEME["bg"],
                       borderwidth=0)
        style.configure("Modern.TNotebook.Tab",
                       background=THEME["bg_card"],
                       foreground=THEME["text"],
                       padding=[20, 10],
                       borderwidth=0)
        style.map("Modern.TNotebook.Tab",
                 background=[("selected", THEME["accent"])],
                 foreground=[("selected", THEME["bg"])])
        
        self.notebook = ttk.Notebook(self, style="Modern.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        self.create_timeline_tab()
        self.create_throw_tab()
        self.create_recording_tab()
        
        btn_frame = tk.Frame(self, bg=THEME["bg"])
        btn_frame.pack(fill="x", padx=25, pady=(0, 20))
        
        ModernButton(
            btn_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            style='success'
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        ModernButton(
            btn_frame,
            text="✗ Close",
            command=self.destroy,
            style='danger'
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))
    
    def create_timeline_tab(self):
        frame = tk.Frame(self.notebook, bg=THEME["bg_secondary"])
        self.notebook.add(frame, text="Timeline Macro")
        
        canvas = tk.Canvas(frame, bg=THEME["bg_secondary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview,
                                bg=THEME["bg_secondary"])
        scrollable = tk.Frame(canvas, bg=THEME["bg_secondary"])
        
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Hide scrollbar if content fits
            if canvas.bbox("all")[3] <= canvas.winfo_height():
                scrollbar.pack_forget()
            else:
                scrollbar.pack(side="right", fill="y")
        
        scrollable.bind("<Configure>", on_configure)
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        
        def add_section(txt):
            tk.Label(
                scrollable,
                text=txt,
                bg=THEME["bg_secondary"],
                fg=THEME["accent"],
                font=THEME["font_subheader"],
            ).pack(anchor="w", pady=(15, 5), padx=20)
        
        def add_entry(txt, key):
            f = tk.Frame(scrollable, bg=THEME["bg_secondary"])
            f.pack(fill="x", pady=5, padx=20)
            tk.Label(
                f, text=txt, bg=THEME["bg_secondary"], fg=THEME["text"],
                width=22, anchor="w", font=THEME["font_main"]
            ).pack(side="left")
            e = tk.Entry(f, bg=THEME["bg_card"], fg=THEME["text"],
                        font=THEME["font_mono"], bd=0, relief="flat",
                        insertbackground=THEME["accent"])
            e.insert(0, str(self.state["config"].get(key, "")))
            e.pack(side="left", fill="x", expand=True, ipady=5, ipadx=8)
            return e
        
        add_section("1. Hold Click")
        self.e_h_st = add_entry("Start Delay (s):", "macro_hold_start")
        self.e_h_ln = add_entry("Duration (s):", "macro_hold_len")
        
        add_section("2. Network")
        self.e_n_st = add_entry("Start Delay (s):", "macro_net_start")
        self.e_n_ln = add_entry("Offline Time (s):", "macro_net_len")
        
        add_section("3. Spam Click")
        self.e_s_st = add_entry("Start Delay (s):", "macro_spam_start")
        self.e_s_ln = add_entry("Duration (s):", "macro_spam_len")
    
    def create_throw_tab(self):
        frame = tk.Frame(self.notebook, bg=THEME["bg_secondary"])
        self.notebook.add(frame, text="Throw Macro")
        
        canvas = tk.Canvas(frame, bg=THEME["bg_secondary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview,
                                bg=THEME["bg_secondary"])
        scrollable = tk.Frame(canvas, bg=THEME["bg_secondary"])
        
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Hide scrollbar if content fits
            if canvas.bbox("all")[3] <= canvas.winfo_height():
                scrollbar.pack_forget()
            else:
                scrollbar.pack(side="right", fill="y")
        
        scrollable.bind("<Configure>", on_configure)
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        
        def add_section(txt):
            tk.Label(
                scrollable,
                text=txt,
                bg=THEME["bg_secondary"],
                fg=THEME["accent"],
                font=THEME["font_subheader"],
            ).pack(anchor="w", pady=(15, 5), padx=20)
        
        def add_entry(txt, key, default=0.0):
            f = tk.Frame(scrollable, bg=THEME["bg_secondary"])
            f.pack(fill="x", pady=5, padx=20)
            tk.Label(
                f, text=txt, bg=THEME["bg_secondary"], fg=THEME["text"],
                width=28, anchor="w", font=THEME["font_main"]
            ).pack(side="left")
            e = tk.Entry(f, bg=THEME["bg_card"], fg=THEME["text"],
                        font=THEME["font_mono"], bd=0, relief="flat",
                        insertbackground=THEME["accent"])
            e.insert(0, str(self.state["config"].get(key, default)))
            e.pack(side="left", fill="x", expand=True, ipady=5, ipadx=8)
            return e
        
        add_section("Timing Delays")
        self.e_throw_start_settle = add_entry("Start Settle Delay (s):", "throw_start_settle_delay", 0.03)
        self.e_throw_pre_drag = add_entry("Pre-Drag Delay (s):", "throw_pre_drag_delay", 0.06)
        self.e_throw_tab_delay = add_entry("Tab Delay After Drag (s):", "throw_tab_delay_after_drag", 0.3)
        self.e_throw_final_settle = add_entry("Final Settle Delay (s):", "throw_final_settle_delay", 0.05)
        self.e_throw_pre_spam = add_entry("Pre-Spam Delay (s):", "throw_pre_spam_delay", 0.0)
        self.e_throw_post_tab_spam = add_entry("Post-Tab to Spam Delay (s):", "throw_post_tab_to_spam_delay", 0.004)
        
        add_section("Tap Timing")
        self.e_throw_post_clumsy = add_entry("Post-Clumsy Tap Delay (s):", "throw_post_clumsy_tap_delay", 0.021)
        self.e_throw_post_tab = add_entry("Post-Tab Tap Delay (s):", "throw_post_tab_tap_delay", 0.021)
        self.e_throw_clumsy_deactivate = add_entry("Clumsy Deactivate After Spam (s):", "throw_clumsy_deactivate_after_spam", 0.20)
        
        add_section("Key Dwell Times")
        self.e_throw_tab_dwell = add_entry("Tab Dwell (s):", "throw_tab_dwell", 0.02)
        self.e_throw_e_dwell = add_entry("E Dwell (s):", "throw_e_dwell", 0.0389)
        
        add_section("Spam Settings")
        self.e_throw_spam_duration = add_entry("Spam Duration (s):", "throw_spam_duration", 2.25)
        self.e_throw_e_period = add_entry("E Period (s):", "throw_e_period", 0.0219)
        
        add_section("Drag Settings")
        self.e_throw_drag_time = add_entry("Drag Time (s):", "throw_drag_time", 0.5)
        self.e_throw_drag_pixels = add_entry("Drag Left Pixels:", "throw_drag_left_pixels", -2000)
    
    def create_recording_tab(self):
        frame = tk.Frame(self.notebook, bg=THEME["bg_secondary"])
        self.notebook.add(frame, text="Recording")
        
        container = tk.Frame(frame, bg=THEME["bg_secondary"])
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(
            container,
            text="⏺",
            font=("Segoe UI", 48),
            bg=THEME["bg_secondary"],
            fg=THEME["accent"]
        ).pack(pady=(0, 20))
        
        tk.Label(
            container,
            text="Recording Settings",
            font=THEME["font_subheader"],
            bg=THEME["bg_secondary"],
            fg=THEME["text"],
        ).pack()
        
        tk.Label(
            container,
            text="Recording settings are managed\nthrough the main interface.",
            bg=THEME["bg_secondary"],
            fg=THEME["text_dim"],
            font=THEME["font_main"],
            justify="center"
        ).pack(pady=(10, 0))
    
    def save_settings(self):
        c = self.state["config"]
        
        try:
            c["macro_hold_start"] = float(self.e_h_st.get())
            c["macro_hold_len"] = float(self.e_h_ln.get())
            c["macro_net_start"] = float(self.e_n_st.get())
            c["macro_net_len"] = float(self.e_n_ln.get())
            c["macro_spam_start"] = float(self.e_s_st.get())
            c["macro_spam_len"] = float(self.e_s_ln.get())
            
            c["throw_start_settle_delay"] = float(self.e_throw_start_settle.get())
            c["throw_pre_drag_delay"] = float(self.e_throw_pre_drag.get())
            c["throw_tab_delay_after_drag"] = float(self.e_throw_tab_delay.get())
            c["throw_final_settle_delay"] = float(self.e_throw_final_settle.get())
            c["throw_pre_spam_delay"] = float(self.e_throw_pre_spam.get())
            c["throw_post_tab_to_spam_delay"] = float(self.e_throw_post_tab_spam.get())
            c["throw_post_clumsy_tap_delay"] = float(self.e_throw_post_clumsy.get())
            c["throw_post_tab_tap_delay"] = float(self.e_throw_post_tab.get())
            c["throw_clumsy_deactivate_after_spam"] = float(self.e_throw_clumsy_deactivate.get())
            c["throw_tab_dwell"] = float(self.e_throw_tab_dwell.get())
            c["throw_e_dwell"] = float(self.e_throw_e_dwell.get())
            c["throw_spam_duration"] = float(self.e_throw_spam_duration.get())
            c["throw_e_period"] = float(self.e_throw_e_period.get())
            c["throw_drag_time"] = float(self.e_throw_drag_time.get())
            c["throw_drag_left_pixels"] = int(self.e_throw_drag_pixels.get())
            
            self.save_config_func()
            messagebox.showinfo("Saved", "Settings Updated!")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid value: {e}")
