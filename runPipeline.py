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
    run_sequence_splitter = bool(config["run_sequence_splitter"])
    run_mfcc_normalizer = bool(config["run_mfcc_normalizer"])
    run_model_trainer = bool(config["run_model_trainer"])
    run_level_generator = bool(config["run_level_generator"])

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

    # Step 3: Split sequences
    if run_sequence_splitter:
        run_step([
            "python", "src/data_utils/dataSequenceSplitter.py",
            "--sequence_length", str(config["sequence_length"])
        ], "Split Sequences")

    # Step 4: Normalize MFCCs
    if run_mfcc_normalizer:
        run_step([
            "python", "src/data_utils/mfccNormalizer.py"
        ], "Normalize MFFCs")

    # Step 5: Train model
    if run_model_trainer:
        run_step([
            "python", "-m", "src.model.modelTrainer"
        ], "Train Model")

    # Step 6: Generate level
    if run_level_generator:
        run_step([
            "python", "src/model/levelGenerator.py"
        ], "Generate Level")


if __name__ == "__main__":
    main()