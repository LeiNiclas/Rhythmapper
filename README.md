# osu!-mania level generator
This is an experimental project aiming to create osu!-mania beatmaps using an LSTM-model. Currently, models are only generating 4K-beatmap data.

## Directory structure:
```
root
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
|   |-- model.h5
|   `-- better_model.h5
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
1. numpy
2. pandas
3. tensorflow
4. sklearn
5. librosa

## Prerequisites (data)
1. You have an audio file ready to generate an osu!-mania level for.
2. The audio has a steady BPM.
3. You know the BPM and the timing (in milliseconds) of the first beat of the audio.


## Training pipeline
To get started, follow this procedure:
1. Run ```beatmapDownloader.py```. This will download the 1.000 most recent beatmapsets that contain at least one osu!-mania beatmap (regardless of keycount). (Note: this may take a while because of API-limitations of the osu!-direct API. Feel free to change the amount of beatmapsets to download.)
2. Run ```beatmapPreprocessor.py```. This will preprocess all downloaded beatmaps and categorize them into 6 difficulty ranges. (Note: this also may take a while because of API-limitations (needed for difficutly, mode and keycount check).)
3. Run ```dataSequenceSplitter.py```. This will split all preprocessed data into ```train``` and ```test``` sequences with respect to the given difficulties.
4. Run ```mfccNormalizer.py```. This will normalize the mfcc audio features from all ```train``` sequences and save it to ```mfcc_norm_stats.json``` in the ```root```-directory.
5. Run ```modelTrainer.py```. This will create a new model and train it on the sequence data.
6. Run ```levelGenerator.py```. This will generate a ```.osu``` file with HitObject timing data. You can paste this data into an already existing .osu!-file.

In the future, this process will be a little simpler and more user-friendly.
