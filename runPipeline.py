import argparse
import json
import subprocess
import sys


def run_step(cmd, step_name):
    print(f"\n=== Running: {step_name} ===")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"Step '{step_name}' failed with exit code {result.returncode}. Stopping pipeline.")
        sys.exit(result.returncode)


def main():
    with open("config.json") as f:
        config = json.load(f)
    
    run_beatmap_downloader = bool(config["run_beatmap_downloader"])
    run_beatmap_preprocessor = bool(config["run_beatmap_preprocessor"])
    run_sequence_splitter_raw = bool(config["run_sequence_splitter_raw"])
    run_sequence_splitter_normalized = bool(config["run_sequence_splitter_normalized"])
    run_model_trainer = bool(config["run_model_trainer"])
    run_level_generator = bool(config["run_level_generator"])
    run_feature_stat_computation = bool(config["run_feature_stat_computation"])

    # Step 1: Download beatmaps (optional, num_beatmapsets = 0)
    if run_beatmap_downloader:
        run_step([
            "python", "src/download_utils/beatmapDownloader.py",
            "--num_beatmapsets", str(config["download_beatmapsets"])
        ], "Download Beatmaps")

    # Step 2: Preprocess beatmaps
    if run_beatmap_preprocessor:
        run_step([
            "python", "-m", "src.preprocessing.beatmapPreprocessor",
            "--note_precision", str(config["note_precision"])
        ], "Preprocess Beatmaps")

    # Step 3: Split and save raw sequences (Unnormalized)
    if run_sequence_splitter_raw:
        run_step([
            "python", "src/data_utils/dataSequenceSplitter.py",
            "--sequence_length", str(config["sequence_length"]),
            "--normalize", "False"
        ], "Split Sequences (raw)")
    
    # Step 4: Compute normalization stats
    if run_feature_stat_computation:
        run_step([
            "python", "src/data_utils/featureNormalizer.py"
        ], "Compute Feature Statistics")
    
    # Step 5: Split again with normalization
    if run_sequence_splitter_normalized:
        run_step([
            "python", "src/data_utils/dataSequenceSplitter.py",
            "--sequence_length", str(config["sequence_length"]),
            "--normalize", "True"
        ], "Split Sequences (normalized)")

    # Step 6: Train model
    if run_model_trainer:
        run_step([
            "python", "-m", "src.model.modelTrainer",
            "--difficulty_range", str(config["difficulty_range"]),
            "--max_vram_mb", str(config["max_vram_mb"]),
            "--note_precision", str(config["note_precision"]),
            "--sequence_length", str(config["sequence_length"])
        ], "Train Model")

    # Step 7: Generate level
    if run_level_generator:
        run_step([
            "python", "src/model/levelGenerator.py",
            "--audio_bpm", str(config["audio_bpm"]),
            "--audio_start_ms", str(config["audio_start_ms"]),
            "--note_precision", str(config["note_precision"]),
            "--prediction_threshold", str(config["prediction_threshold"]),
            "--sequence_length", str(config["sequence_length"])
        ], "Generate Level")


if __name__ == "__main__":
    main()