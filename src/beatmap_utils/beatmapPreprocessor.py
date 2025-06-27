from . import beatmapFeatureExtractor as bmfe
from . import beatmapFilter as bmf

import numpy as np
import os


def preprocess_beatmap(beatmapset_path : str, beatmap_ID : int) -> None:
    """
    Preprocesses a given beatmap and saves the normalized data to a CSV-file.

    Args:
        beatmapset_path (str): _The path to the beatmapset of the given beatmap._
        beatmap_ID (int): _The ID of the given beatmap._
    """    
    normalized_merged_data = bmfe.get_merged_beatmap_data(beatmapset_path=beatmapset_path, beatmap_ID=beatmap_ID)
    
    # Early exit if beatmap data cannot be retrieved.
    if normalized_merged_data is None:
        return
    
    is_4k_beatmap, difficulty_label = bmf.filter_beatmap(beatmap_ID=beatmap_ID, keys=4)

    # Early exit if beatmap is not 4k.
    if not is_4k_beatmap:
        return
    
    # Construct the path to the preprocessed data folder.
    preprocess_file_path = os.path.join(
        os.path.dirname(os.path.dirname(beatmapset_path)),
        "preprocessed",
        difficulty_label,
        f"bm_{beatmap_ID}.csv"
    )
    
    fmt = [
        '%d',
        '%.6f',
        '%.6f',
        '%.6f',
        '%.6f',
        '%.6f',
        '%.6f',
        '%d',
        '%d',
        '%d',
        '%d'
    ]
    
    normalized_merged_data = np.array(normalized_merged_data)
    
    if normalized_merged_data.shape[1] != len(fmt):
        print(f"Column mismatch for {preprocess_file_path}: {normalized_merged_data.shape[1]} columns found.")
        return
    
    # Save data to a csv file.
    np.savetxt(
        preprocess_file_path,
        normalized_merged_data,
        delimiter=',',
        header="subbeat_idx,mfcc0,mfcc1,mfcc2,mfcc3,mfcc4,onset,lane0,lane1,lane2,lane3",
        comments='',
        fmt=fmt
    )


def preprocess_all_raw_beatmapsets(raw_beatmapsets_data_path : str) -> None:
    beatmapsets = os.listdir(raw_beatmapsets_data_path)
    total_beatmapsets = len(beatmapsets)
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    
    preprocessed_root = os.path.join(os.path.dirname(raw_beatmapsets_data_path), "preprocessed")
    existing_files = set()
    
    for difficulty_label in os.listdir(preprocessed_root):
        diff_dir = os.path.join(preprocessed_root, difficulty_label)
        
        for beatmap_file in os.listdir(diff_dir):
            existing_files.add(beatmap_file)
    
    for i, beatmapset in enumerate(beatmapsets):
        beatmapset_path = os.path.join(raw_beatmapsets_data_path, beatmapset)
        beatmaps = [beatmap for beatmap in os.listdir(beatmapset_path) if beatmap.startswith("bm")]
        total_beatmaps = len(beatmaps)
        
        for j, beatmap in enumerate(beatmaps):
            # Filter the beatmap first.
            beatmap_ID = int(beatmap.split('_')[-1].split('.')[0])
            
            # Skip beatmap(set) if already converted.
            if (f"bm_{beatmap_ID}.csv") in existing_files:
                break
            
            preprocess_beatmap(beatmapset_path=beatmapset_path, beatmap_ID=beatmap_ID)

            bar_length = 16
            progress = int(bar_length * (j+1) / total_beatmaps)
            bar = '[' + progress * '=' + (bar_length - progress) * ' ' + ']'

            print(
                f"\rProcessed {j+1}/{total_beatmaps} beatmaps of set with ID {beatmapset.split('_')[1]}: "+
                f"{bar} ({((j+1)/total_beatmaps)*100:.1f}%)",
                end='',
                flush=True
            )
        print()
        print(
            f"Processed Beatmapsets: {i+1}/{total_beatmapsets} ({((i+1)/total_beatmapsets)*100:.2f}%)",
            flush=True
        )
    
    print("\nPreprocessing complete.")
    print(f"{68*'='}")


if __name__ == "__main__":
    preprocess_all_raw_beatmapsets("Z:\\Programs\\Python\\osumania-levelgen\\data\\raw")
