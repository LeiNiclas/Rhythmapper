import numpy as np
import tensorflow as tf
import glob
import os


def npy_file_generator(file_pattern : str):
    """
    Generator that yields batches from each .npy-file
    matching the pattern file_pattern.

    Args:
        file_pattern (str): _The file pattern to check for .npy-files._

    Yields:
        _type_: _Sequence data from a .npy-file._
    """
    # Get all .npy-files that match the given pattern.
    files = sorted(glob.glob(file_pattern))
    
    # Load all files.
    for fname in files:
        # print(f"Loading {fname} ...")
        
        arr = np.load(fname, mmap_mode='r')
        
        for seq in arr:
            yield seq


def get_tf_dataset(file_pattern : str, batch_size : int = 64, shuffle_buffer : int = 10000) -> tf.data.Dataset:
    """
    Create a tf.data.Dataset from chunked .npy files.

    Args:
        file_pattern (str): _The file pattern to check for .npy-files._
        batch_size (int, optional): _The batch size of the loaded sequences._ Defaults to 64.
        shuffle_buffer (int, optional): _The number of elements from which
            the new batch will be randomly sampled when shuffling the dataset._ Defaults to 10000.

    Returns:
        tf.data.Dataset: _A dataset created from chunks of .npy-files._
    """
    # Infer shape and dtype from the first file.
    first_file = sorted(glob.glob(file_pattern))[0]
    sample = np.load(first_file, mmap_mode='r')[0]
    
    output_shape = sample.shape
    output_dtype = sample.dtype

    ds = tf.data.Dataset.from_generator(
        lambda: npy_file_generator(file_pattern),
        output_signature=tf.TensorSpec(shape=output_shape, dtype=output_dtype)
    )
    
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    
    return ds


def get_difficulty_dataset(sequences_root : str, difficulty : str, split : str = "train", batch_size : int = 64, shuffle_buffer : int = 10000) ->tf.data.Dataset:
    """
    Load a tf.data.Dataset for a specific difficulty and split.

    Args:
        sequences_root (str): _Root directory where difficulty folders are stored._
        difficulty (str): _Difficulty label (e.g. "Insane", "Easy", etc.)._
        split (str, optional): _Which split to load ("train" or "test")._ Defaults to "train".
        batch_size (int, optional): _Batch size._ Defaults to 64.
        shuffle_buffer (int, optional): _Shuffle buffer size._ Defaults to 10000.

    Returns:
        tf.data.Dataset: _A dataset for the specified difficulty and split._
    """
    pattern = os.path.join(sequences_root, difficulty, split, f"{difficulty}_{split}_sequences_*.npy")
    return get_tf_dataset(pattern, batch_size=batch_size, shuffle_buffer=shuffle_buffer)
