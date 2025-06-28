import numpy as np
import glob
import json


if __name__ == "__main__":
    mfcc_cols = [1, 2, 3, 4, 5]
    all_data = []
    
    for fname in glob.glob(r"Z:\Programs\Python\osumania-levelgen\data\sequences\*\train\*_train_sequences_*.npy"):
        arr = np.load(fname, mmap_mode="r")
        all_data.append(arr)
    
    all_data = np.concatenate(all_data, axis=0)
    
    means = []
    stds = []
    
    for col in mfcc_cols:
        means.append(float(np.mean(all_data[:, :, col])))
        stds.append(float(np.std(all_data[:, :, col])))
    
    with open("mfcc_norm_stats.json", "w") as f:
        json.dump({"means": means, "stds": stds}, f)
    
    print("Saved normalization stats:", means, stds)
