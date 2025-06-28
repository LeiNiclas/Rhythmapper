import numpy as np
import math
import os
import pandas as pd

from glob import glob
from sklearn.model_selection import train_test_split


SEQUENCE_LENGTH = 64


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


def create_and_save_sequences_by_difficulty(preprocessed_root : str, sequence_length : int, out_dir : str, max_gb : float = 1.0, test_ratio :  float = 0.2) -> None:
    """
    Split the data into multiple train and test .npy-files,
    each up to max_gb in size.

    Args:
        preprocessed_root (str): _The directory to the preprocessed data._
        sequence_length (int): _The length of individual sequences._
        out_dir (str): _The output directory for the output file names._
        max_gb (float, optional): _The maximum size in GB for each file._ Defaults to 1.0.
        test_ratio (float, optional): _Fraction of data to use for testing._ Defaults to 0.2.
    """
    for difficulty_label in os.listdir(preprocessed_root):
        diff_dir = os.path.join(preprocessed_root, difficulty_label)
        
        if not os.path.isdir(diff_dir):
            continue
        
        csv_files = glob(os.path.join(diff_dir, "bm_*.csv"))
        data = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                
                if df.empty:
                    continue
                
                data.append(df.values)
            except Exception:
                continue
        
        if not data:
            continue
        
        all_data = np.concatenate(data, axis=0)
        
        # Create sequences for this difficulty
        sequences = create_sequences(all_data, sequence_length=sequence_length)
        
        # -------- Normalization of MFCC columns --------
        mfcc_cols = [1, 2, 3, 4, 5]
        
        for col in mfcc_cols:
            mean = np.mean(sequences[:, :, col])
            std = np.std(sequences[:, :, col])
            sequences[:, :, col] = (sequences[:, :, col] - mean) / (std + 1e-8)
        # -----------------------------------------------
        
        print(f"Total sequences for {difficulty_label}: {len(sequences)}")

        # Split into train and test
        train_sequences, test_sequences = split_train_test(sequences=sequences, test_ratio=test_ratio)
        print(f"Train: {len(train_sequences)}, Test: {len(test_sequences)}")

        # Save and split by max_gb
        diff_out_dir = os.path.join(out_dir, difficulty_label)
        split_and_save_sequences(train_sequences, os.path.join(diff_out_dir, "train"), f"{difficulty_label}_train_sequences", max_gb=max_gb)
        split_and_save_sequences(test_sequences, os.path.join(diff_out_dir, "test"), f"{difficulty_label}_test_sequences", max_gb=max_gb)


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
        
        os.makedirs(file_path, exist_ok=True)
        np.save(os.path.join(file_path, fname), chunk)
        
        print(f"Saved {fname} with shape {chunk.shape}")


if __name__ == "__main__":
    preprocessed_root = "Z:\\Programs\\Python\\osumania-levelgen\\data\\preprocessed"

    print("Creating and saving sequences by difficulty (with splitting)...")
    create_and_save_sequences_by_difficulty(
        preprocessed_root=preprocessed_root,
        sequence_length=SEQUENCE_LENGTH,
        out_dir=os.path.join(os.path.dirname(preprocessed_root), "sequences"),
        max_gb=0.25
    )
