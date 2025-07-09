import os
import shutil


def export_to_osz(audio_file_path : str, beatmap_file_path : str, export_path : str, metadata : dict):
    # Check validty of audio file extension.
    if audio_file_path.split('.')[-1] not in [ "mp3", "wav", "ogg" ]:
        raise ValueError(f"Error: Could not export beatmap. Audio file {audio_file_path} has invalid extension.")
    
    # Check validty of beatmap file extension.
    if beatmap_file_path.split('.')[-1] != "osu":
        raise ValueError(f"Error: Could not export beatmap. Beatmap file {beatmap_file_path} has invalid extension.")
    
    # Create the export directory if it doesn't exist.
    export_dir = os.path.dirname(export_path)
    os.makedirs(export_dir, exist_ok=True)
    os.makedirs(export_path, exist_ok=True)

    beatmap_name = os.path.basename(beatmap_file_path).replace(".osu", "")
    audio_file_name = os.path.basename(audio_file_path)
    
    create_osu_file_template(
        audio_file_name=audio_file_name,
        beatmap_file_path=beatmap_file_path,
        destination_file_path=export_path,
        metadata=metadata
    )
    
    archive_path = os.path.join(export_path, f"{beatmap_name}_exported")
    
    shutil.copy(audio_file_path, export_path)
    shutil.make_archive(base_name=archive_path, format='zip', base_dir=export_path, root_dir=export_path)
    
    os.remove(os.path.join(export_path, f"{beatmap_name}.osu"))
    os.remove(os.path.join(export_path, audio_file_name))
    
    # Rename the .zip file to .osz.
    os.rename(os.path.join(export_path, f"{beatmap_name}_exported.zip"), os.path.join(export_path, f"{beatmap_name}.osz"))


def create_osu_file_template(audio_file_name : str, beatmap_file_path : str, destination_file_path : str, metadata : dict):
    hitobjects = None
    
    with open(beatmap_file_path, "r") as f:
        hitobjects = f.readlines()
    
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
    osu_file_contents += f"Title:{metadata['title']}\n"
    osu_file_contents += f"TitleUnicode:{metadata['title']}\n"
    osu_file_contents += f"Artist:{metadata['artist']}\n"
    osu_file_contents += f"ArtistUnicode:{metadata['artist']}\n"
    osu_file_contents += "Creator:osu!-mania-gen-AI\n"
    osu_file_contents += f"Version:{metadata['difficulty_name']}\n"
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
    osu_file_contents += f"{metadata['audio_start_ms']},{60_000 / float(metadata['audio_bpm'])},{metadata['audio_time_signature']},0,0,100,1,0\n\n"
    
    osu_file_contents += "[HitObjects]\n"
    
    for hitobject in hitobjects:
        osu_file_contents += hitobject + "\n"

    beatmap_name_with_extension = os.path.basename(beatmap_file_path)

    with open(os.path.join(destination_file_path, beatmap_name_with_extension), "x") as f:
        f.write(osu_file_contents)

