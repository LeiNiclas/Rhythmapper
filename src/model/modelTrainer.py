import copy
import tensorflow as tf
import numpy as np
import os

from src.data_utils.dataSequenceLoader import get_difficulty_dataset
from src.model.lstmManiaModel import build_lstm_model
from keras._tf_keras.keras.callbacks import ModelCheckpoint, EarlyStopping


train_pattern = r"Z:\Programs\Python\osumania-levelgen\data\sequences\train\train_sequences_*.npy"
test_pattern = r"Z:\Programs\Python\osumania-levelgen\data\sequences\test\test_sequences_*.npy"

SEQUENCES_ROOT = "Z:\\Programs\\Python\\osumania-levelgen\\data\\sequences"
DATA_NOTE_PRECISION = 2 # beatscale = Quarter note / precision 
MODEL_SEQUENCE_LENGTH = 64
MODEL_TARGET_DIFFICULTY = "3-4_stars"


def split_X_y(batch):
    # X: all columns except first [subbeat_idx] and last 4, y: last 4 columns.
    return batch[:, :, 1:7], batch[:, :, 7:]



if __name__ == "__main__":
    # Create datasets.
    train_ds = get_difficulty_dataset(
        sequences_root=SEQUENCES_ROOT,
        difficulty=MODEL_TARGET_DIFFICULTY,
        split="train",
        batch_size=64
    )
    
    test_ds = get_difficulty_dataset(
        sequences_root=SEQUENCES_ROOT,
        difficulty=MODEL_TARGET_DIFFICULTY,
        split="test",
        batch_size=64
    )
    
    # Map to (X, y) pairs.
    train_ds = train_ds.map(split_X_y)
    test_ds = test_ds.map(split_X_y)
    
    # Build the model.
    sequence_length = MODEL_SEQUENCE_LENGTH
    num_features = 6
    output_dim = 4
    
    model = None
    
    checkpoint_callback = ModelCheckpoint(
        "checkpoint_model.keras",
        save_best_only=False,
        save_weights_only=False
    )
    
    early_stop = EarlyStopping(
        monitor="val_loss",
        patience=7,
        restore_best_weights=True
    )
    
    if not os.path.exists("checkpoint_model.keras"):
        model = build_lstm_model(input_shape=(sequence_length, num_features), output_dim=output_dim)
    else:
        model = tf.keras.models.load_model("checkpoint_model.keras")
    
    # Train the model using the test set for validation.
    model.fit(
        train_ds,
        validation_data = test_ds,
        epochs=100,
        steps_per_epoch=500,
        validation_steps=100,
        callbacks=[checkpoint_callback, early_stop]
    )
    
    model_code = f"{MODEL_TARGET_DIFFICULTY}-P{DATA_NOTE_PRECISION}-S{MODEL_SEQUENCE_LENGTH}"
    
    model.save(f"model-{model_code}.keras")

    
    # -------- Display feature importance --------
    X_val, y_val = next(iter(test_ds))
    X_val = X_val.numpy()
    y_val = y_val.numpy()
    
    baseline = tf.keras.losses.binary_crossentropy(y_val, model.predict(X_val)).numpy().mean()
    
    importances = []
    
    feature_names = ["mfcc0", "mfcc1", "mfcc2", "mfcc3", "mfcc4", "onset"]
    
    for i in range(X_val.shape[-1]):
        X_permuted = copy.deepcopy(X_val)
        flat = X_permuted[..., i].flatten()
        
        np.random.shuffle(flat)
        X_permuted[..., i] = flat.reshape(X_permuted[..., i].shape)
        score = tf.keras.losses.binary_crossentropy(y_val, model.predict(X_permuted)).numpy().mean()
        
        importances.append(score - baseline)
    
    print("Permutation feature importances:")
    
    for name, imp in zip(feature_names, importances):
        print(f"{name}: {imp:.5f}")
    # --------------------------------------------
