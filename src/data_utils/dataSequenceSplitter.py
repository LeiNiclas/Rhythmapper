import argparse
import math
import numpy as np
import os
import pandas as pd

from glob import glob
from sklearn.model_selection import train_test_split

import featureNormalizer as fn


parser = argparse.ArgumentParser()
parser.add_argument("--sequence_length", type=int, default=64)
parser.add_argument("--normalize", type=str, default="True")
args = parser.parse_args()


def load_all_preprocessed_csvs(preprocessed_root : str) -> np.ndarray:
    """
    Load data from the preprocessed CSV-files.

    Args:
        preprocessed_root (str): _The path to the preprocessed CSV-files._

    Raises:
        RuntimeError: _No valid data in preprocessed CSV-files available._

    Returns:
        ndarray: _All data from the preprocessed CSV-files as a single numpy array._
    """
    csv_files = glob(os.path.join(preprocessed_root, "*", "bm_*.csv"))
    data = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            # Skip empty files.
            if df.empty:
                print(f"Warning: {csv_file} is empty, skipping.")
                continue
            
            data.append(df.values)
        except pd.errors.EmptyDataError:
            print(f"Warning: {csv_file} is empty or invalid, skipping.")
            continue
    
    if not data:
        raise RuntimeError("No valid data found in preprocessed CSVs.")
    
    all_data = np.concatenate(data, axis=0)
    
    return all_data


def create_sequences(data : np.ndarray, sequence_length : int) -> np.ndarray:
    """
    Split the data into overlapping sequences of a given length.

    Args:
        data (np.ndarray): _The full dataset as a numpy array._
        sequence_length (int): _The length of each sequence._

    Returns:
        np.ndarray: _Array with the shape (num_sequences, sequence_length, num_features)._
    """
    sequences = []
    
    for i in range(len(data) - sequence_length):
        seq = data[i:i+sequence_length]
        sequences.append(seq)
    
    return np.array(sequences)


def split_train_test(sequences : np.ndarray, test_ratio : float = 0.2, random_state : int = 42) -> list:
    """
    Split the sequences into train and test sets.

    Args:
        sequences (np.ndarray): _The full set of sequences._
        test_ratio (float, optional): _Fraction of data to use for testing._ Defaults to 0.2.
        random_state (int, optional): _Random seed for reproducabilty._ Defaults to 42.

    Returns:
        list: _Train test split with the format (train_sequences, test_sequences)._
    """
    return train_test_split(sequences, test_size=test_ratio, random_state=random_state)


def create_and_save_sequences_by_difficulty(preprocessed_root : str, sequence_length : int, out_dir : str, max_gb : float = 1.0, test_ratio : float = 0.2, normalize : bool = True) -> None:
    """
    Split the data into multiple train and test .npy-files,
    each up to max_gb in size.

    Args:
        preprocessed_root (str): _The directory to the preprocessed data._
        sequence_length (int): _The length of individual sequences._
        out_dir (str): _The output directory for the output file names._
        max_gb (float, optional): _The maximum size in GB for each file._ Defaults to 1.0.
        test_ratio (float, optional): _Fraction of data to use for testing._ Defaults to 0.2.
        normalize (bool, optional): _Whether or not to normalize audio feature data._ Defaults to True.
    """
    normalizer = fn.FeatureNormalizer() if normalize else None
    
    for difficulty_label in os.listdir(preprocessed_root):
        diff_dir = os.path.join(preprocessed_root, difficulty_label)
        
        if not os.path.isdir(diff_dir):
            continue
        
        csv_files = glob(os.path.join(diff_dir, "bm_*.csv"))
        
        print(len(csv_files))
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                if df.empty:
                    continue
                
                data = df.values
                
                # Drop subbeat_idx
                if data.shape[1] == 19:
                    data = data[:, 1:]
                    
                sequences = create_sequences(data=data, sequence_length=sequence_length)
                
                if sequences.size == 0:
                    continue
                
                if normalize:
                    sequences[:, :, :14] = normalizer.normalize(sequences[:, :, :14])
                
                # Save directly as chunked files
                diff_out_dir = os.path.join(out_dir, difficulty_label)
                train_dir = os.path.join(diff_out_dir, "train")
                test_dir = os.path.join(diff_out_dir, "test")
                
                train_sequences, test_sequences = split_train_test(sequences=sequences, test_ratio=test_ratio)
                
                print(f"{os.path.basename(csv_file)} - Train: {len(train_sequences)}, Test: {len(test_sequences)}")
                
                save_sequences_chunked(train_sequences, train_dir, os.path.basename(csv_file).replace(".csv", "_train"))
                save_sequences_chunked(test_sequences, test_dir, os.path.basename(csv_file).replace(".csv", "_test"))
                
            except Exception:
                continue
        

def split_and_save_sequences(sequences : np.ndarray, file_path : str, out_prefix : str, max_gb : float = 1.0) -> None:
    """
    Split a large sequence array into multiple .npy files,
    each up to max_gb in size.

    Args:
        sequences (np.ndarray): _The full set of sequences to split and save._
        file_path (_type_): _The directory where the split files will be saved._
        out_prefix (_type_): _The Prefix for the output file names._
        max_gb (float, optional): _The maximum size in GB for each file._ Defaults to 1.0.
    """
    if os.path.exists(file_path):
        # Remove all files in the directory
        for fname in os.listdir(file_path):
            fpath = os.path.join(file_path, fname)
            
            if os.path.isfile(fpath):
                os.remove(fpath)
    else:
        os.makedirs(file_path, exist_ok=True)
    
    # Calculate bytes per sequence
    bytes_per_seq = sequences[0].nbytes
    seqs_per_file = int((max_gb * 1024**3) // bytes_per_seq)
    total_seqs = len(sequences)
    num_files = math.ceil(total_seqs / seqs_per_file)
    
    print(f"Splitting {total_seqs} sequences into {num_files} files, ~{seqs_per_file} sequences per file.")

    for i in range(num_files):
        start = i * seqs_per_file
        end = min((i+1) * seqs_per_file, total_seqs)
        chunk = sequences[start:end]
        fname = f"{out_prefix}_{i+1}.npy"
        
        os.makedirs(file_path, exist_ok=True)
        np.save(os.path.join(file_path, fname), chunk)
        
        print(f"Saved {fname} with shape {chunk.shape}")


def save_sequences_chunked(sequences : np.ndarray, out_dir : str, base_name : str, chunk_size : int = 10000):
    os.makedirs(out_dir, exist_ok=True)
    total = len(sequences)
    chunks = int(np.ceil(total / chunk_size))
    
    for i in range(chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, total)
        chunk = sequences[start:end]
        
        chunk = chunk.astype(np.float32)
        
        f_name = f"{base_name}_seq_{i:03d}.npy"
        np.save(os.path.join(out_dir, f_name), chunk)
        
        print(f"Saved {f_name} with shape {chunk.shape}")


def main():
    preprocessed_root = "Z:\\Programs\\Python\\osumania-levelgen\\data\\preprocessed"

    print("Creating and saving sequences by difficulty (with splitting)...")
    
    normalize = args.normalize.lower() == "true"
    
    create_and_save_sequences_by_difficulty(
        preprocessed_root=preprocessed_root,
        sequence_length=args.sequence_length,
        out_dir=os.path.join(os.path.dirname(preprocessed_root), "sequences"),
        max_gb=0.5,
        test_ratio=0.2,
        normalize=normalize
    )


if __name__ == "__main__":
    main()
