import json
import os
import tkinter as tk
import subprocess
import sys

from tkinter import filedialog, messagebox, ttk


# -------- Config paths --------
CONFIG_MODEL_PATH = "config_model.json"
CONFIG_PATHS_PATH = "config_paths.json"
CONFIG_GENERATION_PATH = "config_generation.json"
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
 

DIFFICULTY_OPTIONS = [ "0-1_stars", "1-2_stars", "2-3_stars", "3-4_stars", "4-5_stars", "5_stars_plus" ]

GUI_VERSION = "1.2"


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
    style.theme_use("alt")
    
    # General
    # style.configure(".", background=BG_COL, foreground=FONT_COL)
    
    # Tabs
    style.configure("TNotebook", background=BG_COL)
    style.configure("TNotebook.Tab", background=ACCENT_COL, foreground=FONT_COL, padding=[10, 5])
    style.map("TNotebook.Tab", background=[("selected", ACTIVE_COL)])
    
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
    style.configure("TButton", background=BG_COL, foreground=FONT_COL, font=("Segoe UI", 12, "bold"))
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


class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Beatmap Generation Editor v{GUI_VERSION}")
        
        self.model_config = load_json(CONFIG_MODEL_PATH)
        self.paths_config = load_json(CONFIG_PATHS_PATH)
        self.generation_config = load_json(CONFIG_GENERATION_PATH)
        
        setup_style()
        
        self.create_widgets()


    def create_widgets(self) -> None:
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)
        
        self.download_frame = ttk.Frame(notebook)
        self.training_frame = ttk.Frame(notebook)
        self.generation_frame = ttk.Frame(notebook)
        
        for frame in [self.download_frame, self.training_frame, self.generation_frame]:
            for col in range(3):
                frame.columnconfigure(col, weight=1)
        
        notebook.add(self.download_frame, text="Download & Preprocess")
        notebook.add(self.training_frame, text="Sequence & Training")
        notebook.add(self.generation_frame, text="Generation & Visualizer")
        
        self.build_download_frame()
        self.build_training_frame()
        self.build_generation_frame()
        
        # Save buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Save & Exit", command=self.save_and_quit).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Save & Run", command=self.save_and_run).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=sys.exit).grid(row=0, column=2, padx=10)


    def build_download_frame(self) -> None:
        # -------- Path settings --------
        ttk.Label(
            self.download_frame,
            text="Data paths",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        
        self.add_path_entry(self.download_frame, "Raw Data Folder:", "raw_data_path")
        self.add_path_entry(self.download_frame, "Preprocessed Data Folder:", "preprocessed_data_path")
        # -------------------------------
        
        ttk.Separator(self.download_frame, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=[30, 0])
        
        # -------- Download settings --------
        ttk.Label(
            self.download_frame,
            text="Download settings",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        
        self.add_spinbox(self.download_frame, "Number of Beatmapsets to download:", "download_beatmapsets", from_=100, to=2000)
        # -----------------------------------
        
        ttk.Separator(self.download_frame, orient="horizontal").grid(row=6, column=0, columnspan=3, sticky="ew", pady=[30, 0])
        
        # -------- Pipeline settings --------
        ttk.Label(
            self.download_frame,
            text="Pipeline settings",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=7, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        
        self.add_checkbox(self.download_frame, "Run Beatmap Downloader", "run_beatmap_downloader", config=self.model_config)
        self.add_checkbox(self.download_frame, "Run Beatmap Preprocessor", "run_beatmap_preprocessor", config=self.model_config)
        # -----------------------------------


    def build_training_frame(self) -> None:
        # -------- Training settings --------
        ttk.Label(
            self.training_frame,
            text="Training settings",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        
        self.add_dropdown(self.training_frame, "Difficulty Range:", "difficulty_range", DIFFICULTY_OPTIONS)
        self.add_spinbox(self.training_frame, "Note Precision:", "note_precision", from_=1, to=8)
        self.add_spinbox(self.training_frame, "Sequence Length:", "sequence_length", from_=16, to=512)
        self.add_float_entry(self.training_frame, "Prediction Threshold:", "prediction_threshold")
        self.add_int_entry(self.training_frame, "Max VRAM for GPU Training (MB):", "max_vram_mb")
        self.add_path_entry(self.training_frame, "Model output directory:", "model_dir")
        # -----------------------------------
        
        ttk.Separator(self.training_frame, orient="horizontal").grid(row=7, column=0, columnspan=3, sticky="ew", pady=[30, 0])
        
        # -------- Pipeline settings --------
        ttk.Label(
            self.training_frame,
            text="Pipeline settings",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=8, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        
        self.add_checkbox(self.training_frame, "Run Feature Normalizer", "run_feature_normalizer", config=self.model_config)
        self.add_checkbox(self.training_frame, "Run Sequence Splitter", "run_sequence_splitter", config=self.model_config)
        self.add_checkbox(self.training_frame, "Run Model Trainer", "run_model_trainer", config=self.model_config)
        # -----------------------------------


    def build_generation_frame(self) -> None:
        # -------- Audio settings --------
        ttk.Label(
            self.generation_frame,
            text="Audio settings",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        
        self.add_file_entry(self.generation_frame, "Audio File to generate Beatmap for:", "audio_file_path")
        self.add_float_entry(self.generation_frame, "Audio BPM:", "audio_bpm", config=self.generation_config)
        self.add_int_entry(self.generation_frame, "Audio Start Time (ms):", "audio_start_ms", config=self.generation_config)
        # --------------------------------

        ttk.Separator(self.generation_frame, orient="horizontal").grid(row=4, column=0, columnspan=3, sticky="ew", pady=[30, 0])
        
        # -------- Generation settings --------
        ttk.Label(
            self.generation_frame,
            text="Generation settings",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        
        self.add_path_entry(self.generation_frame, "Generation Output Folder:", "generation_dir")
        self.add_str_entry(self.generation_frame, "Beatmap File Name:", "generation_file_name", config=self.paths_config)
        self.add_file_entry(self.generation_frame, "Model to use for generation:", "model_for_generation_path")
        # -------------------------------------
        
        ttk.Separator(self.generation_frame, orient="horizontal").grid(row=9, column=0, columnspan=3, sticky="ew", pady=[30, 0])
        
        # -------- Fallback settings --------
        ttk.Label(
            self.generation_frame,
            text="Fallback Visualizer files",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=10, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        

        self.add_file_entry(self.generation_frame, "Visualizer Beatmap (.osu) File:", "visualizer_beatmap_path")
        self.add_file_entry(self.generation_frame, "Visualizer Audio File:", "visualizer_audio_path")
        # -----------------------------------
        
        ttk.Separator(self.generation_frame, orient="horizontal").grid(row=13, column=0, columnspan=3, sticky="ew", pady=[30, 0])
        
        # -------- Pipeline settings --------
        ttk.Label(
            self.generation_frame,
            text="Pipeline settings",
            font=("Segoe UI", 20, "bold"),
            background=BG_COL, foreground=FONT_COL
        ).grid(row=14, column=0, columnspan=3, sticky="w", pady=(20, 5), padx=5)
        
        self.add_checkbox(self.generation_frame, "Run Level Generator", "run_level_generator", config=self.generation_config)
        self.run_visualizer_var = self.add_checkbox(self.generation_frame, "Run Visualizer After Generation", "run_visualizer", config=self.generation_config)
        self.use_last_generated_level_var = self.add_checkbox(self.generation_frame, "Use Latest Generated file for Visualizer", "visualizer_use_last_gen", config=self.generation_config)
        # -----------------------------------


    def add_path_entry(self, frame : ttk.Frame, label : str, key : str) -> None:
        row = frame.grid_size()[1]
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.StringVar(value=self.paths_config.get(key, ""))
        entry = ttk.Entry(frame, textvariable=var, width=50)
        entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        browse_btn = ttk.Button(frame, text="Browse", command=lambda: var.set(filedialog.askdirectory()))
        browse_btn.grid(row=row, column=2, sticky="ew", padx=5)

        self.paths_config[key] = var


    def add_file_entry(self, frame : ttk.Frame, label : str, key : str) -> None:
        row = frame.grid_size()[1]
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.StringVar(value=self.paths_config.get(key, ""))
        entry = ttk.Entry(frame, textvariable=var, width=50)
        entry.grid(row=row, column=1, sticky="ew", pady=2, padx=5)
        browse_btn = ttk.Button(frame, text="Browse", command=lambda: var.set(filedialog.askopenfilename()))
        browse_btn.grid(row=row, column=2, sticky="ew", padx=5)

        self.paths_config[key] = var


    def add_dropdown(self, frame : ttk.Frame, label : str, key : str, options) -> None:
        row = frame.grid_size()[1]
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.StringVar(value=self.model_config.get(key, options[0]))
        ttk.Combobox(frame, textvariable=var, values=options, state="readonly").grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        self.model_config[key] = var


    def add_spinbox(self, frame : ttk.Frame, label : str, key, from_, to) -> None:
        row = frame.grid_size()[1]
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.IntVar(value=self.model_config.get(key, from_))
        ttk.Spinbox(frame, from_=from_, to=to, textvariable=var).grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        self.model_config[key] = var


    def add_float_entry(self, frame : ttk.Frame, label : str, key, config=None) -> None:
        row = frame.grid_size()[1]
        cfg = config or self.model_config
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.DoubleVar(value=cfg.get(key, 0.0))
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        cfg[key] = var


    def add_int_entry(self, frame : ttk.Frame, label : str, key, config=None) -> None:
        row = frame.grid_size()[1]
        cfg = config or self.model_config
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.IntVar(value=cfg.get(key, 0))
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        cfg[key] = var


    def add_str_entry(self, frame : ttk.Frame, label : str, key, config=None) -> None:
        row = frame.grid_size()[1]
        cfg = config or self.model_config
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2, padx=5)
        var = tk.StringVar(value=cfg.get(key, ""))
        ttk.Entry(frame, textvariable=var).grid(row=row, column=1, sticky="w", pady=2, padx=5)
        
        cfg[key] = var


    def add_checkbox(self, frame : ttk.Frame, label : str, key, config) -> tk.BooleanVar:
        row = frame.grid_size()[1]
        var = tk.BooleanVar(value=config.get(key, False))
        cb = tk.Checkbutton(
            frame, text=label, variable=var,
            bg=BG_COL, fg=FONT_COL,
            selectcolor=ACCENT_COL,
            font=("Segoe UI", 10),
            anchor="w"
        )
        cb.grid(row=row, column=0, columnspan=3, sticky="w", pady=2, padx=5)

        config[key] = var
        return var


    def save_all(self) -> None:
        save_json(CONFIG_MODEL_PATH, {k: try_get(v) for k, v in self.model_config.items()})
        save_json(CONFIG_PATHS_PATH, {k: try_get(v) for k, v in self.paths_config.items()})
        save_json(CONFIG_GENERATION_PATH, {k: try_get(v) for k, v in self.generation_config.items()})
        
        # messagebox.showinfo("Saved", "Configuration saved successfully.")


    def save_and_quit(self) -> None:
        self.save_all()
        sys.exit(0)


    def save_and_run(self) -> None:
        self.save_all()
        
        subprocess.run(["python", "runPipeline.py"])


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg=BG_COL)
    app = ConfigEditor(root=root)
    root.mainloop()
