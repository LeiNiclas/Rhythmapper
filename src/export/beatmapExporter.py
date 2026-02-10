import os
import shutil


RTHM_METADATA_START_LINE = 2
RTHM_METADATA_END_LINE = 6
RTHM_NOTES_START_LINE = 9


def get_rthm_contents(beatmap_file_path : str) -> tuple[dict, list]:
    # Check file extension validity
    if beatmap_file_path.split(".")[-1] != "rthm":
        raise FileNotFoundError(f"Error: Non-rthm beatmap file: {beatmap_file_path}")
    
    rthm_contents = []
    
    with open(beatmap_file_path, "r") as f:
        rthm_contents = f.readlines()
    
    
    raw_metadata = rthm_contents[RTHM_METADATA_START_LINE : RTHM_METADATA_END_LINE]
    raw_notes = rthm_contents[RTHM_NOTES_START_LINE:]
    
    metadata = {}
    
    # Metadata saved in .rthm format "metadata_key:metadata_value"
    # Convert to dict of { metadata_key1: metadata_value1, metadata_key2: metadata_value2, ... }
    for line in raw_metadata:
        key, value = line.strip().split(sep=":", maxsplit=1)
        
        try:
            metadata[key] = float(value)
        except ValueError:
            metadata[key] = value
    
    
    notes = []
    
    # Notes saved in .rthm format "timing|note1_bin:note1_pred|note2_bin:note2_pred|..."
    # Convert to list of [ [timing, lane_idx], [timing, lane_idx], ... ]
    for raw_line in raw_notes:
        if raw_line.isspace():
            continue
        
        raw_line = raw_line.strip()
        
        timing = raw_line.split("|")[0]
        lane_data = raw_line.split("|")[1:]

        for lane_idx, note_data in enumerate(lane_data):
            note_bin = int(note_data.split(":")[0])
            
            if note_bin == 1:
                notes.append([timing, lane_idx])
    
    
    return metadata, notes


def rthm_to_osz(metadata : dict, notes : list, destination_file_path : str) -> None:
    title = metadata.get("title", "Missing title")
    artist = metadata.get("artist", "Missing artist")
    difficulty = metadata.get("difficulty", "Missing difficulty")
    audio_start_timing = int(metadata.get("audio_start", 0.0))
    audio_bpm = float(metadata.get("bpm", 0))
    audio_file_name = os.path.basename(metadata["audiopath"]) # Guaranteed to exist
    
    # -------- Necessary contents --------
    osu_file_contents = "osu file format v14\n\n"
    
    osu_file_contents += "[General]\n"
    osu_file_contents += f"AudioFilename: {audio_file_name}\n"
    osu_file_contents += "AudioLeadIn: 0\n"
    osu_file_contents += "PreviewTime: -1\n"
    osu_file_contents += "Countdown: 0\n"
    osu_file_contents += "SampleSet: Normal\n"
    osu_file_contents += "StackLeniency: 0.7\n"
    osu_file_contents += "Mode: 3\n"
    osu_file_contents += "LetterboxInBreaks: 0\n"
    osu_file_contents += "SpecialStyle: 0\n"
    osu_file_contents += "WidescreenStoryboard: 0\n\n"
    
    osu_file_contents += "[Editor]\n"
    osu_file_contents += "DistanceSpacing: 1\n"
    osu_file_contents += "BeatDivisor: 16\n"
    osu_file_contents += "GridSize: 32\n"
    osu_file_contents += "TimelineZoom: 1\n\n"
    
    osu_file_contents += "[Metadata]\n"
    osu_file_contents += f"Title:{title}\n"
    osu_file_contents += f"TitleUnicode:{title}\n"
    osu_file_contents += f"Artist:{artist}\n"
    osu_file_contents += f"ArtistUnicode:{artist}\n"
    osu_file_contents += "Creator:Rhythmapper\n"
    osu_file_contents += f"Version:{difficulty}\n"
    osu_file_contents += "Source:\n"
    osu_file_contents += "Tags:\n"
    osu_file_contents += "BeatmapID:0\n"
    osu_file_contents += "BeatmapSetID:-1\n\n"
    
    osu_file_contents += "[Difficulty]\n"
    osu_file_contents += "HPDrainRate:7\n"
    osu_file_contents += "CircleSize:4\n"
    osu_file_contents += "OverallDifficulty:8\n"
    osu_file_contents += "ApproachRate:7\n"
    osu_file_contents += "SliderMultiplier:1.4\n"
    osu_file_contents += "SliderTickRate:1\n\n"
    
    osu_file_contents += "[Events]\n"
    osu_file_contents += "//Background and Video events\n"
    osu_file_contents += "//Break Periods\n"
    osu_file_contents += "//Storyboard Layer 0 (Background)\n"
    osu_file_contents += "//Storyboard Layer 1 (Fail)\n"
    osu_file_contents += "//Storyboard Layer 2 (Pass)\n"
    osu_file_contents += "//Storyboard Layer 3 (Foreground)\n"
    osu_file_contents += "//Storyboard Layer 4 (Overlay)\n"
    osu_file_contents += "//Storyboard Sound Samples\n\n"
    
    osu_file_contents += "[TimingPoints]\n"
    osu_file_contents += f"{audio_start_timing},{60_000 / audio_bpm},4,0,0,100,1,0\n\n"
    # ------------------------------------
    
    # -------- HitObject conversion --------
    osu_file_contents += "[HitObjects]\n"
    fixed_hitobject_string = "1,0,0:0:0:0:"

    for note in notes:
        timing = note[0]
        lane_pos = (note[1] * 128) + 64
                
        hit_object = f"{lane_pos},192,{timing}," + fixed_hitobject_string
        osu_file_contents += hit_object + "\n"
    # --------------------------------------
    
    beatmap_name = f"{artist} - {title} (Rhythmapper) [{difficulty}].osu"

    with open(os.path.join(destination_file_path, beatmap_name), "x") as f:
        f.write(osu_file_contents)


