import matplotlib.pyplot as plt
import numpy as np
import os
import librosa


def get_beatmap_BPM(beatmap_file_contents : list[str]) -> tuple[float]:
    """
    Retrieve the BPM of a beatmap through its file contents.

    Args:
        beatmap_file_contents (list[str]): _The contents of the beatmap file._

    Returns:
        tuple[float]: _The BPM and start timing of the BPM in milliseconds._
    """
    for i, line in enumerate(beatmap_file_contents):
        if (line.startswith("[TimingPoints]")):
            # The timing of the BPM data is stored in the first entry of the first timing point line.
            start_time_ms = float(beatmap_file_contents[i+1].split(",")[0])
            
            # BPM data is stored in the second entry of the first timing point line.
            # The BPM value is stored as bpm = 1 / entry * 60000.
            bpm = float(beatmap_file_contents[i+1].split(",")[1])
            bpm = 1.0 / bpm * 60_000
            
            return bpm, start_time_ms


def get_hit_object_timings(beatmap_file_contents : list[str]) ->list[list]:
    """
    Retrieve the HitObject timings of a beatmap through its file contents. 

    Args:
        beatmap_file_contents (list[str]): _The contents of the beatmap file._

    Returns:
        list[list]: _HitObject data with entries in the format
        [timing_ms, lane0, ..., lane3]._
    """
    for i, line in enumerate(beatmap_file_contents):
        if (line.startswith("[HitObjects]")):
            all_timing_data = []
            
            # Timing data has the format [timing_ms, lane0, ..., lane3].
            current_timing_data = [0, 0, 0, 0, 0]
            
            for hit_object_info in beatmap_file_contents[i+1:]:
                # Skip empty lines.
                if hit_object_info.isspace():
                    continue
                
                # Important HitObject data are at positions 0 and 2:
                # lane, -, timing, -, ...
                timing_ms = float(hit_object_info.split(',')[2])
                lane_id = (int(hit_object_info.split(',')[0]) - 64) // 128

                # There is already a note present for the current timing.
                if current_timing_data[0] == timing_ms:
                    current_timing_data[lane_id + 1] = 1
                # The note timing is not present yet
                # HitObject is placed at a new timing.
                else:
                    all_timing_data.append(current_timing_data)
                    current_timing_data = [timing_ms, 0, 0, 0, 0]
                    current_timing_data[lane_id + 1] = 1
            
            return all_timing_data


def get_beatmap_timings(beatmapset_path : str, beatmap_ID : int, note_precision : int = 4) -> list[list]:
    """
    Retrieve normalized HitObject timings for a given beatmap. 

    Args:
        beatmapset_path (str): _The path to the beatmapset of the given beatmap._
        beatmap_ID (int): _The ID of the given beatmap._
        note_precision (int): _The precision at which subbeats are generated.
            The value should be a power of 2.
            For note_precision = 1, subbeats are captured in quarter note timings,
            for note_precision = 2, subbeats are captured in 1/2 quarter note = eigth note timings, and so on._
            Defaults to 4. 

    Returns:
        list[list]: _normalized HitObject data with entries in the format
        [subbeat_idx, timing_ms, lane0, ..., lane3]._
    """
    file_contents = []
    file_path = os.path.join(beatmapset_path, f"bm_{beatmap_ID}.osz")
    
    # Read the file contents of the beatmap to forward it to the other helper methods.
    with open(file_path, "r", encoding="utf-8") as beatmap:
        file_contents = beatmap.readlines()

    # Retrieve the BPM, the start timing of the BPM and the HitObject timings.
    bpm, start_time_ms = get_beatmap_BPM(file_contents)
    hit_object_timings = get_hit_object_timings(file_contents)
    
    # Calculate the duration of a subbeat.
    quarter_note_ms = 60_000 / bpm
    subbeat_ms = quarter_note_ms / note_precision
    
    timing_dict = {}
    
    # Structure the dict with the timing data
    # with the timings as keys and lanes as values.
    for timing_data in hit_object_timings:
        timing = timing_data[0]
        lanes = timing_data[1:]
        timing_dict[timing] = lanes
    
    # Calculate the amount of subbeats for the given beatmap.
    last_timing_ms = hit_object_timings[-1][0]
    num_subbeats = int((last_timing_ms - start_time_ms) // subbeat_ms) + 1
    
    beat_timings = []
    tolerance_ms = 10
    
    # Reassemble the normalized beat timings and lane data.
    for subbeat_idx in range(num_subbeats):
        subbeat_time = start_time_ms + subbeat_idx * subbeat_ms
        
        found = False
        
        # Check if there is a note at this subbeat (within tolerance).
        for timing, lanes in timing_dict.items():
            if abs(timing - subbeat_time) <= tolerance_ms:
                # Note exists at this subbeat => add to the list.
                beat_timings.append([subbeat_idx, subbeat_time] + lanes)
                found = True
                break
        if not found:
            # No note at this subbeat => fill with zeros for all lanes.
            beat_timings.append([subbeat_idx, subbeat_time, 0, 0, 0, 0])

    return beat_timings


def get_audio_features(audio_file_path : str, beat_timings : list[list]) -> list[list]:
    """
    Retrieve audio features for a given audio file with given beat timings.

    Args:
        audio_file_path (str): _The path to the audio file._
        beat_timings (list[list]): _The list of normalized HitObject timings._

    Returns:
        list[list]: _Audio features with entries in the format
        [mfcc0, ..., mfcc4, onset]_
    """
    # Load the audio file.
    y, sr = librosa.load(audio_file_path, sr=None)
    
    hop_length = 512
    
    # Extract relevant audio features for the entire audio.
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length).T
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    # chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop_length).T
    # spec_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop_length).T
    # zcr = librosa.feature.zero_crossing_rate(y=y, hop_length=hop_length).T
    
    features = []
    
    # For each subbeat timing, extract the corresponding feature vector.
    for entry in beat_timings:
        timing_ms = entry[1]
        
        # Convert timing in ms to the corresponding audio frame index.
        frame_idx = int((timing_ms / 1000) * sr / hop_length)
        
        # Clamp frame_idx to the valid range.
        if frame_idx >= mfcc.shape[0]:
            frame_idx = mfcc.shape[0] - 1
        
        # Concatenate selected features for this subbeat.
        feature_vector = np.concatenate([
            mfcc[frame_idx][:5],
            [onset_env[frame_idx] if frame_idx < len(onset_env) else 0],
            # chroma[frame_idx],
            # spec_contrast[frame_idx],
            # zcr[frame_idx]
        ])
        
        features.append(feature_vector)
    
    return features


