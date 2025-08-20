import numpy as np
import matplotlib.pyplot as plt

from .rthmAnalyzer import TimingData, get_note_count_and_density, get_notes_per_lane


def plot_note_distribution_over_time(ax, note_distribution_over_time : list[tuple[int, int]]):
    ax.clear()
    
    if not note_distribution_over_time:
        ax.set_title("Note distribution over time", fontweight="bold")
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Note count")
        ax.grid(True, axis="y", alpha=0.25)
        return 0.0

    # Prepare the data.
    times_ms = [ t for t, _ in note_distribution_over_time ]
    counts = [ c for _, c in note_distribution_over_time ]
    times_sec = [ t / 1000.0 for t in times_ms ]
    
    # Determine bar width / bin size.
    if len(times_sec) > 1:
        deltas = [ b-a for a, b in zip(times_sec[:-1], times_sec[1:])]
        step_sec = max(0.001, min(d for d in deltas if d > 0) if any(d > 0 for d in deltas) else 1.0)
        bar_width = 0.9 * step_sec
    else:
        step_sec = 0.5
        bar_width = 0.5
    
    # Color coding by normalized values.
    max_count_value = max(counts) if counts else 1
    norm_count_values = [ c / max_count_value if max_count_value > 0 else 0.0 for c in counts ]
    cmap = plt.cm.plasma
    colors = [ cmap(v) for v in norm_count_values ]
    
    ax.bar(
        times_sec,
        counts,
        width=bar_width,
        color=colors,
        edgecolor="black",
        linewidth=0.6
    )
    
    ax.set_title("Note distribution over time", fontweight="bold")
    # ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Note count")
    ax.grid(True, axis="y", alpha=0.25)
    
    # Neat x-limits.
    if times_sec:
        left = min(times_sec) - bar_width * 0.5
        right = max(times_sec) - bar_width * 0.5
        
        if left == right:
            left -= 0.5
            right += 0.5
        ax.set_xlim(left, right)
    
    return step_sec


def plot_notes_per_lane_heatmap(ax, timing_data : list[TimingData], bin_size_sec : float):
    ax.clear()
    
    if not timing_data or bin_size_sec <= 0:
        ax.text(0.5, 0.5, "No data to plot", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Lane")
        return

    # Build times and lanes arrays.
    times_sec = np.array([td.get_timing() / 1000.0 for td in timing_data], dtype=float)
    n_lanes = timing_data[0].get_lane_count()
    
    # Bin notes.
    t_min = times_sec.min()
    t_max = times_sec.max()
    
    if t_min == t_max:
        t_max = t_min + bin_size_sec
        
    n_bins = max(1, int(np.ceil((t_max - t_min) / bin_size_sec)))
    heat = np.zeros((n_lanes, n_bins), dtype=int)
    
    for td, t in zip(timing_data, times_sec):
        bin_idx = int((t - t_min) // bin_size_sec)
        bin_idx = min(max(bin_idx, 0), n_bins - 1)
        
        for lane_idx, val in enumerate(td.get_actual_note_values()):
            heat[lane_idx, bin_idx] += val
    
    # Plot heatmap.
    extent = [ t_min, t_min + n_bins * bin_size_sec, -0.5, n_lanes -0.5]
    im = ax.imshow(
        heat[::-1, :],
        aspect="auto",
        interpolation="nearest",
        cmap="magma",
        origin="upper",
        extent=extent
    )
    
    # Set Labels.
    ax.set_yticks(range(n_lanes))
    ax.set_yticklabels([f"{i+1}" for i in range(n_lanes -1, -1, -1)])
    
    # Optional grid lines.
    edges = np.linspace(t_min, t_min + n_bins * bin_size_sec, n_bins + 1)
    
    for x in edges:
        ax.axvline(x, color=(0, 0, 0, 0.15), linewidth=0.8)