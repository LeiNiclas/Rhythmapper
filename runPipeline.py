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
    config = None
    
    with open("json\\config.json") as f:
        config = json.load(f)
    
    config_training = config["Training"]
    config_generation = config["Generation"]
    config_model = config["Model"]
    config_pipeline = config["Pipeline"]
    config_paths = config["Paths"]
    
    # Pipeline
    run_beatmap_downloader = bool(config_pipeline.get("run_beatmap_downloader", False))
    run_beatmap_preprocessor = bool(config_pipeline.get("run_beatmap_preprocessor", False))
    run_feature_normalizer = bool(config_pipeline.get("run_feature_normalizer", False))
    run_sequence_splitter = bool(config_pipeline.get("run_sequence_splitter", False))
    run_model_trainer = bool(config_pipeline.get("run_model_trainer", False))
    run_level_generator = bool(config_pipeline.get("run_level_generator", False))
    run_visualizer = bool(config_pipeline.get("run_visualizer", False))
    
    # Training config
    download_beatmapsets = str(config_training["download_beatmapsets"])
    note_precision = str(config_training["note_precision"])
    sequence_length = str(config_training["sequence_length"])
    split_all_difficulty_sequences = config_training["split_all_difficulty_sequences"]
    difficulty_range = str(config_training["difficulty_range"])
    max_vram_mb = str(config_training["max_vram_mb"])
    training_epochs = str(config_training["training_epochs"])
    
    # Generation config
    audio_bpm = str(config_generation["audio_bpm"])
    audio_start_ms = str(config_generation["audio_start_ms"])
    
    # Model config
    prediction_threshold = str(config_model["prediction_threshold"])
    use_auto_threshold = str(config_model["use_auto_threshold"])
    auto_threshold_percentile = str(config_model["auto_threshold_percentile"])
    
    # Paths config
    raw_data_path = config_paths["raw_data_path"]
    preprocessed_data_path = config_paths["preprocessed_data_path"]
    model_dir = config_paths["model_dir"]
    audio_file_path = config_paths["audio_file_path"]
    model_for_generation_path = config_paths["model_for_generation_path"]
    generation_dir = config_paths["generation_dir"]
    generation_file_name = config_paths["generation_file_name"]

    
    # Step 1: Download beatmaps (optional, num_beatmapsets = 0)
    if run_beatmap_downloader:
        run_step([
            "python", "src/download_utils/beatmapDownloader.py",
            "--num_beatmapsets", download_beatmapsets,
            "--output_dir", raw_data_path
        ], "Download Beatmaps")

    # Step 2: Preprocess beatmaps
    if run_beatmap_preprocessor:
        run_step([
            "python", "-m", "src.preprocessing.beatmapPreprocessor",
            "--note_precision", note_precision,
            "--input_dir", raw_data_path,
            "--output_dir", preprocessed_data_path
        ], "Preprocess Beatmaps")

    # Step 3: Normalize features
    if run_feature_normalizer:
        run_step([
            "python", "src/data_utils/featureNormalizer.py",
            "--input_dir", preprocessed_data_path
        ], "Normalize Features")

    # Step 4: Split sequences
    if run_sequence_splitter:
        difficulty_arg = f"--difficulty_range="
        difficulty_arg += difficulty_range if not split_all_difficulty_sequences else "all"
        
        run_step([
            "python", "src/data_utils/dataSequenceSplitter.py",
            "--sequence_length", sequence_length,
            "--input_dir", preprocessed_data_path,
            difficulty_arg
        ], "Split Sequences")

    # Step 5: Train model
    if run_model_trainer:
        run_step([
            "python", "-m", "src.model.modelTrainer",
            "--difficulty_range", difficulty_range,
            "--max_vram_mb", max_vram_mb,
            "--note_precision", note_precision,
            "--sequence_length", sequence_length,
            "--output_dir", model_dir,
            "--epochs", training_epochs
        ], "Train Model")

    # Step 6: Generate level
    if run_level_generator:
        run_step([
            "python", "src/model/levelGenerator.py",
            "--audio_bpm", audio_bpm,
            "--audio_start_ms", audio_start_ms,
            "--note_precision", note_precision,
            "--sequence_length", sequence_length,
            "--audio_file_path", audio_file_path,
            "--model_path", model_for_generation_path,
            "--output_dir", generation_dir,
            "--file_name", generation_file_name,
            "--prediction_threshold", prediction_threshold,
            "--use_auto_threshold", use_auto_threshold,
            "--auto_threshold_percentile", auto_threshold_percentile
        ], "Generate Level")

    # Step 7: Run visualizer if enabled
    if run_visualizer:
        beatmap_path = os.path.join(config_paths["generation_dir"], f"{config_paths['generation_file_name']}.rthm")
        audio_path = config_paths["audio_file_path"]
        
        run_step([
            "python", "src/visualizer/visualizer.py",
            "--beatmap_path", beatmap_path,
            "--audio_path", audio_path
        ], "Run Visualizer")


if __name__ == "__main__":
    main()
