import json
import os
import threading
import tkinter as tk
import subprocess
import sys

import src.export.beatmapExporter as be

from tkinter import filedialog, messagebox, ttk

# -------- Config paths --------
CONFIG_MODEL_PATH = "configs\\config_model.json"
CONFIG_PATHS_PATH = "configs\\config_paths.json"
CONFIG_GENERATION_PATH = "configs\\config_generation.json"
# ------------------------------

# -------- UI Colors --------
BG_COL = "#1C1C1C"
FONT_COL = "#FCFCFC"
ACCENT_COL = "#272727"
ACTIVE_COL = "#555555"
INACTIVE_COL = "#333333"
DISABLED_COL = "#121212"
BUTTON_TEXT_COL = FONT_COL
# ---------------------------
 
OPEN_CONSOLE_WINDOW_ON_RUN = True

DIFFICULTY_OPTIONS = [ "0-1_stars", "1-2_stars", "2-3_stars", "3-4_stars", "4-5_stars", "5_stars_plus" ]
EXPORT_OPTIONS = [ ".osz", ".qua" ]

GUI_VERSION = "1.4"
TK_THEME = "clam"

local_vars = {}


def try_get(v):
    try:
        return v.get()
    except AttributeError:
        return v


def load_json(path):
    if os.path.exists(path=path):
        with open(path, "r") as f:
            return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def setup_style():
    style = ttk.Style()
    style.theme_use(TK_THEME)

    # Tabs
    style.configure("TNotebook", background=BG_COL)
    style.configure("TNotebook.Tab", background=ACCENT_COL, foreground=FONT_COL, padding=[10, 5])
    style.map("TNotebook.Tab", background=[("selected", BG_COL)])
    
    # Frames & Labels
    style.configure("TFrame", background=BG_COL, )
    style.configure("TLabel", background=BG_COL, foreground=FONT_COL, font=("Segoe UI", 12))
    
    # Checkbuttons
    style.configure(
        "TCheckbutton",
        background=BG_COL,
        foreground=FONT_COL,
        font=("Segoe UI", 10),
        padding=4
    )
    
    style.map(
        "TCheckbutton",
        background=[("active", ACCENT_COL)],
        foreground=[("active", FONT_COL)]
    )
    
    # Buttons
    style.configure("TButton", background=BG_COL, foreground=FONT_COL, font=("Segoe UI", 10))
    style.map(
        "TButton",
        background=[("active", ACTIVE_COL), ("!disabled", INACTIVE_COL)],
        foreground=[("disabled", DISABLED_COL)]
    )
    
    # Combobox
    style.configure("TCombobox", background=ACCENT_COL, foreground=FONT_COL, font=("Segoe UI", 12), padding=[3, 3])
    style.map("TCombobox", fieldbackground=[("active", ACTIVE_COL), ("!disabled", INACTIVE_COL)])
    
    # Spinbox
    style.configure("TSpinbox", background=ACCENT_COL, foreground=FONT_COL, font=("Segoe UI", 12), padding=[3, 3])
    style.map("TSpinbox", fieldbackground=[("active", ACTIVE_COL), ("!disabled", INACTIVE_COL)])
    
    # Entries
    style.configure("TEntry", fieldbackground=INACTIVE_COL, background=ACCENT_COL, foreground=FONT_COL, font=("Consolas", 16), padding=6)
    style.map("TEntry", fieldbackground=[("active", ACTIVE_COL)])
    
    # Seperators
    style.configure("TSeparator", background=BG_COL)


class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget


    def write(self, msg):
        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, msg)
        self.text_widget.see(tk.END)
        self.text_widget.config(state="disabled")


    def flush(self):
        pass