def get_merged_beatmap_data(beatmapset_path : str, beatmap_ID : int) -> list[list]:
    """
    Retrieve the normalized, merged HitObject timing and audio feature data
    for a given beatmap.

    Args:
        beatmapset_path (str): _The path to the beatmapset of the given beatmap._
        beatmap_ID (int): _The ID of the given beatmap._

    Returns:
        list[list]: _Merged beatmap data with entries in the format
        [subbeat_idx, mfcc0, ..., mfcc4, onset, lane0, ..., lane3]._
    """
    # List all files in the beatmapset directory.
    beatmap_files = os.listdir(beatmapset_path)
    audio_file = None
    
    # Try to find the audio file.
    for f in beatmap_files:
        if f.startswith("audio"):
            audio_file = f
    
    # If no audio file is found, return immediately.
    if audio_file is None:
        print(f"ERROR (beatmapFeatureExtractor): Failed to retrieve audio file for beatmap {beatmap_ID}.")
        return None
    
    # Build the full path to the audio file.
    audio_file_path = os.path.join(beatmapset_path, audio_file)
    
    # Extract normalized beatmap timings and audio features.
    beatmap_timings = get_beatmap_timings(beatmapset_path=beatmapset_path, beatmap_ID=beatmap_ID)
    audio_features = get_audio_features(audio_file_path=audio_file_path, beat_timings=beatmap_timings)

    merged_data = []
    
    # Merge beatmap timings and audio features into for each subbeat.
    for bt, feat in zip(beatmap_timings, audio_features):
        # bt[0] = subbeat_idx
        # bt[2:] = [lane0, ..., lane3]
        merged_data.append(list(bt[0]) + list(feat) + list(bt[2:]))
    
    return merged_data


def visualize_data(normalized_merged_data):
    """
    Generate 2 plots showing the HitObject timing spread
    and audio feature data over subbeats.

    Args:
        normalized_merged_data (_type_): _The normalized merged data of a given beatmap
        containing HitObject timings and audio features._
    """
    data = np.array(normalized_merged_data)
    subbeat_idx = data[:, 0]
    mfccs = data[:, 2:7]
    onset = data[:, 7]
    lanes = data[:, 8:12]
    
    # -------- Plot HitObjects over subbeats --------
    plt.figure(figsize=(12, 4))
    
    for lane in range(lanes.shape[1]):
        plt.scatter(subbeat_idx[lanes[:, lane] == 1], [lane]*np.sum(lanes[:, lane] == 1), label=f'Lane {lane}', marker='|', s=100)
    
    plt.xlabel('Subbeat Index')
    plt.yticks(range(4), [f'Lane {i}' for i in range(4)])
    plt.title('Note Hitobjects Over Subbeats')
    plt.legend()
    plt.tight_layout()
    plt.show()
    # -----------------------------------------------
    
    # -------- Plot audio features over subbeats --------
    fig, axs = plt.subplots(1 + mfccs.shape[1], 1, figsize=(12, 8), sharex=True)
    
    axs[0].plot(subbeat_idx, onset, label="Onset strength")
    axs[0].set_ylabel("Onset")
    axs[0].set_title("Onset strength over Subbeats")
    axs[0].legend()
    
    for i in range(mfccs.shape[1]):
        axs[i+1].plot(subbeat_idx, mfccs[:, i], label=f"MFCC {i}")
        axs[i+1].set_ylabel(f"MFCC {i}")
        axs[i+1].legend()
    
    axs[-1].set_xlabel("Subbeat index")
    plt.tight_layout()
    plt.show()
    # ---------------------------------------------------

