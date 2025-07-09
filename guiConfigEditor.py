import json
import os
import tkinter as tk
import subprocess

from tkinter import filedialog, messagebox, ttk


# -------- Config paths --------
CONFIG_MODEL_PATH = "config_model.json"
CONFIG_PATHS_PATH = "config_paths.json"
CONFIG_GENERATION_PATH = "config_generation.json"
# ------------------------------

DIFFICULTY_OPTIONS = [ "0-1_stars", "1-2_stars", "2-3_stars", "3-4_stars", "4-5_stars", "5_stars_plus" ]

GUI_VERSION = "1.1"


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


class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Level Generation Editor v{GUI_VERSION}")
        
        self.model_config = load_json(CONFIG_MODEL_PATH)
        self.paths_config = load_json(CONFIG_PATHS_PATH)
        self.generation_config = load_json(CONFIG_GENERATION_PATH)
        
        self.create_widgets()

    
    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)
        
        self.download_frame = ttk.Frame(notebook)
        self.training_frame = ttk.Frame(notebook)
        self.generation_frame = ttk.Frame(notebook)
        
        notebook.add(self.download_frame, text="Download & Preprocess")
        notebook.add(self.training_frame, text="Sequence & Training")
        notebook.add(self.generation_frame, text="Generation & Visualizer")
        
        self.build_download_frame()
        self.build_training_frame()
        self.build_generation_frame()
        
        # Save buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Save", command=self.save_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Save & Run", command=self.save_and_run).pack(side="left", padx=5)
    
    
    def build_download_frame(self):
        self.add_path_entry(self.download_frame, "Raw Data Folder:", "raw_data_path")
        self.add_path_entry(self.download_frame, "Preprocessed Data Folder:", "preprocessed_data_path")
        
        self.add_spinbox(self.download_frame, "Number of Beatmapsets to download:", "download_beatmapsets", from_=100, to=2000)
        
        self.add_checkbox(self.download_frame, "Run Beatmap Downloader", "run_beatmap_downloader", config=self.model_config)
        self.add_checkbox(self.download_frame, "Run Beatmap Preprocessor", "run_beatmap_preprocessor", config=self.model_config)
    
    
    def build_training_frame(self):
        self.add_dropdown(self.training_frame, "Difficulty Range:", "difficulty_range", DIFFICULTY_OPTIONS)
        self.add_spinbox(self.training_frame, "Note Precision:", "note_precision", from_=1, to=8)
        self.add_spinbox(self.training_frame, "Sequence Length:", "sequence_length", from_=16, to=512)
        self.add_float_entry(self.training_frame, "Prediction Threshold:", "prediction_threshold")
        self.add_int_entry(self.training_frame, "Max VRAM for GPU Training (MB):", "max_vram_mb")

        self.add_checkbox(self.training_frame, "Run Feature Normalizer", "run_feature_normalizer", config=self.model_config)
        self.add_checkbox(self.training_frame, "Run Sequence Splitter", "run_sequence_splitter", config=self.model_config)
        self.add_checkbox(self.training_frame, "Run Model Trainer", "run_model_trainer", config=self.model_config)
    
    
    def build_generation_frame(self):
        self.add_file_entry(self.generation_frame, "Audio File to generate Beatmap for:", "audio_file_path")
        self.add_file_entry(self.generation_frame, "Model to use:", "model_for_generation_path")
        self.add_float_entry(self.generation_frame, "Audio BPM:", "audio_bpm", config=self.generation_config)
        self.add_int_entry(self.generation_frame, "Audio Start Time (ms):", "audio_start_ms", config=self.generation_config)
        self.add_str_entry(self.generation_frame, "Beatmap File Name:", "generation_file_name", config=self.paths_config)
        self.add_path_entry(self.generation_frame, "Generation Output Folder:", "generation_dir")

        self.add_checkbox(self.generation_frame, "Run Level Generator", "run_level_generator", config=self.generation_config)
        self.run_visualizer_var = self.add_checkbox(self.generation_frame, "Run Visualizer After Generation", "run_visualizer", config=self.generation_config)
        self.use_last_generated_level_var = self.add_checkbox(self.generation_frame, "Use Latest Generated file for Visualizer", "visualizer_use_last_gen", config=self.generation_config)

        ttk.Label(self.generation_frame, text="If not using the Latest Generated File, specify which Audio and File to Visualize:", padding=10).pack()
        
        # Optional manual selection for visualizer
        self.add_file_entry(self.generation_frame, "Visualizer Beatmap (.osu) File:", "visualizer_beatmap_path")
        self.add_file_entry(self.generation_frame, "Visualizer Audio File:", "visualizer_audio_path")

    
    def add_path_entry(self, frame : ttk.Frame, label : str, key) -> None:
        ttk.Label(frame, text=label).pack()
        var = tk.StringVar(value=self.paths_config.get(key, ""))
        ttk.Entry(frame, textvariable=var, width=50).pack(pady=2)
        ttk.Button(frame, text="Browse", command=lambda: var.set(filedialog.askdirectory())).pack()
        
        self.paths_config[key] = var
    
    
    def add_file_entry(self, frame : ttk.Frame, label : str, key) -> None:
        ttk.Label(frame, text=label).pack()
        var = tk.StringVar(value=self.paths_config.get(key, ""))
        ttk.Entry(frame, textvariable=var, width=50).pack(pady=2)
        ttk.Button(frame, text="Browse", command=lambda: var.set(filedialog.askopenfilename())).pack()
        
        self.paths_config[key] = var
    
    
    def add_dropdown(self, frame : ttk.Frame, label : str, key, options):
        ttk.Label(frame, text=label).pack()
        var = tk.StringVar(value=self.model_config.get(key, options[0]))
        ttk.Combobox(frame, textvariable=var, values=options, state="readonly").pack()
        
        self.model_config[key] = var

    
    def add_spinbox(self, frame : ttk.Frame, label : str, key, from_, to):
        ttk.Label(frame, text=label).pack()
        var = tk.IntVar(value=self.model_config.get(key, from_))
        ttk.Spinbox(frame, from_=from_, to=to, textvariable=var).pack()
        
        self.model_config[key] = var
    
    
    def add_float_entry(self, frame : ttk.Frame, label : str, key, config=None):
        cfg = config or self.model_config
        ttk.Label(frame, text=label).pack()
        var = tk.DoubleVar(value=cfg.get(key, 0.0))
        ttk.Entry(frame, textvariable=var).pack()
        
        cfg[key] = var
    
    
    def add_int_entry(self, frame : ttk.Frame, label : str, key, config=None):
        cfg = config or self.model_config
        ttk.Label(frame, text=label).pack()
        var = tk.IntVar(value=cfg.get(key, 0))
        ttk.Entry(frame, textvariable=var).pack()
        
        cfg[key] = var
    
    
    def add_str_entry(self, frame : ttk.Frame, label : str, key, config=None):
        cfg = config or self.model_config
        ttk.Label(frame, text=label).pack()
        var = tk.StringVar(value=cfg.get(key, ""))
        ttk.Entry(frame, textvariable=var).pack()
        
        cfg[key] = var
    
    
    def add_checkbox(self, frame : ttk.Frame, label : str, key, config):
        var = tk.BooleanVar(value=config.get(key, False))
        ttk.Checkbutton(frame, text=label, variable=var).pack(anchor="w")
        
        config[key] = var
        return var
    
    
    def save_all(self):
        save_json(CONFIG_MODEL_PATH, {k: try_get(v) for k, v in self.model_config.items()})
        save_json(CONFIG_PATHS_PATH, {k: try_get(v) for k, v in self.paths_config.items()})
        save_json(CONFIG_GENERATION_PATH, {k: try_get(v) for k, v in self.generation_config.items()})
        
        messagebox.showinfo("Saved", "Configuration saved successfully.")
    
    def save_and_run(self):
        self.save_all()
        
        subprocess.run(["python", "runPipeline.py"])
    
    
if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigEditor(root=root)
    root.mainloop()