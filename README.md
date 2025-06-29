# osu!-mania level generator
This is an experimental project aiming to create osu!-mania beatmaps using an LSTM-model. Currently, models are able to generate 4K-beatmap data.

## Directory structure:
```
root
|-- config.json # Configure beatmap and model settings here.
|-- runPipeline.py # Run this script for model and level generation.
|-- data
|   |-- audio # This is where to put audio files for level generation.
|   |   |-- test_audio.mp3
|   |   `-- another_test_audio.mp3
|   |-- preprocessed # Preprocessed beatmap data is stored here.
|   |   |-- 0-1_stars
|   |   |   |-- bm_12345678.csv
|   |   |   `-- bm_42314159.csv
|   |   |-- ...
|   |   |-- 4-5_stars # Same subfolder structure as 0-1_stars.
|   |   `--5_stars_plus # ^
|   |-- raw # Raw beatmap data.
|   `-- sequences # Generated sequence data is stored here.
|       |-- 0-1_stars
|       |   |-- train
|       |   `-- test
|       `-- ... # Same subfolder structure as in preprocessed with addition of train and test subfolders.
|-- models
|   |-- model.keras
|   `-- better_model.keras
`-- src
    |-- data_utils
    |   |-- dataSequenceLoader.py
    |   |-- dataSequenceSplitter.py
    |   `-- mfccNormalizer.py
    |-- download_utils
    |   |-- beatmapDownloader.py
    |   `-- rateLimitOptimizer.py
    |-- model
    |   |-- levelGenerator.py
    |   |-- lstmManiaModel.py
    |   `-- modelTrainer.py
    `-- preprocessing
        |-- beatmapFeatureExtractor.py
        |-- beatmapFilter.py
        `-- beatmapPreprocessor.py
```

## Prerequisites (python-libraries)
In order to run the scripts, you will need to have the following python-libraries installed:
- numpy
- pandas
- tensorflow
- sklearn
- librosa

## Prerequisites (level-generation)
Before generating a level, please make sure all of the following prerequisites apply.
1. You have an audio file ready to generate an osu!-mania level for and put it into the data/audio directory.
2. The audio has a steady BPM. This is mandatory for the level to make sense as the models are only trained on maps with a steady BPM.
3. You know the BPM and the timing (in milliseconds) of the first beat of the audio. If you don't know it, here's how I did it for some audios: Open osu! and drag-and-drop the file into the game. This will open the editor. Fill out the necessary parts of the map-creation GUI and go to the "<b>timing</b>" tab. Use the beat-calculation / -detection tool in the top-right area of the <b>"timings"</b> tab. Make sure the beat matches the audio from the first beat up until the end. If you have done everything correctly, you should have the correct BPM value ready as well as your start timing in milliseconds (which is the value in the "<b>Offset</b>" area).
4. Edit the ```audio_bpm``` and ```audio_start_ms``` settings in the ```config.json``` file.

## Training pipeline
To build models and generate levels, run the ```runPipeline.py``` script in the ```root```-directory, which can be customized through the ```config.json``` file. More info on the this file can be found in the [Configuration-file](#configuration-file) section.

The pipeline works as follows:
1. Run ```beatmapDownloader.py```. This will download the <b>N</b> most recent beatmapsets that contain at least one osu!-mania beatmap (<i>regardless</i> of keycount). The value of <b>N</b> can be changed in the ```config.json``` file. (<i>Note: this script may take a while because of API-limitations of the osu!-direct API. Feel free to change the amount of beatmapsets to download.</i>)
2. Run ```beatmapPreprocessor.py```. This will preprocess all downloaded beatmaps and categorize them into 6 difficulty ranges. (<i>Note: this also may take a while because of API-limitations (needed for difficutly, mode and keycount check).</i>)
3. Run ```dataSequenceSplitter.py```. This will split all preprocessed data into <b>train</b> and <b>test</b> sequences with respect to the given difficulties.
4. Run ```mfccNormalizer.py```. This will normalize the MFCC audio features from all <b>train</b> sequences and save it to ```mfcc_norm_stats.json``` in the ```root```-directory.
5. Run ```modelTrainer.py```. This will create a new model and train it on the sequence data.
6. Run ```levelGenerator.py```. This will generate a ```.osu``` file with HitObject timing data. You can paste this data into an already existing .osu!-file.

## Configuration-file
The ```config.json``` file contains several settings on beatmap-downloading, preprocessing and model-building.

### Beatmap data & Model settings 
- ```difficulty_range```: What beatmap difficulty-range should the model train on?
- ```download_beatmapsets```: How many beatmaps should be downloaded? This is NOT the final count of beatmaps, but rather the <i>raw</i> amount of beatmapsets <i>before</i> preprocessing.
- ```note_precision```: How detailed are the beatmaps being processed / generated? This value should only be a power of 2. It works the following: On the lowest precision (= 1), every quarter note is being extracted from a beatmap-file and generated levels can only have notes placed on quarter notes. For the second level of precision (= 2), every eighth note is included, and so on.
- ```prediction_threshold```: What is the threshold for model predictions to be counted as a note-placement?
- ```sequence_length```: How long are the sequences that are saved during data preprocessing?

### Level generation settings
- ```audio_bpm```: The BPM of the audio.
- ```audio_start_ms```: The time in milliseconds where the first beat occurs in the audio.

### Pipeline settings
- ```run_beatmap_downloader```: Should the beatmap downloader script be run?
- ```run_beatmap_preprocessor```: Should the beatmap preprocessor script be run?
- ```run_sequence_splitter```: Should the sequence splitter script be run?
- ```run_mfcc_normalizer```: Should the MFCC normalizer script be run?
- ```run_model_trainer```: Should the model trainer script be run?
- ```run_level_generator```: Should the level generator script be run?