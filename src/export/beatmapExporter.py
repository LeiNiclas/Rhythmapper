import os
import shutil


def export_to_osz(audio_file_path : str, beatmap_file_path : str, export_path : str, metadata : dict) -> None:
    # Check validty of audio file extension.
    if audio_file_path.split('.')[-1] not in [ "mp3", "wav", "ogg" ]:
        raise ValueError(f"Error: Could not export beatmap to .osz. Audio file {audio_file_path} has invalid extension.")
    
    # Check validty of beatmap file extension.
    if beatmap_file_path.split('.')[-1] != "osu":
        raise ValueError(f"Error: Could not export beatmap .osz. Beatmap file {beatmap_file_path} has invalid extension.")
    
    beatmap_name = os.path.basename(beatmap_file_path).replace(".osu", "")
    audio_file_name = os.path.basename(audio_file_path)
    
    temp_dir = os.path.join(export_path, f"{beatmap_name}_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    create_osu_file_template(
        audio_file_name=audio_file_name,
        beatmap_file_path=beatmap_file_path,
        destination_file_path=temp_dir,
        metadata=metadata
    )
    
    shutil.copy(audio_file_path, os.path.join(temp_dir, audio_file_name))

    archive_base = os.path.join(export_path, f"{beatmap_name}_exported")
    shutil.make_archive(base_name=archive_base, format='zip', root_dir=temp_dir)
    
    shutil.rmtree(temp_dir)
    
    # Rename the .zip file to .osz.
    os.rename(f"{archive_base}.zip", os.path.join(export_path, f"{beatmap_name}.osz"))


def export_to_qua(audio_file_path : str, beatmap_file_path : str, export_path : str, metadata : dict) -> None:
    # Check validity of audio file extension.
    if audio_file_path.split('.')[-1] not in [ "mp3", "wav", "ogg" ]:
        raise ValueError(f"Error: Could not export beatmap. Audio file {audio_file_path} has invalid extension.")

    # Check validity of beatmap file extension.
    if beatmap_file_path.split('.')[-1] != "osu":
        raise ValueError(f"Error: Could not export beatmap. Beatmap file {beatmap_file_path} has invalid extension.")

    title = metadata["title"]
    artist = metadata["artist"]
    difficulty = metadata["difficulty_name"]
    audio_file_name = os.path.basename(audio_file_path)
    
    # Create folder for export.
    beatmap_folder_name = f"{artist} - {title} (Quaver-map-gen-AI) [{difficulty}]"
    beatmap_export_dir = os.path.join(export_path, beatmap_folder_name)
    os.makedirs(beatmap_export_dir, exist_ok=True)

    # Create .qua file.
    create_qua_file_template(
        audio_file_name=audio_file_name,
        beatmap_file_path=beatmap_file_path,
        destination_file_path=beatmap_export_dir,
        metadata=metadata
    )

    # Copy audio to target location.
    shutil.copy(audio_file_path, os.path.join(beatmap_export_dir, audio_file_name))


def create_osu_file_template(audio_file_name : str, beatmap_file_path : str, destination_file_path : str, metadata : dict) -> str:
    hitobjects = None
    
    with open(beatmap_file_path, "r") as f:
        hitobjects = f.readlines()
    
    title = metadata["title"]
    artist = metadata["artist"]
    difficulty = metadata["difficulty_name"]
    audio_start_timing = int(metadata["audio_start_ms"])
    audio_bpm = float(metadata["audio_bpm"])
    audio_time_signature = int(metadata["audio_time_signature"])
    
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
    osu_file_contents += "Creator:osu-mania-gen-AI\n"
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
    osu_file_contents += f"{audio_start_timing},{60_000 / audio_bpm},{audio_time_signature},0,0,100,1,0\n\n"
    
    osu_file_contents += "[HitObjects]\n"
    
    for hitobject in hitobjects:
        osu_file_contents += hitobject + "\n"

    beatmap_name = f"{artist} - {title} (osu-mania-gen-AI) [{difficulty}].osu"

    with open(os.path.join(destination_file_path, beatmap_name), "x") as f:
        f.write(osu_file_contents)


def create_qua_file_template(audio_file_name : str, beatmap_file_path : str, destination_file_path : str, metadata : dict) -> str:
    hitObjects = None
    
    with open(beatmap_file_path, "r") as f:
        hitObjects = f.readlines()
    
    title = metadata["title"]
    artist = metadata["artist"]
    difficulty = metadata["difficulty_name"]
    audio_start_timing = int(metadata["audio_start_ms"])
    audio_bpm = float(metadata["audio_bpm"])
    audio_time_signature = int(metadata["audio_time_signature"])
    
    qua_file_contents = f"AudioFile: {audio_file_name}\n"
    qua_file_contents += "SongPreviewTime: 0\n"
    qua_file_contents += "BackgroundFile: \n"
    qua_file_contents += "Mode: Keys4\n"
    qua_file_contents += f"Title: {title}"
    qua_file_contents += f"Artist: {artist}"
    qua_file_contents += "Source: \n"
    qua_file_contents += "Tags: \n"
    qua_file_contents += "Creator: Quaver-map-gen-AI\n"
    qua_file_contents += f"DifficultyName: {difficulty}\n"
    qua_file_contents += "Description: AI generated map. (https://github.com/LeiNiclas/osu-mania-level-gen-AI)\n"
    qua_file_contents += "EditorLayers: []\n\n"
    
    qua_file_contents += "TimingPoints:\n"
    qua_file_contents += f"- StartTime: {audio_start_timing}\n"
    qua_file_contents += f"  Bpm: {audio_bpm}\n\n"
    
    qua_file_contents += "SliderVelocities: []\n\n"
    
    qua_file_contents += "HitObjects:\n"
    
    for line in hitObjects:
        split = line.strip().split(",")
        
        timing = split[2]
        x_pos = int(split[0])
        lane_idx = ((x_pos - 64) // 128) + 1
        
        qua_file_contents += f"- StartTime: {timing}\n"
        qua_file_contents += f"  Lane: {lane_idx}\n"
    
    beatmap_name = f"{artist} - {title} (Quaver-map-gen-AI) [{difficulty}].qua"
    
    with open(os.path.join(destination_file_path, beatmap_name), "x", encoding="utf-8") as f:
        f.write(qua_file_contents)

