import tensorflow as tf

from src.data_utils.dataSequenceLoader import get_difficulty_dataset
from src.model.lstmManiaModel import build_lstm_model


train_pattern = r"Z:\Programs\Python\osumania-levelgen\data\sequences\train\train_sequences_*.npy"
test_pattern = r"Z:\Programs\Python\osumania-levelgen\data\sequences\test\test_sequences_*.npy"


def split_X_y(batch):
    # X: all columns except last 4, y: last 4 columns.
    return batch[:, :, :7], batch[:, :, 7:]



if __name__ == "__main__":
    sequences_root = "Z:\\Programs\\Python\\osumania-levelgen\\data\\sequences"
    target_difficulty = "4-5_stars"
    
    import numpy as np
    arr = np.load("Z:/Programs/Python/osumania-levelgen/data/sequences/4-5_stars/train/4-5_stars_train_sequences_1.npy", mmap_mode='r')
    y = arr[:, :, 7:]
    print("Lane note ratio:", np.mean(y))  # Should be >0.1 for balanced data
    
    # Create datasets.
    train_ds = get_difficulty_dataset(
        sequences_root=sequences_root,
        difficulty=target_difficulty,
        split="train",
        batch_size=64
    )
    
    test_ds = get_difficulty_dataset(
        sequences_root=sequences_root,
        difficulty=target_difficulty,
        split="test",
        batch_size=64
    )
    
    # Map to (X, y) pairs.
    train_ds = train_ds.map(split_X_y)
    test_ds = test_ds.map(split_X_y)
    
    # Build the model.
    sequence_length = 32
    num_features = 7
    output_dim = 4
    
    #model = build_lstm_model(input_shape=(sequence_length, num_features), output_dim=output_dim)
#
    ## Train the model using the test set for validation
    #model.fit(
    #    train_ds,
    #    validation_data = test_ds,
    #    epochs=20,
    #    steps_per_epoch=200,
    #    validation_steps=40
    #)
    #
    #model.save("mania_lstm_model_3.h5")
    
    print("\nEvaluating model predictions at different thresholds:")
    
    model = tf.keras.models.load_model("mania_lstm_model_3.h5", compile=False)
    
    for batch_x, batch_y in test_ds.take(1):
        y_pred = model.predict(batch_x)
        y_true = batch_y.numpy()
        
        for thresh in [0.45, 0.425, 0.4]:
            y_pred_bin = (y_pred > thresh).astype(int)
            
            true_positives = np.sum((y_pred_bin == 1) & (y_true == 1))
            predicted_positives = np.sum(y_pred_bin == 1)
            actual_positives = np.sum(y_true == 1)
            
            recall = true_positives / actual_positives if actual_positives > 0 else 0
            precision = true_positives / predicted_positives if predicted_positives > 0 else 0
            
            print(f"Threshold {thresh:.2f}: recall={recall:.3f}, precision={precision:.3f}, predicted notes={predicted_positives}, actual notes={actual_positives}")