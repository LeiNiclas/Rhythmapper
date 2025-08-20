import matplotlib.pyplot as plt
import os
import sys
import tkinter as tk

import src.analyzer.rthmAnalyzer as ra
import src.analyzer.rthmPlotter as rp

from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.analyzer.rthmAnalyzer import TimingData



# -------- UI Colors --------
BG_COL = "#1C1C1C"
FONT_COL = "#FCFCFC"
ACCENT_COL = "#272727"
ACTIVE_COL = "#555555"
INACTIVE_COL = "#333333"
DISABLED_COL = "#121212"
BUTTON_TEXT_COL = FONT_COL
TK_THEME = "clam"
# ---------------------------

# -------- UI Fonts --------
FONT = "Segoe UI"

H1_FONT_SIZE = 20
H2_FONT_SIZE = 18
H3_FONT_SIZE = 16
P_FONT_SIZE = 14
# --------------------------


def setup_style(root : tk.Tk):
    # Root background
    root.configure(bg=BG_COL)
    
    style = ttk.Style()
    style.theme_use(TK_THEME)
    
    # Frames and labels
    style.configure("TFrame", background=BG_COL)
    style.configure("TLabel", background=BG_COL, foreground=FONT_COL, font=(FONT, H2_FONT_SIZE))
    
    # Buttons
    style.configure("TButton", background=BG_COL, foreground=FONT_COL, font=(FONT, P_FONT_SIZE))
    style.map(
        "TButton",
        background=[("active", ACTIVE_COL), ("!disabled", INACTIVE_COL)],
        foreground=[("disabled", DISABLED_COL)]
    )
    
    # Spinbox
    style.configure("TSpinbox", background=ACCENT_COL, foreground=FONT_COL, font=(FONT, P_FONT_SIZE), padding=[3, 3])
    style.map(
        "TSpinbox",
        fieldbackground=[("active", ACTIVE_COL), ("!disabled", INACTIVE_COL)]
    )


