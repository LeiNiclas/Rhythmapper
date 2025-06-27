import numpy as np
import math
import os
import pandas as pd

from glob import glob
from sklearn.model_selection import train_test_split


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
        np.save(os.path.join(file_path, fname), chunk)
        
        print(f"Saved {fname} with shape {chunk.shape}")


if __name__ == "__main__":
    preprocessed_root = "Z:\\Programs\\Python\\osumania-levelgen\\data\\preprocessed"
    sequence_length = 64

    print("Loading data...")
    all_data = load_all_preprocessed_csvs(preprocessed_root)
    print(f"Loaded data shape: {all_data.shape}")

    print("Creating sequences...")
    sequences = create_sequences(all_data, sequence_length)
    print(f"Total sequences: {len(sequences)}")

    print("Splitting train/test...")
    train_seqs, test_seqs = split_train_test(sequences)
    print(f"Train sequences: {len(train_seqs)}, Test sequences: {len(test_seqs)}")

    train_data_path = os.path.join(os.path.dirname(preprocessed_root), "sequences", "train")
    test_data_path = os.path.join(os.path.dirname(preprocessed_root), "sequences", "test")
    
    print("Splitting and saving train sequences...")
    split_and_save_sequences(train_seqs, train_data_path, "train_sequences", max_gb=1.0)
    print("Splitting and saving test sequences...")
    split_and_save_sequences(test_seqs, test_data_path, "test_sequences", max_gb=1.0)
