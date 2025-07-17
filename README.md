# Rhythmapper
***Rhythmapper*** is an experimental tool that uses LSTM-based neural network models to generate beatmaps for rhythm games like [osu!](https://osu.ppy.sh/)-mania or [Quaver](https://quavergame.com/).
The system can transform any audio file into structured and playable 4K beatmap data (i.e. with 4 lanes), enabling automatic chart creation synced to the song's rhythm.


## 📁 Directory structure
Below is an overview of how the project files are structured. Note that directories, which are not existing on the repo (and which you would have to create on your own), are marked with an [ / ] in the comment next to it.  

```
root
|-- config_generation.json     # Stores all values relevant to level generation and the visualizer.
|-- config_model.json          # Stores all model and training-specific values.
|-- config_paths.json          # Stores all relevant directory and file paths.
|
|-- feature_norm_stats.json    # Stores generated feature normalization statistics.
|
|-- guiConfigEditor.py         # Provides an interactive GUI for editing and executing pipeline steps.
|
|-- runPipeline.py             # Launches the complete pipeline based on the config files.
|
|-- data
|   |-- preprocessed           # Contains preprocessed beatmap data categorized by difficulty.
|   |-- raw                    # [/] Stores raw downloaded beatmap data.
|   `-- sequences              # [/] Stores split training and testing sequences.
|
|-- models
|   |-- model.keras
|   `-- better_model.keras
|
|-- generation                 # [/] Recommended directory to store generated content and related files.
|   |-- audio_files            # [/] Recommended directory for audio files to use for generation.
|   |-- levels                 # [/] Recommended directory for generated levels.
|   `-- exports                # [/] Recommended directory for exported levels.
|
`-- src                        # Contains all functional scripts.
    |-- data_utils             # Contains scripts for normalization and sequence generation and loading.
    |-- download_utils         # Contains scripts for downloading beatmaps.
    |-- model                  # Contains scripts that interact / modify / train the model.
    |-- preprocessing          # Contains scripts for preprocessing beatmap data.
    `-- visualizer             # Contains scripts (and additional files) for the visualizer.
```


## ❗Prerequisites (Python libraries)
All necessary Python libraries can be found in the <a href="REQUIREMENTS.txt">REQUIREMENTS.txt</a> file. The core library used (as with many ML projects) is the TensorFlow library. If you are new to using TensorFlow, check out their tutorial on how to install it via pip [here](https://www.tensorflow.org/install/pip). (*Building / installing a TensorFlow version with GPU support is heavily recommended if you intend to train models; **Training via the GPU can drastically decreases model training time!***)



## ❗Prerequisites (Level generation)
Before running the generation step, make sure:
1. You have an `.mp3`, `.ogg` or `.wav` audio file placed in a known location (can be selected via the GUI).
2. The audio has a steady BPM, as the models are trained on maps with constant tempo.
3. You know the BPM and the offset of the first beat in milliseconds. If you don't know these values yet, try the following steps:
   - Open osu!, drag the audio file into the editor.
   - Use the timing setup panel to find the BPM and offset.
   - Use the GUI to enter both Values into their designated input fields.

This procedure can get a bit tedious, especially if you wanted to generate beatmaps for different songs quickly. A BPM + offset detection system that is built-in the GUI is planned to make this process a bit easier and faster.

## 🤖 Training & Generation Pipeline
To configure training settings and start the pipeline, you can run this command:
```bash
python guiConfigEditor.py
```

Alternatively, only run the pipeline (*without GUI*):
```bash
python runPipeline.py
```

**Using the GUI is highly recommended**. You can use it to:
- Edit config files in a structured way.
- Browse for input / output paths.
- Trigger specific stages of the pipeline individually or collectively.


## 🧩 Pipeline Steps
Each pipeline step can be toggled via a checkbox in the GUI or corresponding boolean flags in the config files:

1. **Beatmap Downloader**
   - Downloads recent osu!-mania beatmapsets.
   - Controlled by `run_beatmap_downloader` in `config_model.json`.

2. **Beatmap Preprocessor**
   - Categorizes beatmaps into difficulty ranges and filters by keymode.
   - Controlled by `run_beatmap_preprocessor`.

3. **Feature Normalizer**
   - Computes normalization stats for all audio features.
   - Controlled by `run_feature_normalizer`.

4. **Sequence Splitter**
   - Splits beatmaps into train / test sequences.
   - Controlled by `run_sequence_splitter`.

5. **Model Trainer**
   - Trains the LSTM model on sequence data.
   - Controlled by `run_model_trainer`.

6. **Level Generator**
   - Predicts note placements based on audio features.
   - Controlled by `run_level_generator` in `config_generation.json`.

7. **Visualizer (optional)**
   - Visualizes generated `.osu` files synced with the audio.
   - Controlled by `run_visualizer` and `visualizer_use_last_gen`.


## ⚙️ Configuration Files
There are three separate configuration files. The configuration files contain the following configuration settings: 

### `config_model.json`: Model & Data Settings
- `download_beatmapsets`: The amount of beatmapsets to download. (*Note: beatmapsets $\neq$ beatmaps $\rarr$ each beatmapset may contain more than one beatmap.*)
- `note_precision`: How detailed are the beatmaps being processed / generated? This value should only be a power of 2. It works the following: On the lowest precision (= 1), every quarter note is being extracted from a beatmap-file and generated levels can only have notes placed on quarter notes. For the second level of precision (= 2), every eighth note is included, and so on.
- `prediction_threshold`: For which prediction values $v \in [0,1]$ should the model output generate a note?
- `sequence_length`: How long are the sequences that are saved during data preprocessing? (*How many subbeats are passed to the model as one continuous sequence?*)
- `split_all_difficulty_sequences`: If *false*, only create sequences for the desired difficulty range.
- `difficulty_range`: What beatmap difficulty-range should the model train on (or the sequences be split for)?
- `max_vram_mb`: If using the GPU during training, change this value to limit the amount of VRAM that is being used during model training.
- `training_epochs`: The maximum amount of (additional) epochs that a model will train for if it keeps improving (without overfitting).
- `run_beatmap_downloader`: Should the beatmap downloader script be run?
- `run_beatmap_preprocessor`: Should the beatmap preprocessor script be run?
- `run_sequence_splitter`: Should the sequence splitter script be run?
- `run_feature_normalizer`: Should the feature normalizer script be run?
- `run_model_trainer`: Should the model trainer script be run?

### `config_paths.json`: Path settings
- `raw_data_path`: Beatmaps will be downloaded to this path.
- `preprocessed_data_path`: Preprocessed beatmaps will be saved to this path.
- `model_dir`: Models will be saved here.
- `model_for_generation_path`: The path to the model that will be used for beatmap generation.
- `generation_dir`: Generated beatmaps will be saved to this path.
- `generation_file_name`: The generated beatmap will have this name.
- `audio_file_path`: The beatmap generation will use this audio.
- `visualizer_beatmap_path`: If you are not visualizing the most recently generated beatmap, the visualizer will use the beatmap at this path. (*For more info: Look into the* `config_generation.json` *settings.*)
- `visualizer_audio_path`: Like `visualizer_beatmap_path`, the audio file at this path will be used if you are not visualizing the most recently generated beatmap.

### `config_generation.json`: Beatmap-generation settings
- `audio_bpm`: The BPM of the audio file that is being used to generate a new beatmap.
- `audio_start_ms`: The time in milliseconds where the first beat occurs in the audio.
- `run_level_generator`: Should the level generator script be run?
- `run_visualizer`: Should the visualizer script be run?
- `visualizer_use_last_gen`: If set to true, the visualizer will use the most recently generated beatmap and audio (found at `generation_dir`/`generation_file_name` and `audio_file_path`).


## 🛠️ GUI Configuration Editor
To streamline configuration, run:

```bash
python guiConfigEditor.py
```

The editor is split into 4 tabs:

1. **Download & Preprocess Settings**
   - Beatmap downloader, preprocessor, raw/preprocessed paths.

2. **Sequence & Training Settings**
   - Sequence length, difficulty range, threshold, training toggle.

3. **Generation & Visualizer**
   - Audio file, BPM, start offset, visualizer file inputs.
   - Optional: Automatically run the visualizer after generation.

4. **Export**
   - Beatmap to export, beatmap metadata, export format.

Each setting has an intuitive interface, and changes can be saved with:
- **Save and Quit**
- **Save and Run** (triggers `runPipeline.py`)
- **Export** (triggers `beatmapExporter.py`)

---
>⚠️ *Note that Commits prior to* 0f91584 *follow a custom format like* "[#XXX-F] commit-msg"*, which might look unconventional*.
> *Originally, this repository wasn't intended to be public - I just had fun with it locally. In hindsight, not the brightest choice for long-term clarity.*
>
> *Starting from commit* 0f91584, *commit messages aim to be clearer and more structured.*

