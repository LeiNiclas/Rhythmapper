import json
import os
import subprocess
import sys


def run_step(cmd, step_name):
    print(f"\n=== Running: {step_name} ===")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"Step '{step_name}' failed with exit code {result.returncode}. Stopping pipeline.")
        sys.exit(result.returncode)


def main():
    config_model = None
    config_paths = None
    config_generation = None
    
    with open("config_model.json") as f:
        config_model = json.load(f)
        
    with open("config_paths.json") as f:
        config_paths = json.load(f)
    
    with open("config_generation.json") as f:
        config_generation = json.load(f)
    
    
    run_beatmap_downloader = bool(config_model.get("run_beatmap_downloader", False))
    run_beatmap_preprocessor = bool(config_model.get("run_beatmap_preprocessor", False))
    run_feature_normalizer = bool(config_model.get("run_feature_normalizer", False))
    run_sequence_splitter = bool(config_model.get("run_sequence_splitter", False))
    run_model_trainer = bool(config_model.get("run_model_trainer", False))
    run_level_generator = bool(config_generation.get("run_level_generator", False))

    # Step 1: Download beatmaps (optional, num_beatmapsets = 0)
    if run_beatmap_downloader:
        run_step([
            "python", "src/download_utils/beatmapDownloader.py",
            "--num_beatmapsets", str(config_model["download_beatmapsets"]),
            "--output_dir", config_paths["raw_data_path"]
        ], "Download Beatmaps")

    # Step 2: Preprocess beatmaps
    if run_beatmap_preprocessor:
        run_step([
            "python", "-m", "src.preprocessing.beatmapPreprocessor",
            "--note_precision", str(config_model["note_precision"]),
            "--input_dir", config_paths["raw_data_path"],
            "--output_dir", config_paths["preprocessed_data_path"]
        ], "Preprocess Beatmaps")

    # Step 3: Normalize features
    if run_feature_normalizer:
        run_step([
            "python", "src/data_utils/featureNormalizer.py",
            "--input_dir", config_paths["preprocessed_data_path"]
        ], "Normalize Features")

    # Step 4: Split sequences
    if run_sequence_splitter:
        run_step([
            "python", "src/data_utils/dataSequenceSplitter.py",
            "--sequence_length", str(config_model["sequence_length"]),
            "--input_dir", config_paths["preprocessed_data_path"]
        ], "Split Sequences")

    # Step 5: Train model
    if run_model_trainer:
        run_step([
            "python", "-m", "src.model.modelTrainer",
            "--difficulty_range", str(config_model["difficulty_range"]),
            "--max_vram_mb", str(config_model["max_vram_mb"]),
            "--note_precision", str(config_model["note_precision"]),
            "--sequence_length", str(config_model["sequence_length"]),
            "--output_dir", config_paths["model_dir"]
        ], "Train Model")

    # Step 6: Generate level
    if run_level_generator:
        run_step([
            "python", "src/model/levelGenerator.py",
            "--audio_bpm", str(config_generation["audio_bpm"]),
            "--audio_start_ms", str(config_generation["audio_start_ms"]),
            "--note_precision", str(config_model["note_precision"]),
            "--prediction_threshold", str(config_model["prediction_threshold"]),
            "--sequence_length", str(config_model["sequence_length"]),
            "--audio_file_path", config_paths["audio_file_path"],
            "--model_path", config_paths["model_for_generation_path"],
            "--output_dir", config_paths["generation_dir"],
            "--file_name", config_paths["generation_file_name"]
        ], "Generate Level")

    # Step 7: Run visualizer if enabled
    if config_generation.get("run_visualizer", False):
        beatmap_path = config_paths["visualizer_beatmap_path"]
        audio_path = config_paths["visualizer_audio_path"]
        
        if config_generation.get("visualizer_use_last_gen", True):
            beatmap_path = os.path.join(config_paths["generation_dir"], f"{config_paths['generation_file_name']}.osu")
            audio_path = config_paths["audio_file_path"]
        
        run_step([
            "python", "src/visualizer/visualizer.py",
            "--beatmap_path", beatmap_path,
            "--audio_path", audio_path
        ], "Run Visualizer")

if __name__ == "__main__":
    main()