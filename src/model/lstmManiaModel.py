import tensorflow as tf

from keras._tf_keras.keras.losses import BinaryFocalCrossentropy
from keras._tf_keras.keras.metrics import Recall, Precision


MODEL_SEQUENCE_LENGTH = 64


def build_lstm_model(input_shape: tuple, output_dim: int) -> tf.keras.Model:
    """
    Build and return a sequential LSTM model for osu!mania sequence generation.

    Args:
        input_shape (tuple): _Shape of the input sequence, e.g. (sequence_length, num_features)._
        output_dim (int): _Number of output units (e.g. 4 for 4 lanes)._

    Returns:
        tf.keras.Model: _The Compiled LSTM model._
    """
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=input_shape),
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(256, return_sequences=True)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(128, return_sequences=True)),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(64, activation='relu')),
        tf.keras.layers.TimeDistributed(tf.keras.layers.Dense(output_dim, activation='sigmoid'))
    ])
    
    model.compile(
        optimizer='adam',
        loss=BinaryFocalCrossentropy(gamma=1.5),
        metrics=[Recall(), Precision()]
    )
    
    return model

if __name__ == "__main__":
    num_features = 11
    output_dim = 4

    model = build_lstm_model(input_shape=(MODEL_SEQUENCE_LENGTH, num_features), output_dim=output_dim)
    model.summary()