class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Beatmap Generation Editor v{GUI_VERSION}")
        
        self.model_config = load_json(CONFIG_MODEL_PATH)
        self.paths_config = load_json(CONFIG_PATHS_PATH)
        self.generation_config = load_json(CONFIG_GENERATION_PATH)
        self.output_window = None
        self.console_text_widget = None
        
        setup_style()
        
        self.create_widgets()


    def create_widgets(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.pipeline_frame = ttk.Frame(notebook)
        self.download_frame = ttk.Frame(notebook)
        self.training_frame = ttk.Frame(notebook)
        self.generation_frame = ttk.Frame(notebook)
        self.export_frame = ttk.Frame(notebook)
        
        for frame in [self.pipeline_frame, self.download_frame, self.training_frame, self.generation_frame, self.export_frame]:
            for col in range(3):
                frame.columnconfigure(col, weight=1)
        
        notebook.add(self.pipeline_frame, text="Pipeline")
        notebook.add(self.download_frame, text="Download & Preprocess")
        notebook.add(self.training_frame, text="Sequence & Training")
        notebook.add(self.generation_frame, text="Generation & Visualizer")
        notebook.add(self.export_frame, text="Beatmap Export")
        
        self.build_pipeline_frame()
        self.build_download_frame()
        self.build_training_frame()
        self.build_generation_frame()
        self.build_export_frame()
        
        # Buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=sys.exit).grid(row=0, column=0, padx=50)
        ttk.Button(btn_frame, text="Save & Exit", command=self.save_and_quit).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Save & Run", command=self.save_and_run).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Export", command=self.export).grid(row=0, column=3, padx=[5, 50])
        ttk.Button(btn_frame, text="View Console Output", command=self.open_output_window).grid(row=0, column=4, padx=[5, 50])
        
        self.toggle_threshold_mode()


    def build_pipeline_frame(self) -> None:
        # -------- Pipeline steps --------
        self.add_header(self.pipeline_frame, 0, "Pipeline steps")
        
        self.add_checkbox(self.pipeline_frame, "Run Beatmap Downloader", "run_beatmap_downloader", config=self.model_config)
        self.add_checkbox(self.pipeline_frame, "Run Beatmap Preprocessor", "run_beatmap_preprocessor", config=self.model_config)
        self.add_checkbox(self.pipeline_frame, "Run Feature Normalizer", "run_feature_normalizer", config=self.model_config)
        self.add_checkbox(self.pipeline_frame, "Run Sequence Splitter", "run_sequence_splitter", config=self.model_config)
        self.add_checkbox(self.pipeline_frame, "Run Model Trainer", "run_model_trainer", config=self.model_config)
        self.add_checkbox(self.pipeline_frame, "Run Beatmap Generator", "run_level_generator", config=self.generation_config)
        self.add_checkbox(self.pipeline_frame, "Run Visualizer (after generation)", "run_visualizer", config=self.generation_config)
        # --------------------------------
        
        self.add_separator(self.pipeline_frame, 8)
        
        # -------- Step buttons --------
        self.add_header(self.pipeline_frame, 9, "Actions")
        
        action_btn_frame = ttk.Frame(self.pipeline_frame)
        action_btn_frame.grid(row=10, column=0, padx=20, pady=(5, 15), sticky="w")
        
        action_btn_frame.grid_columnconfigure(0, weight=1)
        
        btn_width = 25
        
        ttk.Button(action_btn_frame, text="Run Selected Steps", width=btn_width, command=self.save_and_run).grid(row=0, column=0, pady=10, sticky="ew")
        ttk.Button(action_btn_frame, text="Reset Settings", width=btn_width, command=self.reset_settings).grid(row=1, column=0, pady=10, sticky="ew")
        ttk.Button(action_btn_frame, text="Delete Generated Files", width=btn_width, command=self.delete_gen_files).grid(row=2, column=0, pady=10, sticky="ew")
        ttk.Button(action_btn_frame, text="Construct Directory Structure", width=btn_width, command=self.construct_dir_struct).grid(row=3, column=0, pady=10, sticky="ew")
        # ------------------------------


    def build_download_frame(self) -> None:
        # -------- Path settings --------
        self.add_header(self.download_frame, 0, "Path settings")
        
        self.add_path_entry(self.download_frame, "Raw Data Folder:", "raw_data_path")
        self.add_path_entry(self.download_frame, "Preprocessed Data Folder:", "preprocessed_data_path")
        # -------------------------------
        
        self.add_separator(self.download_frame, 3)
        
        # -------- Download settings --------
        self.add_header(self.download_frame, 4, "Download settings")
        
        self.add_spinbox(self.download_frame, "Number of Beatmapsets to download:", "download_beatmapsets", from_=100, to=2000)
        # -----------------------------------


    def build_training_frame(self) -> None:
        # -------- Training settings --------
        self.add_header(self.training_frame, 0, "Training settings")
        
        self.add_dropdown(self.training_frame, "Difficulty Range:", "difficulty_range", DIFFICULTY_OPTIONS)
        self.add_checkbox(self.training_frame, "Generate Sequences for all Difficulties", "split_all_difficulty_sequences", config=self.model_config)
        self.add_spinbox(self.training_frame, "Note Precision:", "note_precision", from_=1, to=8)
        self.add_spinbox(self.training_frame, "Sequence Length:", "sequence_length", from_=16, to=512)
        self.add_int_entry(self.training_frame, "Max VRAM for GPU Training (MB):", "max_vram_mb")
        self.add_spinbox(self.training_frame, "Training epochs:", "training_epochs", from_=1, to=1000)
        self.add_path_entry(self.training_frame, "Model output directory:", "model_dir")
        # -----------------------------------


    def build_generation_frame(self) -> None:
        # -------- Audio settings --------
        self.add_header(self.generation_frame, 0, "Audio settings")
        
        self.add_file_entry(self.generation_frame, "Audio File to generate Beatmap for:", "audio_file_path")
        self.add_float_entry(self.generation_frame, "Audio BPM:", "audio_bpm", config=self.generation_config)
        self.add_int_entry(self.generation_frame, "Audio Start Time (ms):", "audio_start_ms", config=self.generation_config)
        # --------------------------------

        self.add_separator(self.generation_frame, 4)
        
        # -------- Generation settings --------
        self.add_header(self.generation_frame, 5, "Generation settings")
        
        self.add_path_entry(self.generation_frame, "Generation Output Folder:", "generation_dir")
        self.add_str_entry(self.generation_frame, "Beatmap File Name:", "generation_file_name", config=self.paths_config)
        self.add_file_entry(self.generation_frame, "Model to use for Generation:", "model_for_generation_path")
        # -------------------------------------
        
        self.show_advanced_generation = tk.BooleanVar(value=False)
        self.show_advanced_generation_cb = ttk.Checkbutton(
            self.generation_frame,
            text="Show advanced Threshold Setttings",
            variable=self.show_advanced_generation,
            command=self.toggle_advanced_generation_frame
        )
        self.show_advanced_generation_cb.grid(row=10, column=0, columnspan=1, pady=(10, 10), sticky="w")
        
        self.advanced_generation_frame = ttk.Frame(self.generation_frame, borderwidth=1, relief="groove")
        self.advanced_generation_frame.grid(row=11, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        self.manual_threshold_entry = self.add_float_entry(self.advanced_generation_frame, "Model Prediction Threshold", "model_prediction_threshold", config=self.generation_config)
        self.use_auto_threshold = self.add_checkbox(self.advanced_generation_frame, "Use Auto Thresholding", "model_use_auto_threshold", config=self.generation_config, command=self.toggle_threshold_mode)
        self.percentile_entry = self.add_float_entry(self.advanced_generation_frame, "Auto Threshold Percentile", "model_auto_threshold_percentile", config=self.generation_config)

        self.toggle_advanced_generation_frame()
        self.toggle_threshold_mode()


    def build_export_frame(self) -> None:
        # -------- Path settings --------
        self.add_header(self.export_frame, 0, "Export paths")
        
        self.export_beatmap_file_path = self.add_file_entry(self.export_frame, "Beatmap to export:", "beatmap_path", is_config_var=False)
        self.export_destination_dir = self.add_path_entry(self.export_frame, "Path to save export to:", "export_destionation_path", is_config_var=False)
        # -------------------------------
        
        self.add_separator(self.export_frame, 3)
        
        # -------- Export settings --------
        self.add_header(self.export_frame, 4, "Metadata")
        
        self.export_audio_start_time_ms = self.add_int_entry(self.export_frame, "Audio Start Time (ms):", "audio_start_ms", is_config_var=False)
        self.export_audio_time_signature = self.add_int_entry(self.export_frame, "Audio Time Signature ([4]/4 | [3]/4):", "audio_time_signature", is_config_var=False)
        self.export_audio_title = self.add_str_entry(self.export_frame, "Audio Title:", "title", is_config_var=False)
        self.export_audio_artist = self.add_str_entry(self.export_frame, "Artist:", "artist", is_config_var=False)
        self.export_difficulty_name = self.add_str_entry(self.export_frame, "Difficulty Name:", "difficulty_name", is_config_var=False)
        
        self.export_format = self.add_dropdown(self.export_frame, "Export format:", "export_format", options=EXPORT_OPTIONS, is_config_var=False)
        # ---------------------------------


    def add_header(self, frame : ttk.Frame, row : int, text : str) -> None:
        ttk.Label(
            frame,
            text=text,
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)


    def add_separator(self, frame : ttk.Frame, row : int) -> None:
        ttk.Separator(frame, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=[30, 0])


    def add_path_entry(self, frame : ttk.Frame, label : str, key : str, is_config_var : bool = True) -> ttk.Entry:
        row = frame.grid_size()[1]
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.StringVar(value=self.paths_config.get(key, ""))
        entry = ttk.Entry(frame, textvariable=var, width=50)
        entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        browse_btn = ttk.Button(frame, text="Browse", command=lambda: var.set(filedialog.askdirectory()))
        browse_btn.grid(row=row, column=2, sticky="ew", padx=5)
        
        if is_config_var:
            self.paths_config[key] = var
        return entry


    def add_file_entry(self, frame : ttk.Frame, label : str, key : str, is_config_var : bool = True) -> ttk.Entry:
        row = frame.grid_size()[1]
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.StringVar(value=self.paths_config.get(key, ""))
        entry = ttk.Entry(frame, textvariable=var, width=50)
        entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        browse_btn = ttk.Button(frame, text="Browse", command=lambda: var.set(filedialog.askopenfilename()))
        browse_btn.grid(row=row, column=2, sticky="ew", padx=5)
        
        if is_config_var:
            self.paths_config[key] = var
        return entry


    def add_dropdown(self, frame : ttk.Frame, label : str, key : str, options, config = None, is_config_var : bool = True) -> ttk.Combobox:
        cfg = config or self.model_config
        row = frame.grid_size()[1]
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.StringVar(value=cfg.get(key, options[0]))
        cbb = ttk.Combobox(frame, textvariable=var, values=options, state="readonly")
        cbb.grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        if is_config_var:
            cfg[key] = var
        return cbb 


    def add_spinbox(self, frame : ttk.Frame, label : str, key, from_, to, is_config_var : bool = True) -> None:
        row = frame.grid_size()[1]
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.IntVar(value=self.model_config.get(key, from_))
        ttk.Spinbox(frame, from_=from_, to=to, textvariable=var).grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        if is_config_var:
            self.model_config[key] = var


    def add_float_entry(self, frame : ttk.Frame, label : str, key : str, config=None, is_config_var : bool = True) -> ttk.Entry:
        row = frame.grid_size()[1]
        cfg = config or self.model_config
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.DoubleVar(value=cfg.get(key, 0.0))
        entry = ttk.Entry(frame, textvariable=var)
        entry.grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        if is_config_var:
            cfg[key] = var
        return entry


    def add_int_entry(self, frame : ttk.Frame, label : str, key : str, config=None, is_config_var : bool = True) -> ttk.Entry:
        row = frame.grid_size()[1]
        cfg = config or self.model_config
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.IntVar(value=cfg.get(key, 0))
        entry = ttk.Entry(frame, textvariable=var)
        entry.grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        if is_config_var:
            cfg[key] = var
        return entry


    def add_str_entry(self, frame : ttk.Frame, label : str, key : str, config=None, is_config_var : bool = True) -> ttk.Entry:
        row = frame.grid_size()[1]
        cfg = config or self.model_config
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.StringVar(value=cfg.get(key, ""))
        entry = ttk.Entry(frame, textvariable=var)
        entry.grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        if is_config_var:
            cfg[key] = var
        return entry


    def add_checkbox(self, frame : ttk.Frame, label : str, key : str, config, is_config_var : bool = True, command = None) -> tk.BooleanVar:
        row = frame.grid_size()[1]
        var = tk.BooleanVar(value=config.get(key, False))
        cb = tk.Checkbutton(
            frame, text=label, variable=var,
            bg=BG_COL, fg=FONT_COL,
            selectcolor=ACCENT_COL,
            font=("Segoe UI", 10),
            anchor="w",
            command=command
        )
        cb.grid(row=row, column=0, columnspan=3, sticky="w", pady=2, padx=5)

        if is_config_var:
            config[key] = var
        return var


    def toggle_threshold_mode(self):
        auto_mode = self.use_auto_threshold.get()
        
        self.manual_threshold_entry.configure(state="disabled" if auto_mode else "normal")
        self.percentile_entry.configure(state="normal" if auto_mode else "disabled")

    
    def toggle_advanced_generation_frame(self):
        if self.show_advanced_generation.get():
            self.advanced_generation_frame.grid(row=11, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        else:
            self.advanced_generation_frame.grid_remove()


    def export(self) -> None:
        bm_fp = self.export_beatmap_file_path.get()
        e_dd = self.export_destination_dir.get()
        
        bpm = self.export_audio_bpm.get()
        start_time = self.export_audio_start_time_ms.get()
        time_signature = self.export_audio_time_signature.get()
        title = self.export_audio_title.get()
        artist = self.export_audio_artist.get()
        difficulty = self.export_difficulty_name.get()
        fmt = self.export_format.get()
        
        metadata = {
            "audio_bpm": bpm,
            "audio_start_ms": start_time,
            "audio_time_signature": time_signature,
            "title": title,
            "artist": artist,
            "difficulty_name": difficulty
        }
        
        # Automatically open the console window.
        if OPEN_CONSOLE_WINDOW_ON_RUN:
            self.open_output_window()
        
        if fmt == ".osz":
            be.export_to_osz(beatmap_file_path=bm_fp, export_path=e_dd, metadata=metadata)
        elif fmt == ".qua":
            be.export_to_qua(beatmap_file_path=bm_fp, export_path=e_dd, metadata=metadata)
        else:
            messagebox.showerror("Error", f"Beatmap could not be exported.")
            return

        messagebox.showinfo("Success", "Export complete.")

    
    def open_output_window(self) -> None:
        if self.output_window is not None and self.output_window.winfo_exists():
            self.output_window.lift()
            return
        
        self.output_window = tk.Toplevel(self.root)
        self.output_window.title("Console Output")
        self.output_window.configure(bg=BG_COL)

        self.console_text_widget = tk.Text(self.output_window, wrap="word", bg=BG_COL, fg=FONT_COL, font=("Consolas", 12))
        self.console_text_widget.pack(expand=True, fill="both", padx=10, pady=10)
        self.console_text_widget.config(state="disabled")

        sys.stdout = ConsoleRedirector(self.console_text_widget)
        sys.stderr = ConsoleRedirector(self.console_text_widget)

        print(f"Console window initialized.\n{27*'='}")


    def save_all(self) -> None:
        save_json(CONFIG_MODEL_PATH, {k: try_get(v) for k, v in self.model_config.items()})
        save_json(CONFIG_PATHS_PATH, {k: try_get(v) for k, v in self.paths_config.items()})
        save_json(CONFIG_GENERATION_PATH, {k: try_get(v) for k, v in self.generation_config.items()})


    def save_and_quit(self) -> None:
        self.save_all()
        sys.exit(0)


    def save_and_run(self) -> None:
        if OPEN_CONSOLE_WINDOW_ON_RUN:
            self.open_output_window()
        
        self.save_all()
        
        thread = threading.Thread(target=self.run_pipeline)
        thread.start()
        
    
    def run_pipeline(self) -> None:
        if self.console_text_widget is not None:
            process = subprocess.Popen(
                ["python", "-u", "runPipeline.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            for line in process.stdout:
                self.console_text_widget.config(state="normal")
                self.console_text_widget.insert(tk.END, line)
                self.console_text_widget.see(tk.END)
                self.console_text_widget.config(state="disabled")
        else:
            subprocess.run(["python", "runPipeline.py"])
    
    
    def reset_settings(self) -> None:
        pass


    def delete_gen_files(self) -> None:
        pass


    def construct_dir_struct(self) -> None:
        pass


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg=BG_COL)
    app = ConfigEditor(root=root)
    root.mainloop()