def rthm_to_qua(metadata : dict, notes : list, destination_file_path : str) -> None:
    title = metadata.get("title", "Missing title")
    artist = metadata.get("artist", "Missing artist")
    difficulty = metadata.get("difficulty", "Missing difficulty")
    audio_start_timing = int(metadata.get("audio_start", 0.0))
    audio_bpm = float(metadata.get("bpm", 0))
    audio_file_name = os.path.basename(metadata["audiopath"]) # Guaranteed to exist
    
    # -------- Necessary contents --------
    qua_file_contents = f"AudioFile: {audio_file_name}\n"
    qua_file_contents += "SongPreviewTime: 0\n"
    qua_file_contents += "BackgroundFile: \n"
    qua_file_contents += "Mode: Keys4\n"
    qua_file_contents += f"Title: {title}\n"
    qua_file_contents += f"Artist: {artist}\n"
    qua_file_contents += "Source: \n"
    qua_file_contents += "Tags: \n"
    qua_file_contents += "Creator: Rhythmapper\n"
    qua_file_contents += f"DifficultyName: {difficulty}\n"
    qua_file_contents += "Description: AI generated map. (https://github.com/LeiNiclas/Rhythmapper)\n"
    qua_file_contents += "EditorLayers: []\n\n"
    
    qua_file_contents += "TimingPoints:\n"
    qua_file_contents += f"- StartTime: {audio_start_timing}\n"
    qua_file_contents += f"  Bpm: {audio_bpm}\n\n"
    
    qua_file_contents += "SliderVelocities: []\n\n"
    
    qua_file_contents += "HitObjects:\n"
    # ------------------------------------
    
    # -------- HitObject conversion --------
    for note in notes:
        timing = note[0]
        lane_idx = note[1]
        
        hit_object =  f"- StartTime: {timing}\n"
        hit_object += f"  Lane: {lane_idx + 1}\n"
        
        qua_file_contents += hit_object
    # --------------------------------------
    
    beatmap_name = f"{artist} - {title} (Rhythmapper) [{difficulty}].qua"
    
    with open(os.path.join(destination_file_path, beatmap_name), "x", encoding="utf-8") as f:
        f.write(qua_file_contents)


def export_to_osz(beatmap_file_path : str, export_path : str, additional_metadata : dict = None) -> None:
    rthm_metadata, rthm_notes = get_rthm_contents(beatmap_file_path=beatmap_file_path)
    
    # Ensure audiopath exists in file.
    audio_file_path = rthm_metadata.get("audiopath")
    
    if not audio_file_path:
        raise AttributeError(f"Error: Could not resolve audiopath from .rthm file")
    
    # Merge metadata dicts.
    if additional_metadata:
        for key, value in  additional_metadata.items():
            if not rthm_metadata.get(key):
                rthm_metadata[key] = value
    
    # Use base names from existing files for exporting.
    beatmap_name = os.path.basename(beatmap_file_path).replace(".rthm", "")
    audio_file_name = os.path.basename(audio_file_path)
    
    # Export file to given path.
    # [!]   The export process involves creating a temporary directory
    #       at the export path to which the exported files are saved.
    #       After both the beatmap file and audio file are successfully
    #       copied into this directory, it is converted into a .zip
    #       and renamed to a .osz.
    #       Finally, the temporary directory can be removed.
    temp_dir = os.path.join(export_path, f"{beatmap_name}_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    rthm_to_osz(
        metadata=rthm_metadata,
        notes=rthm_notes,
        destination_file_path=temp_dir
    )
    
    shutil.copy(audio_file_path, os.path.join(temp_dir, audio_file_name))

    archive_base = os.path.join(export_path, f"{beatmap_name}_exported")
    shutil.make_archive(base_name=archive_base, format='zip', root_dir=temp_dir)
    
    shutil.rmtree(temp_dir)
    
    # Rename the .zip file to .osz.
    os.rename(f"{archive_base}.zip", os.path.join(export_path, f"{beatmap_name}.osz"))


def export_to_qua(beatmap_file_path : str, export_path : str, additional_metadata : dict = None) -> None:
    rthm_metadata, rthm_notes = get_rthm_contents(beatmap_file_path=beatmap_file_path)
    
    # Ensure audiopath exists in file.
    audio_file_path = rthm_metadata.get("audiopath")
    
    if not audio_file_path:
        raise AttributeError(f"Error: Could not resolve audiopath from .rthm file")
    
    # Merge metadata dicts.
    if additional_metadata:
        for key, value in additional_metadata.items():
            if not rthm_metadata.get(key):
                rthm_metadata[key] = value
    
    title = rthm_metadata.get("title", "Missing title")
    artist = rthm_metadata.get("artist", "Missing artist")
    difficulty = rthm_metadata.get("difficulty", "Missing difficulty")
    audio_file_name = os.path.basename(audio_file_path)
    
    # Create folder for export.
    beatmap_folder_name = f"{artist} - {title} (Rhythmapper) [{difficulty}]"
    beatmap_export_dir = os.path.join(export_path, beatmap_folder_name)
    os.makedirs(beatmap_export_dir, exist_ok=True)

    # Create .qua file.
    rthm_to_qua(
        metadata=rthm_metadata,
        notes=rthm_notes,
        destination_file_path=beatmap_export_dir
    )

    # Copy audio to target location.
    shutil.copy(audio_file_path, os.path.join(beatmap_export_dir, audio_file_name))