class RthmFileBrowser:
    def __init__(self, root):
        setup_style(root=root)
        self.root = root
        self.root.title("Rthm File Browser")
        
        # State
        self.current_dir : str | None = None
        self.current_file : str | None = None
        self.rthm_data : list[str] | None = []
        self.timing_data : list[TimingData] | None = []
        self.note_distribution_data : list[tuple[int, int]] | None = []
        self.lane_count : int = 0
        self.duration_ms : int = 0
        
        # Layout: Left (browser), Right (stats + plot + spinbox)  
        self.browser_frame = ttk.Frame(root, padding=(6, 6))
        self.browser_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.analytics_frame = ttk.Frame(root, padding=(6, 6))
        self.analytics_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # -------- Browser --------
        ttk.Label(self.browser_frame, text=".rthm Files", font=(FONT, H1_FONT_SIZE, "bold")).pack(anchor="w", pady=(0, 6))
        
        list_container_frame = ttk.Frame(self.browser_frame)
        list_container_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(
            list_container_frame,
            width=36,
            height=18,
            bg=ACCENT_COL,
            fg=FONT_COL,
            selectbackground=ACTIVE_COL,
            selectforeground=FONT_COL,
            highlightthickness=0,
            relief="flat",
            font=(FONT, P_FONT_SIZE)
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        list_scrollbar = ttk.Scrollbar(list_container_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=list_scrollbar.set)
        
        # Buttons
        listbox_buttons_frame = ttk.Frame(self.browser_frame)
        listbox_buttons_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Button(listbox_buttons_frame, text="Choose folder", command=self.choose_folder).pack(side=tk.LEFT)
        ttk.Button(listbox_buttons_frame, text="Clear", command=self.clear_data).pack(side=tk.LEFT, padx=6)
        
        # Path info
        self.path_label = ttk.Label(
            self.browser_frame,
            text="No file selected",
            foreground=FONT_COL,
            wraplength=260,
            font=(FONT, H3_FONT_SIZE)
        )
        self.path_label.pack(anchor="w", pady=(8, 0))
        
        
        # -------- Stats panel --------
        self.stats_frame = ttk.Frame(self.analytics_frame)
        self.stats_frame.pack(fill=tk.X)
        
        ttk.Label(self.stats_frame, text="Statistics", font=(FONT, H1_FONT_SIZE, "bold")).pack(anchor="w")
        
        self.stats_text = tk.Text(
            self.stats_frame,
            height=8,
            wrap="word",
            bg=BG_COL,
            fg=FONT_COL,
            insertbackground=FONT_COL,
            font=(FONT, P_FONT_SIZE),
            relief="flat",
            highlightthickness=0
        )
        self.stats_text.pack(fill=tk.X, pady=(4, 0))
        
        # Plot frame
        self.plot_frame = ttk.Frame(self.analytics_frame)
        self.plot_frame.pack(fill=tk.X, pady=(8, 0))
        self.plot_frame.configure(height=int(self.root.winfo_screenheight() * 0.5))
        self.plot_frame.pack_propagate(False)
        
        # Matplotlib figures
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.mpl_style_axes(self.ax)
        self.figure_canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        
        canvas_widget = self.figure_canvas.get_tk_widget()
        canvas_widget.configure(bg=BG_COL, highlightthickness=0)
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Spinbox below plot
        spin_frame = ttk.Frame(self.analytics_frame)
        spin_frame.pack(fill=tk.X, pady=8)
        
        ttk.Label(spin_frame, text="Window size (rows):").pack(side=tk.LEFT, padx=(0, 8))
        self.window_size_spin = ttk.Spinbox(
            spin_frame,
            from_=1,
            to=64,
            width=6,
            command=self.on_window_size_changed
        )
        self.window_size_spin.set("8")
        self.window_size_spin.pack(side=tk.LEFT)
        
        # Quit button
        quit_frame = ttk.Frame(self.analytics_frame)
        quit_frame.pack(side=tk.BOTTOM, anchor="e", pady=(6, 0))
        
        ttk.Button(
            quit_frame,
            text="Quit",
            command=sys.exit
        ).pack(side=tk.RIGHT, padx=(0, 4), pady=(4, 4))
        
        self.window_size_spin.bind("<Return>", lambda e: self.on_window_size_changed())
        self.window_size_spin.bind("<FocusOut>", lambda e: self.on_window_size_changed())
        
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)
        
        # Initial empty UI
        self.update_stats_text()
        self.update_plots()
        
    
    def choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select folder with .rthm files")
        
        # Abort if no folder was chosen.
        if not folder:
            return
        
        files = None
        
        # Populate list with .rthm files.
        try:
            files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".rthm"))
        except Exception as e:
            messagebox.showerror("Error getting .rthm files:", str(e))
            return

        # Update state values.
        self.current_dir = folder
        self.file_listbox.delete(0, tk.END)
        
        for f in files:
            self.file_listbox.insert(tk.END, f)
        
        # Show chosen folder path.
        self.path_label.config(text=folder)
        
        # Clear current file-related state until a file is chosen.
        self.current_file = None
        self.rthm_data = []
        self.timing_data = []
        self.note_distribution_data = []
        self.lane_count = 0
        self.duration_ms = 0
        
        # Refresh the UI to show changes.
        self.refresh_ui()


    def on_file_selected(self, event_=None) -> None:
        if not self.current_dir:
            return
        
        selection = self.file_listbox.curselection()
        
        if not selection:
            return
        
        file_name = self.file_listbox.get(selection[0])
        file_path = os.path.join(self.current_dir, file_name)
        self.load_file(file_path)
    
    
    def load_file(self, path : str):
        try:
            raw = ra.get_raw_rthm_data(path=path)
            lane_count = ra.get_lane_count(raw)
            timing_data = ra.get_timing_data(raw, lane_count)
            duration = ra.get_duration_ms(raw)
        except Exception as e:
            messagebox.showerror("Error loading file:", str(e))
            return
    
        # Update state values.
        self.current_file = path
        self.rthm_data = raw
        self.lane_count = lane_count
        self.timing_data = timing_data
        self.duration_ms = duration
        
        # Update path UI.
        self.path_label.config(text=path)
        
        # Refresh UI to show changes.
        self.compute_data()
        self.refresh_ui()
        
    
    def clear_data(self):
        self.current_file = None
        self.current_dir = None
        self.rthm_data = []
        self.timing_data = []
        self.note_distribution_data = []
        self.lane_count = 0
        self.duration_ms = 0
        
        self.file_listbox.delete(0, tk.END)
        self.path_label.config(text="No file selected")
        
        self.refresh_ui()
    
    
    def window_size_value(self) -> int:
        try:
            v = int(self.window_size_spin.get())
            return max(1, v)
        except Exception:
            return 8
    
    
    def on_window_size_changed(self):
        if not self.rthm_data:
            return
        
        self.compute_data()
        self.refresh_ui()
    
    
    def compute_data(self):
        window_size = self.window_size_value()
        
        try:
            self.note_distribution_data = ra.get_notes_over_time(self.timing_data, window_size)
        except Exception as e:
            messagebox.showerror("Computation error:", str(e))
            self.note_distribution_data = []
    
    
    def refresh_ui(self):
        self.update_stats_text()
        self.update_plots()
    
    
    def update_stats_text(self):
        self.stats_text.delete("1.0", tk.END)
        
        if not self.timing_data:
            self.stats_text.insert(tk.END, "Load a .rthm file to see statistics.")
            return
        
        total_notes, density = ra.get_note_count_and_density(self.timing_data)
        notes_per_lane = ra.get_notes_per_lane(self.timing_data)
        duration_sec = self.duration_ms / 1000.0 if self.duration_ms > 0 else 0.0
        
        lines = []
        lines.append(f"Total notes: {total_notes}")
        lines.append(f"Note density: {density:.3f}")
        lines.append(f"Lane count: {self.lane_count}")
        lines.append(f"Duration: {int(duration_sec // 60)}m {int(duration_sec % 60)}s")
        lines.append("Notes per lane:")
        lines.append("  " + ", ".join(f"L{i+1}: {v}" for i, v in enumerate(notes_per_lane)))
        
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert(tk.END, "\n".join(lines))
        self.stats_text.see(tk.END)
        self.stats_text.config(state="disabled")
    
    
    def update_plots(self):
        self.fig.clear()
        gridspec = self.fig.add_gridspec(
            nrows=2, ncols=1, 
            height_ratios=[2, 1],
            hspace=0.1
        )
        
        ax_note_distribution = self.fig.add_subplot(gridspec[0, 0])
        ax_note_distribution.tick_params(
            axis="x",
            which="both",
            bottom=False,
            labelbottom=False
        )
        ax_note_lane_heatmap = self.fig.add_subplot(gridspec[1, 0], sharex=ax_note_distribution)
        
        if not self.note_distribution_data:
            self.mpl_style_axes(ax_note_distribution)
            self.mpl_style_axes(ax_note_lane_heatmap)
            
            ax_note_distribution.set_title("Note distribution + heatmap", color=FONT_COL, fontweight="bold", fontsize=H2_FONT_SIZE)
            # ax_note_distribution.set_xlabel("Time (seconds)", color=FONT_COL, fontsize=H3_FONT_SIZE)
            ax_note_distribution.set_ylabel("Note count", color=FONT_COL, fontsize=H3_FONT_SIZE)
            ax_note_distribution.grid(True, axis="y", alpha=0.25, color=ACTIVE_COL)
            
            #ax_note_lane_heatmap.set_title("Notes per lane heatmap", color=FONT_COL, fontweight="bold", fontsize=H2_FONT_SIZE)
            ax_note_lane_heatmap.set_xlabel("Time (seconds)", color=FONT_COL, fontsize=H3_FONT_SIZE)
            ax_note_lane_heatmap.set_ylabel("Lane", color=FONT_COL, fontsize=H3_FONT_SIZE)
            
            self.figure_canvas.draw_idle()
            return

        # Plot distribution graph.
        bin_size = rp.plot_note_distribution_over_time(ax_note_distribution, self.note_distribution_data)
        self.mpl_style_axes(ax_note_distribution)
        
        ax_note_distribution.set_title("Note distribution + heatmap", color=FONT_COL, fontweight="bold", fontsize=H2_FONT_SIZE)
        # ax_note_distribution.set_xlabel("Time (seconds)", color=FONT_COL, fontsize=H3_FONT_SIZE)
        ax_note_distribution.set_ylabel("Note count", color=FONT_COL, fontsize=H3_FONT_SIZE)
        ax_note_distribution.grid(True, axis="y", alpha=0.25, color=ACTIVE_COL)
        
        # Plot heatmap.
        rp.plot_notes_per_lane_heatmap(ax_note_lane_heatmap, self.timing_data, bin_size)
        self.mpl_style_axes(ax_note_lane_heatmap)
        
        # ax_note_lane_heatmap.set_title("Notes per lane heatmap", color=FONT_COL, fontweight="bold", fontsize=H2_FONT_SIZE)
        ax_note_lane_heatmap.set_xlabel("Time (seconds)", color=FONT_COL, fontsize=H3_FONT_SIZE)
        ax_note_lane_heatmap.set_ylabel("Lane", color=FONT_COL, fontsize=H3_FONT_SIZE)
        
        self.figure_canvas.draw_idle()
        
        
    def mpl_style_axes(self, ax):
        self.fig.patch.set_facecolor(BG_COL)
        ax.set_facecolor(ACCENT_COL)
        
        # Spines
        for spine in ax.spines.values():
            spine.set_color(INACTIVE_COL)
        
        # Ticks
        ax.tick_params(colors=FONT_COL, which="both")
        
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color(FONT_COL)
            label.set_fontsize(H3_FONT_SIZE)
            label.set_fontname(FONT)


def main():
    root = tk.Tk()
    app = RthmFileBrowser(root)
    root.mainloop()


if __name__ == "__main__":
    main()