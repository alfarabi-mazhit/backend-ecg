import tensorflow as tf
import os
from tensorflow.keras import layers
from keras.utils import custom_object_scope


class ModelManager:
    model = None

    @staticmethod
    def load_model(model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        ModelManager.model = tf.keras.models.load_model(model_path)
        print(f"Model loaded successfully from {model_path}")

    @staticmethod
    def predict(preprocessed_image):
        if ModelManager.model is None:
            raise RuntimeError("Model is not loaded. Please load the model first.")
        predictions = ModelManager.model.predict(preprocessed_image)
        return predictions
