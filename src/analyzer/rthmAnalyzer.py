import numpy as np
import os


class TimingData:
    """
    Represents a single timing row with per-lan (actual, prediction) values.
    actual: 0 or 1, prediction: float in [0, 1]
    """
    def __init__(self, timing : int, note_values : list[tuple[int, float]]):
        self.timing = timing
        self.note_values = note_values
    
    
    def get_timing(self):
        return self.timing
    
    
    def get_actual_note_values(self):
        return [ a for a, _ in self.note_values ]
    
    
    def get_prediction_values(self):
        return [ p for _, p in self.note_values ]
    
     
    def get_lane_count(self):
        return len(self.note_values)
     

def get_raw_rthm_data(path : str) -> list[str]:
    # Check for file existance.
    if not os.path.exists(path=path):
        raise FileNotFoundError("ERROR: Could not find .rthm file at the given path.")

    with open(path, "r", encoding="utf-8") as rthm_file:
        return [ line.strip() for line in rthm_file if line.strip() ]


def get_metadata(raw_data : list[str]) -> list[str]:
    pass


def get_duration_ms(raw_data : list[str]) -> int:
    try:
        return int(raw_data[-1].split("|")[0])
    except ValueError:
        return 0

def get_lane_count(raw_data : list[str]) -> int:
    for line in raw_data[::-1]:
        parts = line.split("|")
        
        if len(parts) > 1:
            return len(parts) - 1
    
    raise ValueError("ERROR: Could not infer lane count from .rthm file correctly.")


def get_timing_data(raw_data : list[str], lane_count : int) -> list[TimingData]:
    timing_data : list[TimingData] = []
    
    # Let  n := lane_count
    for line in raw_data:
        parts = line.split("|")
        
        # Lane-data lines always have n+1 parts.
        # Skip non-lane-data lines.
        if len(parts) != lane_count + 1:
            continue
        
        # The timing is the first part of a Lane-data line.
        timing = 0
        
        try:
            timing = int(parts[0])
        except ValueError:
            continue # Skip invalid time
        
        # The remaining n parts consist of lane-note-placement and prediction data.
        lanes : list[tuple[int, float]] = []
        valid = True
        
        for segment in parts[1:]:
            try:
                a_str, p_str = segment.split(":")
                actual_value = int(a_str)
                prediction_value = float(p_str)
                
                lanes.append((actual_value, prediction_value))
            except ValueError:
                valid = False
                break
        
        if valid and len(lanes) == lane_count:
            timing_data.append(TimingData(timing=timing, note_values=lanes))
    
    return timing_data


def get_note_count_and_density(timing_data : list[TimingData]) -> tuple[int, float]:
    if not timing_data:
        return 0, 0.0
    
    arr = np.asarray([ td.get_actual_note_values() for td in timing_data ])
    flat = arr.ravel()
    
    note_count = int(np.count_nonzero(flat))
    note_density = float(np.mean(flat))
    
    return note_count, note_density


def get_notes_per_lane(timing_data : list[TimingData]) -> list[int]:
    if not timing_data:
        return []
    
    lane_count = timing_data[0].get_lane_count()
    notes_per_lane = [ 0 ] * lane_count
    
    # Iterate over all timing data entries and add actual note placement values.
    for td in timing_data:
        for i, a in enumerate(td.get_actual_note_values()):
            notes_per_lane[i] += a
    
    return notes_per_lane


def get_notes_over_time(timing_data : list[TimingData], window_size : int = 8) -> list[tuple[int, int]]:
    if window_size <= 0:
        raise ValueError("ERROR: window_size must be > 0.")
    
    result : list[tuple[int, int]] = []
    n = len(timing_data)
    
    if n == 0:
        return result

    # Loop over all timings with a given window- / step-size.
    for start in range(0, n, window_size):
        chunk = timing_data[start : start+window_size]
        start_timing = chunk[0].get_timing()
        count = sum(sum(td.get_actual_note_values()) for td in chunk)
        result.append((start_timing, count))
    
    return result

