import glob
import json
import numpy as np
import os


SEQUENCES_PATH = "Z:\\Programs\\Python\\osumania-levelgen\\data\\sequences"


class FeatureNormalizer():
    def __init__(self, stats_file : str = "feature_norm_stats.json"):
        with open(stats_file, "r") as f:
            stats = json.load(f)
        
        self.means = np.array(stats["means"], dtype=np.float32)
        self.stds = np.array(stats["stds"], dtype=np.float32)
        
        # Prevent division by 0.
        self.stds[self.stds == 0] = 1.0
    
    def normalize(self, feature_array : np.ndarray) -> np.ndarray:
        """
        Normalize a feature array of shape (timesteps, 14)
        or (batch_size, timesteps, 14)

        Args:
            feature_array (np.ndarray): _The array of audio features._

        Returns:
            np.ndarray: _Normalized version of the features_array._
        """
        if feature_array.ndim == 2:
            return (feature_array - self.means) / self.stds
        elif feature_array.ndim == 3:
            return (feature_array - self.means[None, None, :]) / self.stds[None, None, :]
        else:
            raise ValueError(f"[featureNormalizer]: Invalid input shape {feature_array.shape} for normalization.")


def compute_feature_stats(sequences_path : str) -> None:
    """
    Compute mean and std for all audio features across all sequences in the training set.

    Args:
        sequences_path (str): _The root directory containing per-difficulty train/test .npy files._
    """
    count = 0
    mean = np.zeros(14, dtype=np.float32)
    M2 = np.zeros(14, dtype=np.float32)
    
    pattern = os.path.join(sequences_path, "*", "train", "*_seq_*.npy")
    files = glob.glob(pattern)
    
    if not files:
        raise RuntimeError(f"[featureNormalizer.compute_feature_stats] No sequence files found in {sequences_path}.")

    print(f"Streaming feature stats from {len(files)} files...")
    
    for f_idx, f_name in enumerate(files):
        print(f"[{f_idx+1}/{len(files)}] Processing {os.path.basename(f_name)}")
        
        arr = np.load(f_name, mmap_mode="r")
        
        feature_data = arr[:, :, :14].reshape(-1, 14)
        
        n = feature_data.shape[0]
        new_mean = feature_data.mean(axis=0)
        new_var = feature_data.var(axis=0) * n
        
        total = count + n
        delta = new_mean - mean
        
        mean += delta * (n / total)
        M2 += new_var + delta**2 * (count * n / total)
        
        count = total
    
    std = np.sqrt(M2 / max(count - 1, 1))
    
    stats = {
        "means": mean.tolist(),
        "stds": std.tolist()
    }
    
    with open("feature_norm_stats.json", "w") as f:
        json.dump(stats, f, indent=4)
    
    print(f"\nSaved feature stats to 'feature_norm_stats.json'.")
    
    for i, (m, s) in enumerate(zip(mean, std)):
        print(f"Feature {i:2d}: mean = {m:.6f} | std = {s:.6f}")


if __name__ == "__main__":
    compute_feature_stats(sequences_path=SEQUENCES_PATH)
