import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 1. Project Directory Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
FIRMWARE_DIR = os.path.join(BASE_DIR, "firmware", "esp32_prefall_detector")
os.makedirs(MODELS_DIR, exist_ok=True)

# 2. Load Processed Dataset
MODE = "insole"
data_path = os.path.join(DATA_DIR, "X_insole_50hz.npy")
labels_path = os.path.join(DATA_DIR, "y_labels_50hz.npy")

if not os.path.exists(data_path):
    MODE = "wrist"
    data_path = os.path.join(DATA_DIR, "X_wrist_50hz.npy")

X = np.load(data_path)
y = np.load(labels_path)
model_name = f"{MODE}_fall_model"

print(f"Loaded {MODE} data: Raw Shape {X.shape}, Labels {y.shape}")

# Flatten: 50 timesteps * 6 channels = 300 flat features
X_flat = X.reshape((X.shape[0], -1)).astype(np.float32)
y = y.astype(np.float32)

# 3. Stratified Train-Validation Split
X_train, X_val, y_train, y_val = train_test_split(
    X_flat, y, test_size=0.20, random_state=42, stratify=y
)

num_inputs = X_train.shape[1]  # Exactly 300
print(f"Input features: {num_inputs} | Training records: {len(X_train)}")

# 4. Strict Version-1-Only TinyML Graph (Dense + ReLU only, Linear Logit Output)
def build_network(batch_size=None):
    if batch_size is not None:
        inputs = layers.Input(batch_shape=(batch_size, num_inputs))
    else:
        inputs = layers.Input(shape=(num_inputs,))

    x = layers.Dense(32, activation="relu")(inputs)
    x = layers.Dropout(0.20)(x)
    x = layers.Dense(16, activation="relu")(x)
    # Output raw linear logit directly: Eliminates LOGISTIC, SOFTMAX, and EXPAND_DIMS
    outputs = layers.Dense(1, activation=None)(x)

    return models.Model(inputs=inputs, outputs=outputs)

# Train model
train_model = build_network(batch_size=None)
train_model.compile(
    optimizer="adam",
    loss=tf.keras.losses.BinaryCrossentropy(from_logits=True),
    metrics=["accuracy"]
)
train_model.summary()

# 5. Model Training
print("\n--- Training Model ---")
early_stopping = EarlyStopping(
    monitor="val_loss",
    patience=8,
    restore_best_weights=True,
    verbose=1
)

train_model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=50,
    batch_size=64,
    callbacks=[early_stopping],
    verbose=1
)

# 6. Evaluation with C++ Emulated Sigmoid
logits = train_model.predict(X_val)
val_probs = 1.0 / (1.0 + np.exp(-logits))
val_preds = (val_probs > 0.5).astype(int).flatten()
print("\n--- Validation Performance Report ---")
print(classification_report(y_val, val_preds, target_names=["Normal", "Pre-Fall"]))

# 7. Build Static Model (batch_size=1) for TFLite Micro Conversion
deploy_model = build_network(batch_size=1)
deploy_model.set_weights(train_model.get_weights())

print("\n--- Quantizing to INT8 for ESP32 ---")

def representative_dataset_gen():
    for i in range(min(150, len(X_train))):
        sample = np.expand_dims(X_train[i], axis=0)  # (1, 300)
        yield [sample]

converter = tf.lite.TFLiteConverter.from_keras_model(deploy_model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset_gen
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]

# Keep input/output as float32 to let the TFLite runtime handle quant/dequant internally
# This prevents EloquentTinyML array type cast assertion panics on the ESP32
converter.inference_input_type = tf.float32
converter.inference_output_type = tf.float32

quantized_tflite_model = converter.convert()

tflite_path = os.path.join(MODELS_DIR, f"{model_name}_quant.tflite")
with open(tflite_path, "wb") as f:
    f.write(quantized_tflite_model)

size_kb = os.path.getsize(tflite_path) / 1024.0
print(f"\n[SUCCESS] Quantized Model Saved: {tflite_path}")
print(f"[SUCCESS] Model Size: {size_kb:.2f} KB")

# 8. Export to C Header Array (model_data.h)
def export_c_header(target_path):
    with open(target_path, "w") as f:
        f.write(f"// Auto-generated TinyML Model: {model_name}\n")
        f.write(f"// Size: {len(quantized_tflite_model)} bytes\n\n")
        f.write("#ifndef MODEL_DATA_H\n#define MODEL_DATA_H\n\n")
        f.write(f"const unsigned int fall_model_quant_len = {len(quantized_tflite_model)};\n")
        f.write("const unsigned char fall_model_quant_tflite[] = {\n    ")
        
        for i, byte in enumerate(quantized_tflite_model):
            f.write(f"0x{byte:02x}, ")
            if (i + 1) % 12 == 0:
                f.write("\n    ")
                
        f.write("\n};\n\n#endif // MODEL_DATA_H\n")
    print(f"[SUCCESS] C Header Synced: {target_path}")

export_c_header(os.path.join(MODELS_DIR, "model_data.h"))

if os.path.exists(FIRMWARE_DIR):
    export_c_header(os.path.join(FIRMWARE_DIR, "model_data.h"))