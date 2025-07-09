import argparse
import glob
import json
import numpy as np
import os
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--input_dir", type=str, default=os.path.join(os.getcwd(), "data", "preprocessed"))
args = parser.parse_args()



if __name__ == "__main__":
    feature_cols = [ i for i in range(7) ]
    all_data = []
    
    for f_name in glob.glob(args.input_dir + r"\**\bm_*.csv", recursive=True):
        df = pd.read_csv(f_name)
        all_data.append(df.values)
    
    all_data = np.concatenate(all_data, axis=0)
    
    means = []
    stds = []
    
    for col in feature_cols:
        means.append(float(np.mean(all_data[:, col])))
        stds.append(float(np.std(all_data[:, col])))
    
    with open("feature_norm_stats.json", "w") as f:
        json.dump({"means": means, "stds": stds}, f)
    
    print("Saved normalization stats:", means, stds)
