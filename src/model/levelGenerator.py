import argparse
import json
import librosa
import numpy as np
import os
import tensorflow as tf


parser = argparse.ArgumentParser()
parser.add_argument("--prediction_threshold", type=float, default=0.45)
parser.add_argument("--sequence_length", type=int, default=64)
parser.add_argument("--note_precision", type=int, default=2)
parser.add_argument("--audio_bpm", type=float, default=100)
parser.add_argument("--audio_start_ms", type=int, default=0)
parser.add_argument("--audio_file_path", type=str, default="")
parser.add_argument("--model_path", type=str, default=os.path.join(os.getcwd(), "models", "model-3-4_stars-P4-S128-V3.keras"))
parser.add_argument("--output_dir", type=str, default=os.path.join(os.getcwd(), "generation"))
parser.add_argument("--file_name", type=str, default="test")
args = parser.parse_args()

AUDIO_PATH = args.audio_file_path
MODEL_PATH = args.model_path
NORM_STATS_PATH = os.path.join(os.getcwd(), "feature_norm_stats.json")

AUDIO_BPM = args.audio_bpm
AUDIO_START_MS = args.audio_start_ms
SEQUENCE_LENGTH = args.sequence_length
THRESHOLD = args.prediction_threshold
NOTE_PRECISION = args.note_precision


def calculate_subbeat_timings(audio_path, audio_start_ms, audio_bpm, note_precision):
    ms_per_beat = 60_000 / audio_bpm
    ms_per_subbeat = ms_per_beat / note_precision
    
    y, sr = librosa.load(audio_path, sr=None)
    duration_ms = librosa.get_duration(y=y, sr=sr) * 1000
    
    num_subbeats = int((duration_ms - audio_start_ms) // ms_per_subbeat)
    
    subbeat_times_ms = [audio_start_ms + (i * ms_per_subbeat) for i in range(num_subbeats)]
    
    return subbeat_times_ms


def extract_features(audio_path, audio_bpm, audio_start_ms, sequence_length, note_precision, means, stds):
    y, sr = librosa.load(audio_path, sr=None)
    hop_length = 512
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=5, hop_length=hop_length).T
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

    # Ensure all arrays are aligned in time.
    max_frames = min(len(onset_env), len(rms), mfcc.shape[0])
    mfcc = mfcc[:max_frames]
    onset_env = onset_env[:max_frames]
    rms = rms[:max_frames]

    subbeat_times_ms = calculate_subbeat_timings(
        audio_path=audio_path,
        audio_start_ms=audio_start_ms,
        audio_bpm=audio_bpm,
        note_precision=note_precision
    )
     
    features = []
    
    # No need for subbeat_idxs.
    for t_ms in subbeat_times_ms:
        frame_idx = int((t_ms / 1000) * sr / hop_length)
        frame_idx = min(max(frame_idx, 0), max_frames - 1)
        
        feature_vector = list(mfcc[frame_idx])
        feature_vector.append(float(onset_env[frame_idx]))
        feature_vector.append(float(rms[frame_idx]))
        
        features.append(feature_vector)
    
    
    features = np.array(features)
    
    # -------- Normalize features --------
    if features.ndim == 2 and features.shape[0] > 0:
        for col in range(features.shape[1]):
            features[:, col] = (features[:, col] - means[col]) / (stds[col] + 1e-6)
    else:
        raise ValueError(f"Feature extraction failed: features shape is {features}")
    # ---------------------------------
    
    n = features.shape[0]
    n_trim = n - (n % sequence_length)
    
    features = features[:n_trim]
    features = features.reshape(-1, sequence_length, features.shape[1])
    
    return features


def post_process_predictions(raw_predictions):
    preds_binary = (raw_predictions > THRESHOLD).astype(int)
    
    return preds_binary


def convert_predictions_to_gblf_format(raw_predictions, post_processed_predictions, subbeat_timings):
    gblf_contents = ""
    
    for i, (raw_prediction, post_processed_prediction) in enumerate(zip(raw_predictions, post_processed_predictions)):
        pred_line = f"{int(subbeat_timings[i])}|"
        
        for j in range(len(raw_prediction) - 1):
            pred_line += f"{post_processed_prediction[j]}:{raw_prediction[j]:.3f}|"
        
        pred_line += f"{post_processed_prediction[-1]}:{raw_prediction[-1]:.3f}"
    
        gblf_contents += pred_line + "\n"
    
    return gblf_contents


def main():
    stats = None
    
    with open(NORM_STATS_PATH, "r") as f:
        stats = json.load(f)
    
    means = stats["means"]
    stds = stats["stds"]
    
    features = extract_features(
        audio_path=AUDIO_PATH,
        audio_bpm=AUDIO_BPM,
        audio_start_ms=AUDIO_START_MS,
        sequence_length=SEQUENCE_LENGTH,
        note_precision=NOTE_PRECISION,
        means=means,
        stds=stds
    )
    
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    preds = model.predict(features)
    preds = preds.reshape(-1, preds.shape[-1])
    preds_bin = post_process_predictions(preds)
    
    note_density = np.mean(preds_bin)
    
    print("Predictions stats:")
    print("Min:", np.min(preds))
    print("Max:", np.max(preds))
    print("Mean:", np.mean(preds))
    print(f"Note density: {note_density}")
    
    subbeat_timings = calculate_subbeat_timings(
        audio_path=AUDIO_PATH,
        audio_start_ms=AUDIO_START_MS,
        audio_bpm=AUDIO_BPM,
        note_precision=NOTE_PRECISION
    )
    
    gblf_contents = convert_predictions_to_gblf_format(
        raw_predictions=preds,
        post_processed_predictions=preds_bin,
        subbeat_timings=subbeat_timings
    )

    output_path = os.path.join(args.output_dir, args.file_name)
    
    with open(f"{output_path}.gblf", "w", encoding="utf-8") as f:
        f.write(gblf_contents)


if __name__ == "__main__":
    main()