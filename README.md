# osu!-mania level generator

This is an experimental project aiming to create osu!-mania beatmaps using an LSTM-based model. Currently, models are able to generate 4K-beatmap data.


## 📁 Directory structure
```bash
root
|-- config_generation.json     # Stores all values relevant to level generation and the visualizer.
|-- config_model.json          # Stores all model and training-specific values.
|-- config_paths.json          # Stores all relevant directory and file paths.
|
|-- feature_norm_stats.json    # Stores generated feature normalization statistics.
|-- runPipeline.py             # Launches the complete pipeline based on the config files.
|-- guiConfigEditor.py         # Provides an interactive GUI for editing and executing pipeline steps.
|
|-- data
|   |-- preprocessed           # Contains preprocessed beatmap data categorized by difficulty.
|   |-- raw                    # Stores raw downloaded beatmap data.
|   `-- sequences              # Stores split training and testing sequences.
|-- models
|   |-- model.keras
|   `-- better_model.keras
|-- generated
|   |-- generated.osu          # Example generated beatmap file.
`-- src
    |-- data_utils
    |-- download_utils
    |-- model
    |-- preprocessing
    `-- visualizer
```


## ❗Prerequisites (Python libraries)
Install the following libraries:
- `numpy`
- `pandas`
- `tensorflow`
- `sklearn`
- `librosa`
- `pygame`
- `tkinter`


## ❗Prerequisites (Level generation)
Before running the generation step, make sure:
1. You have an `.mp3`, `.ogg` or `.wav` audio file placed in a known location (can be selected via the GUI).
2. The audio has a steady BPM, as the models are trained on maps with constant tempo.
3. You know the BPM and the offset of the first beat in milliseconds. If you don't know these values yet, try the following steps:
   - Open osu!, drag the audio file into the editor.
   - Use the timing setup panel to find the BPM and offset.
   - Insert these values into `config_generation.json` or, if using the GUI, enter them into the specific input fields.


## Training & Generation Pipeline
To configure training settings and start the pipeline, you can run this command:
```bash
python guiConfigEditor.py
```

Alternatively, only run the pipeline (without GUI):
```bash
python runPipeline.py
```

Using the GUI is highly recommended. You can use it to:
- Edit config files in a structured way.
- Browse for input / output paths.
- Trigger specific stages of the pipeline individually or collectively.


## Pipeline Steps
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
- `difficulty_range`: What beatmap difficulty-range should the model train on?
- `download_beatmapsets`: The amount of beatmapsets to download. (*Note: beatmapsets $\neq$ beatmaps $\rarr$ each beatmapset may contain more than one beatmap*)
- `note_precision`: How detailed are the beatmaps being processed / generated? This value should only be a power of 2. It works the following: On the lowest precision (= 1), every quarter note is being extracted from a beatmap-file and generated levels can only have notes placed on quarter notes. For the second level of precision (= 2), every eighth note is included, and so on.
- `prediction_threshold`: For which prediction values v $\in [0,1]$ should the model output generate a note?
- `sequence_length`: How long are the sequences that are saved during data preprocessing?
- `max_vram_mb`: If using the GPU during training, change this value to limit the amount of VRAM that is being used during model training.
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


## GUI Configuration Editor
To streamline configuration, run:

```bash
python guiConfigEditor.py
```

The editor is split into 3 tabs:

1. **Download & Preprocess Settings**
   - Beatmap downloader, preprocessor, raw/preprocessed paths.

2. **Sequence & Training Settings**
   - Sequence length, difficulty range, threshold, training toggle.

3. **Generation & Visualizer**
   - Audio file, BPM, start offset, visualizer file inputs.
   - Optional: Automatically run the visualizer after generation.

Each setting has an intuitive interface, and changes can be saved with:
- **Save Only**
- **Save and Run** (triggers `runPipeline.py`)
