import tensorflow as tf
import os
from tensorflow.keras import layers
from keras.utils import custom_object_scope

# Attention Module
class AttentionModule(tf.keras.layers.Layer):
    def __init__(self, trainable=True, dtype="float32", **kwargs):
        super(AttentionModule, self).__init__(trainable=trainable, dtype=dtype, **kwargs)
        self.channel = None
        self.mlp = None
        self.spatial_conv = layers.Conv2D(1, kernel_size=7, activation="sigmoid", padding="same")

    def build(self, input_shape):
        self.channel = input_shape[-1]
        self.mlp = tf.keras.Sequential([
            layers.Dense(self.channel // 8, activation="relu"),
            layers.Dense(self.channel, activation="sigmoid"),
        ])

    def call(self, input_feature):
        # Channel Attention
        avg_pool = tf.reduce_mean(input_feature, axis=[1, 2], keepdims=True)
        max_pool = tf.reduce_max(input_feature, axis=[1, 2], keepdims=True)
        avg_out = self.mlp(avg_pool)
        max_out = self.mlp(max_pool)
        channel_scale = avg_out + max_out
        feature = input_feature * channel_scale

        # Spatial Attention
        avg_pool_spatial = tf.reduce_mean(feature, axis=-1, keepdims=True)
        max_pool_spatial = tf.reduce_max(feature, axis=-1, keepdims=True)
        concat = tf.concat([avg_pool_spatial, max_pool_spatial], axis=-1)
        spatial_scale = self.spatial_conv(concat)

        feature = feature * spatial_scale
        return feature


class ModelManager:
    model = None

    @staticmethod
    def load_model(model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        with custom_object_scope({"AttentionModule": AttentionModule}):
            ModelManager.model = tf.keras.models.load_model(model_path)
        print(f"Model loaded successfully from {model_path}")

    @staticmethod
    def predict(preprocessed_image):
        if ModelManager.model is None:
            raise RuntimeError("Model is not loaded. Please load the model first.")
        predictions = ModelManager.model.predict(preprocessed_image)
        return predictions
